# System Architecture & Technical Specifications

---

## 🏗️ Architectural Flow Overview

```mermaid
graph TD
    Client[Next.js Client / Streamlit App] --> API[FastAPI REST Layer]
    API --> AIKernel[AI Kernel Execution Engine]
    
    subgraph Data & Storage Layer
        AIKernel --> Qdrant[Qdrant Dense Vector Database]
        AIKernel --> BM25[BM25 Lexical Sparse Store]
        AIKernel --> Postgres[PostgreSQL Relational DB]
    end
    
    subgraph Reasoning & LLM Gateway
        AIKernel --> ReAct[ReAct Cognitive Loop]
        ReAct --> Gateway[Dual-Tier LLM Gateway]
        Gateway --> Cloud[Cloud LLMs: Gemini / DeepSeek]
        Gateway --> Local[Local Ollama: qwen2.5-coder:7b]
    end
```

---

## ⚙️ Module Responsibilities

1. **FastAPI Application Layer (`noray/api`)**: Exposes REST endpoints (`/api/documents`, `/api/workspace/chat`, `/api/health`, `/api/system/ingestion-diagnostics`). Handles Pydantic validation and CORS headers.
2. **Hybrid RAG Core (`noray/rag`)**: Implements dual vector/BM25 retrieval, Reciprocal Rank Fusion, cross-encoder reranking, and context compression.
3. **AI Gateway (`noray/gateway`)**: Manages model routing, health probes, and automatic fallback from cloud APIs to local Ollama runtimes.
