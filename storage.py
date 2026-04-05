from supabase import create_client
import streamlit as st

BUCKET = "verification-uploads"


def _client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def upload_file(verification_id: str, file_name: str, file_bytes: bytes) -> str:
    path = f"{verification_id}/{file_name}"
    _client().storage.from_(BUCKET).upload(path, file_bytes, {"upsert": "true"})
    return path
