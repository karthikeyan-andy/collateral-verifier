from supabase import create_client, Client
import streamlit as st

BUCKET = "verification-uploads"


@st.cache_resource
def _client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


def upload_file(verification_id: str, file_name: str, file_bytes: bytes) -> str:
    path = f"{verification_id}/{file_name}"
    _client().storage.from_(BUCKET).upload(
        path, file_bytes, file_options={"upsert": "true"}
    )
    return path
