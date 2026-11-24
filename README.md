# Análise de Futebol: Classificação & Scouting (FCM Unesp)

Pipeline automatizado em Python para coleta de classificações do Campeonato Brasileiro, extração de dados de relatórios de scouting em PDF e visualização integrada em dashboard interativo.

## Estrutura do Projeto

```text
Trabalho_FCM_Unesp/
├── Scripts/
│   ├── web_scraping.py       # Etapa 1: Coleta das tabelas das Séries A, B e C via Playwright
│   ├── leitor_pdf.py         # Etapa 2: Extração estruturada dos relatórios PDF via PyPDF2/Regex
│   ├── tratamento.py         # Limpeza, tipagem e cruzamento entre jogadores e clubes
│   └── dashboard.py          # Etapa 3: Interface interativa e orquestração em Streamlit
├── arquivos_auxiliares/
│   ├── relatorios_futebol_leitor_pdf/   # Laudos de scouting em PDF (Relatorio_1_FCM a Relatorio_15_FCM)
│   ├── tabelas_jogadores_leitor_pdf/    # Base estruturada dos atletas (tabela_jogadores.csv)
│   └── tabelas_web_scraping/            # Classificações históricas extraídas (Séries A, B e C)
├── pesquisa_financeira/      # Bases e análises de gastos anuais da Série A (2023–2025)
├── tests/                    # Testes automatizados do pipeline
├── ANALISE_DESCRITIVA.md     # Metodologia e notas da análise financeira
├── .gitignore
├── requirements.txt
└── README.md
```

## Como executar

1. **Crie e ative o ambiente virtual:**

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
```

2. **Instale as dependências e o navegador do Playwright:**

```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Inicie o dashboard:**

```bash
streamlit run Scripts/dashboard.py
```

## Análise descritiva de gastos e desempenho

A aba **Gastos × desempenho (Série A)** acrescenta a análise de 2023, 2024 e 2025, com gráficos de gastos, pontos, quadrantes, indicador de pontos por unidade de gasto e comparação entre temporadas. Os filtros por clube/posição do scouting e as demais abas continuam disponíveis.

As bases de custos do futebol e despesas operacionais EY ficam separadas, com fonte, página e ressalvas em **Dados e método**. A tabela financeira já está incluída no repositório; não é preciso rodar nova coleta para abrir a análise. A documentação detalhada está em `ANALISE_DESCRITIVA.md`.

Para executar os testes:

```bash
python -m unittest discover -s tests -v
```
