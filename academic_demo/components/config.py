import os
import streamlit as st


def get_api_base_url() -> str:
    """Resolve backend URL: env var > Streamlit secrets > localhost fallback."""
    env_url = os.getenv("NORAY_API_URL")
    if env_url:
        return env_url.rstrip("/")

    try:
        if hasattr(st, "secrets") and "NORAY_API_URL" in st.secrets:
            return str(st.secrets["NORAY_API_URL"]).rstrip("/")
    except Exception:
        pass

    return "http://localhost:8001"


API_BASE_URL = get_api_base_url()
