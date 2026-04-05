from supabase import create_client, Client
import streamlit as st
from collections import Counter


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def insert_verification(label: str, source_docs: list[str]) -> str:
    result = _client().table("verifications").insert({
        "label": label or None,
        "source_docs": source_docs,
    }).execute()
    return result.data[0]["id"]


def insert_collateral_result(
    verification_id: str,
    file_name: str,
    file_type: str,
    summary: str,
    pass_count: int,
    fail_count: int,
    uncertain_count: int,
) -> str:
    result = _client().table("collateral_results").insert({
        "verification_id": verification_id,
        "file_name": file_name,
        "file_type": file_type,
        "summary": summary,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "uncertain_count": uncertain_count,
    }).execute()
    return result.data[0]["id"]


def insert_check_items(collateral_result_id: str, items: list[dict]) -> None:
    rows = [
        {
            "collateral_result_id": collateral_result_id,
            "field_name": item["field_name"],
            "claimed_value": item["claimed_value"],
            "actual_value": item["actual_value"],
            "status": item["status"],
        }
        for item in items
    ]
    if rows:
        _client().table("check_items").insert(rows).execute()


def fetch_history() -> list[dict]:
    result = _client().table("verifications").select(
        "id, created_at, label, source_docs, collateral_results(id, file_name, file_type, fail_count, uncertain_count, pass_count)"
    ).order("created_at", desc=True).limit(100).execute()
    return result.data


def fetch_check_items(collateral_result_id: str) -> list[dict]:
    result = _client().table("check_items").select("*").eq(
        "collateral_result_id", collateral_result_id
    ).execute()
    return result.data


def fetch_metrics() -> dict:
    c = _client()

    total_runs = c.table("verifications").select("id", count="exact").execute().count

    items = c.table("check_items").select("status, field_name").execute().data
    status_counts = Counter(i["status"] for i in items)

    collaterals = c.table("collateral_results").select("file_type, fail_count").execute().data
    errors_by_type: dict[str, int] = {}
    for row in collaterals:
        ft = row["file_type"]
        errors_by_type[ft] = errors_by_type.get(ft, 0) + (row["fail_count"] or 0)

    wrong_fields = Counter(
        i["field_name"] for i in items if i["status"] == "incorrect" and i["field_name"]
    )

    return {
        "total_runs": total_runs or 0,
        "total_correct": status_counts.get("correct", 0),
        "total_incorrect": status_counts.get("incorrect", 0),
        "total_uncertain": status_counts.get("uncertain", 0),
        "errors_by_type": errors_by_type,
        "top_wrong_fields": wrong_fields.most_common(10),
    }
