import json
import anthropic
import streamlit as st


def format_facts(facts_list: list) -> str:
    lines = []
    for facts in facts_list:
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


def _build_content(
    prompt: str,
    collateral_text: str,
    all_images: list,
) -> list:
    full_text = prompt
    if collateral_text:
        full_text += f"\n\nCOLLATERAL TEXT CONTENT:\n{collateral_text}"

    content = [{"type": "text", "text": full_text}]

    for b64, media_type in all_images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            },
        })

    return content


def verify_collateral(
    facts_text: str,
    source_pdf_images: list,
    collateral_text: str,
    collateral_images: list,
) -> dict:
    prompt = f"""You are a fact-checker for insurance marketing collaterals at Loop Health.

SOURCE OF TRUTH (from official policy documents):
{facts_text}

{"Source policy document images follow (marked SOURCE)." if source_pdf_images else ""}

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

    # Source PDF images come first (context), then collateral images
    all_images = source_pdf_images + collateral_images

    content = _build_content(prompt, collateral_text, all_images)

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wraps JSON anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
