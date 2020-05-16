# Script Anais-Anpuh
*Projeto de script para web scraping da página de [Anais da Anpuh](https://anpuh.org.br/index.php/documentos/anais).
 Parte de projeto de História Digital desenvolvido na Unilab, campus dos Malês sob coordenação do professor [Eric Brasil](https://ericbrasiln.github.io/) em parceria com o [Laboratório de Humanidades Digitais da Ufba](http://labhd.ufba.br/).*

*O Script Anais-Anpuh realiza a raspagem dos papers em pdf de todos os eventos entre 1963 até 2019.*

**A ferramenta foi desenvolvida apenas para pesquisas acadêmicas, sem fins lucrativos.**
##

Esse script foi pensado como uma ferramenta metodológica da pesquisa em humanidades
digitais. Sua criação é fruto das reflexões e experiências empíricas de historiadores e 
sociológos que têm enfrentado o
[desafio de fazer ciências humanas no mundo digital](http://bibliotecadigital.fgv.br/ojs/index.php/reh/article/view/79933).
Defendemos a importância da apropriação, uso, desenvolvimento e aprimoramento de ferramentas
digitais para as humanidades, assim como a urgência na sofisticação teórica, metodológica e epistemológica sobre as
chamadas Humanidades Digitais.

É crescente o número de repositórios de fontes e dados on-line, assim como o acesso, busca, pesquisa e, muitas vezes,
dependência de pesquisadores/as a eles.
Os Simpósios Nacionais da Anpuh, que aconcetecem bienalmente, têm reunido importantes reflexões sobre as mais variadas perspectivas historiográficas. Por conseguinte, os anais de cada evento constitui um importante repositório para pesquisas nos mais variados campos de estudo.

## Índice

- [Instalação](#instalação)
  - [Python](#python)
    - [Bibliotecas e módulos](#bibliotecas-e-módulos)
- [Parâmetros de pesquisa](#parâmetros-de-pesquisa)
    - [Termo de busca](#termo-de-busca)
    - [Definir ordem dos resultados](#definir-ordem-dos-resultados)
    - [Definir intervalo cronológico da busca](#definir-intervalo-cronológico-da-busca)
- [Saídas da pesquisa](#saídas-da-pesquisa)
   - [Informações impressas na tela](#informações-impressas-na-tela)
   - [Pastas com conteúdos](#pastas-com-conteúdos)
- [Licença](#licença)


## Instalação

Para executar o Jusbr Script, vc precisa acessar a pasta da ferramenta no
[GitHub do LABHDUFBA](https://github.com/leofn/LABHDUFBA/tree/master/JusBrasil). Faça download do arquivo jusbr.py
e salve na pasta que deseja que os resultados e seus respectivos arquivos sejam armazenados. Antes de executar o script,
é preciso preparar seu computador, como mostramos abaixo.

### Python

A ferramenta consiste num script escrito em [Python](https://www.python.org/). Esta é uma linguagem de programação que
te permite trabalhar rapidamente e integrar diferentes sistemas com maior eficiência.
Para executar o arquivo .py é preciso instalar o Python3 em seu computador.

[Clique aqui](https://python.org.br/instalacao-windows/) para um tutorial de instalação do Python no Windows,
[clique aqui](https://python.org.br/instalacao-linux/) para Linux e [clique aqui](https://python.org.br/instalacao-mac/)
para Mac.

Após a instalação, vc pode executar o arquivo .py direto do prompt de comando do Windows ou pelo terminal do Linux,
ou utilizar as diversas [IDE](https://pt.wikipedia.org/wiki/Ambiente_de_desenvolvimento_integrado) disponíveis.

Exemplo de como executar utilizando o terminal do Linux:

1. Acesse o diretório em que o arquivo .py está salvo:
   ```sh
   $ cd user/local
   ```

1. Execute o arquivo usando Python3
   ```sh
   $ python3 nomedoarquivo.py
   ```


#### Bibliotecas e módulos

- **urllib.requests**: módulo do Python que ajuda a acessar urls.
[Saiba mais.](https://docs.python.org/pt-br/3/library/urllib.request.htmll)
- **datetime**: módulo do Python para manipular datas e horários.
[Saiba mais.](https://docs.python.org/pt-br/3/library/datetime.html)
- **os**: módulo do Python que permite manipular funções do sistema operacional.
[Saiba mais.](https://docs.python.org/pt-br/3/library/os.html)
- **bs4**: [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) é uma biblioteca Python para extrair
 dados de arquivos HTML e XML.
- **pandas**: [Pandas](https://pandas.pydata.org/) é uma biblioteca escrita em Python para manipulação e análise de dados. 

## Parâmetros de pesquisa

O Jusbr Script possibilita que a pesquisa seja efetuada diretamente pelo terminal ou por qualquer outra IDE que execute
o arquivo .py.
O/a pesquisador/a tem a opção de determinar alguns parâmetros báscios para a busca, disponíveis no site do JusBrasil.
Esses parâmetros serão registrados e processados e, ao final do processo, farão parte do relatório final.

### Termo de busca

Recomendações para definir o termo de sua pesquisa:
- **Não utilizar acentos e/ou caracteres especiais** (como "ç", "~", "/", "%", entre outros);
- Para buscar expressões exatas, **colocar entre aspas["]**

### Definir ordem dos resultado

Será perguntado ao usuário se deseja ordenar os resultados por data. Se a resposta for positiva,
os resutlados serão listados do mais recente ao mais antigo. Se a resposta for negativa, os resultados serão
apresentados por relevância, conforme padrão do JusBrasil.

### Definir intervalo cronológico da busca

O JusBrasil possibilita definir um período específico para a sua busca, e você também pode definir esse parâmetro
através da Jusbr Script. O seguinte será impresso na tela:

    - Inserir intervalo personalizado de busca -
    Se desejar pesquisar um determinano intervalo, insira a data de início e a data de fim.
    O padrão dever ser AAAA-MM-DD
    Deseja incluir intervalo de busca (s/n)? 
Se a resposta for 's':

    Insira a data de início (AAAA-MM-DD):
    Insira a data de término (AAAA-MM-DD):
Se a resposta for 'n', todos os resultados serão buscados, sem recorte de data.

## Saídas da pesquisa

Enquanto o JusbrScript estiver executando sua busca, ele vai imprimir algumas informações
na tela e ao, após encontrar o último resultado, vai salvar os arquivos.

### Informações impressas na tela:
1. Url da página dos resultados da busca;
2. Hora e data da busca;
3. Total de ocorências;
4. Url da página de resultado atual;
5. Apresenta o título do resultado que está sendo raspado;
6. Dados do relatório final:
    - *Termo da busca*
    - *Tipo de ordenação*
    - *Total de ocorrências*
    - *Data*
    - *Horário*
    - *Quantidade de arquivos .txt*
    - *Quantidade de Diários Oficiais*
    - *Quantidade de Jurisprudências*
    - *Quantidade de Artigos*
    - *Quantidade de Legislações*
    - *Quantidade de Noticias*
    - *Quantidade de Modelos e Peças*
    - *Nome do arquivo.csv*
7. Titulo do Arquivo csv. O título do arquivo final é "JusBrasil_[DATA]_[TERMO DA BUSCA].csv" e pode ser aberto em
qualquer editor de planilhas e inserido em outros programas de banco de dados) contendo as seguintes colunas:
'tipo', 'titulo', 'link', 'descricao', 'conteudo'.
8. Salva o relatório final e o csv.

### Pastas com conteúdos
Os resultados são salvos em uma pasta nomeada com o termo da busca.
Em seu interior consta o **relatório final**, o arquivo **csv** e as **pastas com os conteúdos**,
também salvos em txt e organizados por tipo de documento (Diário Oficial, Jusrisprudência,
Artigos, Legislações, Notícias e Modelos e Peças).

## Licença

MIT licensed

Copyright (C) 2020 Eric Brasil, Gabriel Andrade, http://labhd.ufba.br/

