# NORAY OS — Academic RAG Demonstration App

A lightweight, high-fidelity **Streamlit** dashboard representing the underlying **Retrieval-Augmented Generation (RAG)** pipeline of the NORAY AI Operating System.

Designed to fulfill course submission requirements while utilizing the exact same API service endpoints without duplications.

---

## 🚀 Features

1. **Ingestion Zone (`1_Upload.py`)**: Drag-and-drop document upload (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, Images) directly into namespaces mapped onto the FastAPI backend service.
2. **Conversational Workspace (`2_Ask.py`)**: ChatGPT-like chat interface communicating directly with `/api/workspace/chat` to retrieve nodes, fuse results (RRF), cross-encoder rerank, compress context, and formulate streaming answers.
3. **Execution Tracer (`3_RAG_Pipeline.py`)**: Clean interactive layout of the step-by-step ingestion, parsing, chunking, embedding, vector database indexing, and LLM prompt compiling process.
4. **System Diagnostics (`4_System_Info.py`)**: Full monitoring panel reading health checks, embedding vector sizes, database connections, and roundtrip ping times.

---

## 🛠️ Local Installation & Running

1. **Prerequisites**:
   Ensure you have the main python environment installed and the FastAPI server is running:
   ```bash
   python -m uvicorn noray.api.app:app --host 127.0.0.1 --port 8001
   ```

2. **Install Streamlit Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application**:
   ```bash
   streamlit run streamlit_app.py
   ```
   Open the browser to [http://localhost:8501](http://localhost:8501).
