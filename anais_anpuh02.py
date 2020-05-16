from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
import re

dicionario = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

urlbase = 'https://anpuh.org.br'
url = 'https://anpuh.org.br/index.php/documentos/anais'

reqopen = Request(url, headers=dicionario)
req = urlopen(reqopen)
bs = BeautifulSoup(req.read(), 'lxml')
boxAnais = bs.find(id='cobalt-section-1')
links = boxAnais.find_all('a', href=re.compile(r'(1-anais-simposios-anpuh/)'))
print(links)
for linkAnais in links:
    linkEvento = linkAnais['href']     
    linkEventoFinal = urlbase + linkEvento
    print (linkEventoFinal)
