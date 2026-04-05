import io
import pandas as pd


def extract_excel_facts(file_bytes: bytes) -> dict:
    xls = io.BytesIO(file_bytes)
    try:
        all_sheets = pd.read_excel(xls, sheet_name=None, engine="openpyxl")
    except Exception:
        return {}

    facts = {}

    if "Policy Info" in all_sheets:
        facts["policy_info"] = _extract_policy_info(all_sheets["Policy Info"])

    if "Modular Plan" in all_sheets:
        raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Modular Plan",
                            header=None, engine="openpyxl")
        facts["plans"] = _extract_modular_plans(raw)

    if "Raters" in all_sheets:
        facts["benefits"] = _extract_rater_benefits(all_sheets["Raters"])

    return facts


def _extract_policy_info(df: pd.DataFrame) -> dict:
    result = {}
    for _, row in df.iterrows():
        label = str(row.iloc[0]).strip()
        value = row.iloc[1] if len(row) > 1 else None
        if pd.notna(value) and label not in ("nan", "", "Modular Policy Placement Slip Details"):
            result[label] = str(value).strip()
    return result


def _extract_modular_plans(df: pd.DataFrame) -> dict:
    if df.shape[0] < 2:
        return {}

    # Row index 1 has plan names starting from column index 5
    plan_name_row = df.iloc[1]
    plan_cols, plan_names = [], []
    for col_idx in range(5, df.shape[1]):
        val = plan_name_row.iloc[col_idx]
        if pd.notna(val) and str(val).strip() not in ("nan", ""):
            plan_cols.append(col_idx)
            plan_names.append(str(val).strip())

    plans: dict = {name: {} for name in plan_names}

    # Benefit data rows start at index 6
    for row_idx in range(6, df.shape[0]):
        row = df.iloc[row_idx]
        benefit = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        if not benefit or benefit == "nan":
            continue
        for col_idx, plan_name in zip(plan_cols, plan_names):
            val = row.iloc[col_idx] if col_idx < df.shape[1] else None
            if pd.notna(val):
                plans[plan_name][benefit] = str(val).strip()

    return plans


def _extract_rater_benefits(df: pd.DataFrame) -> list:
    name_col = "Benefit name (for reference only)"
    premium_col = "Premium"
    if name_col not in df.columns:
        return []

    benefits = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name or name == "nan":
            continue
        premium = float(row[premium_col]) if premium_col in df.columns and pd.notna(row.get(premium_col)) else 0.0
        benefits.append({"name": name, "premium": premium})
    return benefits
