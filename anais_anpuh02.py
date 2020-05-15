from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
import pandas

dicionario = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

urlbase = 'https://anpuh.org.br/documentos/anais/category-items/1-anais-simposios-anpuh/{}'
opção = input('Insira a opção de Anais para raspar a partir da lista abaixo:\n'
'2019, Recife: 1\n'
'2017, Brasília: 2\n')
if opção == '1':
    opção = '35-snh29'
else:
    opção = '34-snh28'
urlanais = urlbase.format(opção)

print(urlanais)

reqopen = Request(urlanais, headers=dicionario)
req = urlopen(reqopen)
bs = BeautifulSoup(req.read(), 'lxml')
acabou = False

#while acabou == False:    
boxPapers = bs.find(id='cobalt-section-1')
papers = boxPapers.find_all(class_='has-context')
for paper in papers:
    título = paper.h2.text
    pdf = paper.find('li').a['href']
    linkPdf = 'https://anpuh.org.br/'+pdf
    print(linkPdf)
    