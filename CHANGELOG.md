# Changelog

All notable changes to the **NORAY** project will be documented in this file.

---

## [1.0.0] - 2026-07-27

### Added
- **Academic Streamlit Demo**: Lightweight course submission demo interface under `academic_demo/` calling direct FastAPI endpoints.
- **Dynamic Port & Host Resolving**: Parameterized WebSockets and streaming fetch engines to automatically bind dynamically based on browser location.
- **Dockerization Orchestration**: Multi-stage production `Dockerfile` configurations for both frontend and backend services.
- **Dynamic CORS Controls**: Integrated `ALLOWED_ORIGINS` support in backend settings.
- **Diagnostics API Endpoint**: Built `GET /api/system/ingestion-diagnostics` for monitoring RAG collections and indexing counts.
- **CI/CD Actions Workflows**: Added test checks and docker build validations in `.github/workflows/`.

### Changed
- **Qdrant Storage Locking Fallback**: Upgraded local `QdrantClient(path=...)` to process-wide thread-safe Singleton to prevent portalocker concurrency errors.
- **Postgres Schema Compatibility**: Resolved `postgres://` prefix compatibility automatically.
- **Optimized Standalone Frontend builds**: Configured Next.js output to `standalone`.
