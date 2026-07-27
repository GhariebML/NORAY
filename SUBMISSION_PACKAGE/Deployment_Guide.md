# Multi-Cloud Deployment Guide

This document summarizes production deployment steps across cloud targets.

---

## 🚀 Target Platforms

### 1. Vercel (Next.js Frontend)
- Set root directory to `frontend`.
- Environment variable: `NEXT_PUBLIC_API_URL` pointing to backend host.

### 2. Railway / Render (FastAPI Backend & Databases)
- Deploy PostgreSQL and Redis services.
- Deploy `qdrant/qdrant:v1.7.0` container.
- Deploy root `Dockerfile` for FastAPI app.
- Set environment variables (`DATABASE_URL`, `REDIS_URL`, `QDRANT_URL`, `ALLOWED_ORIGINS`).

### 3. Streamlit Community Cloud (Academic Demo)
- Deploy `academic_demo/streamlit_app.py`.
- Add secret variable `NORAY_API_URL` in dashboard settings.
