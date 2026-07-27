# Changelog

All notable changes to NORAY OS are documented in this file.

## [v1.0.0] — July 2026

### Added
- Initial production prototype release.
- AI Workspace Canvas with streaming chat, reasoning timeline, and RAG inspector panel.
- Hybrid RAG pipeline: dense vector search (Qdrant), BM25 sparse retrieval, and Reciprocal Rank Fusion.
- Document ingestion pipeline supporting PDF, DOCX, TXT, Markdown, CSV, XLSX, PPTX.
- Global Knowledge Upload Center ("+ Add Knowledge") with namespace-aware indexing.
- Unified LLM Gateway with local (Ollama: Llama 3.1 8B, Qwen 2.5 7B) and cloud (Gemini, OpenRouter, Together AI, DeepSeek) providers, including cost/latency-aware routing and automatic failover.
- AI Document Generator (CV, Statement of Purpose, Motivation Letter, Research Proposal).
- Command Center: Execution DAG visualization, Agent Monitor, Retriever Inspector, Model Observatory, Telemetry Dashboard, Governance panel.
- System Diagnostics for provider/database/vector-store health monitoring.
- Job Search Engine and Scholarship Search Engine (partial provider integration).
- Applications Tracker, Profile & Upskill modules (partial).
- Memory architecture spanning Conversation, Workspace, Semantic, Episodic, and Procedural memory (partial beyond Conversation/Workspace).
- Custom AI Kernel orchestration framework (not LangChain/LangGraph-based).

### In Progress (see [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md))
- Graph RAG / Knowledge Graph traversal.
- Notebook Workspace advanced workflows.
- Human-in-the-Loop Inbox UI completion.
- Formal automated testing and performance benchmarking.
- Multi-user authentication.

### Known Limitations
- No authentication layer; single-user local deployment only.
- Latency/resource figures shown in the UI are illustrative development telemetry, not certified benchmarks.
- Hallucination Risk indicator is heuristic, not yet backed by an automated grounding-evaluation pipeline.
