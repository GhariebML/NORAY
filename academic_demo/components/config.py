import os

# Backend API Configuration
API_BASE_URL = os.getenv("NORAY_API_URL", "http://localhost:8001")
print(f"[Streamlit Config] Connecting to NORAY Backend at: {API_BASE_URL}")
