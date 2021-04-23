import re
import os
import pandas as pd

def make_new_folder(*paths):
    """Cria diretório caso ele ainda não exista e retorna o path
    correspondente."""
    folder_path = os.path.join(*paths)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def csv_file(final_list):
    """Exporta CSV com informações gerais dos papers."""
    print('Salvando arquivo .csv com todas as informações: autores/instituições, título, tipo, evento, ano, link do pdf')
    df = pd.DataFrame(final_list, columns=['Autor(es)/Instituições', 'Título', 'Tipo', 'Evento', 'Ano', 'Link do Arquivo'])
    df.to_csv('anais-anpuh-infos.csv')
    print('Raspagem completa.')
