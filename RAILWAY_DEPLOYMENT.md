# FastAPI & Database Railway Deployment Guide

This guide details how to deploy the **FastAPI Backend**, **PostgreSQL database**, **Redis cache**, and **Qdrant Vector Database** to **Railway** (railway.app).

---

## 🏗️ Multi-Service Setup on Railway

### 1. Provision Databases
1. Go to your [Railway Dashboard](https://railway.app/) and create a new empty project.
2. Click **+ Add Service** ➔ Select **Database** ➔ **Add PostgreSQL**.
3. Click **+ Add Service** ➔ Select **Database** ➔ **Add Redis**.

### 2. Deploy Qdrant Container
1. Click **+ Add Service** ➔ Select **Docker Image**.
2. Input: `qdrant/qdrant:v1.7.0` and deploy.
3. In Qdrant Service settings:
   - Create a volume mount under **Settings** ➔ **Volumes** ➔ Set Mount Path to `/qdrant/storage`.
   - Expose port `6333`.

### 3. Deploy the FastAPI Backend
1. Click **+ Add Service** ➔ Select **GitHub Repo** ➔ Import repository.
2. Under **Settings**:
   - Ensure Railway resolves the **Dockerfile** at the root of the project.
   - Set the port to `8001`.
3. Add **Environment Variables**:
   - `ENVIRONMENT` = `production`
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` *(Binds automatically to Postgres)*
   - `REDIS_URL` = `${{Redis.REDIS_URL}}` *(Binds automatically to Redis)*
   - `QDRANT_URL` = `http://qdrant.railway.internal:6333` *(Points to internal Qdrant container)*
   - `ALLOWED_ORIGINS` = `https://your-vercel-frontend.vercel.app` *(Set to your Vercel URL)*
   - Add LLM API Keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`).
   - `EMBEDDINGS_PROVIDER` = `local` or `openai`
