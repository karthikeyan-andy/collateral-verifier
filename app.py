import streamlit as st

st.set_page_config(
    page_title="Collateral Verifier",
    page_icon="🔍",
    layout="wide",
)

# Password gate
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔍 Collateral Verifier")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == st.secrets.get("APP_PASSWORD", ""):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

from tabs import verify, history, metrics

tab1, tab2, tab3 = st.tabs(["🔍 Verify", "📋 History", "📊 Metrics"])

with tab1:
    verify.render()

with tab2:
    history.render()

with tab3:
    metrics.render()
