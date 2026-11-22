
#! =========================================================================
#! Etapa final: Criação do DashBoard com streamlit
#! =========================================================================


import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

#! Importando funções dos outros scripts

from web_scraping import executar_scraping
from leitor_pdf import executar_leitura_pdfs
from tratamento_dados import (
    carregar_e_tratar_classificacoes,
    carregar_e_tratar_jogadores,
    cruzar_jogadores_clubes,
)

st.set_page_config(page_title="Scouting & Classificação - FCM Unesp", layout="wide")
st.title("Dashboard Integrado: Classificação & Scouting")

# --- BARRA LATERAL: PIPELINE DE COLETA ---
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


# --- LEITURA COM CACHE ---
@st.cache_data
def obter_dados():
    return carregar_e_tratar_jogadores(), carregar_e_tratar_classificacoes()


df_jog, df_clas = obter_dados()

if df_jog.empty or df_clas.empty:
    st.warning("Arquivos CSV não encontrados. Use os botões na barra lateral para gerar os dados.")
    st.stop()

# --- FILTROS ---
st.sidebar.header("Filtros da Análise")
serie_sel = st.sidebar.selectbox("Série (Aba Classificação)", sorted(df_clas["Serie"].unique()))
ano_sel = st.sidebar.selectbox("Temporada (Ano)", sorted(df_clas["Ano"].unique(), reverse=True))

df_clas_filtrado = df_clas[
    (df_clas["Serie"] == serie_sel) & (df_clas["Ano"] == ano_sel)
].sort_values("Pos")

# --- ABAS ---
aba1, aba2, aba3 = st.tabs([
    "Classificação (Web Scraping)",
    "Relatórios de Scouting (PDFs)",
    "Análise Cruzada (Clube x Jogador)",
])

with aba1:
    lider = df_clas_filtrado.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Líder", lider["Clube"], f"{lider['Pts']} pts")
    c2.metric("Média de Gols Pró", f"{df_clas_filtrado['GM'].mean():.1f}")
    c3.metric("Melhor Saldo", df_clas_filtrado.sort_values("SG", ascending=False).iloc[0]["Clube"])
    c4.metric("Clubes na Divisão", len(df_clas_filtrado))

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_clas_filtrado, x="Pts", y="Clube", hue="Zona", dodge=False, ax=ax)
    ax.set_title(f"Pontuação - Brasileirão Série {serie_sel} ({ano_sel})")
    ax.set_xlabel("Pontos")
    ax.set_ylabel("")
    ax.legend(title="Zona", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(df_clas_filtrado, use_container_width=True, hide_index=True)

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
    plt.close(fig_jog)

    st.subheader("Fichas Extraídas")
    st.dataframe(df_jog, use_container_width=True, hide_index=True)

with aba3:
    st.subheader(f"Contexto Competitivo dos Clubes Monitorados ({ano_sel})")
    df_cruzado = cruzar_jogadores_clubes(df_jog, df_clas, ano_sel)
    st.dataframe(df_cruzado, use_container_width=True, hide_index=True)