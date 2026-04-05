import fitz  # pymupdf


def extract_pdf_images(file_bytes: bytes, dpi: int = 150) -> list[bytes]:
    """Render each PDF page as PNG bytes."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images
