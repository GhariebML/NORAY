# AI Kernel

The AI Kernel is NORAY OS's custom orchestration engine — the component responsible for coordinating retrieval, memory, tools, and language models into a single coherent request/response cycle. It is a **custom-built framework**, not based on LangChain or LangGraph.

## Design Rationale

A custom kernel was chosen over adopting an existing agent framework in order to keep NORAY OS framework-independent, to allow tight control over routing/cost/latency trade-offs, and to make the execution pipeline fully observable through the Command Center. The long-term goal (see [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md)) is to evolve this kernel into a fully autonomous, capability-driven planning engine — while remaining framework-independent rather than migrating to an external orchestrator.

## Core Components

| Component | Status | Description |
|---|---|---|
| Orchestrator | ✅ Implemented | Coordinates the request lifecycle: intent → context → retrieval → generation → response. |
| Capability Registry | ✅ Implemented | Registry of what the system can do (tools, retrieval strategies, generation modes). |
| Agent Registry | 🟡 Partial | Registers available agents; multi-agent collaboration is still evolving. |
| Execution DAG | ✅ Implemented (visualization) / 🟡 Partial (dynamic generation) | Represents task execution as a directed graph, visualized live in the Command Center. |
| Task Runner | ✅ Implemented | Executes background and foreground tasks, with retry and progress tracking. |
| Planning Engine | 🟡 Partial | Rule-assisted orchestration with cognitive execution scaffolding; fully autonomous dynamic planning is a future goal. |
| Context Engine | ✅ Implemented | Assembles the working context from memory, retrieval results, and conversation state. |
| Universal Retriever | ✅ Implemented | Combines dense, sparse, and metadata retrieval strategies. |
| HITL Manager | 🟡 Partial | Backend architecture and approval workflow exist; UI integration is still being finalized. |
| Tool Registry | ✅ Implemented (core) / ⚪ Planned (MCP, plugins) | Supports native tools and Python tools today; REST/MCP/plugin ecosystem is planned. |
| Memory Manager | 🟡 Partial | Coordinates access across the six memory types (see [`MEMORY_SYSTEM.md`](./MEMORY_SYSTEM.md)). |

## Architectural Principles

The AI Kernel follows **SOLID principles** and **Clean Architecture** patterns, with clear separation between:

- **API Layer** — request/response boundary (FastAPI)
- **Services** — business logic
- **AI Kernel** — orchestration and routing
- **RAG Engine** — retrieval and context assembly
- **LLM Gateway** — provider abstraction and routing
- **Memory / Intelligence / Telemetry** — cross-cutting capabilities
- **Database / Models** — persistence layer

This layering is intended to let individual components (e.g., the planner, or a specific memory type) evolve independently without destabilizing the rest of the system.

## Current Limitations (Stated Explicitly)

- The Execution DAG shown in the Command Center currently reflects a largely fixed pipeline structure for observability; fully dynamic, per-query DAG generation is not yet implemented.
- Multi-agent collaboration exists at the registry/architecture level but is not yet driving autonomous multi-agent task decomposition in production.
