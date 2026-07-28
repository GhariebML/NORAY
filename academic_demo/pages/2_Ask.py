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
from academic_demo.components.api import chat_workspace

st.set_page_config(page_title="Ask AI — NORAY OS", page_icon="💬", layout="wide")
inject_custom_styles()
render_header("AI Workspace", "Ask questions based on your custom ingested knowledge repository.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and "citations" in msg:
            if msg["citations"]:
                with st.expander("🔍 Citations & Retrieved Sources"):
                    for idx, cit in enumerate(msg["citations"]):
                        source = cit.get("source", "Unknown")
                        score = cit.get("score", 0.0)
                        st.markdown(f"**[{idx + 1}] {source}** — similarity: `{score:.4f}`")

            if "explainability" in msg:
                exp = msg["explainability"]
                with st.expander("⚙️ Explainability & Traceability"):
                    st.markdown(f"- **Confidence**: `{exp.get('confidence_score', 0.0):.2%}`")
                    steps = exp.get("reasoning_steps", [])
                    if steps:
                        st.markdown("**Reasoning Steps:**")
                        for s in steps:
                            st.markdown(f"1. {s}")

query = st.chat_input("Ask a question about your documents...")

if query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        start_time = time.time()
        with st.spinner("Retrieving knowledge nodes & thinking..."):
            try:
                res = chat_workspace(query)
            except Exception as e:
                res = {
                    "response": f"Error: {e}",
                    "citations": [],
                    "explainability": {},
                    "intent": "error",
                }
        duration = time.time() - start_time

        response_text = res.get("response", "No response generated.")
        citations = res.get("citations", [])
        explainability = res.get("explainability", {})

        streamed_text = ""
        for word in response_text.split(" "):
            streamed_text += word + " "
            message_placeholder.markdown(streamed_text + "▌")
            time.sleep(0.03)
        message_placeholder.markdown(response_text)

        st.caption(f"Latency: {duration:.2f}s · Provider: {res.get('intent', 'RAG')}")

        if citations:
            with st.expander("🔍 Citations & Retrieved Sources"):
                for idx, cit in enumerate(citations):
                    source = cit.get("source", "Unknown")
                    score = cit.get("score", 0.0)
                    st.markdown(f"**[{idx + 1}] {source}** — similarity: `{score:.4f}`")

        if explainability:
            with st.expander("⚙️ Explainability & Traceability"):
                st.markdown(f"- **Confidence**: `{explainability.get('confidence_score', 0.0):.2%}`")
                steps = explainability.get("reasoning_steps", [])
                if steps:
                    st.markdown("**Reasoning Steps:**")
                    for s in steps:
                        st.markdown(f"1. {s}")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_text,
            "citations": citations,
            "explainability": explainability,
        })
