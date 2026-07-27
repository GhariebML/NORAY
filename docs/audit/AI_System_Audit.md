# AI System Audit

**Project:** NORAY OS
**Audit Date:** July 2026

---

## 1. AI Subsystems Overview

`mermaid
graph TB
    subgraph Intelligence Layer
        KERNEL[AIKernel]
        REASONING[ReasoningEngine]
        PLANNING[PlanningMode]
        CONTEXT[ContextEngine]
        GOV[GovernanceEngine]
        EVAL[EvaluationEngine]
    end

    subgraph LLM Layer
        SMART[SmartRouter]
        ROUTER[ModelRouter]
        FACTORY[LLMProviderFactory]
        HEALTH[HealthMonitor]
        BUDGET[BudgetManager]
    end

    subgraph RAG Layer
        PIPELINE[RetrievalPipeline]
        QUERY[QueryProcessor]
        FUSION[RRF Fusion]
        RERANK[Reranker]
        COMPRESS[ContextCompressor]
        VECTOR[VectorStore]
        SPARSE[BM25Index]
    end

    subgraph Memory Layer
        CONV_MEM[ConversationMemory]
        PROF_MEM[ProfileMemory]
        GRAPH_MEM[KnowledgeGraphMemory]
    end

    subgraph Knowledge Layer
        GRAPH[KnowledgeGraph]
        EXTRACTOR[EntityExtractor]
        GRAPH_RAG[GraphRAGFuser]
    end

    KERNEL --> REASONING
    KERNEL --> CONTEXT
    KERNEL --> GOV
    KERNEL --> EVAL
    REASONING --> SMART
    CONTEXT --> PIPELINE
    CONTEXT --> CONV_MEM
    CONTEXT --> PROF_MEM
    PIPELINE --> QUERY
    PIPELINE --> FUSION
    PIPELINE --> RERANK
    PIPELINE --> COMPRESS
    PIPELINE --> VECTOR
    PIPELINE --> SPARSE
    GRAPH_RAG --> GRAPH
    GRAPH_RAG --> EXTRACTOR
`

---

## 2. LLM Router System

### 2.1 SmartRouter (Enterprise Router)
**File:** 
oray/llm/smart_router.py (1,137 lines)

#### Architecture
`mermaid
stateDiagram-v2
    [*] --> Closed
    Closed --> Open: 3 consecutive failures
    Open --> HalfOpen: 5-minute cooldown
    HalfOpen --> Closed: Test request succeeds
    HalfOpen --> Open: Test request fails
`

#### Features
| Feature | Implementation | Status |
|---|---|---|
| Circuit Breaker | Per-provider state tracking | Functional |
| Exponential Backoff | Base delay + jitter | Functional |
| Free Provider Priority | Gemini ? OpenRouter ? Together ? Groq | Functional |
| Health Monitoring | 60-second HTTP pings | Functional |
| Streaming Continuity | Seamless provider switching | Functional |
| Offline Mode | Graceful degradation | Functional |
| Conversation Cache | Persistent across switches | Functional |
| Analytics | Per-provider metrics | Functional |

#### Provider Configuration
| Provider | Priority | Circuit Breaker | Health Check |
|---|---|---|---|
| Ollama | 1 (Local) | Disabled | Port check |
| Google Gemini | 2 (Free) | Enabled | HTTP ping |
| OpenRouter | 3 (Free) | Enabled | HTTP ping |
| Together AI | 4 (Free) | Enabled | HTTP ping |
| Groq | 5 (Free) | Enabled | HTTP ping |
| DeepSeek | 6 (Low Cost) | Enabled | HTTP ping |
| OpenAI | 7 (Premium) | Enabled | HTTP ping |
| Anthropic | 8 (Premium) | Enabled | HTTP ping |

### 2.2 ModelRouter (Legacy Router)
**File:** 
oray/llm/router.py (~200 lines)

| Feature | Status |
|---|---|
| Tier-based scoring | Functional |
| Model selection | Functional |
| Fallback logic | Basic |
| Health monitoring | ? Missing |
| Circuit breaker | ? Missing |

**Issue:** Legacy system, appears unused in production.

### 2.3 TaskAnalyzer
**File:** 
oray/llm/task_analyzer.py

| Feature | Status |
|---|---|
| Query classification | Functional |
| Model family mapping | Functional |
| Confidence scoring | Partial |

---

## 3. Prompt Manager

**File:** 
oray/prompts/loader.py

### Template System
| Template | File | Purpose |
|---|---|---|
| Career | career/v1.yaml | Career agent prompts |
| Coding | coding/v1.yaml | Code generation prompts |
| Governance | governance/v1.yaml | Policy enforcement prompts |
| Planner | planner/v1.yaml | Task planning prompts |
| Research | esearcher/v1.yaml | Research prompts |
| Scholarship | scholarship/v1.yaml | Scholarship prompts |
| System | system/v1.yaml | System-level prompts |
| Tools | 	ools/v1.yaml | Tool usage prompts |

### Features
| Feature | Status |
|---|---|
| YAML-based templates | Functional |
| Variable interpolation | Functional |
| Template versioning | Functional |
| Hot reloading | ? Missing |
| Version migration | ? Missing |

---

## 4. Reasoning Engine

**File:** 
oray/intelligence/core/reasoning.py

### ReAct Loop (9-Step)
`mermaid
flowchart TD
    A[1. Receive Query] --> B[2. Analyze Intent]
    B --> C[3. Discover Tools]
    C --> D[4. Plan Execution]
    D --> E[5. Execute Action]
    E --> F[6. Observe Result]
    F --> G{7. Evaluate}
    G -->|Need More| E
    G -->|Complete| H[8. Generate Response]
    H --> I[9. Self-Reflection]
`

### Planning Modes
| Mode | Iterations | Timeout | Use Case |
|---|---|---|---|
| Fast | 1 | 30s | Simple queries |
| Balanced | 3 | 60s | Standard tasks |
| Deep Research | 5 | 120s | Complex analysis |
| Autonomous | 10 | 300s | Multi-step workflows |
| Experimental | 20 | 600s | Research tasks |

### Assessment
| Aspect | Rating | Notes |
|---|---|---|
| Tool Discovery | Good | Dynamic tool registration |
| Execution Flow | Good | Sequential and parallel support |
| Error Recovery | Fair | Basic retry logic |
| Reflection | Fair | Limited self-evaluation |
| Memory Integration | Fair | Basic context passing |

---

## 5. Memory System

### 5.1 Conversation Memory
**File:** 
oray/rag/memory.py

| Feature | Status | Notes |
|---|---|---|
| Session persistence | Partial | PostgreSQL-backed |
| Message history | Functional | With citations |
| Context window | Functional | Configurable size |
| Compression | ? Missing | No summarization |
| Search | ? Missing | No semantic search in history |

### 5.2 Profile Memory
**File:** 
oray/rag/memory.py

| Feature | Status | Notes |
|---|---|---|
| Profile storage | Functional | JSON blob |
| Profile update | Functional | Merge/diff logic |
| Version history | ? Missing | No change tracking |
| Cross-session | Functional | Persistent across chats |

### 5.3 Knowledge Graph Memory
**File:** 
oray/graph/graph_rag.py

| Feature | Status | Notes |
|---|---|---|
| Entity extraction | Partial | Regex + optional LLM |
| Relationship mapping | Functional | Graph storage |
| Multi-hop traversal | Functional | BFS 1-2 hops |
| Graph embedding | ? Missing | No graph neural networks |
| Temporal reasoning | ? Missing | No time-based queries |

---

## 6. Retrieval System

### 6.1 Query Processor
**File:** 
oray/rag/query_processor.py

| Feature | Status | Notes |
|---|---|---|
| Intent classification | Functional | Maps to retrieval strategy |
| HyDE | Functional | Hypothetical document embedding |
| Query expansion | Functional | LLM-based expansion |
| Query rewriting | Functional | Clarification generation |

### 6.2 Embeddings
**File:** 
oray/rag/embeddings.py

| Provider | Model | Dimension | Status |
|---|---|---|---|
| Local (ST) | all-MiniLM-L6-v2 | 384 | Functional |
| Local (BGE) | bge-m3 | 1024 | Functional |
| Local (Jina) | jina-embeddings-v4 | varies | Functional |
| OpenAI | text-embedding-3-small | 1536 | Functional |
| Voyage | voyage-3 | 1024 | Functional |
| Jina | jina-embeddings-v2-base-en | 768 | Functional |

**?? Issue:** Config defaults to ge-m3 (1024-dim) but Qdrant collection created for 384-dim.

### 6.3 Vector Store
**File:** 
oray/rag/vector_store.py

| Backend | Implementation | Status |
|---|---|---|
| Qdrant (primary) | Thread-safe singleton | Functional |
| FAISS (fallback) | Pure NumPy cosine similarity | Functional |

### 6.4 Sparse Search (BM25)
**File:** 
oray/rag/sparse_index.py

| Feature | Status | Notes |
|---|---|---|
| BM25 indexing | Functional | rank_bm25 library |
| Serialization | Functional | Pickle-based |
| Incremental updates | ? Missing | Full rebuild required |
| Tokenization | Basic | Whitespace-based |

### 6.5 RRF Fusion
**File:** 
oray/rag/fusion.py

| Feature | Status | Notes |
|---|---|---|
| Reciprocal Rank Fusion | Functional | Standard implementation |
| Configurable k | Functional | Default k=60 |
| Score normalization | Functional | Rank-based |

### 6.6 Reranker
**File:** 
oray/rag/reranker.py

| Provider | Model | Status |
|---|---|---|
| Local (CrossEncoder) | BAAI/bge-reranker-base | Functional |
| Jina | jina-reranker-v2-base-multilingual | Functional |
| Cohere | rerank-english-v3.0 | Functional |

### 6.7 Context Compressor
**File:** 
oray/rag/compressor.py

| Feature | Status | Notes |
|---|---|---|
| Deduplication | Functional | Hash-based |
| Merge adjacent chunks | Functional | Overlap detection |
| Token budget | Functional | Configurable limit |

---

## 7. Context Builder

**File:** 
oray/intelligence/memory/context_engine.py

### Context Assembly Flow
`mermaid
flowchart LR
    Q[Query] --> GATHER[Gather Context]
    GATHER --> PROFILE[Profile Data]
    GATHER --> DOCS[Relevant Documents]
    GATHER --> HISTORY[Conversation History]
    GATHER --> GRAPH[Knowledge Graph]
    
    PROFILE --> RANK[Rank & Score]
    DOCS --> RANK
    HISTORY --> RANK
    GRAPH --> RANK
    
    RANK --> COMPRESS[Compress]
    COMPRESS --> INJECT[Inject into Prompt]
`

### Features
| Feature | Status | Notes |
|---|---|---|
| Multi-source gathering | Functional | Profile, docs, history, graph |
| Relevance scoring | Functional | Cosine similarity |
| Ranking | Functional | Score-based?? |
| Compression | Functional | Token budget |
| Token counting | Functional | tiktoken-based |

---

## 8. Knowledge Injection

### Injection Points
| Point | Method | Status |
|---|---|---|
| System prompt | Profile context | Functional |
| User message | Retrieved documents | Functional |
| Tool results | Execution context | Functional |
| Graph triples | Entity relationships | Partial |

### Quality Assessment
| Aspect | Rating | Notes |
|---|---|---|
| Relevance | Good | Reranking improves quality |
| Diversity | Fair | Limited diversity strategies |
| Freshness | Fair | No staleness detection |
| Completeness | Fair | May miss important context |

---

## 9. Response Generator

**File:** 
oray/llm/response_builder.py

### Response Envelope
`json
{
  "content": "string",
  "model": "string",
  "provider": "string",
  "tokens_used": 0,
  "latency_ms": 0,
  "confidence": 0.0,
  "sources": [],
  "citations": [],
  "reasoning_trace": []
}
`

### Features
| Feature | Status | Notes |
|---|---|---|
| Structured responses | Functional | Pydantic models |
| Source attribution | Functional | Citation tracking |
| Confidence scoring | Partial | Basic implementation |
| Streaming support | Functional | SSE-based |

---

## 10. Fallback Logic

### Fallback Chain
`mermaid
flowchart TD
    A[Primary Provider] -->|Failure| B[Secondary Provider]
    B -->|Failure| C[Tertiary Provider]
    C -->|Failure| D[Local Ollama]
    D -->|Failure| E[Offline Mode]
    E -->|Failure| F[Error Response]
`

### Fallback Configuration
| Level | Trigger | Action |
|---|---|---|
| Provider Switch | 3 failures | Switch to next provider |
| Circuit Open | 5-minute cooldown | Skip provider |
| All Providers Failed | All circuits open | Local Ollama |
| Ollama Unavailable | Connection refused | Offline mode |
| Offline Disabled | ALLOW_OFFLINE=false | Error response |

---

## 11. Streaming

**Implementation:** Server-Sent Events (SSE)

| Feature | Status | Notes |
|---|---|---|
| Token-by-token streaming | Functional | Via SSE |
| Provider switching mid-stream | Functional | Seamless handoff |
| Client disconnection handling | Functional | Cleanup on disconnect |
| Buffer management | Functional | Memory-efficient |

---

## 12. Confidence Score

**File:** 
oray/telemetry/explainability.py

### Confidence Factors
| Factor | Weight | Calculation |
|---|---|---|
| Retrieval relevance | 0.3 | Average cosine similarity |
| Source count | 0.2 | Number of supporting documents |
| Model confidence | 0.2 | Provider-specific score |
| Query complexity | 0.15 | Inverse of query length |
| Context completeness | 0.15 | Coverage of query terms |

### Assessment
| Aspect | Rating | Notes |
|---|---|---|
| Accuracy | Fair | Not calibrated against ground truth |
| Calibration | Poor | No probability calibration |
| Usefulness | Fair | Basic but functional |

---

## 13. Grounding & Hallucination Prevention

### Grounding Mechanisms
| Mechanism | Status | Effectiveness |
|---|---|---|
| Source attribution | Functional | Good |
| Citation tracking | Functional | Good |
| Fact verification | ? Missing | N/A |
| Consistency checking | ? Missing | N/A |
| Confidence thresholds | Partial | Basic |

### Hallucination Prevention
| Strategy | Status | Notes |
|---|---|---|
| RAG grounding | Functional | Documents provide context |
| Prompt engineering | Functional | Instruction-based |
| Temperature control | Functional | Low temperature (0.3) |
| Max tokens limit | Functional | Prevents excessive generation |
| Self-consistency | ? Missing | No multi-sample verification |
| Chain-of-thought | Partial | ReAct loop provides some |

---

## 14. Model Registry

**File:** 
oray/llm/model_registry.py

### Supported Models (20+)
| Provider | Models |
|---|---|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-3.5-turbo |
| Anthropic | claude-sonnet-4-20250514, claude-3-haiku |
| Google | gemini-2.0-flash, gemini-1.5-pro |
| DeepSeek | deepseek-chat, deepseek-coder |
| Mistral | mistral-large, mistral-small |
| Ollama | llama3, mistral, codellama |
| Together | meta-llama/llama-3-70b |
| OpenRouter | Various free models |

### Model Metadata
| Attribute | Purpose |
|---|---|
| Capabilities | Code, Math, Reasoning, Creative |
| Context Window | Token limit |
| Cost Tier | Free, Low, Medium, High |
| Speed Tier | Fast, Medium, Slow |
| Recommended For | Task-specific recommendations |

---

## 15. AI System Assessment

### Strengths
| # | Strength |
|---|---|
| 1 | Comprehensive multi-provider routing with circuit breaker |
| 2 | Graceful degradation at every level |
| 3 | 7-stage resilient RAG pipeline |
| 4 | Knowledge graph integration for multi-hop reasoning |
| 5 | 9-step ReAct reasoning loop |
| 6 | Real-time streaming with provider switching |

### Weaknesses
| # | Weakness | Severity |
|---|---|---|
| 1 | Embedding dimension mismatch (config vs Qdrant) | High |
| 2 | No fact verification or consistency checking | High |
| 3 | Confidence scoring not calibrated | Medium |
| 4 | Limited memory compression and search | Medium |
| 5 | Two duplicate routing systems | Medium |
| 6 | No self-consistency verification | Medium |
| 7 | Basic BM25 tokenization | Low |

### Recommendations
| Priority | Recommendation |
|---|---|
| Critical | Fix embedding dimension mismatch |
| High | Add fact verification layer |
| High | Calibrate confidence scoring |
| Medium | Consolidate routing systems |
| Medium | Add memory compression |
| Low | Improve BM25 tokenization |

---

*This document was generated as part of the NORAY OS Phase 1 Technical Audit.*
