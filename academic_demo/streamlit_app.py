import sys
from pathlib import Path

# Ensure repository root & demo directory are in sys.path for Streamlit Cloud
root_dir = Path(__file__).resolve().parent.parent
demo_dir = Path(__file__).resolve().parent
for p in (root_dir, demo_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
from academic_demo.components.utils import inject_custom_styles, render_header
from academic_demo.components.api import get_health

# Page configurations
st.set_page_config(
    page_title="NORAY OS — Academic Demo",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styling
inject_custom_styles()

# Header
render_header("Academic Demo", "Lightweight RAG Demonstration Interface for Course Submission")

# Dashboard Content
col_info, col_status = st.columns([2, 1])

with col_info:
    st.markdown(
        """
        <div class="glass-card">
            <h3 style="color: #ffffff; margin-bottom: 10px;">🧬 Project Overview</h3>
            <p style="color: #d1d5db; line-height: 1.6;">
                <strong>NORAY</strong> is an Enterprise AI Operating System designed to tailor career resumes, statement of purposes, and search for compatible jobs and scholarships based on ingested user knowledge.
            </p>
            <p style="color: #d1d5db; line-height: 1.6;">
                This lightweight academic demo illustrates the core <strong>Retrieval-Augmented Generation (RAG)</strong> architecture. It directly calls the identical, production-hardened APIs utilized by the core Next.js operating system workspace, validating true backend code reuse without logic duplication.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <div class="glass-card">
            <h4 style="color: #ffffff; margin-bottom: 15px;">🏗️ Shared RAG Architecture Workflow</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.image(
        "https://raw.githubusercontent.com/qdrant/qdrant/master/docs/logo.svg",
        width=100,
        caption="Qdrant Vector Database"
    )
    
    st.markdown(
        """
        ```mermaid
        graph TD
            Doc[User Document] -->|Upload API| Parser[pdfplumber / docx / OCR]
            Parser -->|Chunker| Semantic[Semantic Character Chunks]
            Semantic -->|Embeddings| LocalEmbed[SentenceTransformers: all-MiniLM-L6-v2]
            LocalEmbed -->|Upsert| VectorStore[(Qdrant Vector Store)]
            LocalEmbed -->|Fit| SparseStore[(BM25 Sparse Index)]
            
            Query[Ask Question] -->|Chat API| RAG[Retrieval Pipeline]
            RAG -->|Dense Search| VectorStore
            RAG -->|Sparse Search| SparseStore
            VectorStore -->|RRF Fusion| Rerank[Cross-Encoder Reranker]
            SparseStore -->|RRF Fusion| Rerank
            Rerank -->|Context Compressor| LLM[LLM Generator]
            LLM -->|Response| UserResponse[Streaming Answer]
        ```
        """,
        unsafe_allow_html=True
    )

with col_status:
    st.markdown(
        """
        <div class="glass-card">
            <h3 style="color: #ffffff; margin-bottom: 15px;">💻 Connection Status</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    health = get_health()
    if health["status"] == "healthy":
        st.success(f"🟢 Connected to FastAPI Backend")
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-value">{health['latency_ms']} ms</div>
                <div class="metric-label">API Ping Latency</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("🔴 Backend Server Offline")
        st.info("Ensure the FastAPI server is running with: python -m uvicorn noray.api.app:app --port 8001")
        
    st.markdown(
        """
        <div class="glass-card" style="margin-top: 15px;">
            <h4 style="color: #ffffff; margin-bottom: 10px;">🚀 Quick Actions</h4>
            <p style="color: #a1a1aa; font-size: 13px;">Use the left sidebar navigation pages to access demo modules:</p>
            <ul style="color: #d1d5db; padding-left: 20px; line-height: 1.8;">
                <li><strong>1_Upload</strong>: Index resume and paper documents.</li>
                <li><strong>2_Ask</strong>: Query AI with streaming RAG context.</li>
                <li><strong>3_RAG_Pipeline</strong>: Inspect vector retrieval metadata.</li>
                <li><strong>4_System_Info</strong>: View hardware & diagnostics parameters.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; color: #71717a; font-size: 12px; font-family: monospace;">
        NORAY AI OS v1.0.0 • Academic RAG Submission Demo
    </div>
    """,
    unsafe_allow_html=True
)
