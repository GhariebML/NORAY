# Executive Summary — NORAY AI Operating System

---

## Overview

NORAY is a full-stack AI Operating System designed to unify career optimization, academic research, and knowledge management into a single intelligent platform. It implements a **Hybrid RAG (Retrieval-Augmented Generation)** pipeline that fuses dense vector search (Qdrant + MiniLM-L6-v2) with sparse keyword retrieval (BM25) through **Reciprocal Rank Fusion (RRF)** and **Cross-Encoder reranking**, delivering grounded, citation-backed AI responses.

## Core Innovation

Unlike conventional chatbot systems that rely on a single retrieval method, NORAY's dual-retrieval architecture ensures that:

1. **Dense search** captures semantic similarity — finding documents that mean the same thing even when different words are used.
2. **Sparse search** captures exact keyword matches — ensuring high-precision lexical hits are never missed.
3. **RRF fusion** mathematically combines rankings from both retrievers, producing a final ranked list that is more robust than either retriever alone.

## Technical Architecture

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 15 + React 19 + Framer Motion | Enterprise dashboard with glassmorphism UI |
| **Backend** | FastAPI + Pydantic | REST API with WebSocket streaming |
| **Vector Database** | Qdrant | Dense embedding storage and cosine similarity search |
| **Sparse Index** | BM25 (Rank-BM25) | Keyword-based lexical retrieval |
| **Relational DB** | PostgreSQL | User profiles, applications, settings |
| **Cache** | Redis | Session state, rate limiting, response caching |
| **LLM Gateway** | Multi-provider router | Gemini → OpenRouter → Together → DeepSeek → Local Ollama |
| **Academic Demo** | Streamlit | Lightweight evaluation interface with offline fallback |

## Deployment Strategy

NORAY implements a **dual-deployment** model:

1. **Enterprise Stack**: Dockerized Next.js + FastAPI + PostgreSQL + Redis + Qdrant for cloud deployment (Vercel + Railway/Render).
2. **Academic Demo**: Streamlit application deployable on Streamlit Community Cloud for immediate course evaluation.

Both targets share the same backend logic — no business logic is duplicated.

## Key Metrics

- **Test Coverage**: 511 passed, 1 skipped (100% success rate)
- **Frontend Quality**: 0 ESLint errors, 17/17 Next.js routes compiled
- **Provider Resilience**: Automatic failover across 7+ LLM providers
- **RAG Fusion**: Dense + Sparse + RRF + Cross-Encoder reranking pipeline

## Author

**Mohamed Gharieb** — AI/ML Engineer  
GitHub: [github.com/GhariebML](https://github.com/GhariebML)
