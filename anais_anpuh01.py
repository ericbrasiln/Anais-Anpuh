from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
import pandas

urlbase = 'https://anpuh.org.br'
urlinicial = 'https://anpuh.org.br/index.php/documentos/anais'

dicionario = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}

req = Request(urlinicial, headers=dicionario)
req = urlopen(req)
bs = BeautifulSoup(req.read(), 'lxml')
acabou = False

boxDeItens = bs.find(id='cobalt-section-1')
itens = boxDeItens.find_all(class_='span3 category-box')

for anais in itens:   
    imagem = anais.find(class_='category_icon')['src']
    link = urlbase + anais.h4.a['href']
    títuloDosAnais = anais.h4.text

    while acabou == False:    
        req = urlopen(link)
        paginaDosAnais = BeautifulSoup(req.read(), 'lxml')
        papers = paginaDosAnais.find_all(class_='has-context')
        for paper in papers:
            título = paper.h2.text
            linkPdf = paper.find('li').a['href']
            print(urlbase + linkPdf)
        try:
            #TENTA EXECUTAR ISSO
            proximaPagina = paginaDosAnais.find(title='Próx')
            if proximaPagina == True:
                link = proximaPagina['href']
            print('Passando para a próxima página...')
        except:
            #SE DER ERRO VEM PRA CÁ
            acabou = True
            print('Página não foi encontrada!')
            