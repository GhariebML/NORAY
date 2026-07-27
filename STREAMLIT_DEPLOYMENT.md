# Streamlit Community Cloud Deployment Guide

This guide details how to deploy the **NORAY Academic RAG Demo** to **Streamlit Community Cloud** (share.streamlit.io).

---

## 🏗️ Deployment Architecture

The Streamlit application functions exclusively as a lightweight frontend. It calls the existing production-ready NORAY FastAPI REST backend over HTTPS.

```
[ Streamlit Community Cloud (Frontend) ]
                  │
                  │ (HTTPS Request)
                  ▼
    [ Railway / Render (FastAPI Backend) ]
```

---

## 🚀 Step-by-Step Deployment

### 1. Push to GitHub
Ensure the `academic_demo/` folder and the requirements files are pushed to a public or private GitHub repository.

### 2. Sign In to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Log in using your GitHub account credentials.

### 3. Configure the Application Deployment
Click **New App** and configure the fields:
- **Repository**: Select your repository (e.g., `username/NORAY`).
- **Branch**: Select the active branch (e.g., `main`).
- **Main file path**: Set this to `academic_demo/streamlit_app.py`.

---

## ⚙️ Environment Secrets Configuration

Before deploying, click **Advanced settings...** or configure the app's Secrets:

Add the backend URL in the Secrets textarea:
```toml
# .streamlit/secrets.toml format
NORAY_API_URL = "https://your-fastapi-backend-url.up.railway.app"
```

*Note: Replace the URL with your active public FastAPI endpoint hosted on Railway or Render.*

---

## 🧪 Verification after Deployment
Once Streamlit builds and launches the container:
1. Check the landing page **Connection Status** section. It should display a green **Connected to FastAPI Backend** state.
2. Go to page **1_Upload** and index a test PDF.
3. Query the index on **2_Ask** to verify fused vector matches and context syntheses.
