# NORAY OS

**Enterprise AI Operating System with Hybrid Retrieval-Augmented Generation**

Version `v1.0.0` · Status: **Production Prototype (Beta)** · Independent Project

---

## Overview

NORAY OS is an independent, enterprise-grade AI Operating System that unifies hybrid Retrieval-Augmented Generation (RAG), local and cloud LLM routing, document intelligence, and a custom multi-agent orchestration framework into a single cognitive workspace.

Rather than a single-purpose chatbot, NORAY OS is designed as a platform: a set of composable AI-native modules — workspace, retriever, memory, document generator, job/scholarship search, and observability — coordinated by a custom AI Kernel.

NORAY OS was designed, architected, and developed independently by **Mohamed Gharieb**, and was built to fulfill the Retrieval-Augmented Generation requirements of the Digilians *AI Tools & Emerging Technologies* course (Lab 2 + Lab 6), extended into a complete enterprise software platform.

> This documentation set follows a strict maturity model. Every capability is labeled ✅ **Implemented**, 🟡 **Partial**, or ⚪ **Planned**. No planned or partial capability is described as production-complete.

---

## Core Capabilities

| Module | Status |
|---|---|
| AI Workspace Canvas | ✅ Implemented |
| Hybrid RAG Pipeline (Dense + Sparse + RRF) | ✅ Implemented |
| Knowledge Upload & Ingestion | ✅ Implemented |
| AI Document Generator (CV / SOP / Motivation Letter / Research Proposal) | ✅ Implemented |
| Command Center (Execution DAG, Observability) | ✅ Implemented |
| System Diagnostics | ✅ Implemented |
| AI Telemetry | ✅ Implemented |
| Job Search Engine | 🟡 Partial |
| Scholarship Search Engine | 🟡 Partial |
| Applications Tracker | 🟡 Partial |
| AI Memory Center | 🟡 Partial |
| Notebook Workspace | 🟡 Partial |
| Human-in-the-Loop Inbox | 🟡 Partial |
| Graph RAG / Knowledge Graph Traversal | 🟡 Partial (architecture only) |
| Multi-user Authentication | ⚪ Planned |

See [`FEATURES.md`](./FEATURES.md) for full detail on each module.

---

## Architecture at a Glance

```
User Request → AI Kernel → Intent Classification → Context Builder
      → Universal Retriever (Dense + BM25 + Metadata) → RRF Fusion
      → LLM Gateway (Local + Cloud Router) → Response Builder → Streaming Response
```

Full architecture, including the planned Phase 5+ cognitive flow (dynamic planning, Graph RAG, reflection loop), is documented in [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md).

---

## Technology Stack

- **Frontend:** Next.js 15, React, TypeScript, Tailwind CSS, React Flow, Zustand
- **Backend:** Python, FastAPI, AsyncIO, SQLAlchemy, Alembic
- **Database:** SQLite (development) · PostgreSQL (production, via Docker)
- **Vector Store:** Qdrant (self-hosted)
- **Local LLM Runtime:** Ollama (Llama 3.1 8B, Qwen 2.5 7B, Nomic Embed Text)
- **Cloud LLM Providers:** Google Gemini, OpenRouter, Together AI, DeepSeek
- **Infrastructure:** Docker Compose, Redis

Full rationale and alternatives considered are in [`TECH_STACK.md`](./TECH_STACK.md).

---

## Documentation Index

| Document | Purpose |
|---|---|
| [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) | Mission, vision, goals |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | End-to-end architecture, diagrams, folder structure |
| [RAG_PIPELINE.md](./RAG_PIPELINE.md) | Full retrieval-augmented generation pipeline |
| [AI_KERNEL.md](./AI_KERNEL.md) | Custom orchestration & agent framework |
| [TECH_STACK.md](./TECH_STACK.md) | Stack decisions and alternatives |
| [FEATURES.md](./FEATURES.md) | Feature-by-feature breakdown |
| [INSTALLATION.md](./INSTALLATION.md) | Local setup guide |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Docker Compose & infrastructure |
| [API_REFERENCE.md](./API_REFERENCE.md) | Representative API endpoints |
| [AI_MODELS.md](./AI_MODELS.md) | Model routing, providers, failover |
| [KNOWLEDGE_MANAGEMENT.md](./KNOWLEDGE_MANAGEMENT.md) | Ingestion, chunking, namespaces |
| [COMMAND_CENTER.md](./COMMAND_CENTER.md) | Observability & governance UI |
| [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) | Multi-agent design |
| [MEMORY_SYSTEM.md](./MEMORY_SYSTEM.md) | Memory types and status |
| [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) | Next milestones & long-term vision |
| [TESTING.md](./TESTING.md) | QA approach |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |
| [LICENSE.md](./LICENSE.md) | Licensing status |

---

## Repository & Links

- **GitHub:** [github.com/GhariebML/NORAY](https://github.com/GhariebML/NORAY)
- **Portfolio:** [mohamed-gharieb-portfolio.vercel.app](https://mohamed-gharieb-portfolio.vercel.app/)
- **Google Drive:** `[GOOGLE_DRIVE_PUBLIC_LINK]` — pending
- **Live Demo:** Local development only at this stage

## Creator

Independently designed and developed by **Mohamed Gharieb** — AI Solutions Architect, Lead AI Engineer, Full-Stack Developer.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for a note on AI-assisted engineering practices used during development.
