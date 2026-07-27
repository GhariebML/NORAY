"""
06_retrieve_context.py
========================
Step 6 of the RAG pipeline: given a user query, retrieve the most
relevant chunks from the persisted Chroma vector store.

Run standalone:
    python 06_retrieve_context.py "What is the remote work policy?"
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from _module_loader import load_module

_store = load_module("05_create_chroma_store")
_vectors = load_module("04_vector_representation")

DEFAULT_TOP_K = 4


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    filename: str
    distance: float


def retrieve_context(query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Embeds the query and returns the top_k most similar chunks from
    the persisted Chroma collection, ordered by relevance."""
    client = _store.get_chroma_client()
    collection = client.get_collection(
        name=_store.COLLECTION_NAME,
        embedding_function=_vectors.get_embedding_function(),
    )

    results = collection.query(query_texts=[query], n_results=top_k)

    retrieved: list[RetrievedChunk] = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for chunk_id, text, meta, distance in zip(ids, documents, metadatas, distances):
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=text,
                filename=meta.get("filename", "unknown"),
                distance=distance,
            )
        )
    return retrieved


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "What is the remote work policy?"
    results = retrieve_context(query)

    print(f"Query: {query}\n")
    print(f"Top {len(results)} result(s):\n")
    for r in results:
        preview = r.text[:120].replace("\n", " ")
        print(f"[{r.filename}] (distance={r.distance:.4f})\n  {preview}...\n")
