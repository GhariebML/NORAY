# Refactoring Plan

**Project:** NORAY OS
**Audit Date:** July 2026

---

## 1. Executive Summary

This refactoring plan addresses structural issues identified in the codebase audit. The goal is to improve maintainability, reduce technical debt, and prepare for production deployment.

---

## 2. Folder Restructuring

### 2.1 Current Structure Issues
| Issue | Location | Impact |
|---|---|---|
| Dead code in gateway/ | 
oray/gateway/ | Confusion, maintenance burden |
| Mocked retriever | 
oray/rag/universal_retriever.py | Misleading |
| Standalone demo | ag_project/ | Repo clutter |
| Educational notebooks | Notebooks_RAGs/ | Repo clutter |
| Empty output dirs | scholarships/, upskill/ | Confusion |

### 2.2 Recommended Structure
`mermaid
graph TB
    ROOT[NORAY-main] --> NORAY[noray/]
    ROOT --> FRONTEND[frontend/]
    ROOT --> TESTS[tests/]
    ROOT --> DOCS[docs/]
    ROOT --> SCRIPTS[scripts/]
    ROOT --> ARCHIVE[archive/]
    
    NORAY --> API[api/]
    NORAY --> RAG[rag/]
    NORAY --> LLM[llm/]
    NORAY --> AGENTS[agents/]
    NORAY --> INTELLIGENCE[intelligence/]
    NORAY --> GRAPH[graph/]
    NORAY --> MODELS[models/]
    NORAY --> SERVICES[services/]
    NORAY --> OBSERVABILITY[observability/]
    NORAY --> SHARED[shared/]
    NORAY --> CONFIG[config/]
    
    ARCHIVE --> GATEWAY_OLD[archive/gateway/]
    ARCHIVE --> RAG_DEMO[archive/rag_project/]
    ARCHIVE --> NOTEBOOKS[archive/Notebooks_RAGs/]
`

### 2.3 Actions
| Action | Priority | Effort |
|---|---|---|
| Move gateway/ to rchive/ | High | Low |
| Move ag_project/ to rchive/ | High | Low |
| Move Notebooks_RAGs/ to rchive/ | Medium | Low |
| Remove universal_retriever.py | High | Low |
| Create scripts/ directory | Medium | Low |

---

## 3. Architecture Improvements

### 3.1 Consolidate Routing Systems
**Current:** Two routing systems (ModelRouter and SmartRouter)
**Target:** Single SmartRouter with all features

`mermaid
graph LR
    CURRENT[Current] --> MR[ModelRouter]
    CURRENT --> SR[SmartRouter]
    
    TARGET[Target] --> UNIFIED[Unified SmartRouter]
    
    MR --> UNIFIED
    SR --> UNIFIED
`

**Actions:**
| Action | Priority | Effort |
|---|---|---|
| Merge ModelRouter into SmartRouter | High | Medium |
| Update all imports | High | Low |
| Remove outer.py | High | Low |
| Add tier-based scoring to SmartRouter | Medium | Medium |

### 3.2 Consolidate Embedding Managers
**Current:** Two embedding managers (EmbeddingsManager and LocalEmbeddings)
**Target:** Single EmbeddingsManager with local support

**Actions:**
| Action | Priority | Effort |
|---|---|---|
| Merge LocalEmbeddings into EmbeddingsManager | High | Medium |
| Update all imports | High | Low |
| Remove local_embeddings.py | High | Low |

### 3.3 Consolidate Reranker Managers
**Current:** Two reranker systems
**Target:** Single RerankerManager

**Actions:**
| Action | Priority | Effort |
|---|---|---|
| Merge reranker implementations | Medium | Medium |
| Update all imports | Medium | Low |

---

## 4. Reusable Components

### 4.1 Backend Shared Utilities
| Component | Location | Purpose | Status |
|---|---|---|---|
| is_port_open | database.py, health.py | Port checking | Duplicate |
| Retry logic | smart_router.py | Retry with backoff | Inconsistent |
| Circuit breaker | smart_router.py | Failure detection | Inconsistent |
| Health check | health.py | Service checking | Good |

**Actions:**
| Action | Priority | Effort |
|---|---|---|
| Extract is_port_open to shared/utils.py | Medium | Low |
| Extract retry logic to shared/retry.py | Medium | Medium |
| Extract circuit breaker to shared/circuit_breaker.py | Medium | Medium |

### 4.2 Frontend Shared Components
| Component | Location | Purpose | Status |
|---|---|---|---|
| Card patterns | Multiple pages | Data display | Inconsistent |
| Loading spinners | Multiple pages | Loading state | Inconsistent |
| Error alerts | Multiple pages | Error state | Inconsistent |

**Actions:**
| Action | Priority | Effort |
|---|---|---|
| Standardize Card components | Medium | Medium |
| Create shared Loading component | Medium | Low |
| Create shared Error component | Medium | Low |

---

## 5. State Management

### 5.1 Current State
| Approach | Usage | Issues |
|---|---|---|
| Zustand | Global state | Good |
| React hooks | Local state | Good |
| API client | Data fetching | Monolithic |

### 5.2 Recommendations
| Recommendation | Priority | Effort |
|---|---|---|
| Split pi.ts by domain | High | Medium |
| Add React Query for data fetching | Medium | High |
| Add optimistic updates | Medium | Medium |

---

## 6. Hooks & Services

### 6.1 Recommended Hooks
| Hook | Purpose | Priority |
|---|---|---|
| useAuth | Authentication state | Critical |
| useJobs | Job search data | High |
| useScholarships | Scholarship data | High |
| useProfile | Profile management | High |
| useDocuments | Document management | Medium |
| useChat | Chat session | Medium |

### 6.2 Recommended Services
| Service | Purpose | Priority |
|---|---|---|
| AuthService | Authentication logic | Critical |
| JobService | Job search logic | High |
| ScholarshipService | Scholarship logic | High |
| ProfileService | Profile management | High |
| DocumentService | Document management | Medium |
| ChatService | Chat logic | Medium |

---

## 7. Controllers

### 7.1 Recommended Backend Controllers
| Controller | Purpose | Priority |
|---|---|---|
| AuthController | Authentication endpoints | Critical |
| JobController | Job search endpoints | High |
| ScholarshipController | Scholarship endpoints | High |
| ProfileController | Profile endpoints | High |
| DocumentController | Document endpoints | Medium |
| ChatController | Chat endpoints | Medium |

---

## 8. Dependency Injection

### 8.1 Current State
| Feature | Status | Notes |
|---|---|---|
| IoC container | Functional | intelligence/core/di.py |
| FastAPI DI | Functional | Route dependencies |
| Service registration | Partial | Some manual wiring |

### 8.2 Recommendations
| Recommendation | Priority | Effort |
|---|---|---|
| Extend IoC container to all services | Medium | Medium |
| Add service interfaces | Medium | Medium |
| Add configuration-based registration | Low | Low |

---

## 9. Repository Pattern

### 9.1 Current State
| Pattern | Status | Notes |
|---|---|---|
| Direct ORM queries | Functional | In routes |
| Repository abstraction | Partial | In some services |
| Unit of Work | ? Missing | No transaction management |

### 9.2 Recommendations
| Recommendation | Priority | Effort |
|---|---|---|
| Create repository interfaces | High | Medium |
| Implement repositories for all models | High | High |
| Add Unit of Work pattern | Medium | Medium |

---

## 10. Caching

### 10.1 Current State
| Feature | Status | Notes |
|---|---|---|
| Redis cache | Functional | TTL-based |
| Memory fallback | Functional | In-memory |
| Query caching | ? Missing | No query results |

### 10.2 Recommendations
| Recommendation | Priority | Effort |
|---|---|---|
| Add query result caching | High | Medium |
| Add response caching | Medium | Medium |
| Add cache invalidation | Medium | Medium |

---

## 11. Testing

### 11.1 Current State
| Feature | Status | Notes |
|---|---|---|
| Test framework | Configured | pytest |
| Unit tests | ? Missing | No tests |
| Integration tests | ? Missing | No tests |
| E2E tests | ? Missing | No tests |

### 11.2 Recommendations
| Recommendation | Priority | Effort |
|---|---|---|
| Add unit tests for core modules | Critical | High |
| Add integration tests for API | High | High |
| Add E2E tests for critical flows | Medium | High |
| Add test fixtures | High | Medium |
| Add test coverage reporting | Medium | Low |

---

## 12. Refactoring Priority Matrix

| Category | Items | Priority | Effort |
|---|---|---|---|
| Dead code removal | gateway/, universal_retriever.py, ag_project/ | Critical | Low |
| Consolidate routing | Merge ModelRouter into SmartRouter | High | Medium |
| Consolidate embeddings | Merge embedding managers | High | Medium |
| Extract shared utilities | is_port_open, retry, circuit breaker | Medium | Low |
| Add authentication | AuthService, AuthController | Critical | High |
| Add RBAC | Role-based access control | High | High |
| Add tests | Unit, integration, E2E | Critical | High |
| Split pi.ts | Domain-based API client | High | Medium |
| Add hooks | React Query hooks | Medium | Medium |
| Add repositories | Repository pattern | Medium | Medium |

---

## 13. Refactoring Timeline

`mermaid
gantt
    title Refactoring Timeline
    dateFormat  YYYY-MM-DD
    section Quick Wins
    Remove dead code           :a1, 2026-08-01, 3d
    Extract shared utils       :a2, 2026-08-01, 5d
    Fix embedding dimension    :a3, 2026-08-01, 1d
    section Consolidation
    Merge routing systems      :b1, 2026-08-05, 7d
    Merge embedding managers   :b2, 2026-08-05, 5d
    Merge reranker managers    :b3, 2026-08-12, 5d
    section Architecture
    Add authentication         :c1, 2026-08-19, 21d
    Add RBAC                   :c2, 2026-09-09, 14d
    Add repositories           :c3, 2026-09-23, 14d
    section Frontend
    Split api.ts               :d1, 2026-08-19, 7d
    Add React Query            :d2, 2026-08-26, 14d
    Standardize components     :d3, 2026-09-09, 14d
    section Testing
    Add unit tests             :e1, 2026-09-23, 21d
    Add integration tests      :e2, 2026-10-14, 14d
    Add E2E tests              :e3, 2026-10-28, 14d
`

---

## 14. Success Metrics

| Metric | Current | Target |
|---|---|---|
| Dead code lines | ~1,500 | 0 |
| Duplicate code | ~800 lines | < 100 |
| Test coverage | 0% | > 70% |
| Files > 500 lines | 3 | 0 |
| API client lines | 596 | < 200 per file |
| Component reusability | Low | High |

---

*This document was generated as part of the NORAY OS Phase 1 Technical Audit.*
