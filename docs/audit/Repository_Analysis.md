# Repository Analysis

**Project:** NORAY OS
**Audit Date:** July 2026

---

## 1. Folder Structure Overview

`mermaid
graph TB
    ROOT[NORAY-main] --> FRONTEND[frontend/]
    ROOT --> NORAY[noray/]
    ROOT --> DATA[data/]
    ROOT --> DOCS[docs/]
    ROOT --> CV[cv/]
    ROOT --> COVER[cover_letters/]
    ROOT --> DOCUMENTS[documents/]
    ROOT --> TESTS[tests/]
    ROOT --> NOTEBOOKS[Notebooks_RAGs/]
    ROOT --> RAG_DEMO[rag_project/]
    ROOT --> TOOLS[tools/]
    ROOT --> UPSKILL[upskill/]
    ROOT --> SCHOLARSHIPS[scholarships/]
    ROOT --> JOB_SCRAPER[job_scraper/]
    
    FRONTEND --> FE_SRC[src/]
    FE_SRC --> APP[app/]
    FE_SRC --> COMPONENTS[components/]
    FE_SRC --> LIB[lib/]
    
    NORAY --> AGENTS[agents/]
    NORAY --> API[api/]
    NORAY --> RAG[rag/]
    NORAY --> LLM[llm/]
    NORAY --> GRAPH[graph/]
    NORAY --> INTELLIGENCE[intelligence/]
    NORAY --> OBSERVABILITY[observability/]
    NORAY --> MODELS[models/]
    NORAY --> SERVICES[services/]
    NORAY --> GATEWAY[gateway/]
    NORAY --> CAREER[career_agent/]
    NORAY --> SCHOLARSHIP_AGT[scholarship_agent/]
    NORAY --> UPSKILL_AGT[upskill_agent/]
`

---

## 2. File Statistics

| Directory | Files | Lines (est.) | Purpose |
|---|---|---|---|
| 
oray/ | ~80 Python files | ~15,000 | Core backend package |
| rontend/src/ | ~25 TypeScript files | ~8,000 | Frontend application |
| 	ests/ | ~5 files | ~200 | Test suite |
| docs/ | ~10 files | ~500 | Documentation |
| cv/ | ~5 files | ~500 | LaTeX CV templates |
| cover_letters/ | ~3 files | ~300 | LaTeX cover letter templates |
| Notebooks_RAGs/ | ~20 files | ~2,000 | Jupyter notebooks (standalone) |
| ag_project/ | ~10 files | ~1,000 | Streamlit RAG demo (standalone) |

---

## 3. Dead Code Analysis

### 3.1 
oray/gateway/ — Duplicate LLM Layer
| File | Lines | Status | Issue |
|---|---|---|---|
| ase.py | ~50 | Dead | Abstract base class not used |
| acade.py | ~100 | Dead | Gateway facade not imported |
| hardware_detector.py | ~80 | Dead | GPU detection not integrated |
| installer.py | ~100 | Dead | Model installer not integrated |
| ollama_manager.py | ~120 | Dead | Duplicate of llm/providers/ollama_provider.py |
| egistry.py | ~60 | Dead | Provider registry not used |
| outer.py | ~100 | Dead | Duplicate of llm/router.py |
| providers/*.py | ~400 | Dead | 5 provider implementations duplicated in llm/providers/ |

**Total Dead Code:** ~1,010 lines

### 3.2 
oray/rag/universal_retriever.py — Mocked Interface
| Method | Implementation | Status |
|---|---|---|
| etrieve() | Returns hardcoded mock data | Mocked |
| index() | No-op | Mocked |
| delete() | No-op | Mocked |
| search() | Returns empty list | Mocked |

**Issue:** Entire file is a mock. Not used in actual retrieval pipeline.

### 3.3 ag_project/ — Standalone Demo
| File | Purpose | Integration |
|---|---|---|
| pp.py | Streamlit RAG demo | ? Not integrated |
| ag_engine.py | ChromaDB-based RAG | ? Not integrated |
| equirements.txt | Separate dependencies | ? Not integrated |

**Issue:** Separate project using ChromaDB + OpenAI. Completely independent from NORAY's Qdrant-based RAG.

### 3.4 Notebooks_RAGs/ — Jupyter Notebooks
| Notebook | Purpose | Integration |
|---|---|---|
| Lab1/ - Lab9/ | RAG tutorials | ? Not integrated |
| Various | Image processing, text preprocessing | ? Not integrated |

**Issue:** Educational notebooks not connected to the main codebase.

### 3.5 Empty/Placeholder Directories
| Directory | Contents | Status |
|---|---|---|
| scholarships/ | .gitkeep only | Empty output directory |
| upskill/ | .gitkeep only | Empty output directory |
| job_scraper/seen_jobs.json | Runtime data | Should not be tracked |

---

## 4. Duplicated Code Analysis

### 4.1 Two Routing Systems
| System | File | Lines | Features |
|---|---|---|---|
| ModelRouter | 
oray/llm/router.py | ~200 | Tier-based scoring |
| SmartRouter | 
oray/llm/smart_router.py | 1,137 | Circuit breaker, failover, health |

**Issue:** Both systems exist. SmartRouter is used in production; ModelRouter appears unused.

### 4.2 Two Embedding Managers
| System | File | Features |
|---|---|---|
| EmbeddingsManager | 
oray/rag/embeddings.py | Factory pattern, provider abstraction |
| LocalEmbeddings | 
oray/rag/local_embeddings.py | Local model management |

**Issue:** Overlapping responsibilities. Both manage embedding model loading.

### 4.3 Two Reranker Systems
| System | File | Features |
|---|---|---|
| RerankerManager | 
oray/rag/reranker.py | Factory pattern |
| Local reranker | Integrated in pipeline | CrossEncoder loading |

**Issue:** Duplicate abstraction layers.

### 4.4 Duplicate is_port_open Functions
| File | Implementation |
|---|---|
| 
oray/database.py:31 | socket.create_connection with 2s timeout |
| 
oray/health.py:8 | socket.create_connection with 1s timeout |

**Issue:** Same function implemented twice with different timeouts.

---

## 5. Large Files (Decomposition Candidates)

| File | Lines | Issue | Recommendation |
|---|---|---|---|
| 
oray/llm/smart_router.py | 1,137 | Monolithic router | Split into: circuit_breaker.py, health_monitor.py, router_core.py |
| rontend/src/app/page.tsx | 730 | Dashboard with mock data | Extract components, connect to live API |
| rontend/src/lib/api.ts | 596 | Single API client | Split by domain (jobs, scholarships, workspace) |
| 
oray/rag/retrieval_pipeline.py | ~500 | 7-stage pipeline | Well-structured but could be decomposed |
| 
oray/intelligence/core/reasoning.py | ~400 | ReAct loop | Reasonable size, minor cleanup |

---

## 6. Circular Dependencies

### Potential Issues
| Module A | Module B | Risk |
|---|---|---|
| 
oray.config | 
oray.database | Low — config imports first |
| 
oray.llm.smart_router | 
oray.intelligence.core.reasoning | Medium — bidirectional imports possible |
| 
oray.agents.agent_router | 
oray.llm.smart_router | Medium — agent uses router |

**Assessment:** No critical circular dependencies detected, but import chains are complex.

---

## 7. Dependency Graph

### Python Dependencies (Key Relationships)
`mermaid
graph TD
    FASTAPI[FastAPI] --> UVICORN[Uvicorn]
    FASTAPI --> PYDANTIC[Pydantic]
    SQLALCHEMY[SQLAlchemy] --> ALEMBIC[Alembic]
    SQLALCHEMY --> PSYCOPG2[psycopg2]
    QDRANT[qdrant-client] --> QDRANT_SERVER[Qdrant Server]
    SENTENCE_TRANSFORMERS[sentence-transformers] --> TORCH[PyTorch]
    HTTPX[httpx] --> PROVIDERS[LLM Providers]
    
    NORAY[noray] --> FASTAPI
    NORAY --> SQLALCHEMY
    NORAY --> QDRANT
    NORAY --> SENTENCE_TRANSFORMERS
    NORAY --> HTTPX
`

### Frontend Dependencies (Key Relationships)
`mermaid
graph TD
    NEXTJS[Next.js 16] --> REACT[React 19]
    NEXTJS --> TAILWIND[Tailwind CSS 4]
    ZUSTAND[Zustand] --> REACT
    FRAMER[Framer Motion] --> REACT
    RECHARTS[Recharts] --> REACT
    XYFLOW["@xyflow/react"] --> REACT
    
    NORAY_FE[Frontend] --> NEXTJS
    NORAY_FE --> ZUSTAND
    NORAY_FE --> FRAMER
    NORAY_FE --> RECHARTS
    NORAY_FE --> XYFLOW
`

---

## 8. Technical Debt Summary

### High Priority
| Item | Impact | Effort |
|---|---|---|
| Remove gateway/ module | -1,010 lines dead code | Low |
| Remove universal_retriever.py | Cleaner RAG architecture | Low |
| Remove ag_project/ | Cleaner repo structure | Low |
| Fix embedding dimension mismatch | Prevent runtime errors | Low |

### Medium Priority
| Item | Impact | Effort |
|---|---|---|
| Consolidate routing systems | Single routing abstraction | Medium |
| Consolidate embedding managers | Single embedding abstraction | Medium |
| Extract is_port_open to utils | DRY compliance | Low |
| Decompose smart_router.py | Better maintainability | Medium |
| Decompose page.tsx | Better React performance | Medium |

### Low Priority
| Item | Impact | Effort |
|---|---|---|
| Remove empty directories | Cleaner repo | Low |
| Archive notebooks | Clear separation | Low |
| Add type hints to universal_retriever.py | Type safety | Low |

---

## 9. Code Duplication Matrix

| Component | Duplicate Location | Severity |
|---|---|---|
| LLM Provider abstraction | gateway/providers/ vs llm/providers/ | High |
| Routing logic | gateway/router.py vs llm/router.py vs llm/smart_router.py | High |
| Embedding management | ag/embeddings.py vs ag/local_embeddings.py | Medium |
| Reranker management | ag/reranker.py vs inline in pipeline | Medium |
| Port checking | database.py vs health.py | Low |
| Ollama management | gateway/ollama_manager.py vs llm/providers/ollama_provider.py | Medium |

---

## 10. Recommendations

### Immediate Actions
1. **Delete 
oray/gateway/** — 1,010 lines of dead code
2. **Delete 
oray/rag/universal_retriever.py** — Mocked, unused
3. **Archive ag_project/** — Move to rchive/ or delete
4. **Archive Notebooks_RAGs/** — Move to rchive/ or delete

### Short-Term Refactoring
1. **Consolidate routing** — Keep SmartRouter, remove ModelRouter
2. **Consolidate embeddings** — Merge into single EmbeddingsManager
3. **Extract shared utilities** — is_port_open, retry logic, circuit breaker
4. **Split large files** — smart_router.py, page.tsx, pi.ts

### Long-Term Improvements
1. **Module boundaries** — Enforce clear import paths
2. **Plugin architecture** — For new providers and agents
3. **API versioning** — /api/v1/ prefix
4. **Type safety** — Reduce Any usage across codebase

---

*This document was generated as part of the NORAY OS Phase 1 Technical Audit.*
