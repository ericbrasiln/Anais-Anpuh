"""
Módulo depreciado — funcionalidade incorporada em script-anais-anpuh.py.
Mantido apenas para compatibilidade retroativa.
"""
import warnings
warnings.warn(
    "open_url está depreciado. Use as funções de script-anais-anpuh.py diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

def get_soup(url, headers=HEADERS):
    req = Request(url, headers=headers)
    resp = urlopen(req, timeout=30)
    return BeautifulSoup(resp.read(), "html.parser")