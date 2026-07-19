import os
from typing import List, Dict, Any, Optional

class BaseVectorStore:
    def create_collection(self, collection_name: str, vector_size: int) -> None:
        raise NotImplementedError

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """
        points list: [{"id": str_or_int, "vector": List[float], "payload": Dict[str, Any]}]
        """
        raise NotImplementedError

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns list of hits: [{"id": ..., "score": float, "payload": Dict}]
        """
        raise NotImplementedError

    def delete(self, collection_name: str, point_ids: List[Any]) -> None:
        raise NotImplementedError


class QdrantVectorStore(BaseVectorStore):
    """Qdrant client integration supporting in-memory, local file, or remote server modes."""
    def __init__(self, location: str = ":memory:", path: str = None, url: str = None, api_key: str = None):
        self.location = location
        self.path = path
        self.url = url
        self.api_key = api_key
        self.client = None

    def _lazy_init(self):
        if self.client is None:
            from qdrant_client import QdrantClient
            
            # Setup environment variable fallbacks
            q_url = self.url or os.getenv("QDRANT_URL")
            q_api_key = self.api_key or os.getenv("QDRANT_API_KEY")
            
            if q_url:
                self.client = QdrantClient(url=q_url, api_key=q_api_key)
            elif self.path:
                self.client = QdrantClient(path=self.path)
            elif os.getenv("QDRANT_PATH"):
                self.client = QdrantClient(path=os.getenv("QDRANT_PATH"))
            else:
                # Fallback to local memory database
                self.client = QdrantClient(location=self.location)

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

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
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

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        self._lazy_init()
        
        q_filter = None
        if filters:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            conditions = []
            for key, val in filters.items():
                if val is not None:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=val))
                    )
            if conditions:
                q_filter = Filter(must=conditions)

        hits = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=limit
        )
        
        result = []
        for hit in hits:
            result.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })
        return result

    def delete(self, collection_name: str, point_ids: List[Any]) -> None:
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

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
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
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
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

    def delete(self, collection_name: str, point_ids: List[Any]) -> None:
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
    _instance: Optional[BaseVectorStore] = None

    @staticmethod
    def get_vector_store(provider: str = None) -> BaseVectorStore:
        if VectorStoreFactory._instance is not None:
            return VectorStoreFactory._instance

        provider = provider or os.getenv("VECTOR_STORE_PROVIDER", "qdrant").lower()
        
        if provider == "faiss":
            VectorStoreFactory._instance = FAISSVectorStore()
        else:
            # Default is Qdrant
            # Check if Qdrant server is available via environment variables
            q_url = os.getenv("QDRANT_URL")
            q_host = os.getenv("QDRANT_HOST")
            q_port = os.getenv("QDRANT_PORT", "6333")
            
            if q_url:
                VectorStoreFactory._instance = QdrantVectorStore(url=q_url)
            elif q_host:
                VectorStoreFactory._instance = QdrantVectorStore(url=f"http://{q_host}:{q_port}")
            else:
                # Supports qdrant path mapping for file base persistence
                db_path = os.getenv("QDRANT_PATH", "d:/NORAY/data/qdrant")
                if not os.path.exists(db_path):
                    os.makedirs(db_path, exist_ok=True)
                VectorStoreFactory._instance = QdrantVectorStore(path=db_path)
                
        return VectorStoreFactory._instance
