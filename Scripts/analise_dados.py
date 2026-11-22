
#! ================================================================
#! Etapa 3: Análise dos dados extraídos do site e dos PDFs
#! ================================================================

import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns


df_jogadores = pd.read_csv("arquivos_auxiliares/tabelas_jogadores_leitor_pdf/tabela_jogadores.csv") 
df_classificacao = pd.read_csv("arquivos_auxiliares/tabelas_classificacao_web_scraping/serie_a_2023.csv")





