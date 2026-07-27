import os
import streamlit as st

def get_api_base_url() -> str:
    # 1. Environment Variable
    env_url = os.getenv("NORAY_API_URL")
    if env_url:
        return env_url.rstrip("/")

    # 2. Streamlit Secrets
    try:
        if hasattr(st, "secrets") and "NORAY_API_URL" in st.secrets:
            return str(st.secrets["NORAY_API_URL"]).rstrip("/")
    except Exception:
        pass

    # 3. Default fallback for local execution
    return "http://localhost:8001"

API_BASE_URL = get_api_base_url()
print(f"[Streamlit Config] Resolved NORAY Backend Base URL: {API_BASE_URL}")
