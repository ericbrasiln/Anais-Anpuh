from urllib.request import Request, urlopen, urlretrieve
from bs4 import BeautifulSoup
from urllib import request
import re
import os
import urllib
import pandas as pd
import requests
import wget

dicionario = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
urlbase = 'https://anpuh.org.br'
url = 'https://anpuh.org.br/index.php/documentos/anais'

listaFinal =[]
linkAnterior = ""
# Acessa a página inicial dos Anais.
reqopen = Request(url, headers=dicionario)
req = urlopen(reqopen)
bs = BeautifulSoup(req.read(), 'lxml')
# Define e cria a pasta para salvar cada evento.
print('Criando pasta de salvamento...')
pasta = os.path.join('Anais  Anpuh', 'pdf')
if not os.path.exists(pasta):
    os.makedirs(pasta)
#Define os links para cada evento.
print('Criando a lista de eventos a partir da página principal...')
boxAnais = bs.find(id='cobalt-section-1')
links = boxAnais.find_all('a', href=re.compile(r'(1-anais-simposios-anpuh/)'))
for linkAnais in links:
    acabou = False
    linkEvento = linkAnais['href']     
    linkEventoFinal = urlbase + linkEvento    
    numEvento = linkEvento.replace('index.php/documentos/anais/category-items/1-anais-simposios-anpuh/','')    
    # Acessa as páginas de cada evento e raspa os pdfs.
    while acabou == False:
        response = request.urlopen(linkEventoFinal).read()
        soup= BeautifulSoup(response, "html.parser")             
        #Encontra a caixa com os papers
        paperBoxes = soup.find_all(class_='has-context')
        print('Encontrando todos os papers da página...')
        pastaEvento = os.path.join(pasta, numEvento[1:])
        print('Encontrando todos as informações dos papers da página...')
            
        if not os.path.exists(pastaEvento):
            os.makedirs(pastaEvento)
        for paper in paperBoxes:    
            # Encontra os títulos de cada paper.
            title = paper.h2.text
            title = title.strip().lower().replace('/','-')

            informacoes = paper.find_all('dt')
            tipo = ""
            evento = ""
            ano = ""
            autores = ""
            linkArquivo = ""
            for informacao in informacoes:
                if informacao.text.strip() == "Tipo":
                    tipo = informacao.find_next_sibling().text.strip()
                    print (f"Tipo : {tipo}")
                if informacao.text.strip() == "Evento":
                    evento = informacao.find_next_sibling().text.strip()
                    print (f"Evento : {evento}")
                if informacao.text.strip() == "Ano":
                    ano = informacao.find_next_sibling().text.strip()
                    print (f"Ano : {ano}")
                if informacao.text.strip() == "Arquivo":
                    arquivo = informacao.find_next_sibling().a['href']
                    linkArquivo = urlbase + arquivo
                    print (f"Arquivo : {linkArquivo}")
                if informacao.text.strip() == "PDF LINK":
                    arquivo = informacao.find_next_sibling().a['href']
                    if arquivo.startswith('https://') == True:
                        linkArquivo = arquivo
                        print (f"Arquivo : {linkArquivo}")
                    else:
                        linkArquivo = urlbase + arquivo
                        print (f"Arquivo : {linkArquivo}")
                if informacao.text.strip() == "Autor(es)":
                    autores = informacao.find_next_sibling().text.strip()
                    print (f"Autor(es) : {autores}")
            listaInterna = [autores, title, tipo, evento, ano, linkArquivo]
            listaFinal.append(listaInterna)

            # Encontra os links para os pdfs.
            print('Encontrando link do paper...')
            try:
                arquivolink = paper.find('a',href=re.compile(r'(.pdf)'))
                link = arquivolink['href']
                if not link in linkAnterior:
                    linkAnterior = link
                    if link.startswith('https://'):
                        fullLink = link
                        fullName = os.path.join(pastaEvento, title.replace(' ','_') + '.pdf')
                    else:
                        fullLink = "https://anpuh.org.br" + link            
                        alterar = ['"', '*', ':', '<', '>', '?', '/', "\\", '|' , '_' , '@' , '+', '...']
                        for x in alterar:
                            title = title.replace(x, '')
                        fullName = os.path.join(pastaEvento, title.replace(' ','_') + '.pdf')
                    if not os.path.exists(fullName):
                        print('Salvando o pdf na pasta...\n')
                        try:
                            #request.urlretrieve(fullLink, fullName)
                            wget.download(fullLink, out=fullName)
                        except Exception as e:
                            print(e)
                    else:
                        print("Arquivo já existe.")
                else:
                    print("PDF desse paper é igual ao do paper anterior.")
            except Exception as e:
                print (e)
                link = paper.find('a', href=re.compile(r'(.pdf)'))
                link = None
                print('Paper sem pdf disponível para download.')
        # Busca a próxima página de papers.
        menuFinal = soup.find(class_='pagination')
        print('Procurando pŕoxima página...')
        try:
            proximaPag = menuFinal.find('a', title=re.compile(r'(Próx)'))
            linkProximaPag = proximaPag['href']
            print(numEvento)
            print('Página encontrada: https://anpuh.org.br' + linkProximaPag)
            linkEventoFinal = 'https://anpuh.org.br' + linkProximaPag
        except:                        
            print("Final das Páginas de Papers desse evento.")
            acabou = True
print('Salvando arquivo .csv com todas as informações: autores/instituições, título, tipo, evento, ano, link do pdf')
df = pd.DataFrame(listaFinal, columns=['Autor(es)/Instituições', 'Título', 'Tipo', 'Evento', 'Ano', 'Link do Arquivo'])
df.to_csv('anais-anpuh-infos.csv')
print('Raspagem completa.')
