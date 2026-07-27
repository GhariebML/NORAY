# NORAY OS — Refactoring Plan

**Audit Date:** July 2026

---

## 1. Folder Restructuring

### Current Structure Issues
- `noray/agents/` vs `noray/career_agent/` vs `noray/intelligence/` — three agent-related directories
- `noray/services/` is a grab-bag of unrelated services
- `noray/shared/` contains both models and utilities
- `rag_project/` is orphaned

### Recommended Structure

```
noray/
├── api/                      # API layer (keep as-is)
│   ├── routes/
│   ├── schemas.py
│   └── middleware/
├── core/                     # NEW: Consolidated core
│   ├── config.py             # From config.py + config/
│   ├── models.py             # From shared/models.py
│   ├── prompts.py            # From shared/prompts.py + prompts/
│   └── exceptions.py         # From api/errors.py + new
├── llm/                      # LLM layer (keep as-is)
│   ├── providers/
│   ├── smart_router.py
│   └── factory.py
├── agents/                   # CONSOLIDATED: All agents
│   ├── base.py               # Agent base class
│   ├── career.py             # From career_agent/
│   ├── scholarship.py        # From scholarship_agent/
│   ├── upskill.py            # From upskill_agent/
│   ├── document.py           # From document_generator/
│   ├── research.py           # From research/
│   └── tools/                # From agents/tools/
├── rag/                      # RAG layer (keep as-is)
├── graph/                    # Graph layer (keep as-is)
├── data/                     # NEW: Data access layer
│   ├── profile.py            # From shared/profile_store.py
│   ├── applications.py       # From dashboard/
│   └── cache.py              # From cache/
├── services/                 # CONSOLIDATED: Only shared services
│   ├── conversation.py       # From services/conversation_manager.py
│   └── task_runner.py        # From services/task_runner.py
└── observability/            # Observability (keep as-is)
```

---

## 2. Architecture Improvements

### 2.1 Consolidate Document Generation

**Current:** 3 implementations
- `noray/document_generator/service.py` (modern, AI-powered)
- `noray/career_agent/cv_optimizer.py` (legacy, LaTeX)
- `noray/career_agent/cover_letter_generator.py` (legacy, LaTeX)

**Action:** Deprecate legacy generators. Keep `document_generator/service.py` as single source. Move LaTeX compilation to a shared utility.

### 2.2 Consolidate Prompt Management

**Current:** 2 systems
- `noray/prompts/*.yaml` (versioned, with loader)
- `noray/shared/prompts.py` (Python strings)

**Action:** Migrate all prompts to YAML system. Create a single `PromptManager` that loads from YAML with fallback to defaults.

### 2.3 Consolidate LLM Calling

**Current:** 3 patterns
- `SmartRouter.generate_with_fallback()` (intended)
- `LLMProviderFactory.get_provider().generate()` (bypasses router)
- `shared/llm_utils.call_llm()` (simple wrapper)

**Action:** Deprecate direct provider calls and `call_llm()`. Route everything through SmartRouter.

---

## 3. Reusable Components

### 3.1 Frontend Component Library

Create dedicated component files instead of monolithic `ui.tsx`:

```
components/ui/
├── Button.tsx
├── Card.tsx
├── Badge.tsx
├── Modal.tsx          # NEW
├── DataTable.tsx      # NEW
├── FormInput.tsx      # NEW
├── Tooltip.tsx        # NEW
├── Dropdown.tsx       # NEW
├── Tabs.tsx           # NEW
├── ErrorBoundary.tsx  # NEW
├── SkeletonLoader.tsx
├── LoadingSpinner.tsx
├── EmptyState.tsx
├── Toast.tsx
├── PageHeader.tsx
└── StatCard.tsx
```

### 3.2 Backend Service Layer

Create proper service interfaces:

```python
# noray/services/base.py
class BaseService:
    def __init__(self, db: Session, cache: RedisCache):
        self.db = db
        self.cache = cache

# noray/services/job_service.py
class JobService(BaseService):
    def search(self, query: str, filters: dict) -> list[Job]:
        ...
    def score(self, job: Job, profile: CareerProfile) -> JobScore:
        ...
    def apply(self, job_id: str, profile: CareerProfile) -> Application:
        ...
```

---

## 4. State Management

### Current (Frontend)
- Zustand stores for command center only (5 stores)
- All page state is local `useState`
- No global state for user profile, settings, or notifications

### Recommended
```
stores/
├── authStore.ts        # NEW: Authentication state
├── profileStore.ts     # NEW: User profile (cached from API)
├── notificationStore.ts # NEW: Notifications
├── settingsStore.ts    # NEW: App settings
├── dagStore.ts         # Existing
├── agentStore.ts       # Existing
├── layoutStore.ts      # Existing
├── logStore.ts         # Existing
└── websocketClient.ts  # Existing
```

---

## 5. Custom Hooks

Create reusable hooks:

```typescript
// hooks/
├── useApi.ts           # API call with loading/error states
├── useAuth.ts          # Authentication state
├── useProfile.ts       # Profile data
├── useWebSocket.ts     # WebSocket connection
├── useDebounce.ts      # Debounced search
├── useLocalStorage.ts  # Persistent state
└── useToast.ts         # Toast notifications
```

---

## 6. Services & Controllers

### Current
Routes contain business logic directly:

```python
@router.post("/search")
async def search_jobs(request: JobSearchRequest):
    # 20 lines of business logic in the route
    profile = load_profile()
    results = search_jobs(...)
    return results
```

### Recommended
Separate controllers from routes:

```python
# noray/api/routes/jobs.py
@router.post("/search")
async def search_jobs(request: JobSearchRequest):
    return await job_controller.search(request)

# noray/api/controllers/job_controller.py
class JobController:
    async def search(self, request: JobSearchRequest):
        profile = self.profile_service.get()
        results = self.job_service.search(request.query, profile)
        return results
```

---

## 6. Dependency Injection

### Current
- `DIContainer` exists in `intelligence/core/di.py` but only used by intelligence layer
- Most modules use direct imports and lazy imports

### Recommended
Expand DI to all layers:

```python
# noray/core/container.py
class Container:
    def __init__(self):
        self.db = DatabaseSession()
        self.cache = RedisCache()
        self.profile = ProfileService(self.db)
        self.smart_router = SmartRouter()
        self.job_service = JobService(self.db, self.cache, self.smart_router)
        self.document_service = DocumentService(self.smart_router, self.profile)
```

---

## 7. Repository Pattern

### Current
Direct SQLAlchemy queries in routes and services:

```python
apps = db.query(ApplicationModel).filter(...).all()
```

### Recommended
Repository abstraction:

```python
# noray/data/repositories/application_repository.py
class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, filters: dict) -> list[Application]:
        return self.db.query(ApplicationModel).filter(...).all()
    
    def create(self, data: dict) -> Application:
        app = ApplicationModel(**data)
        self.db.add(app)
        self.db.commit()
        return app
```

---

## 8. Testing Improvements

### Current Issues
- Heavy mocking (mock SmartRouter, mock providers)
- 2 test files hang (call real LLM)
- No integration tests
- No e2e tests

### Recommended
```
tests/
├── unit/               # Fast, no I/O
│   ├── test_models.py
│   ├── test_task_analyzer.py
│   └── test_fusion.py
├── integration/        # Real DB, real Qdrant
│   ├── test_api.py
│   ├── test_rag_pipeline.py
│   └── test_profile_store.py
├── e2e/                # Full stack
│   ├── test_document_generation.py
│   └── test_job_search.py
└── fixtures/           # Shared test data
```

---

## Refactoring Priority

| Priority | Item | Effort | Risk |
|----------|------|--------|------|
| 1 | Delete `rag_project/` orphan | 5 min | None |
| 2 | Delete unused frontend components | 30 min | None |
| 3 | Unify error response format | 2 hrs | Low |
| 4 | Add React error boundaries | 2 hrs | Low |
| 5 | Consolidate LLM calling patterns | 1 day | Medium |
| 6 | Consolidate prompt systems | 2 days | Medium |
| 7 | Extract frontend UI components | 3 days | Low |
| 8 | Add custom hooks | 2 days | Low |
| 9 | Implement repository pattern | 3 days | Medium |
| 10 | Consolidate document generators | 2 days | Medium |
| 11 | Add DI to all layers | 3 days | Medium |
| 12 | Restructure folders | 1 day | High |
