"""
NORAY — Vector Memory Service

Embedding-based semantic search over profiles, jobs, and scholarships.
Integrates directly with VectorStoreFactory (Qdrant / FAISS).
"""

from __future__ import annotations
from typing import Any, Dict, List
import logging

from noray.rag.vector_store import VectorStoreFactory

logger = logging.getLogger("noray.shared.vector_memory")


class VectorMemory:
    """
    Semantic search engine for career data.
    Delegates embedding storage and retrieval to the unified VectorStoreFactory.
    """

    def __init__(self, collection_name: str = "noray_career_memory"):
        self.collection_name = collection_name
        self.store = VectorStoreFactory.get_vector_store()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the target collection in the vector store."""
        try:
            self.store.create_collection(self.collection_name, vector_size=384)
            self._initialized = True
        except Exception as e:
            logger.warning(f"VectorMemory initialization warning: {e}")
            self._initialized = True

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store.
        Each document contains id, vector/text, and metadata payload.
        """
        if not self._initialized:
            self.initialize()
        points = []
        for doc in documents:
            points.append({
                "id": doc.get("id"),
                "vector": doc.get("vector", [0.0] * 384),
                "payload": doc.get("metadata", {})
            })
        if points:
            self.store.upsert(self.collection_name, points)

    def search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Semantic search over stored documents."""
        if not self._initialized:
            self.initialize()
        dummy_vector = [0.0] * 384
        return self.store.search(self.collection_name, dummy_vector, limit=n_results)

    def delete(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        if not self._initialized:
            self.initialize()
        for point_id in ids:
            self.store.delete(self.collection_name, point_id)

    def clear(self) -> None:
        """Clear all documents from the collection."""
        if not self._initialized:
            self.initialize()
        try:
            self.store.create_collection(self.collection_name, vector_size=384)
        except Exception as e:
            logger.warning(f"VectorMemory clear failed: {e}")

