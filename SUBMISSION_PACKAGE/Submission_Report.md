# Course Final Project Submission Report

**Project Title**: NORAY — Next-Generation Enterprise Agentic RAG Operating System  
**Repository**: [https://github.com/GhariebML/NORAY](https://github.com/GhariebML/NORAY)  
**Submission Date**: July 27, 2026  

---

## 1. Executive Summary

NORAY is an autonomous **Retrieval-Augmented Generation (RAG)** platform designed to ingest user career records, academic papers, and general knowledge, dynamically indexing them across dense vector databases (Qdrant) and sparse lexical search indices (BM25). 

The platform supports a **dual-deployment architecture**:
1. **Enterprise Production Profile**: Full Next.js 16 frontend + FastAPI backend + PostgreSQL + Redis + Qdrant.
2. **Academic Evaluation Profile**: A lightweight Streamlit web application interfacing directly with identical backend APIs for rapid course evaluation and live demonstrations.

---

## 2. Technical Architecture & Innovation

### 2.1 Hybrid RAG Engine
- **Dense Vector Search**: Powered by Qdrant with 384-dimensional `all-MiniLM-L6-v2` embeddings.
- **Sparse Lexical Search**: Powered by `rank_bm25` for keyword precision.
- **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse result lists using reciprocal rank scoring.
- **Cross-Encoder Reranking**: Re-scores candidate documents for semantic alignment.
- **Context Compressor**: Dynamically merges adjacent text chunks to optimize LLM context usage.

### 2.2 ReAct Cognitive Loop & Failover Router
- Autonomous **Reasoning + Acting** loop allowing the engine to execute tools, inspect local databases, and evaluate confidence before responding.
- Dual-tier routing that falls back from cloud models (Gemini, DeepSeek, OpenRouter) to local **Ollama** (`qwen2.5-coder:7b`) when offline.

---

## 3. Key Achievements & Verification Metrics

- **Unit & Integration Test Coverage**: **96 / 96 passed** (`pytest`).
- **Frontend Code Quality**: **0 ESLint Errors**, 17/17 routes compiled cleanly in Next.js standalone mode.
- **Deployment Compatibility**: Production Docker containers verified for both FastAPI and Next.js.
