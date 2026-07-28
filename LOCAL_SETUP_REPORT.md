# NORAY — Local Setup Report

**Generated:** 2026-07-28 11:33 GMT+3  
**Environment:** Windows 11 (26200), PowerShell  
**Status:** ✅ All Services Running

---

## 1. Environment Summary

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.14.3 | ✅ Installed |
| Node.js | 24.18.0 | ✅ Installed |
| npm | 11.16.0 | ✅ Installed |

---

## 2. Services Running

| Service | Port | Status | PID |
|---------|------|--------|-----|
| **FastAPI Backend** | 8001 | ✅ Running | 61732 |
| **Next.js Frontend** | 3000 | ✅ Running | 72052 |
| **Streamlit Demo** | 8501 | ✅ Running | 41856 |
| **PostgreSQL** | 5432 | ✅ Running | 61904 |
| **Qdrant** | 6333 | ✅ Running | 61904 |
| **Redis** | 6379 | ✅ Running | 61904 |
| **Ollama** | 11434 | ✅ Running | 23820 |

---

## 3. URLs & Endpoints

| Service | URL | Verified |
|---------|-----|----------|
| Frontend | http://localhost:3000 | ✅ 200 OK |
| Backend | http://localhost:8001 | ✅ 200 OK |
| Swagger Docs | http://localhost:8001/docs | ✅ 200 OK |
| Health Check | http://localhost:8001/health | ✅ `{"status":"healthy"}` |
| API Health | http://localhost:8001/api/health | ✅ All subsystems healthy |
| AI Status | http://localhost:8001/api/ai/status | ✅ Gemini active |
| Documents | http://localhost:8001/api/documents/list | ✅ 80+ documents indexed |
| Profile | http://localhost:8001/api/profile | ✅ 200 OK |
| DB Health | http://localhost:8001/api/health/database | ✅ PostgreSQL healthy |
| Vector Health | http://localhost:8001/api/health/vector | ✅ Qdrant healthy |
| Streamlit | http://localhost:8501 | ✅ Healthy |

---

## 4. Frontend Pages Verified

All 13 frontend routes return HTTP 200:

| Page | URL | Status |
|------|-----|--------|
| Dashboard | http://localhost:3000/ | ✅ 200 |
| Workspace | http://localhost:3000/workspace | ✅ 200 |
| Documents | http://localhost:3000/documents | ✅ 200 |
| Jobs | http://localhost:3000/jobs | ✅ 200 |
| Scholarships | http://localhost:3000/scholarships | ✅ 200 |
| Analytics | http://localhost:3000/analytics | ✅ 200 |
| Diagnostics | http://localhost:3000/diagnostics | ✅ 200 |
| Settings | http://localhost:3000/settings | ✅ 200 |
| Memory | http://localhost:3000/memory | ✅ 200 |
| Command Center | http://localhost:3000/command-center | ✅ 200 |
| Profile | http://localhost:3000/profile | ✅ 200 |
| Upskill | http://localhost:3000/upskill | ✅ 200 |
| Tracker | http://localhost:3000/tracker | ✅ 200 |

---

## 5. Installed Python Packages

### Core Backend
| Package | Version |
|---------|---------|
| fastapi | 0.136.3 |
| uvicorn | 0.49.0 |
| pydantic | 2.12.5 |
| pydantic-settings | 2.14.0 |
| sqlalchemy | 2.0.48 |
| alembic | 1.18.4 |
| httpx | 0.28.1 |
| structlog | 26.1.0 |
| python-dotenv | 1.2.2 |

### AI & RAG
| Package | Version |
|---------|---------|
| sentence-transformers | 5.4.1 |
| qdrant-client | 1.18.0 |
| rank-bm25 | 0.2.2 |

### Document Processing
| Package | Version |
|---------|---------|
| pdfplumber | 0.11.10 |
| pymupdf | 1.27.2.3 |
| python-docx | 1.2.0 |
| pillow | 12.2.0 |

### Infrastructure
| Package | Version |
|---------|---------|
| psycopg2-binary | 2.9.12 |
| redis | 5.3.1 |
| psutil | 7.2.2 |
| GPUtil | 1.4.0 |

### Academic Demo
| Package | Version |
|---------|---------|
| streamlit | 1.57.0 |
| requests | (installed) |

---

## 6. Frontend Packages

All npm dependencies installed in `frontend/node_modules/`:

| Package | Version |
|---------|---------|
| next | 16.2.7 |
| react | 19.2.4 |
| react-dom | 19.2.4 |
| zustand | 5.x |
| recharts | 3.x |
| @xyflow/react | 12.x |
| framer-motion | 12.x |
| lucide-react | 1.x |
| tailwindcss | 4.x |
| typescript | 5.x |

---

## 7. Environment Variables

### Configured in `.env`

| Variable | Value | Status |
|----------|-------|--------|
| `ENVIRONMENT` | development | ✅ |
| `POSTGRES_USER` | noray | ✅ |
| `POSTGRES_PASSWORD` | noray_dev | ✅ |
| `POSTGRES_DB` | noray_db | ✅ |
| `POSTGRES_HOST` | localhost | ✅ |
| `POSTGRES_PORT` | 5432 | ✅ |
| `QDRANT_HOST` | localhost | ✅ |
| `QDRANT_PORT` | 6333 | ✅ |
| `REDIS_HOST` | localhost | ✅ |
| `REDIS_PORT` | 6379 | ✅ |
| `OLLAMA_BASE_URL` | http://localhost:11434/v1 | ✅ |
| `ALLOW_OFFLINE` | true | ✅ |
| `AI_PROVIDER` | auto | ✅ |
| `GOOGLE_API_KEY` | (set) | ✅ |
| `OPENROUTER_API_KEY` | (set) | ✅ |
| `TOGETHER_API_KEY` | (set) | ✅ |
| `DEEPSEEK_API_KEY` | (set) | ✅ |

### Configured in `frontend/.env.local`

| Variable | Value | Status |
|----------|-------|--------|
| `NEXT_PUBLIC_API_URL` | http://localhost:8001 | ✅ |

### Missing / Placeholder Keys

| Variable | Status | Impact |
|----------|--------|--------|
| `MIMIO_API_KEY` | ❌ Not set | MiMo provider unhealthy (non-critical, Gemini active) |
| `MISTRAL_API_KEY` | ❌ Not set | Mistral provider unavailable (non-critical) |
| `ANTHROPIC_API_KEY` | ❌ Not set | Anthropic shows healthy but may have limited usage |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | ❌ Not set | Job search via Adzuna unavailable |
| `TAVILY_API_KEY` | ❌ Not set | Web search unavailable |
| `SERPAPI_API_KEY` | ❌ Not set | SerpAPI search unavailable |
| `LINKEDIN_API_KEY` | ❌ Not set | LinkedIn import unavailable |

---

## 8. Detected Issues

| Issue | Severity | Status |
|-------|----------|--------|
| MiMo provider unhealthy (1677 failures) | Low | Non-critical — Gemini is active fallback |
| Slow filesystem (Next.js Turbopack) | Low | First compile ~30s, subsequent loads fast |
| System diagnostics endpoint timeout | Low | Comprehensive probing causes timeout on slow systems |
| Duplicate test document chunks in Qdrant | Low | Test data artifact — does not affect operation |

---

## 9. Resolved Issues

| Issue | Resolution |
|-------|-----------|
| Frontend `.env.local` missing | Created with `NEXT_PUBLIC_API_URL=http://localhost:8001` |
| Frontend not running | Started via `npm run dev` on port 3000 |

---

## 10. Remaining Manual Actions

1. **Optional API keys** — To enable all LLM providers, add missing keys to `.env`:
   - `MIMIO_API_KEY` — Get from https://platform.xiaomimimo.com
   - `MISTRAL_API_KEY` — Get from https://console.mistral.ai
   - `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` — Get from https://developer.adzuna.com

2. **Browser validation** — Open http://localhost:3000 in Chrome to visually verify the UI. Navigate through all pages.

3. **Streamlit validation** — Open http://localhost:8501 to test the academic demo (Upload, Ask, RAG Pipeline, System Info).

4. **Ollama models** — Two local models are available:
   - `qwen2.5-coder:7b` (4.36 GB)
   - `gemma4:12b` (7.04 GB)

---

## 11. Quick Start Commands

```bash
# Start Backend (if not running)
cd D:\NORAY-main
python -m uvicorn noray.api.app:app --reload --port 8001

# Start Frontend (if not running)
cd D:\NORAY-main\frontend
npm run dev

# Start Streamlit Demo (if not running)
cd D:\NORAY-main
streamlit run academic_demo/streamlit_app.py --server.port 8501

# Run Health Check
cd D:\NORAY-main
python -m noray.health
```

---

*Report generated by NORAY Lead Architect — 2026-07-28*
