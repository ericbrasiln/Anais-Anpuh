"""
Módulo depreciado — funcionalidade incorporada em script-anais-anpuh.py.
Mantido apenas para compatibilidade retroativa.
"""
import warnings
warnings.warn(
    "outputs está depreciado. Use as funções de script-anais-anpuh.py diretamente.",
    DeprecationWarning,
    stacklevel=2,
)

import os
import pandas as pd

def make_new_folder(*paths):
    folder_path = os.path.join(*paths)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def csv_file(final_list):
    df = pd.DataFrame(final_list, columns=[
        'Autor(es)/Instituições', 'Título', 'Tipo', 'Evento', 'Ano', 'Link do Arquivo'
    ])
    df.to_csv('anais-anpuh-infos.csv', index=False, encoding='utf-8-sig')