# Análise descritiva — gastos e desempenho na Série A

## Recorte

A aba **Gastos × desempenho (Série A)** analisa 2023, 2024 e 2025. A integração mantém os filtros por clube e posição dos relatórios de scouting, os leitores de PDF e as rotinas de coleta existentes.

O painel financeiro usa uma tabela já preparada e funciona sem nova coleta ou acesso à internet durante a apresentação. Os links de fontes servem para consulta aos documentos originais.

## Bases separadas

`arquivos_auxiliares/financeiro/gastos_serie_a_2023_2025.csv` contém duas bases, sem misturá-las automaticamente:

| Chave | Conteúdo | Cobertura |
|---|---|---|
| `futebol` | Custos/gastos com futebol publicados, com complementos explicitados | 20 clubes em cada um dos anos 2023, 2024 e 2025 |
| `operacional_EY` | Despesas operacionais totais publicadas pela EY | 20 clubes em 2023 e 20 em 2025; sem dados inventados para 2024 |

São 60 registros clube/temporada na compilação de futebol e 40 na base EY. A cobertura não significa harmonização contábil integral.

Cada registro identifica rubrica, fonte, URL, página, observação e alertas de escopo/divergência. Valores em reais nominais, expressos em milhões. Não são orçamentos planejados antes da temporada: são gastos publicados referentes aos exercícios.

### Origem dos dados financeiros

- **Sports Value:** relatório referente a 2025, tabela histórica da página 75, e complementos do relatório referente a 2024, página 59.
- **PLURI:** relatórios individuais edição 2025, página 3, para Goiás e Coritiba em 2023.
- **Criciúma:** balanço oficial de 2025, comparativo de 2024, página 4, departamento de futebol profissional.
- **Juventude:** demonstrações financeiras de 2025/2024, página 11, custo da atividade do desporto.
- **EY:** levantamentos referentes a 2023, página 41, e 2025, página 36, despesas operacionais. A base de 2025 preserva os valores da planilha original do grupo.

Os URLs exatos estão nas colunas de fonte dos CSVs e em **Dados e método**, no painel. A pasta `pesquisa_financeira/` versiona somente os quatro CSVs necessários para reconstruir a seleção; PDFs, imagens, backups e arquivos de trabalho locais não são publicados.

### Ressalvas específicas

- América-MG/2023 na compilação de futebol usa a despesa operacional da EY como exceção explícita; não foi rebatizada como custo exclusivo do futebol.
- Há valores históricos divergentes entre edições da Sports Value. A seleção usa a tabela histórica da edição 2025 quando disponível; as diferenças permanecem documentadas. Não se tirou média entre versões.
- Cuiabá/2023 na base EY tem alerta de escopo pelo valor publicado de R$ 2 milhões. Não deve ser interpretado isoladamente como eficiência excepcional.
- O controle **Ocultar registros com ressalva** remove exceções/versões em revisão e recalcula as médias da amostra restante.

## Gráficos e indicadores

1. Barras de gasto publicado por clube.
2. Barras de pontos na liga.
3. Dispersão gasto × pontos, com médias da temporada e quatro quadrantes.
4. Razão de pontos por R$ 10 milhões publicados.
5. Barras agrupadas para comparar até seis clubes entre temporadas.
6. Tabela de estatísticas descritivas: média, mediana, quartis, extremos e desvio-padrão.

Fórmulas:

```text
Pontos_10mi = Pontos * 10 / Gasto_mi
Custo_ponto_mi = Gasto_mi / Pontos
Aproveitamento_pct = Pontos / (3 * Jogos) * 100
```

Com zero pontos, o custo por ponto fica ausente, não infinito. As médias e os quadrantes são calculados por temporada. Destacar nomes não altera a amostra. O cruzamento valida correspondência exata por clube e ano, sem duplicações e sem aceitar a perda silenciosa de uma temporada inteira.

## Interpretação

Os quadrantes descrevem posição relativa às médias; não comprovam causalidade ou qualidade de gestão. A razão pontos/gasto pode favorecer clubes baratos mesmo com pontuação baixa, por isso deve ser lida junto com pontos e classificação.

Os gastos anuais abrangem outras competições e podem incluir escopos contábeis diferentes entre clubes. Comparações monetárias entre anos são nominais, sem ajuste pela inflação. Ausência de barra indica dado indisponível, clube fora da Série A naquele ano ou registro retirado pelo filtro; nunca significa automaticamente zero.

## Executar

Depois de instalar as dependências da raiz:

```bash
streamlit run Scripts/dashboard.py
```

O roteiro em arquivo separado exporta quatro PNGs e um CSV:

```bash
python Scripts/atividade_aula_futebol.py --ano 2025
python Scripts/atividade_aula_futebol.py --ano 2023 --base operacional_EY
```

Os arquivos são salvos em `previa_exportacoes/`, ignorada pelo Git. Use `--saida` para escolher outra pasta. O roteiro não é exibido na interface.

Para reconstruir a seleção financeira com os quatro CSVs de origem versionados:

```bash
python Scripts/analise_financeira.py
```

Para executar os testes (unittest faz parte do Python):

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem seleção de fontes, fórmulas, anos ausentes, correspondência entre bases, quadrantes, gráficos, downloads, estados dos filtros e integração com os filtros de scouting.
