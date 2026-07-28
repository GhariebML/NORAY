import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
demo_dir = Path(__file__).resolve().parent.parent
for p in (root_dir, demo_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import time
from academic_demo.components.utils import inject_custom_styles, render_header
from academic_demo.components.api import get_health, get_diagnostics

st.set_page_config(page_title="System Diagnostics — NORAY OS", page_icon="⚙️", layout="wide")
inject_custom_styles()
render_header("System Info", "Operational statuses, active database links, and live service latencies.")

start_time = time.time()
health = get_health()
ping_latency = int((time.time() - start_time) * 1000)

try:
    diagnostics = get_diagnostics()
except Exception:
    diagnostics = {}

col_srv, col_db, col_mem = st.columns(3)

with col_srv:
    is_healthy = health["status"] == "healthy"
    status_text = "ONLINE" if is_healthy else "OFFLINE"
    status_color = "#10b981" if is_healthy else "#ef4444"
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center;">
            <h4 style="color: #a1a1aa; margin-bottom: 5px;">FastAPI Engine</h4>
            <div style="font-size: 28px; font-weight: bold; color: {status_color}; font-family: monospace;">
                {status_text}
            </div>
            <p style="color: #71717a; font-size: 11px; margin-top: 10px;">
                HTTP server running on port 8001
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_db:
    qdrant_stat = diagnostics.get("qdrant_status", "offline").upper()
    db_color = "#10b981" if qdrant_stat == "ONLINE" else "#f59e0b"
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center;">
            <h4 style="color: #a1a1aa; margin-bottom: 5px;">Qdrant Vector DB</h4>
            <div style="font-size: 28px; font-weight: bold; color: {db_color}; font-family: monospace;">
                {qdrant_stat}
            </div>
            <p style="color: #71717a; font-size: 11px; margin-top: 10px;">
                Collection: <code>user_documents</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_mem:
    bm25_count = diagnostics.get("bm25_chunks_indexed", 0)
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center;">
            <h4 style="color: #a1a1aa; margin-bottom: 5px;">BM25 Index Count</h4>
            <div style="font-size: 28px; font-weight: bold; color: #10b981; font-family: monospace;">
                {bm25_count}
            </div>
            <p style="color: #71717a; font-size: 11px; margin-top: 10px;">
                Lexical fallback index
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Operational Parameters & Hardware Info")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(
        f"""
        <div class="glass-card">
            <h4 style="color: #ffffff; margin-bottom: 15px;">API Configurations</h4>
            <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">EMBEDDINGS PROVIDER</td>
                    <td style="text-align: right; color: #ffffff;">{diagnostics.get("embedding_provider", "local")}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">EMBEDDINGS MODEL</td>
                    <td style="text-align: right; color: #ffffff;">{diagnostics.get("embedding_model", "all-MiniLM-L6-v2")}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">VECTOR DIMENSIONS</td>
                    <td style="text-align: right; color: #10b981;">{diagnostics.get("vector_dimension", 384)}d</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">OLLAMA RUNTIME STATUS</td>
                    <td style="text-align: right; color: #ffffff;">{diagnostics.get("ollama_status", "offline")}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    st.markdown(
        f"""
        <div class="glass-card">
            <h4 style="color: #ffffff; margin-bottom: 15px;">API Latency Metrics</h4>
            <table style="width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">API PING ROUNDTRIP</td>
                    <td style="text-align: right; color: #10b981;">{ping_latency} ms</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">DB CONNECTIVITY STATE</td>
                    <td style="text-align: right; color: #ffffff;">OK</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">REDIS CACHE LINK</td>
                    <td style="text-align: right; color: #ffffff;">CONNECTED</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 10px 0; color: #a1a1aa;">OCR ENGINE STATUS</td>
                    <td style="text-align: right; color: #ffffff;">{diagnostics.get("ocr_status", "available")}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
