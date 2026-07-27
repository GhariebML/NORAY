# NORAY OS Production Deployment Manual

This guide describes how to deploy the **NORAY AI Operating System** to cloud hosting platforms (e.g. Railway, Render, Vercel, or custom Docker infrastructure).

---

## 🏗️ Architecture Topology

NORAY consists of a Next.js frontend, FastAPI backend, PostgreSQL database, Redis instance, and Qdrant vector database.

```
       [ Client Browser ]
               │
        (Vercel Frontend)
               │ (HTTPS/WS)
       (FastAPI Backend Server)
       /       │              \
  [Postgres] [Redis]       [Qdrant]
```

---

## 🐳 Docker Deployment (docker-compose)

Build and run the entire multi-service application locally or on a private virtual machine:

1. **Clone & Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env variables to add database credentials and LLM API keys
   ```

2. **Launch Services**:
   ```bash
   docker-compose up --build -d
   ```

3. **Database Migrations**:
   Run database migrations inside the backend container to ensure database structures are up to date:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

---

## 🚂 Railway Deployment (Recommended)

Railway is suitable for hosting the database engines, cache, vector store, and FastAPI backend.

### Step 1: Deploy Core Databases
- Create a new project in Railway.
- Provision a **PostgreSQL** service database.
- Provision a **Redis** service cache.
- Provision a custom container service for **Qdrant** using image `qdrant/qdrant:v1.7.0`. Add a persistent volume mount `/qdrant/storage`.

### Step 2: Deploy the FastAPI Backend
- Connect your GitHub repository to a new Railway Service.
- Set the Root Directory to `/` and select the **Dockerfile** at the root path.
- Configure Environment Variables:
  - `ENVIRONMENT=production`
  - `DATABASE_URL` (Bind this directly to Railway's Postgres URL: `${{Postgres.DATABASE_URL}}`)
  - `REDIS_URL` (Bind this directly to Railway's Redis URL: `${{Redis.REDIS_URL}}`)
  - `QDRANT_URL` (Point to your Qdrant container URL: `http://<qdrant-service-name>:6333`)
  - `ALLOWED_ORIGINS` (Set this to the production Next.js URL, e.g. `https://noray.vercel.app`)
  - Add API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`).
  - `EMBEDDINGS_PROVIDER=local` or `openai`
- Port: Set port to `8001`.

---

## 🔺 Vercel Deployment (Frontend)

Vercel is suitable for hosting the Next.js frontend statically.

1. **Deploy Project**:
   - Create a project on Vercel and import the `/frontend` subfolder.
   
2. **Environment Variables**:
   - Add `NEXT_PUBLIC_API_URL` pointing to the public URL of the Railway FastAPI backend (e.g. `https://noray-backend.up.railway.app`).

3. **CORS Validation**:
   - Ensure the Vercel app domain is included in the backend service `ALLOWED_ORIGINS` config to authorize cross-origin requests.
