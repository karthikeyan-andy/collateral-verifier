import base64


_MEDIA_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
}


def get_media_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return _MEDIA_TYPES.get(ext, "image/png")


def image_to_base64(file_bytes: bytes, filename: str) -> tuple[str, str]:
    media_type = get_media_type(filename)
    return base64.standard_b64encode(file_bytes).decode(), media_type
