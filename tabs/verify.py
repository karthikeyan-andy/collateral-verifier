import io
import re
import urllib.request
import streamlit as st
from extractors.excel import extract_excel_facts
from extractors.pdf import extract_pdf_images
from extractors.image import image_to_base64, get_media_type
from extractors.ppt import extract_ppt
from verifier import format_facts, verify_collateral
from tabs import _status_icon


def _gsheets_to_bytes(url: str) -> bytes | None:
    """Convert a Google Sheets share URL to CSV bytes."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        return None
    sheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        with urllib.request.urlopen(export_url, timeout=15) as r:
            return r.read()
    except Exception:
        return None


def _extract_source(file) -> tuple[dict, list[tuple[str, str]]]:
    name = file.name.lower()
    data = file.read()
    if name.endswith((".xlsx", ".xls")):
        return extract_excel_facts(data), []
    if name.endswith(".pdf"):
        imgs = extract_pdf_images(data)
        b64_imgs = [image_to_base64(img, "page.png") for img in imgs]
        return {}, b64_imgs
    return {}, []


def _extract_collateral(file) -> tuple[str, list[tuple[str, str]], str]:
    name = file.name.lower()
    data = file.read()
    if name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        b64, mt = image_to_base64(data, file.name)
        return "", [(b64, mt)], "image"
    if name.endswith(".pdf"):
        imgs = extract_pdf_images(data)
        b64_imgs = [image_to_base64(img, "page.png") for img in imgs]
        return "", b64_imgs, "pdf"
    if name.endswith(".pptx"):
        text, imgs = extract_ppt(data)
        b64_imgs = [image_to_base64(img, "slide.png") for img in imgs]
        return text, b64_imgs, "ppt"
    return "", [], "unknown"


def render():
    st.header("Verify Collaterals")

    with st.form("verify_form"):
        label = st.text_input("Run label (optional)", placeholder="e.g. Situs Jan emailers")

        source_files = st.file_uploader(
            "Source documents (placement slip, rater, policy copy) — max 3",
            accept_multiple_files=True,
            type=["xlsx", "xls", "pdf"],
            key="source_files",
        )

        gsheets_url = st.text_input(
            "Or paste a Google Sheets link (must be set to 'Anyone with link can view')",
            placeholder="https://docs.google.com/spreadsheets/d/...",
        )

        collateral_files = st.file_uploader(
            "Collaterals to verify — max 5",
            accept_multiple_files=True,
            type=["jpg", "jpeg", "png", "webp", "pdf", "pptx"],
            key="collateral_files",
        )

        submitted = st.form_submit_button("Verify", type="primary")

    if not submitted:
        return

    has_source = bool(source_files) or bool(gsheets_url.strip())
    if not has_source:
        st.error("Upload at least one source document or paste a Google Sheets link.")
        return
    if not collateral_files:
        st.error("Upload at least one collateral.")
        return
    if len(source_files) > 3:
        st.error("Maximum 3 source documents.")
        return
    if len(collateral_files) > 5:
        st.error("Maximum 5 collaterals.")
        return

    with st.spinner("Extracting source documents..."):
        all_facts = []
        all_source_pdf_images = []

        for f in source_files:
            facts, pdf_imgs = _extract_source(f)
            if facts:
                all_facts.append(facts)
            all_source_pdf_images.extend(pdf_imgs)

        if gsheets_url.strip():
            with st.spinner("Fetching Google Sheet..."):
                sheet_bytes = _gsheets_to_bytes(gsheets_url.strip())
                if sheet_bytes:
                    facts = extract_excel_facts(sheet_bytes)
                    if facts:
                        all_facts.append(facts)
                else:
                    st.warning("Could not fetch Google Sheet. Make sure it's set to 'Anyone with link can view'.")

    facts_text = format_facts(all_facts)
    if not facts_text and not all_source_pdf_images:
        st.error("Could not extract any data from source documents.")
        return

    st.subheader("Results")

    for col_file in collateral_files:
        col_file.seek(0)
        try:
            with st.spinner(f"Verifying {col_file.name}..."):
                col_text, col_images, col_type = _extract_collateral(col_file)
                result = verify_collateral(facts_text, all_source_pdf_images, col_text, col_images)
        except Exception as e:
            st.error(f"Failed to verify {col_file.name}: {e}")
            continue

        items = result.get("check_items", [])
        fail_count = sum(1 for i in items if i["status"] == "incorrect")
        uncertain_count = sum(1 for i in items if i["status"] == "uncertain")

        header_icon = "❌" if fail_count else "✅"
        with st.expander(
            f"{header_icon} {col_file.name} — {fail_count} errors, {uncertain_count} uncertain",
            expanded=True,
        ):
            st.write(result.get("summary", ""))

            if items:
                # Build table without pandas
                col_headers = ["Field", "Collateral Claims", "Source Says", "Status"]
                rows = []
                for item in items:
                    status_raw = item.get("status", "")
                    status_display = _status_icon(status_raw) + " " + status_raw if status_raw else "❓"
                    rows.append({
                        "Field": item.get("field_name", ""),
                        "Collateral Claims": item.get("claimed_value", ""),
                        "Source Says": item.get("actual_value", ""),
                        "Status": status_display,
                    })
                st.table(rows)
