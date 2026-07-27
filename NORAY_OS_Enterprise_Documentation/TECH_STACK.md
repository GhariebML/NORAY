# Technology Stack

Every technology below is marked with its current status:
✅ Implemented · 🟡 Integrated (requires configuration/API keys) · 🔵 Supported by Architecture · ⚪ Planned for Future Releases

## Frontend

| Technology | Status | Reason | Alternatives Considered |
|---|---|---|---|
| Next.js 15 | ✅ | App Router, server components, strong DX for a workspace-style UI | Vite + React SPA |
| React + TypeScript | ✅ | Type safety across a large, evolving component tree | Vue, Svelte |
| Tailwind CSS | ✅ | Rapid, consistent design system implementation | CSS Modules, styled-components |
| React Flow (@xyflow/react) | ✅ | Powers the Execution DAG / Command Center visualization | D3 (lower-level, more custom work) |
| Zustand | ✅ | Lightweight global state without Redux boilerplate | Redux Toolkit, Context API |
| Framer Motion | ✅ | UI motion for panels, transitions | CSS transitions only |
| React Hook Form | ✅ | Form state for document generation inputs | Formik |

## Backend

| Technology | Status | Reason | Alternatives Considered |
|---|---|---|---|
| Python + FastAPI | ✅ | Async-first, strong typing via Pydantic, natural fit for AI/ML tooling | Django, Flask |
| AsyncIO | ✅ | Non-blocking I/O for streaming and concurrent retrieval calls | Threading |
| SQLAlchemy + Alembic | ✅ | ORM + migrations across SQLite/PostgreSQL | Prisma (Node-centric) |
| Uvicorn | ✅ | ASGI server for FastAPI | Gunicorn (used alongside in production) |

## Database

| Technology | Status | Reason |
|---|---|---|
| SQLite | ✅ Implemented (development) | Zero-config local development and testing |
| PostgreSQL | ✅ Implemented (Docker, production) | Production-grade relational store; the system auto-detects the available database and falls back gracefully |

## Vector Database

| Technology | Status | Reason | Alternatives Considered |
|---|---|---|---|
| Qdrant | ✅ | Self-hosted via Docker; strong filtering + hybrid search support; automatic collection provisioning | Pinecone (managed, cost), Weaviate, pgvector |

## Embedding Models

| Model | Status | Notes |
|---|---|---|
| nomic-embed-text | ✅ Default | Local, via Ollama |
| BAAI/bge-m3 | ✅ Supported | Alternative embedding provider |
| Additional providers | ⚪ Planned | Unified provider architecture allows future additions |

## Retrieval & Fusion

| Component | Status |
|---|---|
| Dense Vector Search | ✅ |
| BM25 Sparse Retrieval | ✅ |
| Metadata Filtering | ✅ |
| Reciprocal Rank Fusion (RRF) | ✅ |
| Cross-encoder Reranker | ⚪ Planned |
| Graph Retrieval | 🟡 Architecture only |

## Local LLM Runtime

| Model | Status |
|---|---|
| Llama 3.1 8B (Ollama) | ✅ |
| Qwen 2.5 7B (Ollama) | ✅ |
| Nomic Embed Text (Ollama) | ✅ |

The Local Runtime Manager automatically detects Ollama availability and downloads required models when needed.

## Cloud LLM Providers

| Provider | Status |
|---|---|
| Google Gemini | ✅ Integrated |
| OpenRouter | ✅ Integrated |
| Together AI | ✅ Integrated |
| DeepSeek | ✅ Integrated |
| OpenAI | 🔵 Supported by architecture (requires API key) |
| Anthropic | 🔵 Supported by architecture (requires API key) |
| Mistral | 🔵 Supported by architecture (requires API key) |

All providers share a unified provider interface; the routing engine skips unavailable providers and continues down the fallback chain.

## Unified LLM Router

✅ Implemented — provider health checks, cost-aware routing, latency-aware routing, context window selection, local-first routing, automatic failover, streaming support, token tracking, cost estimation.

## Authentication

⚪ Planned — no authentication layer exists in the current version. NORAY OS is a local-first, single-user system at this stage. JWT, OAuth, and Enterprise SSO are planned for future phases.

## Deployment

✅ Docker Compose — FastAPI, Next.js, Qdrant, PostgreSQL, Redis.
⚪ Planned — Kubernetes, distributed agents, multi-node execution.

## Agent Framework

✅ Custom-built agent framework (AI Kernel, Orchestrator, Capability Registry, Agent Registry, Execution DAG, Task Runner, Planning Engine, Context Engine, Universal Retriever, HITL Manager, Tool Registry, Memory Manager). Deliberately **not** based on LangChain or LangGraph. Follows SOLID principles and Clean Architecture.
