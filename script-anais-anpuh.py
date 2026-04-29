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

# ── Mapeamento Romano → Arábico + site_ids ────────────────────
# Preenchido dinamicamente raspando a página principal,
# mas mantemos funções de conversão para o filtro do usuário.

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
                return False  # não adianta tentar de novo
            logging.warning("HTTP %d para %s (tentativa %d)", code, url, attempt)
        except Exception as e:
            logging.warning("Erro no download de %s (tentativa %d): %s", url, attempt, e)

        if attempt < retries:
            time.sleep(backoff * attempt)

    return False


# ── Parsear eventos da página principal ───────────────────────
def get_events(soup_home: BeautifulSoup) -> list[dict]:
    """Raspa a lista de eventos e retorna dicts com número arábico, romano e site_id."""
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

        events.append({
            "arabic": arabic,
            "roman": roman_numeral,
            "suffix": suffix,
            "site_id": site_id,
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


# ── Extrair papers de uma página de evento ────────────────────
def parse_paper(paper_box) -> dict | None:
    """Extrai metadados de um paper_box (has-context)."""
    title_tag = paper_box.h2
    if not title_tag:
        return None
    title = title_tag.text.strip()

    info = {
        "autores": "",
        "titulo": title,
        "tipo": "",
        "evento": "",
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
            info["evento"] = dd.text.strip()
        elif label == "Ano":
            info["ano"] = dd.text.strip()
        elif label in ("Arquivo", "PDF LINK"):
            a_tag = dd.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                # Garantir que o link termina com .pdf
                if not href.lower().endswith(".pdf"):
                    href += ".pdf"
                if href.startswith("https://"):
                    info["file_link"] = href
                else:
                    info["file_link"] = BASE_URL + href

    return info


def scrape_event(event: dict, output_dir: Path, downloaded_urls: set[str], skip_download: bool = False) -> list[dict]:
    """Raspa todos os papers de um evento (incluindo paginação)."""
    event_url = event["url"]
    site_id = event["site_id"]
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
            info = parse_paper(box)
            if info is None:
                continue
            all_papers.append(info)

            if skip_download:
                continue

            # Download do PDF
            file_link = info.get("file_link", "")
            if not file_link:
                logging.debug("Paper sem link de arquivo: %s", info["titulo"][:60])
                continue

            # Deduplicação por URL
            if file_link in downloaded_urls:
                logging.debug("PDF já baixado (URL duplicada): %s", file_link)
                continue
            downloaded_urls.add(file_link)

            # Deduplicação por arquivo existente
            safe_title = sanitize_filename(info["titulo"])
            dest = event_folder / f"{safe_title}.pdf"
            if dest.exists():
                logging.debug("Arquivo já existe: %s", dest.name)
                continue

            download_pdf(file_link, dest)

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
    """Limpa um título para uso como nome de arquivo."""
    name = name.strip().lower().replace("/", "-").replace(" ", "_")
    chars_to_remove = ['"', '*', ':', '<', '>', '?', '/', "\\", '|', '@', '+', '...']
    for c in chars_to_remove:
        name = name.replace(c, "")
    # Truncar para evitar nomes muito longos
    if len(name) > 200:
        name = name[:200]
    return name


def save_outputs(papers: list[dict], output_format: str = "csv"):
    """Salva os metadados em CSV e/ou JSON."""
    if not papers:
        logging.warning("Nenhum paper coletado — nenhum arquivo de saída gerado.")
        return

    df = pd.DataFrame(papers)
    df.columns = ["Autor(es)/Instituições", "Título", "Tipo", "Evento", "Ano", "Link do Arquivo"]

    if output_format in ("csv", "both"):
        csv_path = "anais-anpuh-infos.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logging.info("📄 CSV salvo: %s (%d registros)", csv_path, len(df))

    if output_format in ("json", "both"):
        json_path = "anais-anpuh-infos.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        logging.info("📄 JSON salvo: %s (%d registros)", json_path, len(papers))


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
    """Parseia a lista de números/arquivos de simpósios do argumento -s.
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
        print(f"\n{'Nº':>3}  {'Romano':<8}  {'Site ID':<12}  Descrição")
        print("-" * 70)
        for e in sorted(events, key=lambda x: x["arabic"]):
            suff = f" ({e['suffix']})" if e["suffix"] else ""
            print(f"{e['arabic']:>3}  {e['roman']:<8}  {e['site_id']:<12}  {e['text']}")
        print(f"\nTotal: {len(events)} simpósios")
        return

    # 4. Filtrar eventos
    wanted = None
    if args.simpósios:
        wanted = parse_simpósios_arg(args.simpósios)
        logging.info("Filtro: simpósios %s", wanted)
        # Verificar se todos existem
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

    for i, event in enumerate(filtered, 1):
        logging.info("[%d/%d] Raspando: %s", i, len(filtered), event["text"])
        event_papers = scrape_event(event, output_dir, downloaded_urls, skip_download=args.no_download)
        all_papers.extend(event_papers)

        if not args.no_download:
            # Pequena pausa entre eventos para não sobrecarregar o servidor
            if i < len(filtered):
                time.sleep(1)

    # 7. Salvar outputs de metadados
    # Mudar para o diretório de saída para salvar os arquivos lá
    os.chdir(output_dir)
    save_outputs(all_papers, args.format)

    logging.info("🏁 Concluído! %d papers catalogados, %d PDFs baixados.",
                 len(all_papers), len(downloaded_urls))


if __name__ == "__main__":
    main()