# RAG Pipeline

This document explains NORAY OS's Retrieval-Augmented Generation pipeline end to end, from document upload through to a grounded, streamed response. Status markers (✅ / 🟡 / ⚪) apply to each stage individually.

---

## 1. Document Upload → ✅ Implemented

Users add knowledge through the global **Add Knowledge** action, available from any workspace view. Uploaded files are validated for type and size before entering the pipeline.

## 2. Parsing & Text Extraction → ✅ Implemented

Supported formats: PDF, DOCX, TXT, Markdown, CSV, XLSX, PPTX. Image-based documents route through an OCR path that is 🟡 under improvement. Extraction produces raw text plus structural metadata (source file, page/section, upload timestamp).

## 3. Cleaning & Normalization → ✅ Implemented

Extracted text is normalized (whitespace, encoding, boilerplate removal) before chunking to reduce noise in downstream embeddings.

## 4. Chunking → ✅ Implemented (core) / ⚪ Planned (advanced)

Current strategy: recursive, fixed-size chunking with configurable overlap. Each chunk carries metadata (source document, namespace, position) for traceable retrieval.

Planned enhancements: semantic chunking, adaptive chunk sizing, context-aware chunk merging, and parent-child retrieval (retrieving a small chunk but returning its broader parent context).

## 5. Embedding → ✅ Implemented

Default local embedding model: **nomic-embed-text**, served via Ollama. **BAAI/bge-m3** is also supported. The embedding provider is configurable, and the architecture supports adding further providers without structural changes.

## 6. Vector Storage (Qdrant) → ✅ Implemented

Embeddings are stored in **Qdrant**, self-hosted via Docker. Collections are created automatically on startup. Qdrant handles dense vector similarity search and namespace-aware knowledge storage.

## 7. Sparse Retrieval (BM25) → ✅ Implemented

A traditional lexical BM25 index runs alongside vector search, catching exact-term and keyword-level matches that pure semantic search can miss.

## 8. Hybrid Fusion (Reciprocal Rank Fusion) → ✅ Implemented

The **Universal Retriever** combines dense search, BM25, and metadata filtering, then merges the ranked lists using Reciprocal Rank Fusion (RRF) to produce a single, re-ordered candidate context set. This is the current fusion mechanism; a dedicated cross-encoder reranking step is ⚪ planned but not yet implemented — RRF is the sole fusion/re-ranking step today.

## 9. Context Building → ✅ Implemented

The Context Engine assembles the final prompt context from: retrieved chunks, conversation memory, and workspace memory (active documents / project state). Semantic, episodic, and procedural memory contribute at a 🟡 partial level today (see [`MEMORY_SYSTEM.md`](./MEMORY_SYSTEM.md)).

## 10. Prompt Building → ✅ Implemented

Assembled context, conversation history, and the user's query are composed into a structured prompt via NORAY's prompt library, then routed to the LLM Gateway.

## 11. Generation → ✅ Implemented

The **LLM Gateway / Model Router** selects a provider (local Ollama model or a cloud provider — Gemini, OpenRouter, Together AI, DeepSeek) based on cost, latency, and availability, with automatic failover. See [`AI_MODELS.md`](./AI_MODELS.md).

## 12. Grounding & Citations → 🟡 Partial

The Explainability layer records which sources contributed to a response (visible in the RAG Inspector panel) alongside confidence and grounding indicators. These indicators are currently heuristic; a full automated faithfulness/grounding validation pipeline (e.g., RAGAS-style metrics) is ⚪ planned.

## 13. Streaming Response → ✅ Implemented

Responses stream token-by-token to the AI Workspace Canvas, alongside a live reasoning/tool-use trace.

---

## Pipeline Summary Diagram

```
Upload → Extract → Clean → Chunk → Embed → Qdrant Store
                                              │
User Query → Intent → Context Builder → Universal Retriever
                                              │
                              (Dense + BM25 + Metadata)
                                              │
                                        RRF Fusion
                                              │
                                       LLM Gateway
                                              │
                                     Response Builder
                                              │
                                   Streaming + Citations
```

## What This Pipeline Is Not (Yet)

To avoid overstating capability: NORAY OS's current RAG pipeline does not yet include a dedicated reranker model, multi-hop graph reasoning, or automated hallucination scoring against a ground-truth benchmark. These are documented in [`DEVELOPMENT_ROADMAP.md`](./DEVELOPMENT_ROADMAP.md) as near-term priorities.
