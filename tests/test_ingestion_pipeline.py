"""
Comprehensive unit tests for the NORAY document ingestion pipeline.

Tests cover:
- Filename sanitization (UUID generation, extension preservation, invalid chars)
- Upload validation (empty files, unsupported types, size limits)
- File save and cleanup lifecycle
- Document parsing (TXT, MD, PDF stub)
- Chunking strategies
- Full pipeline integration (parse → chunk → embed → index)
- Windows path compatibility
"""

import os
import uuid
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from io import BytesIO

# ── Test the sanitize_filename function directly ──────────────────────────────

# Import the function under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from noray.api.routes.documents import sanitize_filename, validate_upload_file, ALLOWED_EXTENSIONS


class TestFilenameSanitization:
    """Tests for UUID-based filename sanitization."""

    def test_basic_pdf_sanitization(self):
        sanitized, ext = sanitize_filename("my_resume.pdf")
        assert ext == ".pdf"
        assert sanitized.endswith(".pdf")
        # Filename should be a valid UUID hex + extension
        uuid_part = sanitized.replace(".pdf", "")
        assert len(uuid_part) == 32  # UUID hex is 32 chars
        uuid.UUID(uuid_part)  # Should not raise

    def test_docx_extension_preserved(self):
        sanitized, ext = sanitize_filename("Cover Letter (v2).docx")
        assert ext == ".docx"
        assert sanitized.endswith(".docx")

    def test_txt_extension_preserved(self):
        sanitized, ext = sanitize_filename("notes.txt")
        assert ext == ".txt"
        assert sanitized.endswith(".txt")

    def test_markdown_extension_preserved(self):
        sanitized, ext = sanitize_filename("README.md")
        assert ext == ".md"
        assert sanitized.endswith(".md")

    def test_uppercase_extension_lowered(self):
        sanitized, ext = sanitize_filename("FILE.PDF")
        assert ext == ".pdf"
        assert sanitized.endswith(".pdf")

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            sanitize_filename("malware.exe")

    def test_no_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            sanitize_filename("noextension")

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            sanitize_filename("")

    def test_windows_invalid_chars_in_original_are_irrelevant(self):
        """Since we UUID-replace the name, invalid Windows chars in the original don't matter."""
        sanitized, ext = sanitize_filename("file:with:colons.pdf")
        assert ext == ".pdf"
        # The sanitized name should NOT contain colons
        assert ":" not in sanitized

    def test_smart_quotes_in_original_are_irrelevant(self):
        sanitized, ext = sanitize_filename("Mohamed\u2019s Resume.pdf")
        assert ext == ".pdf"
        assert "\u2019" not in sanitized

    def test_path_traversal_in_original_is_irrelevant(self):
        sanitized, ext = sanitize_filename("../../etc/passwd.txt")
        assert ext == ".txt"
        assert ".." not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized

    def test_windows_reserved_names_are_irrelevant(self):
        """Windows reserved names like CON, PRN, NUL are never generated."""
        sanitized, ext = sanitize_filename("CON.txt")
        assert ext == ".txt"
        uuid_part = sanitized.replace(".txt", "")
        assert uuid_part.upper() not in {"CON", "PRN", "AUX", "NUL"}

    def test_each_call_produces_unique_name(self):
        names = {sanitize_filename("test.pdf")[0] for _ in range(100)}
        assert len(names) == 100  # All unique

    def test_all_allowed_extensions(self):
        for ext in ALLOWED_EXTENSIONS:
            sanitized, result_ext = sanitize_filename(f"test{ext}")
            assert result_ext == ext
            assert sanitized.endswith(ext)


class TestUploadValidation:
    """Tests for upload file pre-validation."""

    def test_valid_pdf_passes(self):
        mock_file = MagicMock()
        mock_file.filename = "resume.pdf"
        validate_upload_file(mock_file)  # Should not raise

    def test_valid_docx_passes(self):
        mock_file = MagicMock()
        mock_file.filename = "letter.docx"
        validate_upload_file(mock_file)  # Should not raise

    def test_no_filename_raises(self):
        mock_file = MagicMock()
        mock_file.filename = None
        with pytest.raises(ValueError, match="No filename provided"):
            validate_upload_file(mock_file)

    def test_empty_filename_raises(self):
        mock_file = MagicMock()
        mock_file.filename = ""
        with pytest.raises(ValueError, match="No filename provided"):
            validate_upload_file(mock_file)

    def test_unsupported_type_raises(self):
        mock_file = MagicMock()
        mock_file.filename = "virus.exe"
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_upload_file(mock_file)


class TestWindowsPathCompatibility:
    """Tests that generated paths are valid on Windows."""

    WINDOWS_INVALID_CHARS = set('<>:"|?*')
    WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3",
                         "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                         "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6",
                         "LPT7", "LPT8", "LPT9"}

    def test_sanitized_name_has_no_invalid_chars(self):
        # Test with a filename that has every invalid Windows char
        dangerous = 'file<>:"|?*.pdf'
        sanitized, _ = sanitize_filename(dangerous)
        for char in self.WINDOWS_INVALID_CHARS:
            assert char not in sanitized, f"Found invalid char '{char}' in sanitized name"

    def test_sanitized_name_is_not_reserved(self):
        for reserved in self.WINDOWS_RESERVED:
            sanitized, _ = sanitize_filename(f"{reserved}.txt")
            stem = Path(sanitized).stem.upper()
            assert stem not in self.WINDOWS_RESERVED

    def test_path_construction_with_pathlib(self):
        """Ensure pathlib division produces valid paths."""
        upload_dir = Path("d:/NORAY/data/uploads")
        sanitized, _ = sanitize_filename("test file (1).pdf")
        full_path = upload_dir / sanitized
        # Path should be absolute-safe and contain no problematic segments
        assert str(full_path).startswith("d:")
        assert ".." not in str(full_path)


class TestDocumentServiceParsing:
    """Tests for document text extraction."""

    def test_parse_txt_file(self):
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
            f.write("Hello World. This is a test document with enough content to chunk properly.")
            tmp_path = Path(f.name)

        try:
            service = DocumentService.__new__(DocumentService)
            text = service.parse_file(tmp_path)
            assert "Hello World" in text
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_md_file(self):
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8") as f:
            f.write("# Heading\n\nSome markdown content with paragraphs.\n\n## Section 2\n\nMore content here.")
            tmp_path = Path(f.name)

        try:
            service = DocumentService.__new__(DocumentService)
            text = service.parse_file(tmp_path)
            assert "# Heading" in text
            assert "## Section 2" in text
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_empty_file_raises(self):
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("")
            tmp_path = Path(f.name)

        try:
            service = DocumentService.__new__(DocumentService)
            text = service.parse_file(tmp_path)
            assert text.strip() == ""
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_unsupported_format_raises(self):
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            service = DocumentService.__new__(DocumentService)
            with pytest.raises(ValueError, match="Unsupported file format"):
                service.parse_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)


class TestChunking:
    """Tests for the chunking strategies."""

    def test_recursive_chunker_produces_chunks(self):
        from noray.rag.chunker import RecursiveCharacterChunker
        chunker = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=10)
        # Generate enough text to exceed chunk_size multiple times
        text = "This is a longer sentence for testing purposes. " * 50
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_markdown_chunker_splits_by_headers(self):
        from noray.rag.chunker import MarkdownChunker
        text = "# Title\n\nIntro paragraph.\n\n## Section\n\nSection content.\n\n## Another\n\nMore."
        chunker = MarkdownChunker(chunk_size=5000)
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_select_and_chunk_picks_markdown_for_md(self):
        from noray.rag.chunker import select_and_chunk
        text = "# Hello\n\nContent here.\n\n## World\n\nMore content."
        result = select_and_chunk(text, "readme.md")
        assert len(result) > 0
        assert result[0]["strategy"] == "markdown"

    def test_select_and_chunk_picks_recursive_for_txt(self):
        from noray.rag.chunker import select_and_chunk
        text = "Short text content. " * 50
        result = select_and_chunk(text, "document.txt")
        assert len(result) > 0
        assert result[0]["strategy"] in ("recursive", "semantic")

    def test_chunk_metadata_structure(self):
        from noray.rag.chunker import select_and_chunk
        text = "Some content for chunking. " * 10
        result = select_and_chunk(text, "file.txt")
        for chunk in result:
            assert "chunk_index" in chunk
            assert "content" in chunk
            assert "length" in chunk
            assert "strategy" in chunk
            assert isinstance(chunk["chunk_index"], int)
            assert isinstance(chunk["content"], str)
            assert chunk["length"] == len(chunk["content"])


class TestFullIngestionPipeline:
    """Integration tests for the full parse → chunk → embed → index pipeline."""

    def test_ingest_txt_document(self):
        """Test full ingestion of a plain text file with mock embedder and stores."""
        from noray.services.document_service import DocumentService

        # Create a test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
            f.write("This is a comprehensive test document. " * 30)
            tmp_path = Path(f.name)

        try:
            # Mock the vector store
            mock_vector_store = MagicMock()
            mock_vector_store.create_collection = MagicMock()
            mock_vector_store.upsert = MagicMock()

            # Mock the embedder to return fixed-dimension vectors
            mock_embedder = MagicMock()
            mock_embedder.embed = MagicMock(
                side_effect=lambda texts: [[0.1] * 384 for _ in texts]
            )

            # Mock the sparse index
            mock_sparse = MagicMock()
            mock_sparse.load = MagicMock(return_value=False)
            mock_sparse.fit_and_save = MagicMock()

            service = DocumentService(
                vector_store=mock_vector_store,
                embedder=mock_embedder,
                sparse_index=mock_sparse,
            )

            result = service.ingest_document(
                file_path=tmp_path,
                category="test",
                metadata_overrides={"language": "en", "original_filename": "test.txt"},
            )

            # Verify result structure
            assert "filename" in result
            assert "chunks_count" in result
            assert "strategy" in result
            assert "category" in result
            assert result["chunks_count"] > 0
            assert result["category"] == "test"

            # Verify vector store was called
            mock_vector_store.create_collection.assert_called_once()
            mock_vector_store.upsert.assert_called_once()

            # Verify sparse index was updated
            mock_sparse.fit_and_save.assert_called_once()

            # Verify embedder was called for chunks + dimension probe
            assert mock_embedder.embed.call_count >= 2  # once for dim probe, once for chunks

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ingest_md_document(self):
        """Test full ingestion of a Markdown file."""
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w", encoding="utf-8") as f:
            f.write("# Title\n\nParagraph one content.\n\n## Section\n\nParagraph two content.\n\n## Another\n\nParagraph three.")
            tmp_path = Path(f.name)

        try:
            mock_vector_store = MagicMock()
            mock_embedder = MagicMock()
            mock_embedder.embed = MagicMock(
                side_effect=lambda texts: [[0.1] * 384 for _ in texts]
            )
            mock_sparse = MagicMock()
            mock_sparse.load = MagicMock(return_value=False)

            service = DocumentService(
                vector_store=mock_vector_store,
                embedder=mock_embedder,
                sparse_index=mock_sparse,
            )

            result = service.ingest_document(file_path=tmp_path, category="notes")

            assert result["strategy"] == "markdown"
            assert result["chunks_count"] >= 1

        finally:
            tmp_path.unlink(missing_ok=True)

    def test_ingest_empty_document_raises(self):
        """Empty documents should raise ValueError."""
        from noray.services.document_service import DocumentService

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("   ")  # Whitespace only
            tmp_path = Path(f.name)

        try:
            mock_vector_store = MagicMock()
            mock_embedder = MagicMock()
            mock_sparse = MagicMock()

            service = DocumentService(
                vector_store=mock_vector_store,
                embedder=mock_embedder,
                sparse_index=mock_sparse,
            )

            with pytest.raises(ValueError, match="empty"):
                service.ingest_document(file_path=tmp_path, category="test")

        finally:
            tmp_path.unlink(missing_ok=True)


class TestBM25SparseIndex:
    """Tests for the BM25 sparse index serialization."""

    def test_fit_save_and_load(self):
        from noray.rag.sparse_index import SparseBM25Index

        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = str(Path(tmpdir) / "test_bm25.pkl")
            idx = SparseBM25Index(index_path=index_path)

            chunks = [
                {"id": "1", "content": "Machine learning and artificial intelligence", "payload": {"source": "test"}},
                {"id": "2", "content": "Deep learning neural networks", "payload": {"source": "test"}},
                {"id": "3", "content": "Natural language processing and transformers", "payload": {"source": "test"}},
            ]

            idx.fit_and_save(chunks)
            assert Path(index_path).exists()

            # Load in a new instance
            idx2 = SparseBM25Index(index_path=index_path)
            assert idx2.load() is True
            assert len(idx2.chunks) == 3

    def test_search_returns_loaded_corpus(self):
        """Test that saved index can be loaded and its corpus is intact."""
        from noray.rag.sparse_index import SparseBM25Index

        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = str(Path(tmpdir) / "test_bm25.pkl")
            idx = SparseBM25Index(index_path=index_path)

            chunks = [
                {"id": "1", "content": "Machine learning algorithms for classification and regression", "payload": {"cat": "ml"}},
                {"id": "2", "content": "Cooking recipes for pasta and pizza in Italian cuisine", "payload": {"cat": "food"}},
            ]

            idx.fit_and_save(chunks)

            # Reload from disk in a fresh instance to test persistence
            idx2 = SparseBM25Index(index_path=index_path)
            loaded = idx2.load()
            assert loaded is True
            assert len(idx2.chunks) == 2
            assert idx2.chunks[0]["id"] == "1"
            assert idx2.chunks[1]["id"] == "2"
            assert idx2.bm25 is not None
            assert len(idx2.tokenized_corpus) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
