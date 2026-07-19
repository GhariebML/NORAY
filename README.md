<p align="center">
  <img src="docs/banner.png" alt="NORAY Hero Banner" width="100%" style="border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);"><br><br>
  <h1 align="center">NORAY — Next-Gen Agentic RAG Operating System</h1>
</p>

<p align="center">
  <a href="https://github.com/GhariebML/NORAY/actions"><img src="https://img.shields.io/github/actions/workflow/status/GhariebML/NORAY/test.yml?branch=main&style=flat-square" alt="Build Status"></a>
  <a href="https://github.com/GhariebML/NORAY/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GhariebML/NORAY?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/next.js-14%2B-black?style=flat-square" alt="Next.js">
  <img src="https://img.shields.io/badge/ollama-qwen2.5--coder:7b-emerald?style=flat-square" alt="Ollama Local">
  <img src="https://img.shields.io/badge/qdrant-vector--db-red?style=flat-square" alt="Qdrant">
</p>

**NORAY** is an enterprise-grade, autonomous **Agentic RAG (Retrieval-Augmented Generation)** platform and career/scholarship operating system. Engineered with a unified hybrid RAG engine, multi-index vector/bm25 retrieval, knowledge graph fusion, ReAct cognitive reasoning loops, and an offline-first **Dual-Tier LLM Router** with local **Ollama** support.

---

## 📸 Interface Gallery

Here is a look at the dark-themed Next.js user interface of NORAY.

<table width="100%">
  <tr>
    <td width="50%" align="center">
      <b>Command Center / System Status</b><br>
      <img src="docs/images/media__1784218859065.png" alt="Command Center Dashboard" width="100%">
    </td>
    <td width="50%" align="center">
      <b>AI Workspace Canvas & Search Explainability</b><br>
      <img src="docs/images/media__1784219068523.png" alt="Workspace Chat Page" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <b>Interactive Knowledge Graph</b><br>
      <img src="docs/images/media__1784219068585.png" alt="Knowledge Graph" width="100%">
    </td>
    <td width="50%" align="center">
      <b>Profile Ingestion Interface</b><br>
      <img src="docs/images/media__1784222825317.png" alt="Profile Page" width="100%">
    </td>
  </tr>
</table>

---

## 🏗️ High-Level System Architecture

<p align="center">
  <img src="docs/architecture.png" alt="NORAY System Architecture Visualization" width="100%" style="border-radius: 8px; border: 1px solid #2d2d2d;">
</p>

NORAY relies on a multi-stage query routing pipeline that dynamically fuses dense retrieval (Qdrant), sparse retrieval (BM25), and a Graph RAG database store (SQLAlchemy/PostgreSQL/SQLite).

```mermaid
graph TD
    User([User Prompt / Web Client]) --> API[FastAPI Server]
    API --> Kernel[AIKernel: Central Execution Core]
    Kernel --> ContextEngine[Context Engine & Memory Ranker]
    
    subgraph Data & Hybrid RAG Retrieval Engine
        ContextEngine --> HybridSearch[AgentRouter: Hybrid Search]
        HybridSearch --> Dense[Qdrant Vector DB: BGE / MiniLM]
        HybridSearch --> Sparse[BM25 Index: SparseBM25Index]
        Dense & Sparse --> RRF[Reciprocal Rank Fusion]
        RRF --> Rerank[Cross-Encoder Reranker]
        Rerank --> Compressor[ContextCompressor: Stitch & Merge]
    end
    
    subgraph Knowledge Graph Fusion
        Compressor --> GraphRAG[GraphRAGFuser: Entity Triples]
        GraphRAG --> GraphStore[Postgres / SQLite Graph Store]
    end
    
    subgraph Cognitive Loop & Dual-Tier Router
        Kernel --> ReActEngine[ReAct Reasoning Loop]
        ReActEngine --> Router[Model Router: Active Health Monitor]
        Router --> Tier1[Tier 1: Cloud API - Gemini / DeepSeek / OpenRouter]
        Router --> Tier2[Tier 2: Local Offline Runtime - Ollama qwen2.5-coder:7b]
        Router --> Tier3[Tier 3: Mock Safety Fallback]
    end
    
    ReActEngine --> ResponseBuilder[ResponseBuilder & Evaluation Engine]
    ResponseBuilder --> UI[Next.js 14 Canvas Dashboard]
```

---

## 🧠 ReAct Cognitive Loop & Dual-Tier Model Router

NORAY implements a resilient **ReAct (Reasoning + Acting)** cognitive loop that allows the AI to autonomously inspect available tools, query local indices, extract facts, and evaluate confidence before yielding a final answer.

```mermaid
flowchart TD
    Start([User Chat Request]) --> RouteQuery[ModelRouter: Select Model Candidate]
    
    subgraph Health Monitor & Failover Protocol
        RouteQuery --> HealthCheck{Check Cloud Providers?}
        HealthCheck -- Available --> T1[Tier 1: Gemini / OpenRouter / DeepSeek]
        HealthCheck -- Unavailable / Failed --> T2[Tier 2: Ollama Local qwen2.5-coder:7b]
        T1 -- Error/401/404 --> T2
        T2 -- Error/Offline --> T3[Tier 3: Offline Mock Fallback]
    end
    
    T1 & T2 & T3 --> Loop[Start ReAct Reflection Loop]
    
    subgraph Autonomous Action Loop
        Loop --> LLMTurn[LLM Turn Generation]
        LLMTurn --> CheckAction{Contains Action?}
        CheckAction -- Action Required --> ExecTool[Execute Tool: Search / Profile / Docs]
        ExecTool --> Observation[Append Observation to Messages]
        Observation --> Loop
        CheckAction -- Final Answer --> BuildResponse[Build Response Envelope]
    end
    
    BuildResponse --> ReturnClient[Return ChatResponse JSON with Citations & Traces]
```

---

## ⚡ Document Ingestion Pipeline

To handle document uploads reliably across platforms, NORAY implements a robust sanitization and ingestion workflow with full file path compatibility and thread-safe Qdrant singleton connection management.

```mermaid
graph TD
    A[Browser: PDF/DOCX/TXT/MD Upload] --> B[FastAPI: POST /api/documents/upload]
    B --> C[sanitize_filename: UUID-based names]
    C --> D[pathlib.write_bytes: Safe OS Writes]
    D --> E[DocumentService: Parse & Text Extraction]
    E --> F[select_and_chunk: Content Strategy Detection]
    F --> G[EmbeddingsManager: 384-dim Dense Vectors]
    G --> H[Qdrant: user_documents vector collection]
    H --> I[SparseBM25Index: Fit & Save Serialization]
    I --> J[Temporary File Cleanup]
    J --> K[Return 200 OK Response]
```

---

## ✨ Core Features & Functional Modules

### 🎯 Profile Engine
- **Multi-source Import**: Direct parsers for LaTeX, PDF, DOCX, LinkedIn PDF exports, GitHub API repositories, and certificates.
- **Canonical Synchronization**: All RAG agents synchronize against the canonical `career_profile.json` structure.
- **Smart Merging**: Automatic deduplication, diff tracking, and backup/restore mechanisms on profile updates.

### 💼 Career Command Center
- **Job Portals Integration**: Real-time crawlers with automated relevance and fit scoring (0–100%).
- **ATS Analyzer**: In-depth review of resume matching percentage, keyword optimization proposals, and formatting checks.
- **Tailored Documents**: Full LaTeX generators for resume modifications (`moderncv`) and tailored cover letters (`cover.cls`).
- **Interview Coach**: Structured practice modules based on the STAR framework, customized elevator pitches, and background research cards.

### 🎓 PhD & Scholarship Module
- **13 Ports Aggregator**: Automated scraper for DAAD, Chevening, Fulbright, Erasmus Mundus, Gates Cambridge, Rhodes, etc.
- **Eligibility Scorer**: Multi-criteria weighted matrix analyzing nationality constraints, degree milestones, publication records, and GPA levels.
- **Scholarly Writing**: Tailored outline structures for Statement of Purpose (SOP), Research Proposals, and Recommendation draft emails.

### 📊 Interactive Knowledge Graph & Explainability
- **SVG / Canvas Render**: Fully interactive graphical layout with Node Drag, Zoom, and Pan controls.
- **Grounded Verification**: Highlights RAG traversal paths, confidence scores, and retrieved source chunks dynamically next to chat responses.

---

## 🛠️ Technology Stack

| Component | Technology | Version / Specification |
|---|---|---|
| **Frontend UI** | Next.js / React | 14.x / Tailwind CSS / Lucide Icons |
| **Backend API** | FastAPI / Uvicorn | Python 3.10+ / AsyncIO |
| **Local LLM Runtime** | Ollama | `qwen2.5-coder:7b` (300s timeout tolerance) |
| **Cloud LLMs** | Google Gemini / DeepSeek / OpenRouter | OpenAI-compatible HTTP client |
| **Dense Vector Database** | Qdrant | Local SQLite/RocksDB & Server Mode |
| **Sparse Lexical Search** | BM25 | `rank_bm25` (Pickle serialization) |
| **Embeddings** | SentenceTransformers | `all-MiniLM-L6-v2` / `BGE-M3` |
| **Relational / Graph Storage** | PostgreSQL / SQLite | SQLAlchemy + Alembic |
| **Caching Layer** | Redis / In-Memory Fallback | TTL-based scoring cache |

---

## 🚀 Setup & Quick Start

### 1. Prerequisites
- **Python**: version 3.10+
- **Node.js**: version 18+
- **Ollama**: [Download Ollama](https://ollama.com/) (for local offline LLM execution)
- **LaTeX** (Optional): XeLaTeX / LuaLaTeX compiler (`texlive-full` or MiKTeX) for PDF compilation

### 2. Install Local Ollama Model
```bash
ollama pull qwen2.5-coder:7b
```

### 3. Backend Setup & Startup
Clone the repository:
```bash
git clone https://github.com/GhariebML/NORAY.git
cd NORAY
```

Set up virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

Install python dependencies:
```bash
pip install -e ".[dev]"
```

Start the FastAPI backend server:
```bash
python -m uvicorn noray.api.app:app --host 127.0.0.1 --port 8001 --reload
```

### 4. Frontend Setup & Startup
In a separate terminal tab:
```bash
cd frontend
npm install
npm run dev
```

Open **[http://localhost:3000/workspace](http://localhost:3000/workspace)** in your browser!

---

## ⚙️ Core Slash Commands

| Command | Action |
|---|---|
| `/setup` | Initialize career profiles from raw files in the `documents/` folder |
| `/expand` | Run public profile enrichment over GitHub and online profiles |
| `/find_jobs` | Run multi-portal job crawler matching your profile criteria |
| `/apply_job` | Generate tailored resume PDF and cover letters for a specific job post |
| `/find_scholarships` | Query PhD/Master scholarship portals with profile verification |
| `/generate_sop` | Tailor a Statement of Purpose for selected universities |
| `/dashboard` | View metrics, pipeline conversions, and local server configurations |

---

## 🧪 Testing Suite

NORAY includes a comprehensive test suite verifying RAG routing, parser functions, and API logic.

Run the test suite:
```bash
python -m pytest tests/ -v
```

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for more details.
