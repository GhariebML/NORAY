# Live Product Demonstration Script

---

## 🎬 Demo Workflow

### Step 1: Open the Academic Demo Interface
- Open `http://localhost:8501`. Point out the emerald dark glass styling and live backend health latency indicator.

### Step 2: Document Ingestion
- Navigate to `1_Upload`. Upload a sample PDF paper or resume. Point out that the file is chunked, embedded via MiniLM, and indexed in Qdrant and BM25.

### Step 3: Conversational AI & Citations
- Navigate to `2_Ask`. Query: *"What are the eligibility requirements for the scholarship?"*
- Highlight the streaming word output, citation links, and trust confidence scores.

### Step 4: RAG Pipeline Visualization & System Diagnostics
- Navigate to `3_RAG_Pipeline` and `4_System_Info` to showcase the interactive trace and hardware metrics.
