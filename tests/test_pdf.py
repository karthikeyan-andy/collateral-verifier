import pytest
from extractors.pdf import extract_pdf_images


def _minimal_pdf_bytes() -> bytes:
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000369 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
452
%%EOF"""


def test_extract_pdf_images_returns_list():
    images = extract_pdf_images(_minimal_pdf_bytes())
    assert isinstance(images, list)
    assert len(images) == 1


def test_extract_pdf_images_returns_bytes():
    images = extract_pdf_images(_minimal_pdf_bytes())
    assert isinstance(images[0], bytes)
    assert len(images[0]) > 100  # PNG has some size
