from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

# Define parâmetros para os pedidos HTTP
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

# Cria funções auxiliares
def get_soup(url, headers=HEADERS):
    """Obtém objeto BeautifulSoup (soup) para o url dado."""
    reqopen = Request(url, headers=headers)
    req = urlopen(reqopen)
    soup = BeautifulSoup(req.read(), "html.parser")
    return soup


def get_events_urls():
    """Raspa URLs de todos os eventos da ANPUH."""
    pass


def get_event_id(event_url):
    """Extrai número do evento com base em seu URL."""
    pass
