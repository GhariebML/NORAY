# Features

Maturity model: ✅ Implemented (production-ready end-to-end) · 🟡 Partial (core exists, hardening in progress) · ⚪ Planned.

---

### 1. AI Workspace Canvas — ✅ Implemented

The primary interaction hub. Includes the chat interface, AI Kernel integration, streaming responses, a live document workspace, a reasoning timeline, and a RAG context/inspector panel showing retrieval sources, confidence, and grounding indicators side-by-side with generated content.

### 2. Notebook Workspace — 🟡 Partial

Infrastructure for a NotebookLM-style research workspace, where users organize uploaded documents and generate AI notes/summaries across multiple sources. Core architecture exists; advanced notebook workflows are still under development.

### 3. Job Search Engine — 🟡 Partial

Multi-provider architecture (RemoteOK, Adzuna, Tavily, SerpAPI, etc.) with a provider registry, fallback logic, and AI-based fit scoring. Some providers require API keys and further production validation.

### 4. Scholarship Search Engine — 🟡 Partial

Database connectors, eligibility pipeline, filtering by degree/country/research area, and AI-assisted analysis for scholarships including DAAD, Chevening, Fulbright, Erasmus Mundus, Gates Cambridge, and MEXT. Additional providers and production validation are ongoing.

### 5. AI Document Generator — ✅ Implemented

Generates ATS-optimized resumes/CVs, Statements of Purpose, motivation letters, and research proposals using the AI Kernel and a structured prompt system, tailored to a target company/role and optional job URL.

### 6. Applications Tracker — 🟡 Partial

Tracking infrastructure and UI exist. Advanced Kanban workflow, automation, and synchronization are planned for upcoming phases.

### 7. AI Memory Center — 🟡 Partial

Working Memory, Conversation Memory, and a Semantic Memory architecture with a Memory Explorer UI are implemented. Procedural learning and advanced long-term optimization are still evolving. Full detail in [`MEMORY_SYSTEM.md`](./MEMORY_SYSTEM.md).

### 8. AI Telemetry — ✅ Implemented

Displays execution metrics, token usage, provider information, latency, and cost per request, sourced from the AI Kernel's telemetry layer.

### 9. Command Center (Mission Control) — ✅ Implemented

Live Execution DAG visualization, Agent Monitor, Tool Registry, Memory Explorer, Retriever Inspector, Model Observatory, Telemetry Dashboard, Governance panel, and execution tracing. See [`COMMAND_CENTER.md`](./COMMAND_CENTER.md).

### 10. Global Knowledge Upload Center — ✅ Implemented

The floating **+ Add Knowledge** action, available globally, supports document upload, ingestion, chunking, embedding, indexing, namespace selection, preview, and document management.

### 11. System Diagnostics — ✅ Implemented

Provider health monitoring, Ollama status, API diagnostics, model availability, system metrics, and infrastructure validation.

### 12. Profile & Upskill Modules — 🟡 Partial

User profile management and career-development workflows are available. Personalized AI coaching, adaptive learning plans, and advanced upskilling automation are still under development.

### 13. Human-in-the-Loop (HITL) Inbox — 🟡 Partial

Backend architecture, approval workflow, and Governance Engine exist. UI integration and the full production workflow are still being finalized.

---

## Current Development Focus

NORAY OS's active development is currently concentrated on:

1. Completing all external provider integrations.
2. Finalizing Graph RAG.
3. Production hardening and QA.
4. Advanced Notebook Intelligence.
5. Multi-user authentication.
6. Distributed deployment readiness.
7. Performance optimization and caching.

See [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md) for the full roadmap.
