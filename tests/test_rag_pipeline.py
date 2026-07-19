import os
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from noray.rag.chunker import RecursiveCharacterChunker, MarkdownChunker, select_and_chunk
from noray.rag.embeddings import LocalEmbedder, EmbeddingsManager
from noray.rag.vector_store import VectorStoreFactory, FAISSVectorStore
from noray.rag.sparse_index import SparseBM25Index
from noray.rag.fusion import reciprocal_rank_fusion
from noray.rag.reranker import RerankerManager
from noray.rag.compressor import ContextCompressor
from noray.rag.query_processor import QueryProcessor
from noray.services.document_service import DocumentService
from noray.agents.agent_router import AgentRouter

@pytest.fixture
def temp_markdown_file():
    with NamedTemporaryFile(suffix=".md", mode="w", delete=False, encoding="utf-8") as f:
        f.write(
            "# Chevening Scholarship Guide\n\n"
            "The Chevening Scholarship covers full tuition fees, travel costs, and a monthly stipend "
            "for Master's degrees in the United Kingdom. Applicants must have 2 years of work experience.\n\n"
            "## How to Apply\n\n"
            "Submit applications online through the Chevening portal before November 5, 2026. "
            "You need three university choices and two reference letters."
        )
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()

def test_chunking_strategies():
    text = (
        "# Title\nParagraph one.\n\n"
        "## Subtitle\nParagraph two with some code: `def hello(): print(1)`"
    )
    # Markdown chunker
    md_chunks = MarkdownChunker(chunk_size=100).chunk(text)
    assert len(md_chunks) >= 2
    assert md_chunks[0].startswith("# Title")
    
    # Recursive Chunker
    rec_chunks = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=10).chunk(text)
    assert len(rec_chunks) >= 2

def test_local_embeddings():
    embedder = LocalEmbedder(model_name="all-MiniLM-L6-v2")
    texts = ["Hello world", "Machine Learning with Python"]
    vectors = embedder.embed(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384 # MiniLM dimensions

def test_faiss_vector_store():
    # Force FAISS store
    store = VectorStoreFactory.get_vector_store(provider="faiss")
    assert isinstance(store, FAISSVectorStore)
    
    store.create_collection("test_coll", 4)
    points = [
        {"id": "p1", "vector": [1.0, 0.0, 0.0, 0.0], "payload": {"tag": "first"}},
        {"id": "p2", "vector": [0.0, 1.0, 0.0, 0.0], "payload": {"tag": "second"}}
    ]
    store.upsert("test_coll", points)
    
    # Query matching p1
    hits = store.search("test_coll", [1.0, 0.1, 0.0, 0.0], limit=1)
    assert len(hits) == 1
    assert hits[0]["id"] == "p1"
    assert hits[0]["payload"]["tag"] == "first"

def test_bm25_sparse_index():
    with NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        index_path = f.name
        
    try:
        idx = SparseBM25Index(index_path=index_path)
        chunks = [
            {"id": "c1", "content": "Applying for a visa in Germany requires health insurance.", "payload": {"country": "Germany"}},
            {"id": "c2", "content": "Scholarship guidelines for Fulbright program in US.", "payload": {"country": "US"}},
            {"id": "c3", "content": "This is a dummy document for search index testing purposes.", "payload": {"country": "Other"}}
        ]
        idx.fit_and_save(chunks)
        
        # Load and search
        idx2 = SparseBM25Index(index_path=index_path)
        hits = idx2.search("Fulbright", limit=1)
        assert len(hits) == 1
        assert hits[0]["id"] == "c2"
    finally:
        if os.path.exists(index_path):
            os.remove(index_path)

def test_reciprocal_rank_fusion():
    dense = [
        {"id": "doc1", "score": 0.9},
        {"id": "doc2", "score": 0.8},
        {"id": "doc3", "score": 0.7}
    ]
    sparse = [
        {"id": "doc3", "score": 12.0},
        {"id": "doc1", "score": 10.0},
        {"id": "doc4", "score": 5.0}
    ]
    fused = reciprocal_rank_fusion(dense, sparse, k=60, limit=2)
    assert len(fused) == 2
    # doc1 and doc3 should be highest ranked due to presence in both lists
    assert fused[0]["id"] in ["doc1", "doc3"]

def test_query_understanding():
    qp = QueryProcessor(use_llm=False)
    intent = qp.classify_intent("Tell me about DAAD scholarship opportunities in Germany")
    assert intent == "scholarship"
    
    filters = qp.extract_metadata_filters("Fulbright scholarship guidelines for Master in USA")
    assert filters.get("country") == "United States"
    assert filters.get("degree") == "MSc"

def test_context_compressor():
    comp = ContextCompressor()
    hits = [
        {"id": "doc1", "score": 0.9, "payload": {"source": "guide.md", "chunk_index": 0, "content": "Paragraph part A."}},
        {"id": "doc2", "score": 0.8, "payload": {"source": "guide.md", "chunk_index": 1, "content": "Paragraph part B."}},
        {"id": "doc3", "score": 0.7, "payload": {"source": "unrelated.md", "chunk_index": 0, "content": "Other content."}}
    ]
    # Merges adjacent chunks from guide.md (index 0 and 1)
    merged = comp.clean_and_compress(hits)
    assert len(merged) == 2
    merged_texts = [m.get("content") for m in merged]
    assert any("Paragraph part A. Paragraph part B." in text for text in merged_texts if text)

@pytest.mark.asyncio
async def test_document_ingestion_pipeline(temp_markdown_file):
    # Setup dual indexing with FAISS and temp index
    with NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        index_path = f.name
        
    try:
        store = VectorStoreFactory.get_vector_store(provider="faiss")
        embedder = LocalEmbedder()
        idx = SparseBM25Index(index_path=index_path)
        
        doc_service = DocumentService(vector_store=store, embedder=embedder, sparse_index=idx)
        result = doc_service.ingest_document(
            file_path=temp_markdown_file,
            category="scholarship",
            metadata_overrides={"language": "en"}
        )
        assert result["filename"] == temp_markdown_file.name
        assert result["chunks_count"] >= 2
        assert result["category"] == "scholarship"
    finally:
        if os.path.exists(index_path):
            os.remove(index_path)
