# Development Roadmap

## Next Milestones

1. Complete Graph RAG implementation.
2. Finish Notebook Intelligence (NotebookLM-style research workspace).
3. Finalize production-grade Job and Scholarship search pipelines.
4. Complete the Human-in-the-Loop workflow (UI + full production flow).
5. Complete advanced Memory System optimization (Semantic/Episodic/Procedural).
6. Improve autonomous planning and multi-agent collaboration.
7. Production hardening, QA, and performance optimization.
8. Complete enterprise deployment and monitoring capabilities.

## Long-Term Vision

NORAY OS is intended to evolve into a complete AI Operating System capable of managing knowledge, documents, research, career development, and autonomous AI workflows through a unified cognitive platform. At its current stage, it is documented as an **independent production prototype (Beta)**, built for research, learning, and portfolio demonstration.

## Enterprise Roadmap (⚪ Planned)

- Multi-user authentication (JWT / OAuth)
- Role-based access control (RBAC)
- Multi-tenancy
- Team workspaces
- Organization Memory
- Enterprise dashboards
- Audit logs
- Managed cloud deployment
- Kubernetes support

None of the above are implemented today; they are documented here as roadmap direction only.

## MCP Integration — ⚪ Planned

Model Context Protocol (MCP) support is part of the long-term architecture. The Tool Registry has been designed with MCP-compatible tool support in mind for future releases, but no MCP integration is active today.

## Agent Evolution

NORAY OS will continue using its custom AI Kernel and orchestration framework rather than adopting an external orchestration framework as its primary runtime. The long-term goal is to evolve the existing orchestrator into a fully autonomous, capability-driven planning engine — while remaining framework-independent.

## Open Source Status

The repository is currently maintained as a personal project. No open-source licensing decision has been finalized (see [`LICENSE.md`](./LICENSE.md)).

## Performance & Benchmarking (Planned)

Formal, reproducible latency/throughput benchmarking has not yet been conducted. Values currently visible in the product UI (e.g., latency, VRAM usage) are development-stage telemetry demonstrating that the observability system works, not certified benchmark results. A formal benchmarking pass is part of the "production hardening" milestone above.

## Consistency Statement

This roadmap, the maturity labels used throughout this documentation set, and the lightweight submission package all share the same underlying source of truth. No roadmap item here is described elsewhere in this documentation as already implemented.
