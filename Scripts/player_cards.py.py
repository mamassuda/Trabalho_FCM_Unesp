# player_cards.py
import streamlit as st
import plotly.graph_objects as go


PILARES_COLS = [
    "Nota_Geral_Tecnica",
    "Nota_Geral_Tatica",
    "Nota_Geral_Fisica",
    "Nota_Geral_Mental",
]
PILARES_LABELS = ["Técnica", "Tática", "Física", "Mental"]


def _radar_mini(row, height=220):
    """Radar compacto para o card."""
    vals = [row[c] for c in PILARES_COLS]
    fig = go.Figure(
        go.Scatterpolar(
            r=vals + [vals[0]],
            theta=PILARES_LABELS + [PILARES_LABELS[0]],
            fill="toself",
            line=dict(color="#1f77b4"),
            name="",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], showticklabels=False),
            angularaxis=dict(tickfont=dict(size=9)),
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=height,
    )
    return fig


def _cor_decisao(decisao: str) -> str:
    mapa = {
        "Contratar": "#2ecc71",
        "Monitorar": "#f1c40f",
        "Dispensar": "#e74c3c",
    }
    return mapa.get(str(decisao).strip(), "#95a5a6")


def render_player_card(row, foto_url=None):
    """Renderiza um card individual (foto + métricas + radar)."""
    with st.container(border=True):
        col_foto, col_info = st.columns([1, 2])

        with col_foto:
            if foto_url:
                st.image(foto_url, use_container_width=True)
            else:
                st.markdown(
                    "<div style='height:120px;border-radius:8px;"
                    "background:#eaeaea;display:flex;align-items:center;"
                    "justify-content:center;font-size:48px;'>👤</div>",
                    unsafe_allow_html=True,
                )

        with col_info:
            st.markdown(f"### {row['Nome']}")
            st.caption(f"{row.get('Posicao', '—')} · {row.get('Clube', '—')}")

            decisao = row.get("Decisao", "—")
            cor = _cor_decisao(decisao)
            st.markdown(
                f"<span style='background:{cor};color:white;"
                f"padding:2px 10px;border-radius:12px;font-size:12px;'>"
                f"{decisao}</span>",
                unsafe_allow_html=True,
            )

            st.plotly_chart(
                _radar_mini(row), use_container_width=True,
                key=f"radar_{row['Nome']}",
            )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Técnica", f"{row[PILARES_COLS[0]]:.1f}")
        m2.metric("Tática", f"{row[PILARES_COLS[1]]:.1f}")
        m3.metric("Física", f"{row[PILARES_COLS[2]]:.1f}")
        m4.metric("Mental", f"{row[PILARES_COLS[3]]:.1f}")

        media = sum(row[c] for c in PILARES_COLS) / len(PILARES_COLS)
        st.progress(
            min(media / 5, 1.0),
            text=f"Média geral: {media:.2f} / 5.00",
        )


def render_player_grid(df, cols=3, foto_map=None):
    """Renderiza os jogadores em grade de N colunas."""
    foto_map = foto_map or {}
    if df.empty:
        st.info("Nenhum jogador para exibir com os filtros atuais.")
        return

    nomes = df["Nome"].tolist()
    for i in range(0, len(nomes), cols):
        linha = st.columns(cols)
        for j, nome in enumerate(nomes[i : i + cols]):
            row = df[df["Nome"] == nome].iloc[0]
            with linha[j]:
                render_player_card(row, foto_url=foto_map.get(nome))