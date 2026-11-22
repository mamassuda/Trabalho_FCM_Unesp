
#! =========================================================================
#! Etapa final: Criação do DashBoard com streamlit
#! =========================================================================


from pathlib import Path
import unicodedata
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from web_scraping import executar_scraping
from leitor_pdf import executar_leitura_pdfs

st.set_page_config(page_title="Scouting & Classificação - FCM Unesp", layout="wide")
st.title("Dashboard Integrado: Classificação & Scouting")

# Caminho raiz do projeto (Trabalho_FCM_Unesp), independente de onde o terminal estiver
BASE_DIR = Path(__file__).resolve().parent.parent
ARQ_JOGADORES = BASE_DIR / "arquivos_auxiliares" / "tabelas_jogadores_leitor_pdf" / "tabela_jogadores.csv"
PASTA_SCRAPING = BASE_DIR / "arquivos_auxiliares" / "tabelas_web_scraping"


def normalizar_texto(texto: str) -> str:
    """Remove acentos e deixa minúsculo para facilitar o cruzamento entre nomes de clubes."""
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


#! ==============================================================================
#! BARRA LATERAL: EXECUÇÃO DAS ETAPAS 1 E 2
#! ==============================================================================
st.sidebar.header("Pipeline de Coleta")

if st.sidebar.button("1. Rodar Web Scraping (Classificação)", use_container_width=True):
    with st.spinner("Coletando classificações no navegador..."):
        executar_scraping()
    st.cache_data.clear()
    st.sidebar.success("Classificações atualizadas!")

if st.sidebar.button("2. Processar PDFs (Jogadores)", use_container_width=True):
    with st.spinner("Extraindo dados dos relatórios PDF..."):
        executar_leitura_pdfs()
    st.cache_data.clear()
    st.sidebar.success("Tabela de jogadores atualizada!")

st.sidebar.divider()


#! ==============================================================================
#! CARREGAMENTO E TRATAMENTO DOS DADOS (ETAPA 3)
#! ==============================================================================
@st.cache_data
def carregar_jogadores() -> pd.DataFrame:
    if not ARQ_JOGADORES.exists():
        return pd.DataFrame()

    df = pd.read_csv(ARQ_JOGADORES, sep=";", encoding="utf-8-sig")

    colunas_virgula = [
        "Altura_m",
        "Nota_Forca",
        "Nota_Geral_Tecnica",
        "Nota_Geral_Tatica",
        "Nota_Geral_Fisica",
        "Nota_Geral_Mental",
    ]
    for col in colunas_virgula:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".", regex=False),
                errors="coerce",
            )

    for col in ["Idade", "Peso_kg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    colunas_notas = [
        "Nota_Geral_Tecnica",
        "Nota_Geral_Tatica",
        "Nota_Geral_Fisica",
        "Nota_Geral_Mental",
    ]
    df["Media_Geral"] = df[colunas_notas].mean(axis=1).round(2)
    return df


@st.cache_data
def carregar_classificacoes() -> pd.DataFrame:
    arquivos = sorted(PASTA_SCRAPING.glob("*.csv"))
    if not arquivos:
        return pd.DataFrame()

    lista_dfs = []
    for arquivo in arquivos:
        df_temp = pd.read_csv(arquivo)
        extraido = df_temp["Pos"].astype(str).str.extract(r"^(.*?)\s*(\d+)$")
        df_temp["Zona"] = extraido[0].replace("", "Meio de tabela")
        df_temp["Pos"] = extraido[1].astype(int)

        _, divisao, ano = arquivo.stem.split("_")
        df_temp["Serie"] = divisao.upper()
        df_temp["Ano"] = int(ano)
        lista_dfs.append(df_temp)

    return pd.concat(lista_dfs, ignore_index=True)


df_jog = carregar_jogadores()
df_clas = carregar_classificacoes()

if df_jog.empty or df_clas.empty:
    st.warning("Arquivos CSV não encontrados. Use os botões na barra lateral para gerar os dados.")
    st.stop()


#! ==============================================================================
#! FILTROS GLOBAIS
#! ==============================================================================
st.sidebar.header("Filtros da Análise")
serie_sel = st.sidebar.selectbox("Série (Aba Classificação)", sorted(df_clas["Serie"].unique()))
ano_sel = st.sidebar.selectbox("Temporada (Ano)", sorted(df_clas["Ano"].unique(), reverse=True))

df_clas_filtrado = df_clas[
    (df_clas["Serie"] == serie_sel) & (df_clas["Ano"] == ano_sel)
].sort_values("Pos")


#! ==============================================================================
#! ABAS DO DASHBOARD
#! ==============================================================================
aba1, aba2, aba3 = st.tabs([
    "Classificação (Web Scraping)",
    "Relatórios de Scouting (PDFs)",
    "Análise Cruzada (Clube x Jogador)",
])

# --- ABA 1: CLASSIFICAÇÃO ---
with aba1:
    lider = df_clas_filtrado.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Líder", lider["Clube"], f"{lider['Pts']} pts")
    c2.metric("Média de Gols Pró", f"{df_clas_filtrado['GM'].mean():.1f}")
    c3.metric("Melhor Saldo", df_clas_filtrado.sort_values("SG", ascending=False).iloc[0]["Clube"])
    c4.metric("Clubes na Divisão", len(df_clas_filtrado))

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=df_clas_filtrado,
        x="Pts",
        y="Clube",
        hue="Zona",
        dodge=False,
        ax=ax,
    )
    ax.set_title(f"Pontuação - Brasileirão Série {serie_sel} ({ano_sel})")
    ax.set_xlabel("Pontos")
    ax.set_ylabel("")
    ax.legend(title="Zona", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig)

    st.dataframe(df_clas_filtrado, use_container_width=True, hide_index=True)

# --- ABA 2: JOGADORES (PDFs) ---
with aba2:
    st.subheader("Comparativo dos Pilares de Avaliação (Notas 1 a 5)")

    df_notas = df_jog.melt(
        id_vars=["Nome", "Posicao", "Clube", "Decisao"],
        value_vars=[
            "Nota_Geral_Tecnica",
            "Nota_Geral_Tatica",
            "Nota_Geral_Fisica",
            "Nota_Geral_Mental",
        ],
        var_name="Pilar",
        value_name="Nota",
    )
    df_notas["Pilar"] = df_notas["Pilar"].str.replace("Nota_Geral_", "")

    fig_jog, ax_jog = plt.subplots(figsize=(10, 4))
    sns.barplot(data=df_notas, x="Nome", y="Nota", hue="Pilar", ax=ax_jog)
    ax_jog.set_ylim(0, 5.5)
    ax_jog.set_title("Notas por Pilar de Avaliação")
    ax_jog.set_xlabel("")
    ax_jog.legend(title="Pilar", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig_jog)

    st.subheader("Fichas Extraídas")
    st.dataframe(df_jog, use_container_width=True, hide_index=True)

# --- ABA 3: CRUZAMENTO ---
with aba3:
    st.subheader(f"Contexto Competitivo dos Clubes Monitorados ({ano_sel})")

    df_ano = df_clas[df_clas["Ano"] == ano_sel].copy()
    df_ano["clube_norm"] = df_ano["Clube"].apply(normalizar_texto)

    resultados_cruzados = []
    for _, jog in df_jog.iterrows():
        clube_pdf_norm = normalizar_texto(jog["Clube"])
        # Busca exata ou parcial (ex: 'Sport Club do Recife' encontra 'Sport')
        match = df_ano[
            df_ano["clube_norm"].apply(
                lambda c: c != "" and (c in clube_pdf_norm or clube_pdf_norm in c)
            )
        ]

        if not match.empty:
            time_info = match.iloc[0]
            resultados_cruzados.append({
                "Jogador": jog["Nome"],
                "Posicao": jog["Posicao"],
                "Media_Scouting": jog["Media_Geral"],
                "Decisao": jog["Decisao"],
                "Clube_PDF": jog["Clube"],
                "Serie": time_info["Serie"],
                "Posicao_Tabela": f"{time_info['Pos']}º",
                "Pontos": time_info["Pts"],
                "Situacao_Clube": time_info["Zona"],
            })
        else:
            resultados_cruzados.append({
                "Jogador": jog["Nome"],
                "Posicao": jog["Posicao"],
                "Media_Scouting": jog["Media_Geral"],
                "Decisao": jog["Decisao"],
                "Clube_PDF": jog["Clube"],
                "Serie": "Não encontrado (A/B/C)",
                "Posicao_Tabela": "-",
                "Pontos": None,
                "Situacao_Clube": "-",
            })

    df_cruzado = pd.DataFrame(resultados_cruzados)
    st.dataframe(df_cruzado, use_container_width=True, hide_index=True)


