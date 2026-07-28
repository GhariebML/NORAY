import os
import streamlit as st


def get_api_base_url() -> str:
    """Resolve backend URL: env var > Streamlit secrets > Streamlit Cloud default > localhost fallback."""
    # 1. Environment variable
    env_url = os.getenv("NORAY_API_URL")
    if env_url:
        return env_url.rstrip("/")

    # 2. Streamlit secrets
    try:
        if hasattr(st, "secrets") and "NORAY_API_URL" in st.secrets:
            return str(st.secrets["NORAY_API_URL"]).rstrip("/")
    except Exception:
        pass

    # 3. Streamlit Cloud environment detection
    is_cloud = (
        os.getenv("STREAMLIT_SHARING_MODE") is not None
        or os.environ.get("HOME") == "/home/appuser"
        or os.name != "nt"  # Since local environment is Windows (NT)
    )
    if is_cloud:
        return "https://noray-backend.onrender.com"

    # 4. Local execution fallback
    return "http://localhost:8001"


API_BASE_URL = get_api_base_url()
