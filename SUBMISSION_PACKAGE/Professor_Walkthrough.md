# Professor & Academic Reviewer Walkthrough

Dear Professor / Evaluator,

Thank you for reviewing the **NORAY AI Operating System**. This guide provides a structured evaluation path designed to demonstrate the system's core capabilities within **5–10 minutes**.

---

## ⚡ Quick Start (2 Minutes)

### Option A: Full Enterprise Stack (Docker)
```bash
git clone https://github.com/GhariebML/NORAY.git
cd NORAY
cp .env.example .env
docker compose up -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001/docs`

### Option B: Academic Streamlit Demo
```bash
cd academic_demo
pip install -r requirements.txt
streamlit run streamlit_app.py
```
- Streamlit: `http://localhost:8501`

---

## 🔬 Evaluation Walkthrough

### Step 1: Upload a Document (1 min)
- Navigate to the **Upload** page (Streamlit) or **Knowledge Center** (Next.js).
- Upload any PDF, DOCX, or TXT file.
- Observe: text extraction → chunking → embedding → vector indexing confirmation.

### Step 2: Query the RAG Pipeline (2 min)
- Navigate to the **Ask** page (Streamlit) or **Workspace** (Next.js).
- Enter a question related to the uploaded document.
- Observe: streaming response → citation cards → confidence scores → reasoning steps.

### Step 3: Inspect the RAG Architecture (1 min)
- Navigate to **RAG Pipeline** page.
- Review the mathematical formulation of Reciprocal Rank Fusion (RRF).
- Note the dual-retrieval architecture: Dense (Qdrant) + Sparse (BM25).

### Step 4: System Diagnostics (1 min)
- Navigate to **System Info** page.
- Review live backend health, hardware metrics, and provider status.

### Step 5: Run Automated Tests (2 min)
```bash
python -m pytest tests/ -v
```
Expected: **511 passed, 1 skipped** — 100% success rate.

---

## 📊 Key Technical Highlights for Evaluation

| Criterion | Implementation |
|---|---|
| **RAG Pipeline** | Hybrid Dense+Sparse retrieval with RRF fusion and Cross-Encoder reranking |
| **LLM Integration** | Multi-provider gateway with automatic failover (Gemini → OpenRouter → Together → DeepSeek → Local) |
| **Test Coverage** | 511 automated tests covering API, RAG, gateway, agents, and integration |
| **Deployment** | Docker Compose orchestration with PostgreSQL, Redis, Qdrant |
| **Frontend** | Next.js 15 with glassmorphism dark theme and Framer Motion animations |
| **Academic Demo** | Streamlit application with offline Demo Mode fallback |
| **Documentation** | Complete architecture guides, API reference, and submission package |

---

## 📂 Repository Structure

```
NORAY/
├── noray/                    # Backend (FastAPI + RAG + Gateway)
│   ├── api/                  # REST API routes
│   ├── rag/                  # RAG pipeline (chunker, embedder, retriever, reranker)
│   ├── gateway/              # LLM provider routing & fallback
│   └── agents/               # Career, scholarship, and upskill agents
├── frontend/                 # Next.js 15 enterprise frontend
├── academic_demo/            # Streamlit academic demo
├── tests/                    # 512 automated tests
├── SUBMISSION_PACKAGE/       # Academic submission documents
└── docker-compose.yml        # Full stack orchestration
```

---

Thank you for your time. We welcome any questions or feedback!
