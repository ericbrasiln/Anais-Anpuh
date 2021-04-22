"""
Scraper para os Anais dos Simpósios Nacionais de História, da Anpuh.
Autores: Eric Brasil, Leonardo Nascimento, Gabriel Andrade, Vitor Mussa
"""
from open_url import get_soup,get_events_urls,get_event_id
from outputs import  make_new_folder,csv_file
from infos_paper import get_infos
import re

# Define parâmetros para os pedidos HTTP
BASE_URL = 'https://anpuh.org.br'
URL = 'https://anpuh.org.br/index.php/documentos/anais'

# Cria variáveis auxiliares
final_list = []
previous_link = ""

# Acessa a página inicial dos Anais.
soup_home = get_soup(URL)

# Define e cria a pasta para salvar cada evento.
print('Criando pasta de salvamento...')
folder = make_new_folder('Anais_Anpuh', 'PDF')

# Define os links para cada evento.
print('Criando a lista de eventos a partir da página principal...')
box_anais = soup_home.find(id='cobalt-section-1')
links = box_anais.find_all('a', href=re.compile(r'(1-anais-simposios-anpuh/)'))

for link_anais in links:
    control = False
    event_link = link_anais['href']     
    final_event_link = BASE_URL + event_link    
    event_id = event_link.replace('index.php/documentos/anais/category-items/1-anais-simposios-anpuh/','')[1:]    
    
    # Acessa as páginas de cada evento e raspa os pdfs.
    while control == False:
        soup_eventos = get_soup(final_event_link)
        
        #Encontra a caixa com os papers
        paper_boxes = soup_eventos.find_all(class_='has-context')
        print('Encontrando todos os papers da página...')
        event_folder = make_new_folder(folder, event_id)
        print('Encontrando todos as informações dos papers da página...')    

        get_infos(paper_boxes, BASE_URL, final_list, event_folder, previous_link)
        
        # Busca a próxima página de papers.
        final_menu = soup_eventos.find(class_='pagination')
        print('Procurando próxima página...')

        try:
            next_pag = final_menu.find('a', title=re.compile(r'(Próx)'))
            link_next_pag = next_pag['href']
            print(event_id)
            print('Página encontrada: https://anpuh.org.br' + link_next_pag)
            final_event_link = 'https://anpuh.org.br' + link_next_pag
        except:                        
            print("Final das Páginas de Papers desse evento.")
            control = True

# Exporta CSV com informações gerais dos papers.
csv_file(final_list)
