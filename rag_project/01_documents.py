"""
01_documents.py
================
Step 1 of the RAG pipeline: load raw documents.

Reads every .txt and .pdf file from the `documents/` folder and returns
a list of raw document records. If the folder is empty, a small set of
sample .txt documents is generated automatically so the whole pipeline
can be run end-to-end without any setup.

Run standalone:
    python 01_documents.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"


@dataclass
class RawDocument:
    doc_id: str
    filename: str
    text: str
    metadata: dict = field(default_factory=dict)


_SAMPLE_DOCS = {
    "company_policy.txt": (
        "Remote Work Policy\n\n"
        "Employees may work remotely up to three days per week, subject to "
        "manager approval. Remote workdays must be logged in the HR system "
        "by the end of each week. Employees are expected to be reachable "
        "during core hours, from 10 AM to 4 PM local time, regardless of "
        "their work location.\n\n"
        "Equipment Policy\n\n"
        "The company provides a laptop and a monitor for all remote "
        "employees. Additional equipment requests must be submitted through "
        "the IT portal and approved by a team lead. Employees are "
        "responsible for keeping company equipment secure and up to date."
    ),
    "onboarding_guide.txt": (
        "New Employee Onboarding\n\n"
        "New hires complete a two-week onboarding program covering company "
        "tools, security training, and team introductions. On day one, "
        "employees receive their laptop, email account, and access to the "
        "internal knowledge base.\n\n"
        "Probation Period\n\n"
        "All new employees are on a 90-day probation period. Performance "
        "reviews happen at the 30-day and 90-day marks. Managers are "
        "expected to provide written feedback at each checkpoint."
    ),
    "leave_policy.txt": (
        "Annual Leave\n\n"
        "Full-time employees accrue 22 days of paid annual leave per year, "
        "prorated for part-time staff. Leave requests must be submitted at "
        "least two weeks in advance through the HR portal, except in cases "
        "of emergency.\n\n"
        "Sick Leave\n\n"
        "Employees receive 10 paid sick days per year. A doctor's note is "
        "required for absences longer than three consecutive days."
    ),
}


def _ensure_sample_documents() -> None:
    """Creates a few sample .txt files if the documents/ folder is empty,
    so the pipeline is runnable immediately without external data."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(DOCUMENTS_DIR.glob("*"))
    if existing:
        return
    for filename, content in _SAMPLE_DOCS.items():
        (DOCUMENTS_DIR / filename).write_text(content, encoding="utf-8")


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to read PDF files: pip install pypdf") from exc
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def load_documents() -> list[RawDocument]:
    """Loads every .txt and .pdf file under documents/ into RawDocument
    records. Creates sample documents automatically on first run."""
    _ensure_sample_documents()

    docs: list[RawDocument] = []
    for path in sorted(DOCUMENTS_DIR.iterdir()):
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif path.suffix.lower() == ".pdf":
            text = _read_pdf(path)
        else:
            continue

        if not text.strip():
            continue

        docs.append(
            RawDocument(
                doc_id=path.stem,
                filename=path.name,
                text=text,
                metadata={"source": str(path)},
            )
        )
    return docs


if __name__ == "__main__":
    documents = load_documents()
    print(f"Loaded {len(documents)} document(s) from {DOCUMENTS_DIR}\n")
    for doc in documents:
        preview = doc.text[:80].replace("\n", " ")
        print(f"- {doc.filename} ({len(doc.text)} chars): {preview}...")
