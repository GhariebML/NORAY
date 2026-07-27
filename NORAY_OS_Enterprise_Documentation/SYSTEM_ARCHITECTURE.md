# System Architecture

## Maturity Model (applies throughout this document)

- ✅ **Production Implementation** — fully functional today.
- 🟡 **Implemented Infrastructure** — core architecture exists but requires production completion.
- ⚪ **Architectural Vision** — future capability, already designed, intentionally deferred.

---

## 1. End-to-End RAG Flow

The Command Center visualizes a target cognitive execution pipeline. Not every node in that visualization is fully operational today — the sections below separate what runs in production from what is architectural intent.

### ✅ Current Production Flow

```
User Request
     │
     ▼
AI Kernel
     │
     ▼
Intent Classification
     │
     ▼
Context Builder
(Conversation + Workspace + Memory)
     │
     ▼
Universal Retriever
     │
     ├── Dense Vector Search (Qdrant)
     ├── Sparse BM25 Search
     └── Metadata Filtering
     │
     ▼
Hybrid Fusion (Reciprocal Rank Fusion)
     │
     ▼
LLM Gateway (Model Router)
     │
     ▼
Response Builder
     │
     ▼
Streaming Response
```

### 🟡 Planned Cognitive Flow (Phase 5+)

The following are designed and partially scaffolded but not yet part of the operational runtime:

- Dynamic Task Planner
- Multi-Agent Planning
- Knowledge Graph Traversal (Graph RAG)
- Reflection Loop
- Automated Grounding Validator
- Self-Evaluation

These are documented as Phase 5+ architecture, not current runtime behavior.

---

## 2. Document Ingestion Pipeline

```
User uploads document
     │
     ▼
Document Validation
     │
     ▼
Text Extraction (PDF / DOCX / TXT / MD / CSV / XLSX / PPTX / Images)
     │
     ▼
Cleaning & Normalization
     │
     ▼
Chunking
     │
     ▼
Embedding Generation
     │
     ▼
Qdrant Vector Storage
     │
     ▼
Metadata Registration
     │
     ▼
Immediately searchable inside Chat
```

Supported formats: PDF, DOCX, TXT, Markdown, CSV, XLSX, PPTX, Images (OCR pipeline 🟡 under improvement).

---

## 3. Chunking Strategy

✅ Implemented: recursive fixed-size chunking, configurable overlap, metadata attached per chunk, namespace-aware indexing.

⚪ Planned: semantic chunking, adaptive chunk sizing, context-aware chunk merging, parent-child retrieval.

Chunk size and overlap are configurable and intentionally not hardcoded in this documentation, as they remain subject to optimization.

---

## 4. Memory Architecture

| Memory Type | Status |
|---|---|
| Conversation Memory | ✅ Implemented |
| Workspace Memory | ✅ Implemented |
| Semantic Memory | 🟡 Infrastructure exists; long-term extraction evolving |
| Episodic Memory | 🟡 Interaction history exists; retrieval optimization in progress |
| Procedural Memory | 🟡 Learning-signal architecture exists; automatic adaptation not yet implemented |
| Organization Memory | ⚪ Planned |

Memory retrieval is currently coordinated by the Context Engine. A dedicated Memory Router that dynamically selects optimal memory sources is planned for a future version. Full detail in [`MEMORY_SYSTEM.md`](./MEMORY_SYSTEM.md).

---

## 5. Knowledge Graph

🟡 Graph RAG is under active development.

**Implemented:** Knowledge Graph architecture, interfaces, registry, retrieval abstractions.

**Not yet production complete:** full graph traversal, entity expansion, multi-hop reasoning, production graph indexing.

The Command Center DAG reserves this execution stage because it represents the target cognitive architecture, not current runtime behavior.

---

## 6. Planning Engine

The AI Kernel performs orchestration and routing. Execution DAG infrastructure exists, and task execution can already be represented as DAG nodes. Fully autonomous, dynamic DAG generation per request is still evolving.

Current planner is best described as: **"Rule-assisted orchestration with cognitive execution scaffolding."**

⚪ Future direction: dynamic planning, multi-agent decomposition, autonomous scheduling, recursive planning.

---

## 7. Background Task Engine

✅ Implemented: asyncio-based task runner, database-backed task queue, progress tracking, retry support, human-approval suspension, background indexing.

⚪ Not implemented: Celery, Temporal, distributed workers. The abstraction layer is intentionally designed so these can be introduced later without changing business logic.

---

## 8. Explainability & Grounding Validation

✅ Implemented: the Explainability layer records reasoning steps, selected retrieval sources, tools used, models used, execution metadata, token usage, and costs.

🟡 Hallucination Risk: the UI currently displays a heuristic confidence indicator, not a certified score. A full LLM-as-a-Judge validation pipeline (faithfulness scoring, context precision/recall, answer relevance — via frameworks such as DeepEval or RAGAS) is planned for a future release.

---

## 9. Main Components

- AI Workspace Canvas
- Hybrid RAG Pipeline
- Document Ingestion Engine
- Universal Retriever
- AI Kernel (custom orchestrator)
- Local & Cloud LLM Router
- Command Center (observability & governance)
- Vector Knowledge Base (Qdrant)
- Telemetry & Diagnostics

## 10. Indicative Folder Structure

```
noray-os/
├── backend/
│   ├── api/                 # FastAPI routes
│   ├── kernel/               # AI Kernel, orchestrator, capability registry
│   ├── rag/                  # Retriever, chunking, embedding, fusion
│   ├── llm_gateway/           # Provider adapters, router, failover
│   ├── memory/                # Memory types, context engine
│   ├── intelligence/           # Explainability, reasoning, task runner
│   ├── telemetry/              # Metrics, cost tracking, diagnostics
│   ├── db/                    # Models, migrations (Alembic)
│   └── main.py
├── frontend/
│   ├── app/                  # Next.js app router pages
│   ├── components/            # UI components (Workspace, Command Center, etc.)
│   ├── store/                 # Zustand state
│   └── lib/
├── docker-compose.yml
└── docs/                      # This documentation set
```

This structure reflects the conceptual organization of the codebase; exact paths may vary — refer to the GitHub repository for the current layout.
