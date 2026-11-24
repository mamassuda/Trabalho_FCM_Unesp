# auth.py
import streamlit as st
import hashlib


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def check_login() -> bool:
    """
    Verifica autenticação via st.secrets.

    Em .streamlit/secrets.toml:
        [auth]
        users = { "admin" = "<sha256-da-senha>" }

    Para gerar o hash:
        python -c "import hashlib;print(hashlib.sha256(b'suasenha').hexdigest())"
    """
    if st.session_state.get("autenticado"):
        return True

    st.markdown("## 🔐 Acesso restrito")
    st.caption("Dashboard FCM Unesp — Scouting & Classificação")

    with st.form("login"):
        user = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        ok = st.form_submit_button("Entrar", use_container_width=True)

    if ok:
        try:
            users = st.secrets["auth"]["users"]
        except (KeyError, FileNotFoundError):
            st.error(
                "Arquivo `.streamlit/secrets.toml` não configurado. "
                "Consulte as instruções no README."
            )
            return False

        if user in users and users[user] == _hash(senha):
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = user
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    return False


def logout_button():
    """Botão de sair na sidebar."""
    st.sidebar.divider()
    st.sidebar.caption(
        f"👤 Logado como **{st.session_state.get('usuario', '—')}**"
    )
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()