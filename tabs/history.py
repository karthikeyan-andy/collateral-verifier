import streamlit as st
import db


def _status_icon(status: str) -> str:
    return {"correct": "✅", "incorrect": "❌", "uncertain": "⚠️"}.get(status, "❓")


def render():
    st.header("Verification History")

    runs = db.fetch_history()

    if not runs:
        st.info("No verifications yet. Go to Verify to run your first check.")
        return

    for run in runs:
        label = run.get("label") or "Unlabelled run"
        created = run["created_at"][:10]
        collaterals = run.get("collateral_results", [])
        total_errors = sum(c.get("fail_count", 0) or 0 for c in collaterals)
        collateral_count = len(collaterals)

        header = f"{'❌' if total_errors else '✅'} **{label}** — {created} | {collateral_count} collateral(s) | {total_errors} error(s)"

        with st.expander(header):
            sources = run.get("source_docs") or []
            if sources:
                st.caption("Source docs: " + ", ".join(sources))

            for col in collaterals:
                st.markdown(f"**{col['file_name']}** (`{col['file_type']}`)")
                st.write(
                    f"✅ {col.get('pass_count', 0)}  ❌ {col.get('fail_count', 0)}  ⚠️ {col.get('uncertain_count', 0)}"
                )

                items = db.fetch_check_items(col["id"])
                if items:
                    import pandas as pd
                    df = pd.DataFrame(items)[["field_name", "claimed_value", "actual_value", "status"]]
                    df.columns = ["Field", "Collateral Claims", "Source Says", "Status"]
                    df["Status"] = df["Status"].apply(lambda s: _status_icon(s) + " " + s)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                st.divider()
