"""
02_preprocessing.py
====================
Step 2 of the RAG pipeline: clean raw document text before chunking.

Removes excess whitespace, control characters, and fixes line-wrapped
hyphenation, while preserving sentence/paragraph structure so chunking
(step 3) still has meaningful boundaries to split on.

Run standalone:
    python 02_preprocessing.py
"""

from __future__ import annotations

import re

from _module_loader import load_module

_documents = load_module("01_documents")

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Applies a small, deterministic cleaning pipeline to raw text."""
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _HYPHEN_BREAK_RE.sub(r"\1\2", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()


def preprocess_documents(documents: list) -> list:
    """Returns new RawDocument-like objects with cleaned `.text`.
    Accepts the list produced by 01_documents.load_documents()."""
    cleaned = []
    for doc in documents:
        doc.text = clean_text(doc.text)
        cleaned.append(doc)
    return cleaned


if __name__ == "__main__":
    docs = _documents.load_documents()
    docs = preprocess_documents(docs)
    print(f"Preprocessed {len(docs)} document(s)\n")
    for doc in docs:
        preview = doc.text[:80].replace("\n", " ")
        print(f"- {doc.filename} ({len(doc.text)} chars): {preview}...")
