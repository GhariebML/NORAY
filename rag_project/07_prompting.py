"""
07_prompting.py
================
Step 7 of the RAG pipeline: build a grounded prompt from retrieved
context and call the LLM to generate the final answer.

API KEY RULE
------------
This file NEVER contains a real API key. The key is read at runtime
from an environment variable (OPENAI_API_KEY), which you provide via:
  - a local `.env` file (see .env.example — .env is git-ignored), or
  - Streamlit Cloud's "Secrets" settings when deployed (st.secrets),
    which streamlit_app.py forwards into the environment automatically.

Run standalone (requires OPENAI_API_KEY to be set):
    python 07_prompting.py "What is the remote work policy?"
"""

from __future__ import annotations

import os
import sys

from _module_loader import load_module

_retrieval = load_module("06_retrieve_context")

# Loads OPENAI_API_KEY from a local .env file if present. Harmless no-op
# in deployed environments where the variable is already set (Streamlit
# secrets, Docker env, etc.).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = "gpt-4o-mini"

PROMPT_TEMPLATE = """You are a helpful assistant answering questions using ONLY the context below.
If the answer is not contained in the context, say you don't have enough information — do not make anything up.

Context:
{context}

Question: {question}

Answer:"""


def build_prompt(question: str, chunks: list) -> str:
    context = "\n\n---\n\n".join(
        f"(Source: {c.filename})\n{c.text}" for c in chunks
    )
    return PROMPT_TEMPLATE.format(context=context, question=question)


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a .env file locally "
            "(see .env.example) or set it in Streamlit Cloud secrets."
        )
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def generate_answer(question: str, top_k: int = 4, model: str = DEFAULT_MODEL) -> dict:
    """Runs the full retrieve -> prompt -> generate flow for one question.
    Returns a dict with the answer text and the sources used, so the
    Streamlit UI can display citations alongside the answer."""
    chunks = _retrieval.retrieve_context(question, top_k=top_k)
    if not chunks:
        return {"answer": "No relevant context was found in the vector store.", "sources": []}

    prompt = build_prompt(question, chunks)
    client = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You answer strictly from the provided context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content
    sources = sorted({c.filename for c in chunks})
    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the remote work policy?"
    result = generate_answer(question)

    print(f"Question: {question}\n")
    print(f"Answer:\n{result['answer']}\n")
    print(f"Sources: {', '.join(result['sources'])}")
