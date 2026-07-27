import os
from pathlib import Path
from typing import Any


class BaseVectorStore:
    def create_collection(self, collection_name: str, vector_size: int) -> None:
        raise NotImplementedError

    def upsert(self, collection_name: str, points: list[dict[str, Any]]) -> None:
        """
        points list: [{"id": str_or_int, "vector": List[float], "payload": Dict[str, Any]}]
        """
        raise NotImplementedError

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Returns list of hits: [{"id": ..., "score": float, "payload": Dict}]
        """
        raise NotImplementedError

    def delete(self, collection_name: str, point_ids: list[Any]) -> None:
        raise NotImplementedError


import logging
import threading

logger = logging.getLogger(__name__)

_global_qdrant_client_lock = threading.Lock()
_global_qdrant_client = None

class QdrantVectorStore(BaseVectorStore):
    """Qdrant client integration supporting thread-safe in-memory, local file, or remote server modes."""
    def __init__(self, location: str = ":memory:", path: str = None, url: str = None, api_key: str = None):
        self.location = location
        self.path = path
        self.url = url
        self.api_key = api_key
        self.client = None

    def _lazy_init(self):
        global _global_qdrant_client
        if self.client is not None:
            return

        with _global_qdrant_client_lock:
            if _global_qdrant_client is not None:
                self.client = _global_qdrant_client
                return

            from qdrant_client import QdrantClient

            # Setup environment variable fallbacks
            q_url = self.url or os.getenv("QDRANT_URL")
            q_api_key = self.api_key or os.getenv("QDRANT_API_KEY")

            if q_url:
                try:
                    _global_qdrant_client = QdrantClient(url=q_url, api_key=q_api_key)
                    logger.info("Connected to remote Qdrant server at %s", q_url)
                except Exception as e:
                    logger.warning("Failed to connect to Qdrant server %s: %s. Falling back to local storage.", q_url, e)

            if _global_qdrant_client is None:
                _default_qdrant = str(Path(__file__).resolve().parent.parent.parent / "data" / "qdrant")
                db_path = self.path or os.getenv("QDRANT_PATH", _default_qdrant)
                try:
                    os.makedirs(db_path, exist_ok=True)
                    _global_qdrant_client = QdrantClient(path=db_path)
                    logger.info("Initialized local QdrantClient storage at %s", db_path)
                except Exception as err:
                    logger.warning("Local Qdrant lock error (%s). Falling back to in-memory Qdrant client.", err)
                    _global_qdrant_client = QdrantClient(location=":memory:")

            self.client = _global_qdrant_client

    def create_collection(self, collection_name: str, vector_size: int) -> None:
        self._lazy_init()
        from qdrant_client.http.models import Distance, VectorParams

        # Check if collection already exists
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def upsert(self, collection_name: str, points: list[dict[str, Any]]) -> None:
        self._lazy_init()
        from qdrant_client.http.models import PointStruct

        qdrant_points = []
        for p in points:
            qdrant_points.append(
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                )
            )
        self.client.upsert(collection_name=collection_name, points=qdrant_points)

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a named collection exists in Qdrant."""
        try:
            self._lazy_init()
            if not self.client:
                return False
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False

    def create_collection_if_missing(self, collection_name: str, vector_size: int = 384) -> bool:
        """Auto-create collection if it doesn't exist. Returns True if created."""
        try:
            if not self.collection_exists(collection_name):
                self.create_collection(collection_name, vector_size)
                logger.info(f"Auto-created missing collection: '{collection_name}' (dim={vector_size})")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to auto-create collection '{collection_name}': {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self._lazy_init()

        # Validate collection exists before searching
        if not self.collection_exists(collection_name):
            logger.warning(f"Collection '{collection_name}' does not exist — returning empty results")
            return []

        q_filter = None
        if filters:
            from qdrant_client.http.models import FieldCondition, Filter, MatchValue
            conditions = []
            for key, val in filters.items():
                if val is not None:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=val))
                    )
            if conditions:
                q_filter = Filter(must=conditions)

        if hasattr(self.client, "search"):
            hits = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=q_filter,
                limit=limit
            )
        else:
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=q_filter,
                limit=limit
            )
            hits = response.points

        result = []
        for hit in hits:
            result.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })
        return result

    def delete(self, collection_name: str, point_ids: list[Any]) -> None:
        self._lazy_init()
        from qdrant_client.http.models import PointIdsList
        self.client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=point_ids)
        )


class FAISSVectorStore(BaseVectorStore):
    """Fallback in-memory vector store using pure NumPy to avoid native C++ dependencies like FAISS."""
    def __init__(self):
        self.indexes = {} # Map of collection name to {"vectors": List[List[float]], "ids": List[Any], "payloads": List[Dict], "dimension": int}

    def create_collection(self, collection_name: str, vector_size: int) -> None:
        if collection_name not in self.indexes:
            self.indexes[collection_name] = {
                "vectors": [],
                "ids": [],
                "payloads": [],
                "dimension": vector_size
            }

    def upsert(self, collection_name: str, points: list[dict[str, Any]]) -> None:
        import numpy as np
        if collection_name not in self.indexes:
            dim = len(points[0]["vector"]) if points else 384
            self.create_collection(collection_name, dim)

        coll = self.indexes[collection_name]
        for p in points:
            vec = np.array(p["vector"], dtype=np.float32)
            # Normalize vector for cosine similarity
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            coll["vectors"].append(vec.tolist())
            coll["ids"].append(p["id"])
            coll["payloads"].append(p.get("payload", {}))

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        import numpy as np
        if collection_name not in self.indexes or not self.indexes[collection_name]["vectors"]:
            return []

        coll = self.indexes[collection_name]
        vectors = np.array(coll["vectors"], dtype=np.float32)

        q_vec = np.array(query_vector, dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # Compute cosine similarity (dot product of normalized vectors)
        scores = np.dot(vectors, q_vec)

        # Sort indices by score descending
        sorted_indices = np.argsort(scores)[::-1]

        hits = []
        for idx in sorted_indices:
            payload = coll["payloads"][idx]

            # Apply metadata filters manually
            match = True
            if filters:
                for k, v in filters.items():
                    if payload.get(k) != v:
                        match = False
                        break

            if match:
                hits.append({
                    "id": coll["ids"][idx],
                    "score": float(scores[idx]),
                    "payload": payload
                })
                if len(hits) >= limit:
                    break
        return hits

    def delete(self, collection_name: str, point_ids: list[Any]) -> None:
        if collection_name not in self.indexes:
            return
        coll = self.indexes[collection_name]

        remaining_indices = [
            i for i, pid in enumerate(coll["ids"]) if pid not in point_ids
        ]

        coll["vectors"] = [coll["vectors"][i] for i in remaining_indices]
        coll["ids"] = [coll["ids"][i] for i in remaining_indices]
        coll["payloads"] = [coll["payloads"][i] for i in remaining_indices]


class VectorStoreFactory:
    """Factory to instantiate vector store clients."""
    _instance: BaseVectorStore | None = None

    @staticmethod
    def get_vector_store(provider: str = None) -> BaseVectorStore:
        target_provider = (provider or os.getenv("VECTOR_STORE_PROVIDER", "qdrant")).lower()

        if provider is None and VectorStoreFactory._instance is not None:
            return VectorStoreFactory._instance

        if target_provider == "faiss":
            instance = FAISSVectorStore()
        else:
            # Default is Qdrant
            # Check if Qdrant server is available via environment variables
            q_url = os.getenv("QDRANT_URL")
            q_host = os.getenv("QDRANT_HOST")
            q_port = os.getenv("QDRANT_PORT", "6333")

            if q_url:
                instance = QdrantVectorStore(url=q_url)
            elif q_host:
                instance = QdrantVectorStore(url=f"http://{q_host}:{q_port}")
            else:
                # Supports qdrant path mapping for file base persistence
                _default_qdrant2 = str(Path(__file__).resolve().parent.parent.parent / "data" / "qdrant")
                db_path = os.getenv("QDRANT_PATH", _default_qdrant2)
                if not os.path.exists(db_path):
                    os.makedirs(db_path, exist_ok=True)
                instance = QdrantVectorStore(path=db_path)

        if provider is None:
            VectorStoreFactory._instance = instance

        return instance
