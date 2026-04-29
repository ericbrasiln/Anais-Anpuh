#!/usr/bin/env python3
"""
Scraper para os Anais dos Simpósios Nacionais de História, da Anpuh.
Autores: Eric Brasil, Leonardo Nascimento, Gabriel Andrade, Vitor Mussa
Atualizado para Python 3.12+ com argparse, filtro de simpósios, JSON output,
tratamento de erros e deduplicação de downloads.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

# ── Configuração ──────────────────────────────────────────────
BASE_URL = "https://anpuh.org.br"
ANALS_URL = "https://anpuh.org.br/index.php/documentos/anais"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}
OUTPUT_DIR = "Anais_Anpuh"

# ── Mapeamento Romano → Arábico ──────────────────────────────
ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20,
    "XXI": 21, "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25,
    "XXVI": 26, "XXVII": 27, "XXVIII": 28, "XXIX": 29, "XXX": 30,
    "XXXI": 31, "XXXII": 32, "XXXIII": 33, "XXXIV": 34, "XXXV": 35,
    "XXXVI": 36, "XXXVII": 37, "XXXVIII": 38, "XXXIX": 39, "XL": 40,
}

# ── Logging ───────────────────────────────────────────────────
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


# ── Funções de rede ───────────────────────────────────────────
def get_soup(url: str, retries: int = 3, backoff: float = 2.0) -> BeautifulSoup:
    """Obtém BeautifulSoup para um URL, com retry e backoff."""
    for attempt in range(1, retries + 1):
        try:
            logging.debug("GET %s (attempt %d/%d)", url, attempt, retries)
            req = Request(url, headers=HEADERS)
            resp = urlopen(req, timeout=30)
            return BeautifulSoup(resp.read(), "html.parser")
        except Exception as e:
            logging.warning("Erro ao acessar %s (tentativa %d): %s", url, attempt, e)
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise RuntimeError(f"Falha ao acessar {url} após {retries} tentativas: {e}") from e


def download_pdf(url: str, dest: Path, retries: int = 3, backoff: float = 2.0) -> bool:
    """Baixa PDF de um URL para dest. Retorna True se sucesso."""
    for attempt in range(1, retries + 1):
        try:
            logging.debug("Download %s -> %s (attempt %d)", url, dest.name, attempt)
            resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
            resp.raise_for_status()

            ct = resp.headers.get("Content-Type", "")
            if "pdf" not in ct and not url.lower().endswith(".pdf"):
                logging.warning("Content-Type inesperado para %s: %s", url, ct)

            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size = dest.stat().st_size
            if size < 100:
                logging.warning("PDF suspeito (muito pequeno, %d bytes): %s", size, dest)
                dest.unlink(missing_ok=True)
                return False

            logging.info("✓ Baixado: %s (%d KB)", dest.name, size // 1024)
            return True

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code == 404:
                logging.warning("✗ PDF não encontrado (404): %s", url)
                return False
            logging.warning("HTTP %d para %s (tentativa %d)", code, url, attempt)
        except Exception as e:
            logging.warning("Erro no download de %s (tentativa %d): %s", url, attempt, e)

        if attempt < retries:
            time.sleep(backoff * attempt)

    return False


# ── Parsear eventos da página principal ───────────────────────
def get_events(soup_home: BeautifulSoup) -> list[dict]:
    """Raspa a lista de eventos e retorna dicts com número arábico, romano, site_id e código SNH."""
    box = soup_home.find(id="cobalt-section-1")
    if not box:
        raise RuntimeError("Estrutura do site mudou: não encontrou #cobalt-section-1")

    links = box.find_all("a", href=re.compile(r"(1-anais-simposios-anpuh/)"))
    events = []

    for link in links:
        text = link.text.strip()
        href = link["href"]
        match = re.search(r"1-anais-simposios-anpuh/(.+)$", href)
        if not match:
            continue
        site_id = match.group(1)

        # Extrair o numeral romano do texto
        roman_match = re.match(r"^([IVXL]+)\b", text)
        roman_numeral = roman_match.group(1) if roman_match else ""
        arabic = ROMAN_MAP.get(roman_numeral.upper(), 0)

        # Sufixo como (C) ou (R) para eventos duplicados
        suffix_match = re.search(r"\(([CR])\)", text)
        suffix = suffix_match.group(1) if suffix_match else ""

        # Gerar código do evento: SNH-31, SNH-32, etc.
        event_code = f"SNH-{arabic}" if arabic else site_id

        events.append({
            "arabic": arabic,
            "roman": roman_numeral,
            "suffix": suffix,
            "site_id": site_id,
            "event_code": event_code,
            "text": text,
            "url": BASE_URL + href,
        })

    return events


# ── Filtrar eventos por número arábico ────────────────────────
def filter_events(events: list[dict], wanted: list[int] | None) -> list[dict]:
    """Filtra eventos pelo número arábico. Se wanted é None, retorna todos."""
    if not wanted:
        return events
    wanted_set = set(wanted)
    return [e for e in events if e["arabic"] in wanted_set]


# ── Extrair últimos nomes dos autores ─────────────────────────
def extract_last_names(authors: str) -> str:
    """Extrai os últimos nomes de cada autor a partir do campo 'Autor(es)'.
    
    Formatos comuns no site:
      'SILVA, João; SANTOS, Maria' → silva_santos
      'VIANNA, Eremildo Luiz.' → vianna
      's.a.' → sa
    
    A lógica: separar por ';' primeiro, depois para cada autor pegar a palavra
    antes da vírgula (sobrenome no formato 'SOBRENOME, Nome').
    """
    if not authors or not authors.strip():
        return "desconhecido"

    authors = authors.strip()
    
    # Caso especial: s.a. (sem autor)
    if authors.lower().replace(".", "").strip() in ("sa", "s/n", "n/a", "s/a"):
        return "sa"

    # Separar múltiplos autores por ';' 
    parts = [p.strip() for p in authors.split(";") if p.strip()]
    
    last_names = []
    for part in parts:
        # Formato 'SOBRENOME, Nome' — pegar o que vem antes da primeira vírgula
        if "," in part:
            last_name = part.split(",")[0].strip()
        else:
            # Sem vírgula: última palavra
            words = part.split()
            last_name = words[-1].strip() if words else ""
        
        # Limpar pontos
        last_name = last_name.rstrip(".")
        if last_name:
            last_names.append(last_name)

    if not last_names:
        return "desconhecido"

    result = "_".join(last_names)
    return sanitize_filename(result)


# ── Extrair papers de uma página de evento ────────────────────
def parse_paper(paper_box, event_code: str) -> dict | None:
    """Extrai metadados de um paper_box (has-context)."""
    title_tag = paper_box.h2
    if not title_tag:
        return None
    title = title_tag.text.strip()

    info = {
        "autores": "",
        "titulo": title,
        "tipo": "",
        "evento": event_code,
        "ano": "",
        "file_link": "",
    }

    dts = paper_box.find_all("dt")
    for dt in dts:
        label = dt.text.strip()
        dd = dt.find_next_sibling()
        if dd is None:
            continue

        if label == "Autor(es)":
            info["autores"] = dd.text.strip()
        elif label == "Tipo":
            info["tipo"] = dd.text.strip()
        elif label == "Evento":
            # Manter o código SNH-N se já tiver, senão usar o texto do site
            event_text = dd.text.strip()
            if event_text:
                info["evento"] = event_text
        elif label == "Ano":
            info["ano"] = dd.text.strip()
        elif label in ("Arquivo", "PDF LINK"):
            a_tag = dd.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                if not href.lower().endswith(".pdf"):
                    href += ".pdf"
                if href.startswith("https://"):
                    info["file_link"] = href
                else:
                    info["file_link"] = BASE_URL + href

    # Formatar evento como SNH-N
    if info["evento"] and not info["evento"].startswith("SNH-"):
        # Tentar extrair número do evento do texto
        ev_match = re.search(r"(\d+)°?\s*Simpósio", info["evento"])
        if ev_match:
            num = ev_match.group(1)
            info["evento"] = f"SNH-{num}"

    return info


def scrape_event(event: dict, output_dir: Path, downloaded_urls: set[str],
                 failed_downloads: list[dict], skip_download: bool = False) -> list[dict]:
    """Raspa todos os papers de um evento (incluindo paginação)."""
    event_url = event["url"]
    site_id = event["site_id"]
    event_code = event["event_code"]
    event_folder = output_dir / "PDF" / site_id

    all_papers = []
    page_num = 0

    while True:
        page_num += 1
        logging.info("📋 Evento %s — página %d", site_id, page_num)

        try:
            soup = get_soup(event_url)
        except RuntimeError as e:
            logging.error("Não foi possível acessar evento %s: %s", site_id, e)
            break

        paper_boxes = soup.find_all(class_="has-context")
        if not paper_boxes:
            logging.info("Nenhum paper encontrado na página %d de %s", page_num, site_id)
            break

        for box in paper_boxes:
            info = parse_paper(box, event_code)
            if info is None:
                continue
            all_papers.append(info)

            if skip_download:
                continue

            # Download do PDF
            file_link = info.get("file_link", "")
            if not file_link:
                logging.debug("Paper sem link de arquivo: %s", info["titulo"][:60])
                failed_downloads.append({
                    "titulo": info["titulo"],
                    "autores": info["autores"],
                    "motivo": "Sem link de arquivo",
                    "url": "",
                    "evento": event_code,
                })
                continue

            # Deduplicação por URL
            if file_link in downloaded_urls:
                logging.debug("PDF já baixado (URL duplicada): %s", file_link)
                continue
            downloaded_urls.add(file_link)

            # Nome do arquivo: últimos_nomes_autores_ano.pdf
            # Colisão de nome → sufixo _2, _3, etc.
            # Re-run → se arquivo já existe e é válido, pula download
            last_names = extract_last_names(info["autores"])
            year = info.get("ano", "")
            filename_parts = [last_names]
            if year:
                filename_parts.append(year)
            base_name = "_".join(filename_parts)

            dest = event_folder / f"{base_name}.pdf"
            counter = 2
            while dest.exists():
                if dest.stat().st_size > 100:
                    # Arquivo válido já existe — verificar se é mesmo URL ou outro autor
                    # Se é o primeiro colidente (counter==2), tentar nome com sufixo
                    # Se o sufixo também existe, continuar incrementando
                    filename = f"{base_name}_{counter}.pdf"
                    dest = event_folder / filename
                    counter += 1
                else:
                    # Arquivo corrompido — remover e reusar este nome
                    dest.unlink(missing_ok=True)
                    break

            # Se após resolver colisão o arquivo existe (válidos já preenchidos até o fim),
            # significa que todos os nomes com esse base já foram baixados — pular
            if dest.exists():
                logging.debug("Todos os nomes para '%s' já existem — pulando.", base_name)
                continue

            success = download_pdf(file_link, dest)
            if not success:
                failed_downloads.append({
                    "titulo": info["titulo"],
                    "autores": info["autores"],
                    "motivo": "Falha no download",
                    "url": file_link,
                    "evento": event_code,
                })

        # Paginação
        pagination = soup.find(class_="pagination")
        if not pagination:
            break

        next_pag = pagination.find("a", title=re.compile(r"(Próx)"))
        if next_pag and next_pag.get("href"):
            event_url = BASE_URL + next_pag["href"]
        else:
            break

    logging.info("Evento %s: %d papers, %d páginas", site_id, len(all_papers), page_num)
    return all_papers


# ── Utilidades ────────────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    """Limpa um texto para uso como nome de arquivo."""
    name = name.strip().lower().replace("/", "-").replace(" ", "_")
    chars_to_remove = ['"', '*', ':', '<', '>', '?', '/', "\\", '|', '@', '+', '...', '.', ',']
    for c in chars_to_remove:
        name = name.replace(c, "")
    if len(name) > 200:
        name = name[:200]
    return name


def get_timestamp() -> str:
    """Retorna timestamp formatado para nomes de arquivo: YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_outputs(papers: list[dict], output_format: str = "csv", output_dir: Path = None):
    """Salva os metadados em CSV e/ou JSON com timestamp no nome."""
    if not papers:
        logging.warning("Nenhum paper coletado — nenhum arquivo de saída gerado.")
        return

    ts = get_timestamp()
    df = pd.DataFrame(papers)
    df.columns = ["Autor(es)/Instituições", "Título", "Tipo", "Evento", "Ano", "Link do Arquivo"]

    base_dir = output_dir or Path(".")

    if output_format in ("csv", "both"):
        csv_path = base_dir / f"anais-anpuh-infos_{ts}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logging.info("📄 CSV salvo: %s (%d registros)", csv_path, len(df))

    if output_format in ("json", "both"):
        json_path = base_dir / f"anais-anpuh-infos_{ts}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        logging.info("📄 JSON salvo: %s (%d registros)", json_path, len(papers))

    return ts


def save_report(args: argparse.Namespace, papers: list[dict],
                downloaded_urls: set[str], failed_downloads: list[dict],
                filtered_events: list[dict], output_dir: Path, ts: str):
    """Gera relatório em TXT com parâmetros da coleta e lista de PDFs não baixados."""
    report_path = output_dir / f"relatorio_coleta_{ts}.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("=" * 60)
    lines.append("RELATÓRIO DE COLETA — Anais-Anpuh")
    lines.append("=" * 60)
    lines.append(f"Data/hora: {now}")
    lines.append("")

    # Parâmetros da coleta
    lines.append("--- PARÂMETROS ---")
    lines.append(f"Formato de saída: {args.format}")
    lines.append(f"Diretório de saída: {args.output}")
    lines.append(f"Modo verbose: {'Sim' if args.verbose else 'Não'}")
    lines.append(f"Sem download de PDFs: {'Sim' if args.no_download else 'Não'}")
    simp_text = ", ".join(args.simpósios) if args.simpósios else "Todos"
    lines.append(f"Simpósios filtrados: {simp_text}")
    lines.append("")

    # Eventos raspados
    lines.append("--- EVENTOS RASPADOS ---")
    for e in filtered_events:
        lines.append(f"  {e['event_code']} ({e['roman']}) — {e['site_id']}")
    lines.append("")

    # Resumo
    lines.append("--- RESUMO ---")
    lines.append(f"Total de papers catalogados: {len(papers)}")
    lines.append(f"PDFs baixados com sucesso: {len(downloaded_urls) if not args.no_download else 0}")
    lines.append(f"PDFs não baixados: {len(failed_downloads)}")
    lines.append("")

    # Papers sem PDF / falhas
    if failed_downloads:
        lines.append("--- PDFs NÃO BAIXADOS ---")
        for i, f in enumerate(failed_downloads, 1):
            lines.append(f"  {i}. [{f['evento']}] {f['titulo'][:70]}")
            lines.append(f"     Autores: {f['autores'][:60]}")
            lines.append(f"     Motivo: {f['motivo']}")
            if f['url']:
                lines.append(f"     URL: {f['url']}")
            lines.append("")
    else:
        lines.append("--- PDFs NÃO BAIXADOS ---")
        lines.append("  Nenhum")
        lines.append("")

    lines.append("=" * 60)
    lines.append("Fim do relatório")
    lines.append("=" * 60)

    with open(report_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    logging.info("📋 Relatório salvo: %s", report_path)


# ── CLI ───────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper dos Anais dos Simpósios Nacionais de História (ANPUH)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                              # Baixa todos os simpósios
  %(prog)s -s 31 32                     # Baixa apenas os simpósios 31 (XXXI) e 32 (XXXII)
  %(prog)s -s 26-30                     # Baixa simpósios 26 a 30
  %(prog)s -s 31 32 -f json             # Output apenas em JSON
  %(prog)s -s 31 -f both -v             # Output CSV+JSON, modo verbose
  %(prog)s --list                       # Lista todos os simpósios disponíveis
        """,
    )
    parser.add_argument(
        "-s", "--simpósios",
        nargs="+",
        type=str,
        help="Números dos simpósios (arábicos). Ex: 31 32 ou 26-30 para intervalo.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["csv", "json", "both"],
        default="csv",
        help="Formato de saída dos metadados (padrão: csv)",
    )
    parser.add_argument(
        "-o", "--output",
        default=OUTPUT_DIR,
        help=f"Diretório de saída (padrão: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_events",
        help="Lista todos os simpósios disponíveis e sai.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Modo verbose (debug).",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Não baixa PDFs, apenas coleta metadados.",
    )
    return parser.parse_args()


def parse_simpósios_arg(args: list[str]) -> list[int]:
    """Parseia a lista de números de simpósios do argumento -s.
    Suporta números individuais (31 32) e intervalos (26-30).
    """
    result = set()
    for item in args:
        if "-" in item and not item.startswith("-"):
            parts = item.split("-", 1)
            try:
                start, end = int(parts[0]), int(parts[1])
                result.update(range(start, end + 1))
            except ValueError:
                logging.warning("Intervalo inválido ignorado: %s", item)
        else:
            try:
                result.add(int(item))
            except ValueError:
                logging.warning("Número inválido ignorado: %s", item)
    return sorted(result)


# ── Main ──────────────────────────────────────────────────────
def main():
    args = parse_args()
    setup_logging(args.verbose)

    # 1. Acessar página principal
    logging.info("Acessando página dos Anais da ANPUH...")
    soup_home = get_soup(ANALS_URL)

    # 2. Obter lista de eventos
    events = get_events(soup_home)
    logging.info("Encontrados %d simpósios no site.", len(events))

    # 3. Se --list, mostrar e sair
    if args.list_events:
        print(f"\n{'Nº':>3}  {'Romano':<8}  {'Código':<8}  {'Site ID':<12}  Descrição")
        print("-" * 80)
        for e in sorted(events, key=lambda x: x["arabic"]):
            print(f"{e['arabic']:>3}  {e['roman']:<8}  {e['event_code']:<8}  {e['site_id']:<12}  {e['text']}")
        print(f"\nTotal: {len(events)} simpósios")
        return

    # 4. Filtrar eventos
    wanted = None
    if args.simpósios:
        wanted = parse_simpósios_arg(args.simpósios)
        logging.info("Filtro: simpósios %s", wanted)
        available = {e["arabic"] for e in events}
        missing = set(wanted) - available
        if missing:
            logging.warning("Simpósios não encontrados no site: %s", sorted(missing))

    filtered = filter_events(events, wanted)
    if not filtered:
        logging.error("Nenhum simpósio encontrado para os filtros informados.")
        sys.exit(1)

    logging.info("Serão raspados %d simpósios.", len(filtered))

    # 5. Criar diretório de saída
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 6. Raspagem
    all_papers = []
    downloaded_urls: set[str] = set()
    failed_downloads: list[dict] = []

    for i, event in enumerate(filtered, 1):
        logging.info("[%d/%d] Raspando: %s", i, len(filtered), event["text"])
        event_papers = scrape_event(
            event, output_dir, downloaded_urls, failed_downloads,
            skip_download=args.no_download
        )
        all_papers.extend(event_papers)

        if not args.no_download:
            if i < len(filtered):
                time.sleep(1)

    # 7. Salvar outputs de metadados com timestamp
    ts = save_outputs(all_papers, args.format, output_dir)

    # 8. Gerar relatório
    if ts:
        save_report(args, all_papers, downloaded_urls, failed_downloads,
                     filtered, output_dir, ts)
    else:
        ts = get_timestamp()
        save_report(args, all_papers, downloaded_urls, failed_downloads,
                     filtered, output_dir, ts)

    logging.info("🏁 Concluído! %d papers catalogados, %d PDFs baixados, %d falhas.",
                 len(all_papers),
                 len(downloaded_urls) if not args.no_download else 0,
                 len(failed_downloads))


if __name__ == "__main__":
    main()