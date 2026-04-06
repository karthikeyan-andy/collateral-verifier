import streamlit as st

st.set_page_config(
    page_title="Collateral Verifier",
    page_icon="🔍",
    layout="wide",
)

from tabs import verify, history, metrics

tab1, tab2, tab3 = st.tabs(["🔍 Verify", "📋 History", "📊 Metrics"])

with tab1:
    verify.render()

with tab2:
    history.render()

with tab3:
    metrics.render()
