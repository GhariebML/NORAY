# Installation Guide

> NORAY OS is currently validated for **single-user, local-first deployment**. Multi-user/production deployment guidance is in [`DEPLOYMENT.md`](./DEPLOYMENT.md) and remains partly aspirational (🟡) at this stage.

## Prerequisites

- **Python** 3.11+
- **Node.js** 18+ (for the Next.js frontend)
- **Docker** and **Docker Compose** (for Qdrant, PostgreSQL, Redis)
- **Ollama** (for local LLM + embedding models)
- Optional: API keys for cloud providers (Gemini, OpenRouter, Together AI, DeepSeek)

## 1. Clone the Repository

```bash
git clone https://github.com/GhariebML/NORAY.git
cd NORAY
```

## 2. Backend Setup (Windows / Linux / Mac)

```bash
cd backend
python -m venv venv

# Linux / Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

## 3. Environment Variables

Create a `.env` file in `backend/` (never commit this file):

```env
# Database
DATABASE_URL=sqlite:///./noray.db
# or, for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/noray

# Vector Store
QDRANT_URL=http://localhost:6333

# Local LLM Runtime
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Cloud Providers (optional — omit any you do not use)
GEMINI_API_KEY=
OPENROUTER_API_KEY=
TOGETHER_API_KEY=
DEEPSEEK_API_KEY=
```

## 4. Ollama Setup

```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama serve
```

The Local Runtime Manager will detect Ollama automatically and prompt for model downloads if a required model is missing.

## 5. Docker Services (Qdrant, PostgreSQL, Redis)

```bash
docker compose up -d qdrant postgres redis
```

## 6. Run the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## 7. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:3000`.

## 8. Verify Installation

Open the **Diagnostics** panel inside NORAY OS to confirm:

- SQLite/PostgreSQL connectivity ✅
- Qdrant connectivity ✅
- Ollama model availability ✅
- Configured cloud provider status (🟡 if API keys are not yet set)

## Troubleshooting

| Symptom | Likely Cause |
|---|---|
| Ollama model not found | Run `ollama pull <model>` again; check `OLLAMA_BASE_URL` |
| Qdrant connection refused | Confirm the Docker container is running: `docker ps` |
| Cloud provider shows unavailable | Missing or invalid API key in `.env` |
| Frontend can't reach backend | Confirm backend is running on the expected port and CORS origin is set |
