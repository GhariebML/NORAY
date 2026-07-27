"""
03_chunking.py
==============
Step 3 of the RAG pipeline: split cleaned documents into overlapping
chunks suitable for embedding and retrieval.

Uses a simple word-based sliding window (chunk_size words, chunk_overlap
words repeated between consecutive chunks) — no extra NLP dependency
required, easy to reason about, and good enough for a lab-scale project.

Run standalone:
    python 03_chunking.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

from _module_loader import load_module

_documents = load_module("01_documents")
_preprocessing = load_module("02_preprocessing")

DEFAULT_CHUNK_SIZE = 150      # words per chunk
DEFAULT_CHUNK_OVERLAP = 30    # words repeated between consecutive chunks


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    filename: str
    text: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size - chunk_overlap)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_documents(
    documents: list,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Turns a list of RawDocument objects into a flat list of Chunk
    objects, each tagged with its source document and position."""
    all_chunks: list[Chunk] = []
    for doc in documents:
        pieces = chunk_text(doc.text, chunk_size, chunk_overlap)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}_chunk_{i}",
                    doc_id=doc.doc_id,
                    filename=doc.filename,
                    text=piece,
                    chunk_index=i,
                    metadata={**doc.metadata, "chunk_index": i},
                )
            )
    return all_chunks


if __name__ == "__main__":
    docs = _documents.load_documents()
    docs = _preprocessing.preprocess_documents(docs)
    chunks = chunk_documents(docs)

    print(f"Created {len(chunks)} chunk(s) from {len(docs)} document(s)\n")
    for c in chunks[:5]:
        preview = c.text[:80].replace("\n", " ")
        print(f"- {c.chunk_id}: {preview}...")
    if len(chunks) > 5:
        print(f"... and {len(chunks) - 5} more")
