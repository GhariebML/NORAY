# NORAY — Project Architecture Report

**Generated:** 2026-07-28 11:33 GMT+3  
**Version:** 1.0.0  
**Status:** ✅ All Systems Operational

---

## 1. System Overview

NORAY is an **Enterprise Agentic RAG Operating System** — a full-stack AI platform for career management, scholarship discovery, document intelligence, and autonomous research. It combines:

- A **Next.js 16** enterprise dashboard (App Router, TypeScript, Tailwind CSS)
- A **FastAPI** async Python backend with 60+ REST endpoints
- A **Streamlit** academic demo for lightweight RAG visualization
- A **hybrid RAG engine** (dense vectors + sparse BM25 + knowledge graph)
- A **multi-provider AI gateway** with automatic failover across 10+ LLM providers
- A **multi-agent orchestration framework** with DAG-based task execution

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NORAY AI OS v1.0.0                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐    │
│  │  Next.js 16   │   │  Streamlit   │   │  External Clients    │    │
│  │  Frontend     │   │  Academic    │   │  (API Consumers)     │    │
│  │  :3000        │   │  Demo :8501  │   │                      │    │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘    │
│         │                  │                       │                │
│         └──────────────────┼───────────────────────┘                │
│                            │                                        │
│                    ┌───────▼────────┐                               │
│                    │   FastAPI      │                               │
│                    │   Backend      │                               │
│                    │   :8001        │                               │
│                    └───────┬────────┘                               │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         │                  │                  │                    │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐             │
│  │  AI Gateway  │   │  RAG Engine │   │  Services   │             │
│  │  (10+ LLMs)  │   │  Hybrid     │   │  Career     │             │
│  │              │   │  Search     │   │  Scholar    │             │
│  └──────┬──────┘   └──────┬──────┘   │  Upskill    │             │
│         │                  │          └──────┬──────┘             │
│         │                  │                  │                    │
│  ┌──────▼──────────────────▼──────────────────▼──────┐            │
│  │              Data Layer                            │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │            │
│  │  │PostgreSQL│  │  Qdrant  │  │     Redis        │ │            │
│  │  │  :5432   │  │  :6333   │  │     :6379        │ │            │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │            │
│  └───────────────────────────────────────────────────┘            │
│                                                                     │
│  ┌───────────────────────────────────────────────────┐            │
│  │  Ollama (Local LLM) :11434                        │            │
│  │  Models: qwen2.5-coder:7b, gemma4:12b            │            │
│  └───────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Folder Structure

```
NORAY-main/
├── academic_demo/              # Streamlit Academic RAG Demo
│   ├── components/             # API client, config, utils
│   ├── pages/                  # Upload, Ask, RAG Pipeline, System Info
│   ├── requirements.txt        # Minimal Streamlit dependencies
│   └── streamlit_app.py        # Entry point
├── docs/                       # Documentation & screenshots
├── frontend/                   # Next.js 16 Enterprise Dashboard
│   ├── src/
│   │   ├── app/                # App Router pages (13 routes)
│   │   │   ├── analytics/
│   │   │   ├── command-center/
│   │   │   ├── diagnostics/
│   │   │   ├── documents/
│   │   │   ├── jobs/
│   │   │   ├── memory/
│   │   │   ├── profile/
│   │   │   ├── scholarships/
│   │   │   ├── settings/
│   │   │   ├── tracker/
│   │   │   ├── upskill/
│   │   │   └── workspace/
│   │   ├── components/         # React components (AgentPipeline, KnowledgeDrawer, etc.)
│   │   └── lib/                # API client, knowledge service
│   ├── next.config.ts
│   ├── package.json
│   └── Dockerfile
├── noray/                      # Core Python Package
│   ├── agents/                 # Agent router, planner, MCP adapter
│   ├── alembic/                # Database migrations
│   ├── api/                    # FastAPI app, routes, schemas, middleware
│   │   ├── routes/             # 12 route modules (60+ endpoints)
│   │   └── middleware/         # Request tracing
│   ├── cache/                  # Redis cache layer
│   ├── career_agent/           # Job search, CV optimizer, cover letters, interview coach
│   ├── config/                 # Provider routing YAML
│   ├── dashboard/              # Analytics, applications, jobs, scholarships
│   ├── document_generator/     # Document generation service
│   ├── feedback/               # Feedback tuner
│   ├── gateway/                # AI Gateway (multi-provider LLM routing)
│   │   └── providers/          # Anthropic, Gemini, OpenAI, OpenRouter, Local
│   ├── graph/                  # Knowledge graph (extractor, GraphRAG, Postgres store)
│   ├── intelligence/           # AIKernel, reasoning, planning, DI container
│   │   ├── agents/             # Agent registries
│   │   ├── core/               # Kernel, DI, governance, interfaces
│   │   ├── execution/          # DAG executor
│   │   ├── feedback/           # Evaluation & optimizer
│   │   ├── memory/             # Context engine
│   │   └── tools/              # Tool registry
│   ├── llm/                    # LLM routing, providers, health monitor
│   │   └── providers/          # 10 LLM provider implementations
│   ├── models/                 # SQLAlchemy models (application, chat, feedback, profile)
│   ├── observability/          # Events, event bus, telemetry, WebSocket
│   ├── profile_engine/         # CV importer, GitHub importer, LinkedIn importer
│   ├── prompts/                # YAML prompt templates (career, coding, scholarship, etc.)
│   ├── rag/                    # Hybrid RAG engine
│   │   ├── chunker.py          # Document chunking
│   │   ├── compressor.py       # Context compression
│   │   ├── embeddings.py       # Embedding generation
│   │   ├── fusion.py           # Reciprocal Rank Fusion
│   │   ├── reranker.py         # Cross-encoder reranking
│   │   ├── retrieval_pipeline.py # Full RAG pipeline
│   │   ├── sparse_index.py     # BM25 sparse index
│   │   ├── vector_store.py     # Qdrant vector store
│   │   └── universal_retriever.py
│   ├── scholarship_agent/      # Scholarship search, eligibility, SOP, motivation letters
│   ├── services/               # Document service, conversation manager, evaluation engine
│   ├── shared/                 # Shared utilities (logging, models, prompts, vector memory)
│   ├── telemetry/              # Cost tracking, explainability
│   ├── upskill_agent/          # Skill gap analysis, roadmap builder, learning resources
│   ├── config.py               # Central configuration (pydantic-settings)
│   ├── database.py             # SQLAlchemy engine with resilient DB detection
│   ├── database_init.py        # Database initialization (Alembic + Qdrant)
│   └── health.py               # Health & Recovery Manager
├── tests/                      # Pytest test suite (96 tests)
├── SUBMISSION_PACKAGE/         # Academic submission materials
├── docker-compose.yml          # Multi-service Docker orchestration
├── Dockerfile                  # Multi-stage backend image
├── pyproject.toml              # Python package config
├── requirements.txt            # Python dependencies
├── alembic.ini                 # Alembic migration config
├── render.yaml                 # Render.com deployment
├── vercel.json                 # Vercel deployment
├── Makefile                    # Build commands
└── .env                        # Environment variables
```

---

## 4. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Next.js / React | 16.2.7 / 19.2.4 |
| **Styling** | Tailwind CSS | 4.x |
| **State** | Zustand | 5.x |
| **Charts** | Recharts | 3.x |
| **Flow Graphs** | @xyflow/react | 12.x |
| **Animation** | Framer Motion | 12.x |
| **Backend** | FastAPI / Uvicorn | 0.136 / 0.49 |
| **Python** | CPython | 3.14.3 |
| **ORM** | SQLAlchemy | 2.0.48 |
| **Migrations** | Alembic | 1.18.4 |
| **Validation** | Pydantic | 2.12.5 |
| **Vector DB** | Qdrant | 1.18.0 (client) |
| **Relational DB** | PostgreSQL | 15 (Alpine) |
| **Cache** | Redis | 5.3.1 (client) / 7 (server) |
| **Embeddings** | SentenceTransformers | 5.4.1 |
| **Embedding Model** | all-MiniLM-L6-v2 | 384-dim |
| **Sparse Search** | rank-bm25 | 0.2.2 |
| **PDF Parsing** | pdfplumber / PyMuPDF | 0.11 / 1.27 |
| **LLM Providers** | Gemini, OpenRouter, Together, DeepSeek, Anthropic, Ollama | Various |
| **Local LLM** | Ollama (qwen2.5-coder:7b, gemma4:12b) | — |
| **Academic Demo** | Streamlit | 1.57.0 |

---

## 5. Frontend Flow

### Pages (13 routes)
| Route | Purpose |
|-------|---------|
| `/` | Dashboard home |
| `/workspace` | AI Workspace Canvas with chat |
| `/documents` | Document upload & management |
| `/jobs` | Job search & fit evaluation |
| `/scholarships` | Scholarship search & eligibility |
| `/analytics` | Usage analytics & charts |
| `/diagnostics` | System health diagnostics |
| `/settings` | Configuration settings |
| `/memory` | Knowledge graph explorer |
| `/command-center` | Command center dashboard |
| `/profile` | User profile management |
| `/upskill` | Skill gap analysis & roadmaps |
| `/tracker` | Application tracker |

### API Proxy
Next.js rewrites `/api/*` → `http://localhost:8001/api/*` via `next.config.ts`.

### Key Components
- `AgentPipeline` — Visualizes agent execution flow
- `KnowledgeDrawer` — Knowledge graph sidebar
- `ExplainableAIDrawer` — AI decision explainability
- `CommandPalette` — Keyboard-driven command interface
- `FirstRunWizard` — Initial setup wizard
- `WorkflowTimeline` — Task execution timeline

---

## 6. Backend Flow

### API Routes (60+ endpoints)

| Prefix | Module | Key Endpoints |
|--------|--------|---------------|
| `/api/profile` | Profile | GET/PUT profile, import CV/GitHub |
| `/api/jobs` | Jobs | search, ai-search, evaluate, ai-score, tracker |
| `/api/scholarships` | Scholarships | search, ai-search, ai-eligibility, deadlines, tracker |
| `/api/cv` | CV | generate, optimize, sop, motivation, research, quality |
| `/api/sop` | SOP | sop, motivation, research |
| `/api/applications` | Applications | CRUD + analytics |
| `/api/upskill` | Upskill | analyze, resources, roadmap |
| `/api/workspace` | Workspace | chat, search, research, graph/triples |
| `/api/documents` | Documents | upload, list, reindex, delete |
| `/api/health` | Health | database, vector, graph, llm, mcp, setup |
| `/api/system` | System | diagnostics, telemetry, providers, ingestion |
| `/api/ai` | AI Gateway | status, providers, mode, routing-decision |
| `/api/smart-router` | Smart Router | status, routing |

### Startup Sequence
1. FastAPI app initializes
2. SmartRouter background monitoring starts
3. Model warm-up begins
4. CORS middleware configured
5. All 12 route modules registered

---

## 7. RAG Flow

```
Document Upload → Parser (pdfplumber/docx/OCR) → Chunker → Embeddings → Qdrant

User Query → Hybrid Search:
  ├── Dense Search (Qdrant, cosine similarity)
  ├── Sparse Search (BM25 keyword matching)
  └── Graph Traversal (PostgreSQL knowledge graph)
      ↓
  Reciprocal Rank Fusion (RRF)
      ↓
  Cross-Encoder Reranker
      ↓
  Context Compressor (stitch & merge)
      ↓
  LLM Generation (with streaming)
```

### Vector Store
- **Provider:** Qdrant
- **Collection:** `user_documents`
- **Dimensions:** 384 (all-MiniLM-L6-v2)
- **Distance:** Cosine
- **Documents indexed:** 80+ chunks (resumes + test documents)

---

## 8. Database Flow

### Resilient Database Detection
The system implements a 3-tier fallback:
1. Explicit `DATABASE_URL` from environment
2. PostgreSQL on configured port (5432)
3. PostgreSQL on fallback port (5433)
4. SQLite fallback (`data/noray_fallback.db`)

### Current State
- **Engine:** PostgreSQL on localhost:5432
- **Schema:** Managed by Alembic migrations
- **Models:** Application, Chat, Feedback, Profile

---

## 9. AI Gateway & LLM Routing

### Provider Health Status (at report time)

| Provider | Status | Circuit |
|----------|--------|---------|
| **Gemini** | ✅ Healthy | Closed |
| **OpenRouter** | ✅ Healthy | Closed |
| **Together** | ✅ Healthy | Closed |
| **DeepSeek** | ✅ Healthy | Closed |
| **Anthropic** | ✅ Healthy | Closed |
| **Ollama (local)** | ✅ Healthy | Closed |
| MiMo | ❌ Unhealthy | Open |
| Groq | ❌ Unhealthy | Open |
| HuggingFace | ❌ Unhealthy | Open |
| OpenAI | ❌ Unhealthy | Open |
| Mistral | ❌ Unhealthy | Open |

### Active Configuration
- **Mode:** Auto (cloud/local hybrid)
- **Active Provider:** Gemini
- **Active Model:** gemini-flash-latest
- **Local Models:** qwen2.5-coder:7b, gemma4:12b

---

## 10. Deployment Configuration

| Platform | Config File | Purpose |
|----------|------------|---------|
| Docker | `docker-compose.yml` | Full stack (Postgres + Qdrant + Redis + Backend + Frontend) |
| Render | `render.yaml` | Backend deployment |
| Vercel | `vercel.json` | Frontend deployment |
| Docker | `Dockerfile` | Multi-stage backend image |
| Docker | `frontend/Dockerfile` | Multi-stage frontend image |

---

## 11. Dependencies

### Python (27 packages)
fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, alembic, httpx, structlog, python-dotenv, qdrant-client, rank-bm25, sentence-transformers, pdfplumber, pymupdf, python-docx, pillow, psycopg2-binary, psutil, GPUtil, redis, streamlit, requests

### Node.js (frontend)
next, react, react-dom, zustand, recharts, @xyflow/react, framer-motion, lucide-react, next-themes, tailwindcss, typescript

---

## 12. Known Issues

1. **MiMo provider unhealthy** — The configured MiMo API key appears invalid or the service is unreachable. 1677 consecutive failures recorded. Does not affect operation since Gemini is the active fallback.

2. **Slow filesystem warning** — Next.js Turbopack detected slow filesystem (395ms benchmark). First page compilation takes ~30s. Subsequent requests are fast.

3. **System diagnostics timeout** — The `/api/system/diagnostics` endpoint times out on slow connections due to comprehensive service probing.

4. **Duplicate document chunks** — The Qdrant collection contains duplicate test document chunks from repeated ingestion testing.

---

## 13. Improvement Opportunities

1. **Frontend SSR optimization** — Implement static generation for non-dynamic pages to reduce first-load time.
2. **Document deduplication** — Add hash-based dedup to the ingestion pipeline.
3. **Provider health caching** — Cache provider health status to reduce startup cold-start time.
4. **API rate limiting** — Add rate limiting middleware for production deployment.
5. **WebSocket real-time** — The observability module has WebSocket support; wire it to the frontend for live updates.
6. **Test coverage** — Expand from unit tests to integration/E2E tests.

---

## 14. Technical Debt

1. **Python 3.14** — Running on Python 3.14.3 (pre-release). Some dependencies may have compatibility warnings.
2. **Deprecated `@on_event`** — FastAPI's `@app.on_event("startup")` should migrate to `lifespan` context manager.
3. **Hardcoded origins** — CORS origins are partially hardcoded; should fully rely on environment variables.
4. **SQLite fallback in production** — The database fallback chain could silently use SQLite in production; add environment-aware guards.

---

*Report generated by NORAY Lead Architect — 2026-07-28*
