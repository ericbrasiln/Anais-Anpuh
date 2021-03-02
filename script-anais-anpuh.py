from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import wget

# Define parâmetros para os pedidos HTTP
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
BASE_URL = 'https://anpuh.org.br'
URL = 'https://anpuh.org.br/index.php/documentos/anais'


# Cria funções auxiliares
def get_soup(url, headers=HEADERS):
    """Obtém objeto BeautifulSoup (soup) para o url dado."""
    reqopen = Request(url, headers=headers)
    req = urlopen(reqopen)
    soup = BeautifulSoup(req.read(), "html.parser")
    return soup


def make_new_folder(*paths):
    """Cria diretório caso ele ainda não exista e retorna o path
    correspondente."""
    folder_path = os.path.join(*paths)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def get_events_urls():
    """Raspa URLs de todos os eventos da ANPUH."""
    pass


def get_event_id(event_url):
    """Extrai número do evento com base em seu URL."""
    pass


# Cria variáveis auxiliares
lista_final = []
link_anterior = ""

# Acessa a página inicial dos Anais.
soup_home = get_soup(URL)

# Define e cria a pasta para salvar cada evento.
print('Criando pasta de salvamento...')
pasta = make_new_folder('Anais Anpuh', 'pdf')

# Define os links para cada evento.
print('Criando a lista de eventos a partir da página principal...')
box_anais = soup_home.find(id='cobalt-section-1')
links = box_anais.find_all('a', href=re.compile(r'(1-anais-simposios-anpuh/)'))

for link_anais in links:
    acabou = False
    link_evento = link_anais['href']     
    link_evento_final = BASE_URL + link_evento    
    id_evento = link_evento.replace('index.php/documentos/anais/category-items/1-anais-simposios-anpuh/','')[1:]    
    
    # Acessa as páginas de cada evento e raspa os pdfs.
    while acabou == False:
        soup_eventos = get_soup(link_evento_final)
        
        #Encontra a caixa com os papers
        paper_boxes = soup_eventos.find_all(class_='has-context')
        print('Encontrando todos os papers da página...')
        pasta_evento = make_new_folder(pasta, id_evento)
        print('Encontrando todos as informações dos papers da página...')    
        
        for paper in paper_boxes:    
            # Encontra os títulos de cada paper.
            title = paper.h2.text
            title = title.strip().lower().replace('/','-')

            informacoes = paper.find_all('dt')
            tipo = ""
            evento = ""
            ano = ""
            autores = ""
            link_arquivo = ""

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
                    link_arquivo = BASE_URL + arquivo
                    print (f"Arquivo : {link_arquivo}")
                if informacao.text.strip() == "PDF LINK":
                    arquivo = informacao.find_next_sibling().a['href']
                    if arquivo.startswith('https://') == True:
                        link_arquivo = arquivo
                        print (f"Arquivo : {link_arquivo}")
                    else:
                        link_arquivo = BASE_URL + arquivo
                        print (f"Arquivo : {link_arquivo}")
                if informacao.text.strip() == "Autor(es)":
                    autores = informacao.find_next_sibling().text.strip()
                    print (f"Autor(es) : {autores}")
            
            lista_interna = [autores, title, tipo, evento, ano, link_arquivo]
            lista_final.append(lista_interna)

            # Encontra os links para os pdfs.
            print('Encontrando link do paper...')
            try:
                arquivo_link = paper.find('a',href=re.compile(r'(.pdf)'))
                link = arquivo_link['href']
                if not link in link_anterior:
                    link_anterior = link
                    if link.startswith('https://'):
                        full_link = link
                        full_name = os.path.join(pasta_evento, title.replace(' ','_') + '.pdf')
                    else:
                        full_link = "https://anpuh.org.br" + link            
                        alterar = ['"', '*', ':', '<', '>', '?', '/', "\\", '|' , '_' , '@' , '+', '...']
                        for x in alterar:
                            title = title.replace(x, '')
                        full_name = os.path.join(pasta_evento, title.replace(' ','_') + '.pdf')
                    if not os.path.exists(full_name):
                        print('Salvando o pdf na pasta...\n')
                        try:
                            wget.download(full_link, out=full_name)
                        except Exception as e:
                            print(e)
                    else:
                        print("Arquivo já existe.")
                else:
                    print("PDF desse paper é igual ao do paper anterior.")
            
            except Exception as e:
                print(e)
                link = paper.find('a', href=re.compile(r'(.pdf)'))
                link = None
                print('Paper sem pdf disponível para download.')
        
        # Busca a próxima página de papers.
        menu_final = soup_eventos.find(class_='pagination')
        print('Procurando pŕoxima página...')

        try:
            proxima_pag = menu_final.find('a', title=re.compile(r'(Próx)'))
            link_proxima_pag = proxima_pag['href']
            print(id_evento)
            print('Página encontrada: https://anpuh.org.br' + link_proxima_pag)
            link_evento_final = 'https://anpuh.org.br' + link_proxima_pag
        except:                        
            print("Final das Páginas de Papers desse evento.")
            acabou = True

# Exporta CSV com informações gerais dos papers.
print('Salvando arquivo .csv com todas as informações: autores/instituições, título, tipo, evento, ano, link do pdf')
df = pd.DataFrame(lista_final, columns=['Autor(es)/Instituições', 'Título', 'Tipo', 'Evento', 'Ano', 'Link do Arquivo'])
df.to_csv('anais-anpuh-infos.csv')
print('Raspagem completa.')
