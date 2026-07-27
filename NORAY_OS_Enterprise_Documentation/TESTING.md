# Testing

## Current State — 🟡 Partial

NORAY OS is at a **Production Prototype (Beta)** stage. Testing to date has been primarily manual and development-driven (exercising features through the UI and API during iterative development), rather than a formalized, automated test suite with measured coverage.

Documenting this honestly rather than claiming comprehensive automated coverage that does not yet exist is a deliberate choice, consistent with the maturity model used throughout this documentation.

## What Exists Today

- Manual verification of each feature during development (Diagnostics panel, direct API calls, UI walkthroughs)
- Provider health checks (Ollama, Qdrant, PostgreSQL/SQLite, cloud LLM providers) surfaced via the Diagnostics module
- Informal validation of the RAG pipeline (ingestion → retrieval → generation) against sample documents

## Planned Testing Strategy (⚪ Not Yet Implemented)

| Layer | Planned Approach |
|---|---|
| Unit Tests | pytest for backend services, kernel components, and provider adapters |
| Integration Tests | End-to-end RAG pipeline tests (ingestion → retrieval → generation) against a fixed document set |
| API Tests | FastAPI TestClient coverage for all documented endpoints |
| Frontend Tests | Component-level tests (e.g., React Testing Library) for critical workspace components |
| Load / Performance Tests | Formal latency and throughput benchmarking under concurrent load |
| RAG Quality Evaluation | Automated grounding/faithfulness scoring (e.g., RAGAS, DeepEval) to replace the current heuristic confidence indicator |

## Why This Matters

Formal testing and benchmarking are explicitly called out in [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md) under "Production hardening, QA, and performance optimization" — this is treated as a near-term priority rather than an afterthought, precisely because the project's goal is production-grade engineering credibility, not just feature breadth.
