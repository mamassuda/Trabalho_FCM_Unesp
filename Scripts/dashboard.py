import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from painel_financeiro import renderizar_analise_financeira
from web_scraping import executar_scraping
from leitor_pdf import executar_leitura_pdfs
from tratamento_dados import (
    carregar_e_tratar_classificacoes,
    carregar_e_tratar_jogadores,
    cruzar_jogadores_clubes,
)

st.set_page_config(page_title="FCM Unesp — Gastos, Classificação & Scouting", layout="wide")
st.title("Dashboard Integrado: Futebol & Análise de Dados")
st.caption("Classificação, scouting e análise descritiva de gastos e desempenho na Série A")

# --- BARRA LATERAL: PIPELINE DE COLETA ---
st.sidebar.header("Pipeline de Coleta")

if st.sidebar.button("1. Rodar Web Scraping (Classificação)", width="stretch"):
    with st.spinner("Coletando classificações no navegador..."):
        executar_scraping()
    st.cache_data.clear()
    st.sidebar.success("Classificações atualizadas!")

if st.sidebar.button("2. Processar PDFs (Jogadores)", width="stretch"):
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
st.sidebar.header("Filtros de classificação e análise cruzada")
st.sidebar.caption("A análise financeira tem filtros próprios dentro da sua aba.")
serie_sel = st.sidebar.selectbox("Série (Aba Classificação)", sorted(df_clas["Serie"].unique()))
ano_sel = st.sidebar.selectbox("Temporada (Ano)", sorted(df_clas["Ano"].unique(), reverse=True))

df_clas_filtrado = df_clas[
    (df_clas["Serie"] == serie_sel) & (df_clas["Ano"] == ano_sel)
].sort_values("Pos")

# --- ABAS ---
aba_financeira, aba1, aba2, aba3 = st.tabs([
    "Gastos × desempenho (Série A)",
    "Classificação (Web Scraping)",
    "Relatórios de Scouting (Leitor de PDFs)",
    "Análise Cruzada (Clube x Jogador)",
])

with aba_financeira:
    renderizar_analise_financeira()

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

    st.dataframe(df_clas_filtrado, width="stretch", hide_index=True)

with aba2:
    st.subheader("Comparativo dos Pilares de Avaliação (Notas 1 a 5)")

    # 1. Cria colunas para organizar os filtros lado a lado
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        clubes = df_jog["Clube"].unique().tolist()
        clubes_selecionados = st.multiselect("Filtrar por Clube:", options=clubes, default=clubes)
        
    with col_filtro2:
        posicoes = df_jog["Posicao"].unique().tolist()
        posicoes_selecionadas = st.multiselect("Filtrar por Posição:", options=posicoes, default=posicoes)

    # 2. Aplica os filtros no dataframe original
    df_filtrado = df_jog[
        (df_jog["Clube"].isin(clubes_selecionados)) & 
        (df_jog["Posicao"].isin(posicoes_selecionadas))
    ]

    # 3. Verifica se o dataframe não ficou vazio após o filtro para evitar erros no gráfico
    if df_filtrado.empty:
        st.warning("Nenhum jogador encontrado com os filtros selecionados.")
    else:
        # Prepara os dados derretidos usando o dataframe FILTRADO
        df_notas = df_filtrado.melt(
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

        # Gera o gráfico com os dados filtrados
        fig_jog, ax_jog = plt.subplots(figsize=(10, 4))
        sns.barplot(data=df_notas, x="Nome", y="Nota", hue="Pilar", ax=ax_jog)
        ax_jog.set_ylim(0, 5.5)
        ax_jog.set_title("Notas por Pilar de Avaliação")
        ax_jog.set_xlabel("")
        ax_jog.legend(title="Pilar", bbox_to_anchor=(1.02, 1), loc="upper left")
        
        # Rotaciona os nomes no eixo X para não encavalarem caso haja muitos jogadores
        plt.xticks(rotation=45, ha='right')
        
        st.pyplot(fig_jog)
        plt.close(fig_jog)

    # Mostra a tabela também filtrada
    st.subheader("Fichas Extraídas")
    st.dataframe(df_filtrado, width="stretch", hide_index=True)

with aba3:
    st.subheader(f"Contexto Competitivo dos Clubes Monitorados ({ano_sel})")
    df_cruzado = cruzar_jogadores_clubes(df_jog, df_clas, ano_sel)
    st.dataframe(df_cruzado, width="stretch", hide_index=True)