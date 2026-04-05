import base64
from extractors.image import image_to_base64, get_media_type


def test_image_to_base64_roundtrips():
    raw = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    b64, media_type = image_to_base64(raw, "photo.png")
    assert media_type == "image/png"
    assert base64.b64decode(b64) == raw


def test_get_media_type_png():
    assert get_media_type("foo.png") == "image/png"


def test_get_media_type_jpg():
    assert get_media_type("foo.jpg") == "image/jpeg"
    assert get_media_type("foo.jpeg") == "image/jpeg"


def test_get_media_type_webp():
    assert get_media_type("foo.webp") == "image/webp"


def test_get_media_type_unknown_defaults_to_png():
    assert get_media_type("foo.bmp") == "image/png"
