import os
import httpx
from typing import List, Dict, Any, Tuple, Optional

class BaseReranker:
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError

class LocalReranker(BaseReranker):
    """Uses a local CrossEncoder model for deep semantic re-ranking of retrieved passages."""
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self.model = None

    def _lazy_init(self):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not documents:
            return []
            
        self._lazy_init()
        # Pair query with each document text
        pairs = []
        for doc in documents:
            text = doc.get("content") or doc.get("payload", {}).get("content", "")
            pairs.append((query, text))

        # Predict similarity scores
        scores = self.model.predict(pairs)
        
        # Merge scores back to documents
        ranked_docs = []
        for score, doc in zip(scores, documents):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(score)
            ranked_docs.append(doc_copy)

        # Sort by rerank score descending
        ranked_docs = sorted(ranked_docs, key=lambda x: x["rerank_score"], reverse=True)
        return ranked_docs[:top_k]


class JinaReranker(BaseReranker):
    """Jina AI Re-rank API Client."""
    def __init__(self, model_name: str = "jina-reranker-v2-base-multilingual", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not documents:
            return []
        if not self.api_key:
            raise ValueError("Jina API key missing for reranker. Set JINA_API_KEY.")

        url = "https://api.jina.ai/v1/rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare docs in API format
        api_docs = []
        for doc in documents:
            text = doc.get("content") or doc.get("payload", {}).get("content", "")
            api_docs.append(text)

        payload = {
            "model": self.model_name,
            "query": query,
            "documents": api_docs,
            "top_n": top_k
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            ranked_docs = []
            for item in data.get("results", []):
                idx = item["index"]
                doc = documents[idx].copy()
                doc["rerank_score"] = float(item["relevance_score"])
                ranked_docs.append(doc)
            return ranked_docs


class CohereReranker(BaseReranker):
    """Cohere Re-rank API Client."""
    def __init__(self, model_name: str = "rerank-english-v3.0", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("COHERE_API_KEY", "")

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not documents:
            return []
        if not self.api_key:
            raise ValueError("Cohere API key missing for reranker. Set COHERE_API_KEY.")

        url = "https://api.cohere.ai/v1/rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare docs
        api_docs = []
        for doc in documents:
            text = doc.get("content") or doc.get("payload", {}).get("content", "")
            api_docs.append({"text": text})

        payload = {
            "model": self.model_name,
            "query": query,
            "documents": api_docs,
            "top_n": top_k
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            ranked_docs = []
            for item in data.get("results", []):
                idx = item["index"]
                doc = documents[idx].copy()
                doc["rerank_score"] = float(item["relevance_score"])
                ranked_docs.append(doc)
            return ranked_docs


class RerankerManager:
    """Manager to load and initialize selected reranker client dynamically."""
    _instance: Optional[BaseReranker] = None

    @staticmethod
    def get_reranker(provider: str = None, model_name: str = None) -> BaseReranker:
        if RerankerManager._instance is not None:
            return RerankerManager._instance
            
        provider = provider or os.getenv("RERANKER_PROVIDER", "local").lower()
        
        if provider == "jina":
            model = model_name or os.getenv("RERANKER_MODEL", "jina-reranker-v2-base-multilingual")
            RerankerManager._instance = JinaReranker(model_name=model)
        elif provider == "cohere":
            model = model_name or os.getenv("RERANKER_MODEL", "rerank-english-v3.0")
            RerankerManager._instance = CohereReranker(model_name=model)
        else:
            model = model_name or os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
            RerankerManager._instance = LocalReranker(model_name=model)
            
        return RerankerManager._instance
