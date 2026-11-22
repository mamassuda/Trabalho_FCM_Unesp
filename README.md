# Análise de Futebol: Classificação & Scouting (FCM Unesp)

Pipeline automatizado em Python para coleta de classificações do Campeonato Brasileiro, extração de dados de relatórios de scouting em PDF e visualização integrada em dashboard interativo.

## Estrutura do Projeto

```text
Trabalho_FCM_Unesp/
├── Scripts/
│   ├── web_scraping.py   # Etapa 1: Coleta das tabelas das Séries A, B e C via Playwright
│   ├── leitor_pdf.py     # Etapa 2: Extração estruturada dos relatórios PDF via PyPDF2/Regex
│   ├── tratamento.py     # Limpeza, tipagem e cruzamento entre jogadores e clubes
│   └── dashboard.py      # Etapa 3: Interface interativa e orquestração em Streamlit
├── arquivos_auxiliares/
│   ├── relatorios_futebol_leitor_pdf/
│   ├── tabelas_jogadores_leitor_pdf/
│   └── tabelas_web_scraping/
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