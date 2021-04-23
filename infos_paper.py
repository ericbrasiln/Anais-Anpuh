from bs4 import BeautifulSoup
import os
import re
import wget

def get_links(paper, event_folder, title, previous_link):
    """Encontrar o link e realizar o download do PDF."""
    try:
        link_pdf = paper.find('a',href=re.compile(r'(.pdf)'))
        link = link_pdf['href']
        if not link in previous_link:
            previous_link = link
            if link.startswith('https://'):
                full_link = link
                full_name = os.path.join(event_folder, title.replace(' ','_') + '.pdf')
            else:
                full_link = "https://anpuh.org.br" + link            
                change = ['"', '*', ':', '<', '>', '?', '/', "\\", '|' , '_' , '@' , '+', '...']
                for x in change:
                    title = title.replace(x, '')
                full_name = os.path.join(event_folder, title.replace(' ','_') + '.pdf')
            if not os.path.exists(full_name):
                print('Salvando o pdf na pasta...\n')
                try:
                    wget.download(full_link, out=full_name)
                except Exception as e:
                    print(e)
            else:
                print("Arquivo já existe.\n")
        else:
            print("PDF desse paper é igual ao do paper anterior.\n")
    except Exception as e:
        print(e)
        link = paper.find('a', href=re.compile(r'(.pdf)'))
        link = None
        print('Paper sem pdf disponível para download.\n')


def get_infos(paper_boxes, base_url, final_list, event_folder, previous_link):
    """Raspa as informações de cada paper."""
    for paper in paper_boxes:    
        title = paper.h2.text
        title = title.strip().lower().replace('/','-')
        infos = paper.find_all('dt')
        tipo = ""
        event = ""
        year = ""
        authors = ""
        file_link = ""
        for info in infos:
            if info.text.strip() == "Tipo":
                tipo = info.find_next_sibling().text.strip()
                print (f"Tipo : {tipo}")
            if info.text.strip() == "Evento":
                event = info.find_next_sibling().text.strip()
                print (f"Evento : {event}")
            if info.text.strip() == "Ano":
                year = info.find_next_sibling().text.strip()
                print (f"Ano : {year}")
            if info.text.strip() == "Arquivo":
                file_tag = info.find_next_sibling().a['href']
                file_link = base_url + file_tag
                print (f"Arquivo : {file_link}")
            if info.text.strip() == "PDF LINK":
                file_tag = info.find_next_sibling().a['href']
                if file_tag.startswith('https://') == True:
                    file_link = file_tag
                    print (f"Arquivo : {file_link}")
                else:
                    file_link = base_url + file_tag
                    print (f"Arquivo : {file_link}")
            if info.text.strip() == "Autor(es)":
                authors = info.find_next_sibling().text.strip()
                print (f"\nAutor(es) : {authors}")
        info_list = [authors, title, tipo, event, year, file_link]
        final_list.append(info_list)
        print('Encontrando link do paper...')
        get_links(paper, event_folder, title, previous_link)
