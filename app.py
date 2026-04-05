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
    st.markdown(
        "Verify that your marketing collaterals — emailers, PDFs, images, or PPTs — "
        "are accurate against your source documents like the placement slip, rater, or policy copy."
    )
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**1. Upload source docs**\nPlacement slip · Rater · Policy copy")
    with col2:
        st.markdown("**2. Upload collaterals**\nEmailers · PDFs · Images · PPTs (up to 5)")
    with col3:
        st.markdown("**3. Get results**\nCorrect · Incorrect · Uncertain — per collateral")
    st.markdown("---")
    pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password to continue")
    if st.button("Continue →"):
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
