import base64
import json
import re
import google.generativeai as genai
import streamlit as st


def format_facts(facts_list: list) -> str:
    lines = []
    for facts in facts_list:
        if "raw_sheets" in facts:
            for sheet_name, content in facts["raw_sheets"].items():
                lines.append(f"\n=== SHEET: {sheet_name} ===")
                lines.append(content)

        if "policy_info" in facts:
            lines.append("=== POLICY INFORMATION ===")
            for k, v in facts["policy_info"].items():
                lines.append(f"  {k}: {v}")

        if "plans" in facts:
            lines.append("\n=== INSURANCE PLANS ===")
            for plan_name, benefits in facts["plans"].items():
                lines.append(f"\n  -- {plan_name} Plan --")
                for benefit, value in benefits.items():
                    lines.append(f"    {benefit}: {value}")

        if "benefits" in facts:
            lines.append("\n=== FLEX BENEFITS & PREMIUMS (incl. GST) ===")
            for b in facts["benefits"]:
                lines.append(f"  {b['name']}: \u20b9{b['premium']}")

    return "\n".join(lines)


def verify_collateral(
    facts_text: str,
    source_pdf_images: list,
    collateral_text: str,
    collateral_images: list,
) -> dict:
    prompt = f"""You are a fact-checker for insurance marketing collaterals at Loop Health.

SOURCE OF TRUTH (from official policy documents):
{facts_text}

Your task: Review the marketing collateral content below and check every specific claim \
(coverage amounts, waiting periods, premium figures, plan names, insurer name, benefits, limits) \
against the source of truth.

For EACH claim found in the collateral:
- Identify the field (e.g. "Room Rent Restriction", "Base Sum Insured", "Maternity Cover")
- Note what the collateral claims
- Check it against the source
- Mark status: correct, incorrect, or uncertain (if source doesn't mention it at all)

Return ONLY valid JSON — no markdown, no explanation, just the JSON object:
{{
  "summary": "2-3 sentence overview of accuracy",
  "check_items": [
    {{
      "field_name": "field being checked",
      "claimed_value": "what the collateral says",
      "actual_value": "what the source says (or 'Not mentioned in source')",
      "status": "correct|incorrect|uncertain"
    }}
  ]
}}"""

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    parts = [prompt]

    if collateral_text:
        parts.append(f"\n\nCOLLATERAL TEXT CONTENT:\n{collateral_text}")

    for b64, media_type in (source_pdf_images + collateral_images):
        image_bytes = base64.b64decode(b64)
        parts.append({"inline_data": {"mime_type": media_type, "data": image_bytes}})

    response = model.generate_content(parts)
    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "summary": "Could not parse verification result. Model returned an unexpected format.",
            "check_items": [],
        }
