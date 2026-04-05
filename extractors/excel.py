import io
import openpyxl


def _is_empty(val) -> bool:
    if val is None:
        return True
    return str(val).strip() in ("", "nan", "None")


def extract_excel_facts(file_bytes: bytes) -> dict:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception:
        return {}

    facts = {}

    if "Policy Info" in wb.sheetnames:
        facts["policy_info"] = _extract_policy_info(wb["Policy Info"])

    if "Modular Plan" in wb.sheetnames:
        facts["plans"] = _extract_modular_plans(wb["Modular Plan"])

    if "Raters" in wb.sheetnames:
        facts["benefits"] = _extract_rater_benefits(wb["Raters"])

    return facts


def _extract_policy_info(ws) -> dict:
    result = {}
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 2:
            continue
        label = str(row[0]).strip() if row[0] is not None else ""
        value = row[1]
        if label and not _is_empty(value) and label not in ("nan", "Modular Policy Placement Slip Details"):
            result[label] = str(value).strip()
    return result


def _extract_modular_plans(ws) -> dict:
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return {}

    # Row index 1 (0-based) has plan names starting from column index 5 (0-based)
    plan_name_row = rows[1]
    plan_cols, plan_names = [], []
    for col_idx in range(5, len(plan_name_row)):
        val = plan_name_row[col_idx]
        if not _is_empty(val):
            plan_cols.append(col_idx)
            plan_names.append(str(val).strip())

    plans: dict = {name: {} for name in plan_names}

    # Benefit data rows start at index 6 (0-based)
    for row in rows[6:]:
        if not row or len(row) < 3:
            continue
        benefit = str(row[2]).strip() if row[2] is not None else ""
        if _is_empty(benefit):
            continue
        for col_idx, plan_name in zip(plan_cols, plan_names):
            val = row[col_idx] if col_idx < len(row) else None
            if not _is_empty(val):
                plans[plan_name][benefit] = str(val).strip()

    return plans


def _extract_rater_benefits(ws) -> list:
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # First row is header
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    name_col = next((i for i, h in enumerate(headers) if "Benefit name" in h), None)
    premium_col = next((i for i, h in enumerate(headers) if h == "Premium"), None)

    if name_col is None:
        return []

    benefits = []
    for row in rows[1:]:
        if not row or len(row) <= name_col:
            continue
        name = str(row[name_col]).strip() if row[name_col] is not None else ""
        if _is_empty(name):
            continue
        premium = 0.0
        if premium_col is not None and len(row) > premium_col and row[premium_col] is not None:
            try:
                premium = float(row[premium_col])
            except (ValueError, TypeError):
                premium = 0.0
        benefits.append({"name": name, "premium": premium})
    return benefits
