<p align="center"><img src="images/labhd.png" height="256" width="256"/></p>

[![DOI:10.13140/RG.2.2.34653.03048](https://zenodo.org/badge/DOI/10.13140/RG.2.2.34653.03048.svg)](https://www.researchgate.net/publication/341804201_Script_Anais-Anpuh)
 [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

# Anais-Anpuh

*Projeto de script para web scraping da página de [Anais da Associação Nacional de História - Anpuh](https://anpuh.org.br/index.php/documentos/anais).
 Parte de projeto de História Digital desenvolvido no colegiado do curso de Licenciatura em História (CCLHM) da Unilab, campus dos Malês, sob coordenação do professor [Eric Brasil](https://ericbrasiln.github.io/) em parceria com o [Laboratório de Humanidades Digitais da Ufba](http://labhd.ufba.br/).*

*O Script Anais-Anpuh realiza a raspagem dos papers em pdf dos Simpósios Nacionais da Anpuh (disponíveis no site, de 1963 a 2021).*
___

**A ferramenta foi desenvolvida apenas para pesquisas acadêmicas, sem fins lucrativos.**
___

Esse script foi pensado como uma ferramenta metodológica da pesquisa em humanidades
digitais. Sua criação é fruto das reflexões e experiências empíricas de historiadores e sociólogos que têm enfrentado o [desafio de fazer ciências humanas no mundo digital](http://bibliotecadigital.fgv.br/ojs/index.php/reh/article/view/79933).
Defendemos a importância da apropriação, uso, desenvolvimento e aprimoramento de ferramentas digitais para as humanidades, assim como a urgência na sofisticação teórica, metodológica e epistemológica sobre as chamadas Humanidades Digitais.

É crescente o número de repositórios de fontes e dados on-line, assim como o acesso, busca, pesquisa e, muitas vezes, dependência de pesquisadores/as a eles.
Os Simpósios Nacionais da Anpuh, que acontecem bienalmente, têm reunido importantes reflexões sobre as mais variadas perspectivas historiográficas. Por conseguinte, os anais de cada evento constituem um importante repositório para pesquisas nos mais variados campos de estudo.
___

## Índice

- [Script Anais-Anpuh](#script-anais-anpuh)
  - [Índice](#índice)
  - [Instalação](#instalação)
    - [Python](#python)
      - [Bibliotecas e módulos](#bibliotecas-e-módulos)
  - [Uso](#uso)
    - [Exemplos](#exemplos)
  - [Resultados](#resultados)
  - [Novidades](#novidades)
  - [Licença](#licença)


## Instalação

Para executar o Script Anais-Anpuh, clone ou faça download do repositório. Antes de executar o script, é preciso preparar seu computador, como mostramos abaixo.

### Python

A ferramenta consiste num script escrito em [Python 3.12+](https://www.python.org/). Esta é uma linguagem de programação que te permite trabalhar rapidamente e integrar diferentes sistemas com maior eficiência.
Para executar o arquivo .py é preciso instalar o Python3 em seu computador.

Após a instalação, recomendamos criar um ambiente virtual:

```sh
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
# ou: venv\Scripts\activate  # Windows
```

Instale as bibliotecas requeridas:

```sh
pip install -r requirements.txt
```

#### Bibliotecas e módulos

- **beautifulsoup4**: [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) é uma biblioteca Python para extrair dados de arquivos HTML e XML.
- **requests**: [Requests](https://docs.python-requests.org/) é uma biblioteca HTTP elegante e simples.
- **pandas**: [Pandas](https://pandas.pydata.org/) é uma biblioteca escrita em Python para manipulação e análise de dados.


## Uso

```
python3 script-anais-anpuh.py [opções]
```

**Opções:**

| Flag | Descrição |
|------|-----------|
| `-s`, `--simpósios` | Números dos simpósios (arábicos). Ex: `31 32` ou `26-30` para intervalo |
| `-f`, `--format` | Formato de saída: `csv` (padrão), `json` ou `both` |
| `-o`, `--output` | Diretório de saída (padrão: `Anais_Anpuh`) |
| `--list` | Lista todos os simpósios disponíveis e sai |
| `--no-download` | Não baixa PDFs, apenas coleta metadados |
| `-v`, `--verbose` | Modo verbose (debug) |

### Exemplos

```sh
# Baixar todos os simpósios
python3 script-anais-anpuh.py

# Listar todos os simpósios disponíveis
python3 script-anais-anpuh.py --list

# Baixar apenas os simpósios 31 (XXXI) e 32 (XXXII)
python3 script-anais-anpuh.py -s 31 32

# Baixar simpósios 26 a 30
python3 script-anais-anpuh.py -s 26-30

# Coletar apenas metadados (sem download de PDFs), saída em JSON
python3 script-anais-anpuh.py -s 31 32 -f json --no-download

# Metadados em CSV e JSON, com downloads, modo verbose
python3 script-anais-anpuh.py -s 31 -f both -v
```


## Resultados

O script retorna para o usuário **os pdfs disponíveis nas páginas dos Simpósios Nacionais da Anpuh selecionados**. São criadas pastas com o identificador de cada evento para o armazenamento dos arquivos em PDF.

É importante notar que muitos papers não estão com pdf disponível no site, assim como nas edições mais antigas encontramos arquivos que contém vários papers num único PDF.

O script também gera um arquivo **CSV** e/ou **JSON** contendo os seguintes valores para cada paper: Autor(es)/Instituições, Título, Tipo, Evento, Ano, Link do Arquivo. Esses arquivos podem ser abertos como planilha (CSV) ou processados programaticamente (JSON) e trabalhados em banco de dados.


## Novidades

### v2.0 — Refatoração completa

- **Filtro de simpósios**: opção `-s` para selecionar quais simpósios baixar por número arábico (ex: `-s 31 32` ou `-s 26-30`). Use `--list` para ver todos os disponíveis.
- **Saída JSON**: opção `-f json` (ou `-f both` para CSV+JSON) para exportar metadados em formato JSON.
- **Python 3.12+**: atualização completa do código e dependências para Python 3.12+.
- **Correção de bug crítico**: URLs de PDF eram construídos sem a extensão `.pdf`, causando erro 404. Agora o link é extraído corretamente do campo "Arquivo".
- **Deduplicação de downloads**: por URL e por arquivo existente — não baixa o mesmo PDF duas vezes.
- **Tratamento de erros robusto**: retry com backoff, timeout, verificação de Content-Type, detecção de PDFs corrompidos (muito pequenos).
- **Modo `--no-download`**: coleta apenas metadados sem baixar PDFs.
- **Modo `--verbose`**: logs detalhados para depuração.
- **Remoção da dependência `wget`**: downloads feitos com `requests` (mais robusto e amplamente suportado).
- **Módulos legados preservados**: `open_url.py`, `outputs.py`, `infos_paper.py` mantidos com aviso de depreciação para compatibilidade retroativa.


## Licença

MIT licensed

Copyright (C) 2020 [Eric Brasil](https://github.com/ericbrasiln), [Gabriel Andrade](https://github.com/gabrielsandrade), [Leonardo F. Nascimento](https://github.com/leofn/), [Vitor Mussa](https://github.com/vmussa), [LABHD-UFBA](http://labhd.ufba.br/)