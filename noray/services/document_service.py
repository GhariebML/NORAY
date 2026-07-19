import os
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from noray.rag.chunker import select_and_chunk
from noray.rag.embeddings import EmbeddingsManager
from noray.rag.vector_store import VectorStoreFactory
from noray.rag.sparse_index import SparseBM25Index

class DocumentService:
    """Ingestion pipeline that extracts text from documents, chunks them, embeds them, and updates indexes."""
    def __init__(self, vector_store=None, embedder=None, sparse_index=None):
        self.vector_store = vector_store or VectorStoreFactory.get_vector_store()
        self.embedder = embedder or EmbeddingsManager.get_embedder()
        self.sparse_index = sparse_index or SparseBM25Index()

    def parse_file(self, file_path: Path) -> str:
        """Parse documents based on extension, with OCR fallback for images."""
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext == ".docx":
            return self._parse_docx(file_path)
        elif ext in [".md", ".markdown", ".txt", ".csv"]:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return self._parse_ocr(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_pdf(self, file_path: Path) -> str:
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except ImportError:
            # Fallback to PyMuPDF if pdfplumber is not available
            import fitz
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
        return text

    def _parse_docx(self, file_path: Path) -> str:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    def _parse_ocr(self, file_path: Path) -> str:
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(file_path))
        except Exception as e:
            raise RuntimeError(f"OCR parsing failed: {e}. Check if Tesseract OCR is installed.")

    def ingest_document(self, file_path: Path, category: str = "general", metadata_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs the complete end-to-end extraction, chunking, embedding, and dual-indexing pipeline."""
        filename = file_path.name
        text = self.parse_file(file_path)
        
        if not text.strip():
            raise ValueError(f"Extracted document text is empty: {filename}")

        # Choose chunking strategy and chunk text
        chunks_data = select_and_chunk(text, filename, embedding_model=self.embedder)
        
        # Build document-level metadata
        doc_metadata = {
            "source": filename,
            "category": category,
            "language": "en", # default
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        if metadata_overrides:
            doc_metadata.update(metadata_overrides)

        # 1. Store in Qdrant vector index
        collection_name = "user_documents"
        
        # Test vector dimension to initialize collection config
        sample_vector = self.embedder.embed(["Hello"])[0]
        vector_dim = len(sample_vector)
        self.vector_store.create_collection(collection_name, vector_dim)

        # Embed all chunks
        chunk_texts = [c["content"] for c in chunks_data]
        embeddings = self.embedder.embed(chunk_texts)

        upsert_points = []
        sparse_chunks = []

        for idx, chunk in enumerate(chunks_data):
            chunk_id = str(uuid.uuid4())
            vector = embeddings[idx]
            
            # Combine chunk-level details with doc-level metadata
            payload = doc_metadata.copy()
            payload["content"] = chunk["content"]
            payload["chunk_index"] = chunk["chunk_index"]
            payload["strategy"] = chunk["strategy"]
            
            upsert_points.append({
                "id": chunk_id,
                "vector": vector,
                "payload": payload
            })
            
            sparse_chunks.append({
                "id": chunk_id,
                "content": chunk["content"],
                "payload": payload
            })

        # Vector upload
        self.vector_store.upsert(collection_name, upsert_points)

        # 2. Store in Sparse index
        # Load existing index, append new chunks, and refit
        existing_chunks = []
        if self.sparse_index.load():
            existing_chunks = self.sparse_index.chunks

        all_chunks = existing_chunks + sparse_chunks
        self.sparse_index.fit_and_save(all_chunks)

        return {
            "filename": filename,
            "chunks_count": len(chunks_data),
            "strategy": chunks_data[0]["strategy"] if chunks_data else "none",
            "category": category
        }
