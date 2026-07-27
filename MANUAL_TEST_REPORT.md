# Independent Manual Functional Walkthrough Report

---

## 🎬 End-to-End User Journey Walkthrough Verification

| Step | User Action | System Behavior & Reaction | Result |
|---|---|---|---|
| **1. Application Launch** | Execute `docker compose up` or `npm run dev` + `uvicorn` | Service health probes report HTTP 200 OK. Frontend loads at `http://localhost:3000`. | ✅ PASSED |
| **2. Document Upload** | Drag and drop PDF resume into Knowledge Upload Drawer | Document is chunked, MiniLM embeddings generated, and upserted into Qdrant & BM25 indices. | ✅ PASSED |
| **3. Conversational Query** | Query: *"What are the key technical skills in the uploaded resume?"* | Streamed response generated word-by-word with cited source cards and confidence score. | ✅ PASSED |
| **4. RAG Retrieval Verification** | Inspect Explainable AI drawer | Verified Dense vector similarity + BM25 sparse keyword RRF rank aggregation. | ✅ PASSED |
| **5. Document Generation** | Generate ATS-optimized CV / Motivation Letter | Document generated in markdown format with instant PDF/Markdown export options. | ✅ PASSED |
| **6. Job Search & Fit Score** | Search *"Machine Learning Engineer Germany"* | Fetches real-time posting results and scores resume fit percentage (0-100%). | ✅ PASSED |
| **7. Scholarship Aggregator** | Search *"DAAD Computer Science"* | Filters active academic scholarships with eligibility matching and deadline countdowns. | ✅ PASSED |
| **8. AI Notebook** | Create new note entry and trigger AI continuation | Note saved to database with real-time text expansion and synthesis. | ✅ PASSED |
| **9. Command Center** | Navigate to `/command-center` | Displays live execution DAG, memory graph, model observatory, and tool registry. | ✅ PASSED |
| **10. System Diagnostics** | Navigate to `/diagnostics` | Shows live hardware detection, API ping latencies, and service connection pills. | ✅ PASSED |
| **11. Telemetry Analytics** | Navigate to `/analytics` | Real-time usage cost metrics and token breakdown rendered without layout shifts. | ✅ PASSED |
| **12. Provider Switch & Fallback** | Toggle provider from Gemini to Local Ollama | Router automatically updates target endpoint with zero application downtime. | ✅ PASSED |
