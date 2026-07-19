# Architecture Overview

NORAY is an enterprise-grade AI Operating System designed around a modular, hybrid RAG engine and a multi-agent orchestration framework.

## Core Architecture

```mermaid
graph TD
    User([User Prompt / Web Client]) --> API[FastAPI Server]
    API --> Planner[PlannerAgent: Task Decomposition]
    Planner --> Router[RouterAgent: Agent Dispatcher]
    
    subgraph Data & RAG Engine
        Router --> HybridSearch[AgentRouter: Hybrid Search]
        HybridSearch --> Dense[Qdrant Vector DB: all-MiniLM-L6-v2]
        HybridSearch --> Sparse[BM25 Index: SparseBM25Index]
        Dense & Sparse --> RRF[Reciprocal Rank Fusion]
        RRF --> Rerank[Cross-Encoder Reranker]
        Rerank --> Compressor[ContextCompressor: Stitch & Merge Chunks]
    end
    
    subgraph Knowledge Graph
        Compressor --> GraphRAG[GraphRAGFuser: Context Enrichment]
        GraphRAG --> GraphStore[PostgresGraphStore: Graph DB]
    end
    
    subgraph LLM Generation
        GraphRAG --> AIGateway[Central AI Gateway]
        AIGateway --> LocalProvider[Local Offline Provider: Ollama/LM Studio]
        AIGateway --> CloudProvider[Cloud Providers: Claude/Gemini/OpenAI/OpenRouter]
    end
    
    AIGateway --> Generator[LLM Response & Explainability Info]
    Generator --> UI[Next.js Client]
```

## Component Details

### 1. Unified AI Gateway (`noray/gateway`)
The AI Gateway abstracts away all LLM provider specifics. It routes requests based on constraints (e.g., minimum context window, JSON support, cost limits) and implements a robust fallback chain (e.g., Anthropic -> OpenAI -> Local Qwen). 

### 2. Multi-Agent Orchestration
Tasks are broken down by a `PlannerAgent` into a Directed Acyclic Graph (DAG), and executed concurrently by the `RouterAgent` and domain-specific agents (Career, Scholarship, Upskill).

### 3. Model Context Protocol (MCP)
NORAY acts as an MCP Client, enabling agents to dynamically discover and use external tools (Filesystem, Terminal, SQLite, Git) securely.

### 4. Hybrid Search & Graph RAG
NORAY merges dense vector search (Qdrant), sparse keyword search (BM25), and graph traversal (PostgreSQL). Results are fused via Reciprocal Rank Fusion (RRF) and enriched with explicit entity relationships.
