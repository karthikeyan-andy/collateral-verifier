import streamlit as st
from extractors.excel import extract_excel_facts
from extractors.pdf import extract_pdf_images
from extractors.image import image_to_base64, get_media_type
from extractors.ppt import extract_ppt
from verifier import format_facts, verify_collateral
import db
import storage


def _extract_source(file) -> tuple[dict, list[tuple[str, str]]]:
    """Returns (facts_dict, pdf_images_b64)."""
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
    """Returns (text, images_b64, file_type)."""
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


def _status_icon(status: str) -> str:
    return {"correct": "✅", "incorrect": "❌", "uncertain": "⚠️"}.get(status, "❓")


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

        collateral_files = st.file_uploader(
            "Collaterals to verify (emailers) — max 5",
            accept_multiple_files=True,
            type=["jpg", "jpeg", "png", "webp", "pdf", "pptx"],
            key="collateral_files",
        )

        submitted = st.form_submit_button("Verify", type="primary")

    if not submitted:
        return

    if not source_files:
        st.error("Upload at least one source document.")
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
        source_names = []
        for f in source_files:
            facts, pdf_imgs = _extract_source(f)
            source_names.append(f.name)
            if facts:
                all_facts.append(facts)
            all_source_pdf_images.extend(pdf_imgs)

    facts_text = format_facts(all_facts)
    if not facts_text and not all_source_pdf_images:
        st.error("Could not extract any data from source documents.")
        return

    verification_id = db.insert_verification(label, source_names)

    for source_file in source_files:
        source_file.seek(0)
        storage.upload_file(verification_id, source_file.name, source_file.read())

    st.subheader("Results")

    for col_file in collateral_files:
        col_file.seek(0)
        storage.upload_file(verification_id, col_file.name, col_file.read())

        col_file.seek(0)
        with st.spinner(f"Verifying {col_file.name}..."):
            col_text, col_images, col_type = _extract_collateral(col_file)
            result = verify_collateral(facts_text, all_source_pdf_images, col_text, col_images)

        items = result.get("check_items", [])
        pass_count = sum(1 for i in items if i["status"] == "correct")
        fail_count = sum(1 for i in items if i["status"] == "incorrect")
        uncertain_count = sum(1 for i in items if i["status"] == "uncertain")

        collateral_result_id = db.insert_collateral_result(
            verification_id, col_file.name, col_type,
            result.get("summary", ""), pass_count, fail_count, uncertain_count,
        )
        db.insert_check_items(collateral_result_id, items)

        header_icon = "❌" if fail_count else "✅"
        with st.expander(
            f"{header_icon} {col_file.name} — {fail_count} errors, {uncertain_count} uncertain",
            expanded=True,
        ):
            st.write(result.get("summary", ""))

            if items:
                import pandas as pd
                df = pd.DataFrame(items)[["field_name", "claimed_value", "actual_value", "status"]]
                df.columns = ["Field", "Collateral Claims", "Source Says", "Status"]
                df["Status"] = df["Status"].apply(lambda s: _status_icon(s) + " " + s)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Status": st.column_config.TextColumn(width="small"),
                    },
                )
