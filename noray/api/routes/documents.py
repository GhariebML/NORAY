"""
Document ingestion API routes.

Handles file upload, text extraction, chunking, embedding, and dual-index storage.
All filenames are UUID-sanitized for Windows compatibility.
"""

import uuid
import logging
import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from noray.services.document_service import DocumentService
from noray.rag.sparse_index import SparseBM25Index

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ──────────────────────────────────────────────────────────────────

UPLOAD_DIR = Path("d:/NORAY/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown", ".csv", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_UPLOAD_SIZE_MB = 50


# ── Response / Error Models ───────────────────────────────────────────────────

class UploadResponse(BaseModel):
    filename: str
    sanitized_filename: str
    chunks_count: int
    strategy: str
    category: str

class UploadErrorResponse(BaseModel):
    error: str
    detail: str
    original_filename: Optional[str] = None
    stage: Optional[str] = None

class DocItem(BaseModel):
    id: str
    source: str
    category: str
    content: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def sanitize_filename(original_filename: str) -> tuple[str, str]:
    """
    Generate a UUID-based filename preserving only the file extension.
    Returns (sanitized_name, extension).

    This avoids ALL Windows path issues:
    - Invalid characters: < > : " / \\ | ? *
    - Reserved names: CON, PRN, NUL, COM1, LPT1, etc.
    - Unicode smart quotes, non-ASCII oddities
    - Excessively long filenames
    """
    # Extract extension safely using pathlib
    ext = Path(original_filename).suffix.lower() if original_filename else ""

    # Validate extension
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    sanitized = f"{uuid.uuid4().hex}{ext}"
    return sanitized, ext


def validate_upload_file(file: UploadFile) -> None:
    """Pre-validate an uploaded file before writing to disk."""
    if not file.filename:
        raise ValueError("No filename provided in upload.")

    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general"),
    language: Optional[str] = Form("en"),
):
    """
    Upload a document (PDF, DOCX, TXT, MD, images) and process it into
    vector and sparse indices.

    Pipeline stages:
    1. Validate upload metadata
    2. Generate UUID-sanitized filename
    3. Write to upload directory
    4. Parse document text
    5. Chunk text
    6. Generate embeddings
    7. Upsert into vector store
    8. Upsert into BM25 sparse index
    """
    original_filename = file.filename or "unknown"
    sanitized_name = ""
    file_path: Optional[Path] = None
    stage = "validation"

    try:
        # ── Stage 1: Validate ─────────────────────────────────────────────
        validate_upload_file(file)

        # ── Stage 2: Sanitize filename ────────────────────────────────────
        stage = "filename_sanitization"
        sanitized_name, ext = sanitize_filename(original_filename)
        file_path = UPLOAD_DIR / sanitized_name

        logger.info(
            "Document upload started | "
            "original=%s | sanitized=%s | dir=%s | abs_path=%s | category=%s | mime=%s",
            original_filename,
            sanitized_name,
            str(UPLOAD_DIR),
            str(file_path),
            category,
            file.content_type,
        )

        # ── Stage 3: Write file to disk ───────────────────────────────────
        stage = "file_save"
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise ValueError("Uploaded file is empty (0 bytes).")

        if file_size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise ValueError(
                f"File size ({file_size / (1024*1024):.1f} MB) exceeds "
                f"maximum allowed ({MAX_UPLOAD_SIZE_MB} MB)."
            )

        file_path.write_bytes(content)

        logger.info(
            "File saved | path=%s | size=%d bytes | mime=%s",
            str(file_path),
            file_size,
            file.content_type,
        )

        # ── Stage 4-8: Ingest (parse → chunk → embed → index) ────────────
        stage = "document_parsing"
        doc_service = DocumentService()

        stage = "ingestion_pipeline"
        result = doc_service.ingest_document(
            file_path=file_path,
            category=category,
            metadata_overrides={
                "language": language,
                "original_filename": original_filename,
            },
        )

        logger.info(
            "Ingestion complete | original=%s | chunks=%d | strategy=%s",
            original_filename,
            result["chunks_count"],
            result["strategy"],
        )

        return UploadResponse(
            filename=original_filename,
            sanitized_filename=sanitized_name,
            chunks_count=result["chunks_count"],
            strategy=result["strategy"],
            category=result["category"],
        )

    except ValueError as e:
        # Client-side errors (bad file type, empty file, etc.)
        logger.warning(
            "Upload validation error | file=%s | stage=%s | error=%s",
            original_filename, stage, str(e),
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "detail": str(e),
                "original_filename": original_filename,
                "stage": stage,
            },
        )

    except OSError as e:
        # Filesystem errors (permission denied, invalid path, disk full)
        tb = traceback.format_exc()
        logger.error(
            "Filesystem error during upload | file=%s | sanitized=%s | "
            "path=%s | stage=%s | error=%s\n%s",
            original_filename, sanitized_name, str(file_path), stage, str(e), tb,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "filesystem_error",
                "detail": str(e),
                "original_filename": original_filename,
                "sanitized_filename": sanitized_name,
                "path": str(file_path),
                "stage": stage,
                "traceback": tb,
            },
        )

    except Exception as e:
        # Catch-all for unexpected errors in the pipeline
        tb = traceback.format_exc()
        logger.error(
            "Unexpected ingestion error | file=%s | stage=%s | error=%s\n%s",
            original_filename, stage, str(e), tb,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ingestion_error",
                "detail": str(e),
                "original_filename": original_filename,
                "sanitized_filename": sanitized_name,
                "stage": stage,
                "traceback": tb,
            },
        )

    finally:
        # Clean up the saved upload file (the data lives in vector/sparse indexes now)
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                logger.debug("Cleaned up temp file: %s", str(file_path))
            except OSError as cleanup_err:
                logger.warning("Failed to clean up temp file %s: %s", str(file_path), cleanup_err)


@router.get("/list", response_model=list[DocItem])
async def list_documents():
    """
    Lists unique chunk entries available in the local BM25 indexing database.
    """
    try:
        idx = SparseBM25Index()
        if not idx.load():
            return []

        results = []
        for chunk in idx.chunks:
            payload = chunk.get("payload", {})
            results.append(
                DocItem(
                    id=chunk["id"],
                    source=payload.get("source", "unknown"),
                    category=payload.get("category", "general"),
                    content=chunk["content"][:200]
                    + ("..." if len(chunk["content"]) > 200 else ""),
                )
            )
        return results

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Failed to list documents: %s\n%s", str(e), tb)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "list_error",
                "detail": str(e),
                "traceback": tb,
            },
        )


@router.delete("/{point_id}")
async def delete_document(point_id: str):
    """
    Removes a specific point from Qdrant vector store and BM25 sparse index.
    """
    try:
        # Clean Qdrant
        from noray.rag.vector_store import VectorStoreFactory

        store = VectorStoreFactory.get_vector_store()
        store.delete(collection_name="user_documents", point_ids=[point_id])

        # Clean BM25
        idx = SparseBM25Index()
        if idx.load():
            updated_chunks = [c for c in idx.chunks if c["id"] != point_id]
            idx.fit_and_save(updated_chunks)

        return {"status": "deleted", "id": point_id}

    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Failed to delete document chunk %s: %s\n%s", point_id, str(e), tb)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "delete_error",
                "detail": str(e),
                "point_id": point_id,
                "traceback": tb,
            },
        )
