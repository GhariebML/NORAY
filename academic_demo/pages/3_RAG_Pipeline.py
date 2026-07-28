import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
demo_dir = Path(__file__).resolve().parent.parent
for p in (root_dir, demo_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
from academic_demo.components.utils import inject_custom_styles, render_header
from academic_demo.components.api import get_diagnostics

st.set_page_config(page_title="RAG Pipeline Flow — NORAY OS", page_icon="🔗", layout="wide")
inject_custom_styles()
render_header("RAG Pipeline", "Interactive visual demonstration of the underlying multi-tier RAG architecture.")

try:
    diagnostics = get_diagnostics()
except Exception:
    diagnostics = {}

embed_model = diagnostics.get("embedding_model", "all-MiniLM-L6-v2")
vector_dim = diagnostics.get("vector_dimension", 384)
provider = diagnostics.get("embedding_provider", "local")

st.markdown(
    """
    <div class="glass-card">
        <h3 style="color: #ffffff; margin-bottom: 15px;">Multi-Tier RAG Execution Trace</h3>
        <p style="color: #d1d5db; line-height: 1.6;">
            NORAY implements a resilient retrieval architecture. If the dense vector storage
            (Qdrant) is degraded, the system automatically falls back to sparse lexical
            indexing (BM25) and conversational memory logs, guaranteeing answer generation
            without runtime exceptions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Step-by-Step Architecture Pipeline")

steps = [
    {
        "title": "1. Ingestion & Parsing",
        "desc": "Documents (PDF, DOCX, PPTX, Images) are uploaded. Raw content text is extracted using <code>pdfplumber</code> and fallback <code>Tesseract OCR</code> engines.",
        "icon": "📤",
    },
    {
        "title": "2. Preprocessing & Cleaning",
        "desc": "Non-ASCII formatting characters are sanitized, and paragraph breaks are normalized for unified structural tokenization.",
        "icon": "🧼",
    },
    {
        "title": "3. Semantic Chunking",
        "desc": "Normalized text is segmented using recursive overlap chunking, matching sentence boundaries to preserve conversational context.",
        "icon": "✂️",
    },
    {
        "title": "4. Vector Embedding",
        "desc": f"Each text chunk is converted to a dense float vector using <b>{provider}</b> with model <b>{embed_model}</b> (dimension: <code>{vector_dim}</code>).",
        "icon": "🧬",
    },
    {
        "title": "5. Dual-Indexing",
        "desc": "Generated vectors are loaded into <b>Qdrant Vector DB</b> for semantic searches, and raw text corpus maps are compiled into <b>BM25</b> indices for sparse matches.",
        "icon": "💾",
    },
    {
        "title": "6. Context Retrieval & Fusion",
        "desc": "Incoming queries trigger parallel dense vector searches and sparse keyword searches. Results are fused using Reciprocal Rank Fusion (RRF).",
        "icon": "🔍",
    },
    {
        "title": "7. Reranking & Compression",
        "desc": "Retrieved chunks are scored by a Cross-Encoder reranker. The compressor filters out low-scoring sequences to optimize the LLM context size.",
        "icon": "🚀",
    },
    {
        "title": "8. LLM Context Ingestion",
        "desc": "The compressed document context is formatted with candidate background schemas and fed into the AI Gateway context window.",
        "icon": "🤖",
    },
    {
        "title": "9. Streaming Response",
        "desc": "The target LLM models analyze the context, formulate answers, and stream characters to the user interface.",
        "icon": "💬",
    },
]

for i in range(0, len(steps), 3):
    cols = st.columns(3)
    for j in range(3):
        idx = i + j
        if idx < len(steps):
            step = steps[idx]
            with cols[j]:
                st.markdown(
                    f"""
                    <div class="glass-card" style="height: 250px;">
                        <h4 style="color: #10b981; margin-bottom: 8px;">{step['icon']} {step['title']}</h4>
                        <p style="color: #e4e4e7; font-size: 13px; line-height: 1.6;">
                            {step['desc']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
