#! =========================================================================
#! DASHBOARD INTEGRADO: Classificação & Scouting — FCM Unesp
#! =========================================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from web_scraping import executar_scraping
from leitor_pdf import executar_leitura_pdfs
from tratamento_dados import (
    carregar_e_tratar_classificacoes,
    carregar_e_tratar_jogadores,
    cruzar_jogadores_clubes,
)
from auth import check_login, logout_button
from player_cards import render_player_grid

#! --- Configuração da página ---
st.set_page_config(
    page_title="Scouting & Classificação - FCM Unesp",
    layout="wide",
    initial_sidebar_state="expanded",
)

#! --- AUTENTICAÇÃO ---
if not check_login():
    st.stop()

st.title("📊 Dashboard Integrado: Classificação & Scouting")
st.caption("FCM Unesp — Análise de desempenho e scouting de jogadores")

# Caminhos
CSV_CLASSIF = "classificacoes.csv"
CSV_JOGADORES = "jogadores.csv"
CSV_DENSIDADE = "densidade_regional.csv"
CSV_FOTOS = "fotos.csv"
IMG_MAPAS = "Mapas_Regionais_Brasileirao.png"

#! --- Pipeline (sidebar) ---
st.sidebar.header("⚙️ Pipeline de Coleta")

if st.sidebar.button("1. Rodar Web Scraping", use_container_width=True):
    try:
        with st.spinner("Coletando classificações..."):
            executar_scraping()
        st.cache_data.clear()
        st.sidebar.success("✅ Classificações atualizadas!")
    except Exception as e:
        st.sidebar.error(f"❌ Falha no scraping: {e}")

if st.sidebar.button("2. Processar PDFs", use_container_width=True):
    try:
        with st.spinner("Extraindo dados dos PDFs..."):
            executar_leitura_pdfs()
        st.cache_data.clear()
        st.sidebar.success("✅ Jogadores atualizados!")
    except Exception as e:
        st.sidebar.error(f"❌ Falha na leitura de PDFs: {e}")

st.sidebar.divider()

#! --- Cache helpers ---
def _mtime(*paths):
    return tuple(os.path.getmtime(p) if os.path.exists(p) else 0 for p in paths)

@st.cache_data(show_spinner=False)
def obter_dados(_stamp):
    return carregar_e_tratar_jogadores(), carregar_e_tratar_classificacoes()

@st.cache_data(show_spinner=False)
def obter_densidade(_stamp):
    if not os.path.exists(CSV_DENSIDADE):
        return pd.DataFrame()
    return pd.read_csv(CSV_DENSIDADE)

@st.cache_data(show_spinner=False)
def obter_fotos(_stamp):
    if not os.path.exists(CSV_FOTOS):
        return {}
    df_f = pd.read_csv(CSV_FOTOS)
    return dict(zip(df_f["Nome"], df_f["URL"]))

df_jog, df_clas = obter_dados(_mtime(CSV_JOGADORES, CSV_CLASSIF))

if df_jog.empty or df_clas.empty:
    st.warning(
        "⚠️ CSVs não encontrados. Use os botões na barra lateral "
        "para gerar os dados."
    )
    st.stop()

foto_map = obter_fotos(_mtime(CSV_FOTOS))

#! --- Filtros globais ---
st.sidebar.header("🔎 Filtros")
serie_sel = st.sidebar.selectbox(
    "Série", sorted(df_clas["Serie"].unique())
)
ano_sel = st.sidebar.selectbox(
    "Temporada", sorted(df_clas["Ano"].unique(), reverse=True)
)

df_clas_filtrado = (
    df_clas[(df_clas["Serie"] == serie_sel) & (df_clas["Ano"] == ano_sel)]
    .sort_values("Pos")
    .reset_index(drop=True)
)

#! --- Abas ---
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "🏆 Classificação",
    "🔬 Scouting (PDFs)",
    "🔀 Cruzamento",
    "🗺️ Regional",
    "📈 Comparativo",
])

# ---------------- ABA 1 ----------------
with aba1:
    st.subheader(f"Série {serie_sel} — {ano_sel}")
    lider = df_clas_filtrado.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Líder", lider["Clube"], f"{lider['Pts']} pts")
    c2.metric("Média GM", f"{df_clas_filtrado['GM'].mean():.1f}")
    c3.metric(
        "Melhor Saldo",
        df_clas_filtrado.sort_values("SG", ascending=False).iloc[0]["Clube"],
        int(df_clas_filtrado["SG"].max()),
    )
    c4.metric("Clubes", len(df_clas_filtrado))

    c5, c6, c7 = st.columns(3)
    c5.metric("Média GC", f"{df_clas_filtrado['GC'].mean():.1f}")
    c6.metric("Total Gols (liga)", int(df_clas_filtrado["GM"].sum()))
    c7.metric(
        "Aproveitamento do líder",
        f"{100 * lider['Pts'] / (lider['PJ'] * 3):.1f}%",
    )

    st.divider()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=df_clas_filtrado, x="Pts", y="Clube",
        hue="Zona", dodge=False, ax=ax,
    )
    ax.set_title(f"Pontuação — Série {serie_sel} ({ano_sel})")
    ax.set_xlabel("Pontos"); ax.set_ylabel("")
    ax.legend(title="Zona", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig); plt.close(fig)

    st.dataframe(df_clas_filtrado, use_container_width=True, hide_index=True)

# ---------------- ABA 2 ----------------
with aba2:
    st.subheader("Scouting — Comparativo de Pilares")

    fc1, fc2 = st.columns(2)
    with fc1:
        pos_sel = st.multiselect(
            "Posição", sorted(df_jog["Posicao"].dropna().unique()),
            default=sorted(df_jog["Posicao"].dropna().unique()),
        )
    with fc2:
        dec_sel = st.multiselect(
            "Decisão", sorted(df_jog["Decisao"].dropna().unique()),
            default=sorted(df_jog["Decisao"].dropna().unique()),
        )

    df_jog_filt = df_jog[
        df_jog["Posicao"].isin(pos_sel) & df_jog["Decisao"].isin(dec_sel)
    ]

    st.markdown("### 🪪 Player Cards")
    cols_card = st.radio(
        "Colunas", [2, 3, 4], horizontal=True, index=1,
        key="card_cols",
    )
    render_player_grid(df_jog_filt, cols=cols_card, foto_map=foto_map)

    st.divider()

    st.markdown("### 🎯 Radar comparativo")
    pilares_cols = [
        "Nota_Geral_Tecnica", "Nota_Geral_Tatica",
        "Nota_Geral_Fisica", "Nota_Geral_Mental",
    ]
    labels = ["Técnica", "Tática", "Física", "Mental"]

    nomes_radar = st.multiselect(
        "Jogadores", sorted(df_jog_filt["Nome"].unique()),
        default=sorted(df_jog_filt["Nome"].unique())[:min(2, len(df_jog_filt))],
        key="radar",
    )

    if nomes_radar:
        fig_radar = go.Figure()
        for nome in nomes_radar:
            row = df_jog_filt[df_jog_filt["Nome"] == nome].iloc[0]
            vals = [row[c] for c in pilares_cols]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=labels + [labels[0]],
                fill="toself", name=nome,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            height=500,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    st.markdown("### 🔥 Heatmap dos pilares")
    pivot = df_jog_filt.set_index("Nome")[pilares_cols].sort_index()
    if not pivot.empty:
        fig_hm, ax_hm = plt.subplots(
            figsize=(10, max(3, len(pivot) * 0.35))
        )
        sns.heatmap(
            pivot, annot=True, cmap="RdYlGn", vmin=0, vmax=5,
            ax=ax_hm, cbar_kws={"label": "Nota"},
        )
        ax_hm.set_ylabel("")
        st.pyplot(fig_hm); plt.close(fig_hm)

    st.divider()

    st.subheader("📋 Tabela completa")
    st.dataframe(df_jog_filt, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Baixar jogadores filtrados (CSV)",
        df_jog_filt.to_csv(index=False).encode("utf-8"),
        file_name="jogadores_filtrados.csv", mime="text/csv",
    )

# ---------------- ABA 3 ----------------
with aba3:
    st.subheader(f"Cruzamento Clube × Jogador ({ano_sel})")
    df_cruzado = cruzar_jogadores_clubes(df_jog, df_clas, ano_sel)
    st.dataframe(df_cruzado, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Baixar cruzamento (CSV)",
        df_cruzado.to_csv(index=False).encode("utf-8"),
        file_name=f"cruzamento_{ano_sel}.csv", mime="text/csv",
    )

# ---------------- ABA 4 ----------------
with aba4:
    st.subheader("🗺️ Distribuição Regional (2023–2026)")
    df_dens = obter_densidade(_mtime(CSV_DENSIDADE))

    if df_dens.empty:
        st.info(
            "Arquivo `densidade_regional.csv` não encontrado. "
            "Execute o script R para exportá-lo."
        )
    else:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            fig_reg = px.bar(
                df_dens, x="Região", y="Equipes",
                color="Região", animation_frame="Ano", text="Equipes",
                range_y=[0, df_dens["Equipes"].max() + 3],
                title="Equipes por região (animação)",
            )
            fig_reg.update_traces(textposition="outside")
            st.plotly_chart(fig_reg, use_container_width=True)
        with col_b:
            if os.path.exists(IMG_MAPAS):
                st.image(IMG_MAPAS, caption="Mapa consolidado (R/geobr)")
            else:
                st.caption("PNG dos mapas não encontrado.")

        df_dens_pct = df_dens.copy()
        df_dens_pct["Percentual"] = (
            df_dens_pct.groupby("Ano")["Equipes"]
            .transform(lambda s: 100 * s / s.sum()).round(2)
        )
        st.plotly_chart(
            px.line(
                df_dens_pct, x="Ano", y="Percentual",
                color="Região", markers=True,
                title="Participação percentual por região",
            ),
            use_container_width=True,
        )

        st.dataframe(df_dens, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Baixar densidade (CSV)",
            df_dens.to_csv(index=False).encode("utf-8"),
            file_name="densidade_regional.csv", mime="text/csv",
        )

# ---------------- ABA 5 ----------------
with aba5:
    st.subheader("📈 Comparativo entre temporadas")
    clubes = st.multiselect(
        "Clubes",
        sorted(df_clas["Clube"].unique()),
        default=list(
            df_clas.sort_values("Pts", ascending=False)["Clube"].unique()[:5]
        ),
    )
    if clubes:
        df_evol = df_clas[df_clas["Clube"].isin(clubes)].sort_values("Ano")
        st.plotly_chart(
            px.line(
                df_evol, x="Ano", y="Pts", color="Clube",
                markers=True, title="Pontuação por temporada",
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            px.scatter(
                df_evol, x="GM", y="GC", color="Clube",
                size="Pts", hover_data=["Ano", "Pos"],
                title="Ataque vs Defesa (tamanho = pontos)",
            ),
            use_container_width=True,
        )
        st.dataframe(
            df_evol[["Clube", "Ano", "Serie", "Pos", "Pts", "GM", "GC", "SG"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Selecione ao menos um clube.")

# ---------------- Sidebar: downloads + logout ----------------
st.sidebar.divider()
st.sidebar.header("📥 Exportar")
st.sidebar.download_button(
    "Classificação (CSV)",
    df_clas.to_csv(index=False).encode("utf-8"),
    file_name="classificacao_completa.csv", mime="text/csv",
    use_container_width=True,
)
st.sidebar.download_button(
    "Jogadores (CSV)",
    df_jog.to_csv(index=False).encode("utf-8"),
    file_name="jogadores_completo.csv", mime="text/csv",
    use_container_width=True,
)

logout_button()

st.sidebar.divider()
st.sidebar.caption("FCM Unesp — Dashboard Integrado (Streamlit)")
