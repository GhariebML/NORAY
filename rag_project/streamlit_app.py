"""
streamlit_app.py
=================
Final RAG assistant UI. Ties together steps 1-7 of the pipeline:
documents -> preprocessing -> chunking -> vector representation ->
vector store -> context retrieval -> prompting -> this UI.

Deployment note (API key)
--------------------------
No real API key is stored in this file or anywhere else in the repo.
On Streamlit Community Cloud:
  1. Deploy the app from your GitHub repo.
  2. Open App settings -> Secrets, and add:
         OPENAI_API_KEY = "sk-..."
  3. Streamlit injects this into `st.secrets`, and the block below
     copies it into the process environment so 07_prompting.py (which
     reads os.getenv("OPENAI_API_KEY")) picks it up automatically.

Locally, the same variable is read from a `.env` file instead
(see .env.example).
"""

from __future__ import annotations

import os

import streamlit as st

from _module_loader import load_module

# Forward Streamlit secrets into the environment (no-op if not on
# Streamlit Cloud / no secrets configured — falls back to .env locally).
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

_store = load_module("05_create_chroma_store")
_prompting = load_module("07_prompting")

st.set_page_config(page_title="RAG Assistant", page_icon="📚", layout="wide")

st.title("📚 RAG Assistant")
st.caption(
    "Ask a question and get an answer grounded in the documents in `documents/`."
)

with st.sidebar:
    st.header("⚙️ Settings")

    top_k = st.slider("Number of chunks to retrieve", min_value=1, max_value=10, value=4)
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)

    st.divider()
    st.subheader("🔑 API Key")
    if os.getenv("OPENAI_API_KEY"):
        st.success("API key detected from environment / secrets.")
    else:
        manual_key = st.text_input(
            "Enter OpenAI API key for this session",
            type="password",
            help="Only kept in memory for this browser session — never written to disk.",
        )
        if manual_key:
            os.environ["OPENAI_API_KEY"] = manual_key
            st.success("Key set for this session.")

    st.divider()
    st.subheader("🗂️ Vector Store")
    if st.button("Rebuild vector store from documents/"):
        with st.spinner("Rebuilding: documents → preprocessing → chunking → embeddings → Chroma..."):
            collection = _store.build_vector_store()
        st.success(f"Rebuilt. Collection now has {collection.count()} chunk(s).")

# Ensure the vector store exists at least once (auto-build on first load).
try:
    _client = _store.get_chroma_client()
    _collection = _client.get_collection(_store.COLLECTION_NAME)
    if _collection.count() == 0:
        raise ValueError("empty collection")
except Exception:
    with st.spinner("First run: building the vector store from documents/..."):
        _store.build_vector_store()

question = st.text_input("Ask a question about the documents:", placeholder="e.g. How many sick days do employees get?")
ask_clicked = st.button("Ask", type="primary")

if ask_clicked and question:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please set an API key in the sidebar first.")
    else:
        with st.spinner("Retrieving context and generating answer..."):
            try:
                result = _prompting.generate_answer(question, top_k=top_k, model=model)
            except Exception as exc:
                st.error(f"Something went wrong: {exc}")
                result = None

        if result:
            st.subheader("Answer")
            st.write(result["answer"])

            if result.get("sources"):
                st.subheader("Sources")
                st.write(", ".join(result["sources"]))

            if result.get("chunks"):
                with st.expander("🔍 Retrieved context (for debugging)"):
                    for c in result["chunks"]:
                        st.markdown(f"**{c.filename}** (distance={c.distance:.4f})")
                        st.text(c.text)
                        st.divider()
elif ask_clicked:
    st.warning("Please enter a question.")
