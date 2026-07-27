"""
04_vector_representation.py
============================
Step 4 of the RAG pipeline: turn text chunks into vector embeddings.

Uses OpenAI's embedding API (text-embedding-3-small) — the same
OPENAI_API_KEY already required for answer generation (07_prompting.py)
covers this step too, so the whole project needs exactly one API key.

API KEY RULE: no key is hardcoded here. It is read at runtime from the
OPENAI_API_KEY environment variable (see 07_prompting.py's docstring
for how that variable gets set locally vs. on Streamlit Cloud).

Run standalone (requires OPENAI_API_KEY to be set):
    python 04_vector_representation.py
"""

from __future__ import annotations

import os

from _module_loader import load_module

_documents = load_module("01_documents")
_preprocessing = load_module("02_preprocessing")
_chunking = load_module("03_chunking")

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embedding_function():
    """Returns a Chroma-compatible embedding function backed by OpenAI.
    Every other pipeline file calls ONLY this function — never the
    OpenAI SDK directly — so the embedding backend can be swapped
    (e.g. to a local model) by editing just this one file."""
    from chromadb.utils import embedding_functions

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Create a .env file locally "
            "(see .env.example) or set it in Streamlit Cloud secrets."
        )
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Directly embeds a list of strings — useful for quick checks
    outside of the Chroma collection (e.g. debugging chunk quality)."""
    embed_fn = get_embedding_function()
    return embed_fn(texts)


if __name__ == "__main__":
    docs = _documents.load_documents()
    docs = _preprocessing.preprocess_documents(docs)
    chunks = _chunking.chunk_documents(docs)

    sample_texts = [c.text for c in chunks[:3]]
    vectors = embed_texts(sample_texts)

    print(f"Embedded {len(sample_texts)} sample chunk(s)")
    for text, vector in zip(sample_texts, vectors):
        preview = text[:60].replace("\n", " ")
        print(f"- '{preview}...' -> vector of dimension {len(vector)}")
