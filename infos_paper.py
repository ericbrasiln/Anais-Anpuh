"""
Módulo depreciado — funcionalidade incorporada em script-anais-anpuh.py.
Mantido apenas para compatibilidade retroativa.
"""
import warnings
warnings.warn(
    "infos_paper está depreciado. Use as funções de script-anais-anpuh.py diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

import os
import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

def sanitize_filename(name):
    name = name.strip().lower().replace("/", "-").replace(" ", "_")
    for c in ['"', '*', ':', '<', '>', '?', '/', "\\", '|', '@', '+', '...']:
        name = name.replace(c, "")
    return name[:200]

def get_links(paper, event_folder, title, previous_link, downloaded_urls=None):
    if downloaded_urls is None:
        downloaded_urls = set()
    try:
        link_pdf = paper.find('a', href=re.compile(r'(\.pdf)'))
        if not link_pdf:
            return
        link = link_pdf['href']
        if not link.lower().endswith('.pdf'):
            link += '.pdf'
        if link.startswith('https://'):
            full_link = link
        else:
            full_link = "https://anpuh.org.br" + link

        if full_link in downloaded_urls:
            return
        downloaded_urls.add(full_link)

        safe_title = sanitize_filename(title)
        full_name = os.path.join(event_folder, f"{safe_title}.pdf")

        if not os.path.exists(full_name):
            try:
                resp = requests.get(full_link, headers=HEADERS, timeout=60)
                resp.raise_for_status()
                with open(full_name, 'wb') as f:
                    f.write(resp.content)
            except Exception as e:
                print(f"Erro no download: {e}")
    except Exception as e:
        print(f"Erro ao processar paper: {e}")

def get_infos(paper_boxes, base_url, final_list, event_folder, previous_link, downloaded_urls=None):
    if downloaded_urls is None:
        downloaded_urls = set()
    for paper in paper_boxes:
        title = paper.h2.text.strip() if paper.h2 else ""
        info = {"autores": "", "titulo": title, "tipo": "", "evento": "", "ano": "", "file_link": ""}
        dts = paper.find_all('dt')
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
                a_tag = dd.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    if not href.lower().endswith('.pdf'):
                        href += '.pdf'
                    info["file_link"] = href if href.startswith('https://') else base_url + href
        final_list.append([info["autores"], info["titulo"], info["tipo"], info["evento"], info["ano"], info["file_link"]])
        get_links(paper, event_folder, info["titulo"], previous_link, downloaded_urls)