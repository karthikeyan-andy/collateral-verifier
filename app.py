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
    st.markdown("**An internal tool for the HealthFlex Product Success team.**")
    st.markdown(
        "Upload your source documents (placement slip, rater, policy copy) and up to 5 "
        "marketing collaterals (emailers, PDFs, images, PPTs). The tool checks whether "
        "the information in your collaterals is accurate against the source."
    )
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**📄 Source docs**\nPlacement slip · Rater · Policy copy")
    with col2:
        st.markdown("**🎨 Collaterals**\nEmailers · PDFs · Images · PPTs (up to 5)")
    with col3:
        st.markdown("**✅ Results**\nCorrect · Incorrect · Uncertain — per collateral")
    st.markdown("---")
    pwd = st.text_input("Enter access password to continue", type="password")
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
