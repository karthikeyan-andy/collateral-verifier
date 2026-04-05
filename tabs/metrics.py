import streamlit as st
import db
import pandas as pd


def render():
    st.header("Metrics")

    metrics = db.fetch_metrics()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", metrics["total_runs"])
    col2.metric("Correct Claims", metrics["total_correct"])
    col3.metric("Errors Found", metrics["total_incorrect"])
    col4.metric("Uncertain", metrics["total_uncertain"])

    st.divider()

    if metrics["errors_by_type"]:
        st.subheader("Errors by Collateral Type")
        df_type = pd.DataFrame(
            list(metrics["errors_by_type"].items()),
            columns=["Type", "Errors"]
        ).set_index("Type")
        st.bar_chart(df_type)
    else:
        st.info("No error data yet.")

    if metrics["top_wrong_fields"]:
        st.subheader("Most Commonly Wrong Fields")
        df_fields = pd.DataFrame(metrics["top_wrong_fields"], columns=["Field", "Error Count"])
        st.dataframe(df_fields, use_container_width=True, hide_index=True)
    else:
        st.info("No field-level errors yet.")
