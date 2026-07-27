# Architecture Report

**Project:** NORAY OS
**Audit Date:** July 2026

---

## 1. High-Level Architecture

`mermaid
graph TB
    subgraph Frontend ["Frontend (Next.js 16)"]
        UI[React 19 Dashboard]
        ZS[Zustand State]
        API_CLIENT[API Client]
    end

    subgraph Backend ["Backend (FastAPI)"]
        ROUTES[API Routes]
        MW[Middleware]
        SERVICES[Services Layer]
        AGENTS[Multi-Agent System]
        RAG[Hybrid RAG Engine]
        LLM[LLM Router]
        GRAPH[Knowledge Graph]
    end

    subgraph Data ["Data Layer"]
        PG[PostgreSQL]
        QD[Qdrant]
        RD[Redis]
        BM25[BM25 Index]
        FS[File System]
    end

    subgraph External ["External Providers"]
        OLLAMA[Ollama Local]
        OPENAI[OpenAI]
        ANTHROPIC[Anthropic]
        GEMINI[Gemini]
        OTHER[Other Providers]
    end

    UI --> API_CLIENT
    API_CLIENT -->|HTTP/WebSocket| ROUTES
    ROUTES --> MW
    MW --> SERVICES
    SERVICES --> AGENTS
    AGENTS --> RAG
    AGENTS --> LLM
    AGENTS --> GRAPH
    RAG --> QD
    RAG --> BM25
    RAG --> PG
    LLM --> OLLAMA
    LLM --> OPENAI
    LLM --> ANTHROPIC
    LLM --> GEMINI
    LLM --> OTHER
    SERVICES --> PG
    SERVICES --> RD
    SERVICES --> FS
`

---

## 2. Frontend Architecture

### Technology Stack
| Component | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 16.2.7 |
| UI Library | React | 19.2.4 |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 4.x |
| State Management | Zustand | 5.0.14 |
| Animation | Framer Motion | 12.42.2 |
| Charts | Recharts | 3.9.2 |
| Flow Diagrams | @xyflow/react | 12.11.2 |
| Theming | next-themes | 0.4.6 |

### Page Structure
| Route | Page | Lines | Purpose |
|---|---|---|---|
| / | Dashboard | 730 | Mission Control: health, agents, workflows, charts |
| /workspace | Workspace | ~400 | AI chat canvas with reasoning timeline |
| /jobs | Jobs | ~300 | Job search, AI scoring, applications |
| /scholarships | Scholarships | ~250 | Scholarship search, eligibility |
| /profile | Profile | ~200 | Profile ingestion (CV, LinkedIn, GitHub) |
| /tracker | Tracker | ~200 | Application tracker board |
| /analytics | Analytics | ~150 | Usage analytics |
| /diagnostics | Diagnostics | ~150 | System diagnostics |
| /documents | Documents | ~150 | Document management |
| /memory | Memory | ~150 | Knowledge graph viewer |
| /upskill | Upskill | ~150 | Skill gap analysis |
| /settings | Settings | ~100 | Configuration |

### Component Architecture
`mermaid
graph LR
    LAYOUT[layout.tsx] --> SIDEBAR[Sidebar]
    LAYOUT --> TOPNAV[Top Nav]
    LAYOUT --> TABS[WorkspaceTabs]
    LAYOUT --> TASKBAR[TaskManagerBar]
    LAYOUT --> CHILDREN[Page Children]
    
    COMMAND[CommandPalette] --> SEARCH[Search]
    COMMAND --> ACTIONS[Quick Actions]
    
    INGESTION[IngestionCenter] --> UPLOAD[File Upload]
    INGESTION --> PROCESS[Processing]
`

### State Management
- **Zustand** for global state (no Redux)
- **React hooks** for local state
- **API client** (lib/api.ts) — 596 lines, handles all backend communication
- **No server-side state** — all data fetched client-side

---

## 3. Backend Architecture

### Technology Stack
| Component | Technology | Version |
|---|---|---|
| Framework | FastAPI | 0.104.0+ |
| Server | Uvicorn | 0.24.0+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.12+ |
| Validation | Pydantic | 2.0+ |
| HTTP Client | httpx | 0.25.0+ |
| Logging | structlog | 23.2+ |

### API Routes
| Route Prefix | File | Endpoints |
|---|---|---|
| /api/health | health.py | System status check |
| /api/profile | profile.py | CRUD + import |
| /api/jobs | jobs.py | Search + evaluate + apply + AI search |
| /api/scholarships | scholarships.py | Search + AI search + apply |
| /api/applications | pplications.py | CRUD operations |
| /api/documents | documents.py | Upload + ingestion |
| /api/workspace | workspace.py | Chat + search + research + graph |
| /api/ai | smart_router.py | SmartRouter control |
| /api/cv | cv.py | Generation + optimization |
| /api/sop | sop.py | Statement generation |
| /api/diagnostics | system_diagnostics.py | Telemetry |
| /api/upskill | upskill.py | Analysis + roadmap |
| /api/stream | WebSocket | Real-time events |

### Middleware
- **Tracing Middleware** — X-Trace-ID for request correlation
- **CORS** — Configured in pp.py
- **No authentication middleware** — ?? Critical gap

### Service Layer
`mermaid
graph TB
    subgraph Services
        DOC_SVC[DocumentService]
        CONV_SVC[ConversationManager]
        ARTIFACT_SVC[ArtifactManager]
        BENCH_SVC[BenchmarkEngine]
        EVAL_SVC[EvaluationEngine]
        HITL_SVC[HITL Manager]
        TASK_SVC[TaskRunner]
    end

    subgraph Domain Agents
        CAREER[CareerAgent]
        SCHOLARSHIP[ScholarshipAgent]
        UPSKILL[UpskillAgent]
    end

    subgraph Intelligence
        KERNEL[AIKernel]
        REASONING[ReasoningEngine]
        PLANNING[PlanningMode]
        GOV[GovernanceEngine]
    end

    DOC_SVC --> KERNEL
    CONV_SVC --> KERNEL
    CAREER --> KERNEL
    SCHOLARSHIP --> KERNEL
    UPSKILL --> KERNEL
    KERNEL --> REASONING
    KERNEL --> PLANNING
    KERNEL --> GOV
`

---

## 4. Database Architecture

### Entity Relationship
`mermaid
erDiagram
    PROFILE ||--o{ APPLICATION : has
    PROFILE ||--o{ CHAT_SESSION : creates
    CHAT_SESSION ||--o{ CHAT_MESSAGE : contains
    APPLICATION ||--o{ FEEDBACK : receives
    PROFILE ||--o{ RETRIEVAL_PARAMS : tunes
    PROFILE ||--o{ GRAPH_NODE : contains
    GRAPH_NODE ||--o{ GRAPH_EDGE : connects

    PROFILE {
        int id PK
        jsonb profile_data
        datetime created_at
        datetime updated_at
    }

    APPLICATION {
        int id PK
        int profile_id FK
        string type
        jsonb data
        string status
    }

    CHAT_SESSION {
        int id PK
        int profile_id FK
        string title
        datetime created_at
    }

    CHAT_MESSAGE {
        int id PK
        int session_id FK
        string role
        text content
        jsonb citations
    }

    FEEDBACK {
        int id PK
        int application_id FK
        int rating
        text comment
    }

    GRAPH_NODE {
        int id PK
        int profile_id FK
        string label
        string entity_type
    }

    GRAPH_EDGE {
        int id PK
        int source_id FK
        int target_id FK
        string relationship
    }
`

### Database Resolution Strategy
`mermaid
flowchart TD
    A[Start] --> B{DATABASE_URL set?}
    B -->|Yes| C[Use explicit URL]
    B -->|No| D{Test configured port?}
    D -->|Yes| E[Use configured port]
    D -->|No| F{Test fallback port?}
    F -->|Yes| G[Use fallback port]
    F -->|No| H[Fall back to SQLite]
    
    style C fill:#22c55e,color:#fff
    style E fill:#22c55e,color:#fff
    style G fill:#eab308,color:#000
    style H fill:#ef4444,color:#fff
`

### Tables Summary
| Table | Purpose | Records |
|---|---|---|
| profiles | Career profile JSON blob | User-dependent |
| pplications | Job/scholarship applications | User-dependent |
| chat_sessions | Chat session metadata | User-dependent |
| chat_messages | Chat message history with citations | User-dependent |
| eedbacks | User ratings and corrections | User-dependent |
| etrieval_params | Dynamic retrieval hyperparameters | System |
| graph_nodes | Knowledge graph entities | User-dependent |
| graph_edges | Knowledge graph relationships | User-dependent |

---

## 5. Vector Database Architecture

### Qdrant Collections
| Collection | Dimension | Purpose |
|---|---|---|
| documents | 384/1024 | Document chunk embeddings |
| knowledge | 384/1024 | Knowledge base embeddings |

### Vector Store Factory
`mermaid
flowchart TD
    A[VectorStoreFactory] --> B{Environment?}
    B -->|Qdrant running| C[QdrantVectorStore]
    B -->|Qdrant unavailable| D[FAISSVectorStore]
    
    C --> E[Thread-Safe Singleton]
    D --> F[NumPy Cosine Similarity]
    
    E --> G[CRUD Operations]
    F --> G
`

---

## 6. RAG Pipeline Architecture

### 7-Stage Retrieval Pipeline
`mermaid
flowchart LR
    Q[Query] --> QP[QueryProcessor]
    QP --> S1[1. Dense Vector Search]
    QP --> S2[2. BM25 Sparse Search]
    S1 --> S3[3. RRF Fusion]
    S2 --> S3
    S3 --> S4[4. Cross-Encoder Reranking]
    S4 --> S5[5. Context Compression]
    S5 --> S6{Sufficient?}
    S6 -->|Yes| OUT[Output]
    S6 -->|No| S7[6. Conversation Memory]
    S7 --> S8{Sufficient?}
    S8 -->|Yes| OUT
    S8 -->|No| S9[7. LLM-Only Fallback]
    S9 --> OUT
`

### Embedding Providers
| Provider | Model | Dimension | Default |
|---|---|---|---|
| Local (Sentence Transformers) | all-MiniLM-L6-v2 | 384 | Fallback |
| Local (BGE) | bge-m3 | 1024 | Config default |
| Local (Jina) | jina-embeddings-v4 | varies | Alternative |
| OpenAI | text-embedding-3-small | 1536 | Cloud |
| Voyage | voyage-3 | 1024 | Cloud |
| Jina | jina-embeddings-v2-base-en | 768 | Cloud |

### Reranker Providers
| Provider | Model |
|---|---|
| Local (CrossEncoder) | BAAI/bge-reranker-base |
| Jina | jina-reranker-v2-base-multilingual |
| Cohere | rerank-english-v3.0 |

---

## 7. LLM Router Architecture

### SmartRouter Flow
`mermaid
flowchart TD
    A[Incoming Request] --> B[TaskAnalyzer]
    B --> C{Confidence Check}
    C -->|High| D[Preferred Provider]
    C -->|Low| E[Free Provider Priority]
    
    D --> F[Circuit Breaker Check]
    E --> F
    
    F -->|Open| G[Next Provider]
    F -->|Closed| H[Execute Request]
    
    H -->|Success| I[Reset Circuit]
    H -->|Failure| J[Increment Failure Count]
    J --> K{Failures >= 3?}
    K -->|Yes| L[Open Circuit - 5min Cooldown]
    K -->|No| M[Retry with Backoff]
    
    I --> N[Return Response]
    L --> G
    M --> H
    G --> O{All Providers Failed?}
    O -->|No| F
    O -->|Yes| P[Offline Fallback]
`

### Provider Priority (Free-First)
| Priority | Provider | Type |
|---|---|---|
| 1 | Ollama | Local |
| 2 | Google Gemini | Free tier |
| 3 | OpenRouter | Free models |
| 4 | Together AI | Free tier |
| 5 | Groq | Free tier |
| 6 | DeepSeek | Low cost |
| 7 | OpenAI | Premium |
| 8 | Anthropic | Premium |

### Circuit Breaker Configuration
| Parameter | Value |
|---|---|
| Failure Threshold | 3 consecutive failures |
| Cooldown Period | 300 seconds (5 minutes) |
| Half-Open Test | Single test request after cooldown |
| Health Check Interval | 60 seconds |

---

## 8. Knowledge Graph Architecture

### Graph RAG Flow
`mermaid
flowchart LR
    Q[Query] --> EE[Entity Extractor]
    EE --> EN[Extracted Entities]
    EN --> GN[Find Matching Nodes]
    GN --> BFS[BFS Traversal 1-2 Hops]
    BFS --> TRIPLES[Format Triples]
    TRIPLES --> MERGE[Merge with Vector Context]
    MERGE --> OUT[Enriched Context]
`

### Graph Schema
- **Nodes**: Entity nodes with labels, types, and metadata
- **Edges**: Relationship edges with types and weights
- **Traversal**: Multi-hop BFS with visited node tracking
- **Storage**: PostgreSQL via SQLAlchemy ORM

---

## 9. Multi-Agent Architecture

### Agent Hierarchy
`mermaid
graph TB
    KERNEL[AIKernel] --> REASONING[ReasoningEngine]
    KERNEL --> CONTEXT[ContextEngine]
    KERNEL --> EVAL[EvaluationEngine]
    KERNEL --> GOV[GovernanceEngine]
    
    REASONING --> PLANNER[PlannerAgent]
    PLANNER --> ROUTER[RouterAgent]
    
    ROUTER --> CAREER[CareerAgent]
    ROUTER --> SCHOLARSHIP[ScholarshipAgent]
    ROUTER --> RESEARCH[ResearchAgent]
    ROUTER --> RESUME[ResumeAgent]
    ROUTER --> INTERVIEW[InterviewAgent]
    ROUTER --> DOCUMENT[DocumentAgent]
    ROUTER --> ANALYTICS[AnalyticsAgent]
    ROUTER --> KNOWLEDGE[KnowledgeAgent]
    ROUTER --> WEB[WebAgent]
    ROUTER --> GENERAL[GeneralAgent]
    
    CAREER --> TOOLS[BuiltinToolRegistry]
    SCHOLARSHIP --> TOOLS
    RESEARCH --> TOOLS
`

### Planning Modes
| Mode | Iterations | Use Case |
|---|---|---|
| Fast | 1 | Simple queries |
| Balanced | 3 | Standard tasks |
| Deep Research | 5 | Complex analysis |
| Autonomous | 10 | Multi-step workflows |
| Experimental | 20 | Research tasks |

### Built-in Tools
| Tool | Purpose |
|---|---|
| list_directory | Browse file system |
| ead_file | Read file contents |
| query_db | Execute SQL queries |
| search_vector_store | Semantic search |
| parse_pdf | Extract PDF content |
| local_search | Web search |

---

## 10. Observability Architecture

### Event System
`mermaid
graph LR
    SOURCE[Event Sources] --> BUS[EventBus]
    BUS --> WS[WebSocket /api/stream]
    BUS --> LOG[Structured Logger]
    BUS --> TELEMETRY[Telemetry Store]
    BUS --> LOGFILE[JSONL File]
`

### Event Types
| Category | Events |
|---|---|
| Pipeline | pipeline.step.started, pipeline.step.completed, pipeline.step.failed |
| Agent | gent.task.started, gent.task.completed |
| LLM | llm.request.started, llm.request.completed, llm.provider.switched |
| Document | document.ingested, document.chunked |
| System | system.health.check, system.recovery.attempted |

---

## 11. Configuration Architecture

### Environment Resolution
`mermaid
flowchart TD
    A[.env file] --> SETTINGS[pydantic-settings]
    B[.env.local] --> SETTINGS
    C[Environment Variables] --> SETTINGS
    SETTINGS --> CONFIG[Settings Object]
    CONFIG --> MODULES[All Modules]
`

### Provider Routing (YAML)
`yaml
providers:
  priority: [ollama, gemini, openrouter, together, groq, deepseek, openai, anthropic]
  circuit_breaker:
    failure_threshold: 3
    cooldown_seconds: 300
  retry:
    max_retries: 3
    base_delay: 1.0
    max_delay: 30.0
  health_check:
    interval_seconds: 60
`

---

## 12. Deployment Architecture

### Current State
`mermaid
graph LR
    subgraph Local Dev
        FE[Next.js :3000]
        BE[FastAPI :8001]
        PG[PostgreSQL :5432]
        QD[Qdrant :6333]
        RD[Redis :6379]
        OL[Ollama :11434]
    end

    FE -->|Proxy /api| BE
    BE --> PG
    BE --> QD
    BE --> RD
    BE --> OL
`

### Missing Components
- ? Application Dockerfile
- ? Kubernetes manifests
- ? CI/CD pipeline
- ? Load balancer config
- ? SSL/TLS termination
- ? Monitoring (Prometheus/Grafana)
- ? Log aggregation (ELK)

---

*This document was generated as part of the NORAY OS Phase 1 Technical Audit.*
