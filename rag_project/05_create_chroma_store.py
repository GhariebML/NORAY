"""
05_create_chroma_store.py
==========================
Step 5 of the RAG pipeline: build a persistent Chroma vector store
from the chunked, embedded documents.

Running this script re-creates the collection from scratch each time,
so it's safe to re-run after editing files in documents/. The store is
persisted to ./chroma_db so later steps (retrieval, Streamlit app) can
open it without recomputing embeddings.

Run standalone:
    python 05_create_chroma_store.py
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from _module_loader import load_module

_documents = load_module("01_documents")
_preprocessing = load_module("02_preprocessing")
_chunking = load_module("03_chunking")
_vectors = load_module("04_vector_representation")

CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "rag_documents"


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def build_vector_store() -> chromadb.Collection:
    """Runs steps 1-4 and writes every chunk into a persistent Chroma
    collection, replacing any previous collection of the same name."""
    docs = _documents.load_documents()
    docs = _preprocessing.preprocess_documents(docs)
    chunks = _chunking.chunk_documents(docs)

    if not chunks:
        raise RuntimeError("No chunks produced — check documents/ folder is not empty")

    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # collection didn't exist yet — fine

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_vectors.get_embedding_function(),
    )

    collection.add(
        ids=[c.chunk_id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {"doc_id": c.doc_id, "filename": c.filename, "chunk_index": c.chunk_index}
            for c in chunks
        ],
    )

    return collection


if __name__ == "__main__":
    collection = build_vector_store()
    print(f"Vector store created at {CHROMA_DIR}")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} chunk(s)")
