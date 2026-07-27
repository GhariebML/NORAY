# Environment Variable Configuration Manual

This guide describes all configuration variables used by the **NORAY AI Operating System** to control databases, LLM gateways, and vector layers.

---

## 📋 Variables Reference

### 🌐 System Settings
- `ENVIRONMENT`: Core execution mode (`development` / `production`). Production locks down verbose debugging logs and sets CORS policies.
- `PORT`: Service port for the FastAPI server (default: `8001`).
- `HOST`: Bind address for backend server (default: `0.0.0.0`).
- `ALLOWED_ORIGINS`: Comma-separated list of browser domains allowed to request API data (e.g. `https://noray.vercel.app`).

### 💾 Relational Databases (PostgreSQL / SQLite)
- `DATABASE_URL`: Connection string. Uses PostgreSQL (`postgresql://...`) in production, and SQLite locally (`sqlite:///...`).

### 🧬 Embeddings & Vector Stores
- `VECTOR_STORE_PROVIDER`: Set to `qdrant` in production, or `faiss` to fall back to in-memory numpy indexes.
- `QDRANT_URL`: Public or internal container URL for Qdrant server (e.g. `http://localhost:6333`).
- `QDRANT_API_KEY`: Required if connecting to a managed Qdrant Cloud cluster.
- `EMBEDDINGS_PROVIDER`: Embedder core selection. Options:
  - `local`: Run SentenceTransformers `all-MiniLM-L6-v2` inside backend container (Requires CPU/RAM resource allocations).
  - `openai`: Generates embeddings via OpenAI endpoint. Reduces backend CPU requirements.
- `EMBEDDINGS_MODEL`: Specific model key (e.g., `text-embedding-3-small` or `all-MiniLM-L6-v2`).

### 🤖 LLM Gateways (API Keys)
- `OPENAI_API_KEY`: Key for GPT-4 / Embedding models.
- `GEMINI_API_KEY`: Key for Google Gemini integrations.
- `ANTHROPIC_API_KEY`: Key for Claude model reasoning loops.
- `DEEPSEEK_API_KEY`: Key for DeepSeek engines.
- `OPENROUTER_API_KEY`: Router key connecting to aggregated models.
- `OLLAMA_BASE_URL`: Local LLM runtime endpoint (default: `http://localhost:11434/v1`).
- `ALLOW_OFFLINE`: If `true`, the gateway falls back to Ollama if cloud keys fail or are missing.

### ⚡ Caching Cache & Task Runners
- `REDIS_URL`: Link string connecting to Redis server (e.g., `redis://localhost:6379/0`).
