# Live Demo & Evaluation Presentation Script

---

## 🎬 Part 1: Launch & Connection (1 minute)
- Open `http://localhost:8501`. Show the active connection status pill and API ping latency metric.

## 🎬 Part 2: Knowledge Ingestion (1.5 minutes)
- Open `1_Upload`. Drag and drop an academic paper or resume. Highlight the text parsing, MiniLM vector embedding generation, and Qdrant upsert notification.

## 🎬 Part 3: RAG Retrieval & Reasoning (2 minutes)
- Open `2_Ask`. Enter query: *"What are the key eligibility criteria for the DAAD scholarship?"*
- Highlight word-by-word streaming output, citations, similarity scores, and trust metrics.

## 🎬 Part 4: Technical Diagnostics (1 minute)
- Open `3_RAG_Pipeline` and `4_System_Info`. Explain Reciprocal Rank Fusion (RRF), Cross-Encoder reranking, and live server health metrics.
