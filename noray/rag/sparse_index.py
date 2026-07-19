import re
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class SparseBM25Index:
    """Sparse text retrieval using BM25, with incremental serialization."""
    def __init__(self, index_path: str = "d:/NORAY/data/bm25_index.pkl"):
        self.index_path = Path(index_path)
        self.bm25 = None
        self.chunks = []  # List of dicts: {"id": str, "content": str, "payload": dict}
        self.tokenized_corpus = []

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean non-alphanumeric, and split
        text = text.lower()
        words = re.findall(r"\b\w{2,}\b", text)
        return words

    def fit_and_save(self, chunks: List[Dict[str, Any]]) -> None:
        """Fit BM25 model on a corpus of chunks and serialize to disk."""
        self.chunks = chunks
        self.tokenized_corpus = [self._tokenize(c["content"]) for c in chunks]
        
        if not chunks:
            self.bm25 = None
            return

        from rank_bm25 import BM25Okapi
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        # Save to disk
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "tokenized_corpus": self.tokenized_corpus
            }, f)

    def load(self) -> bool:
        """Load BM25 index from disk. Returns true if successful."""
        if not self.index_path.exists():
            return False
        try:
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.chunks = data["chunks"]
                self.tokenized_corpus = data["tokenized_corpus"]
            
            if self.tokenized_corpus:
                from rank_bm25 import BM25Okapi
                self.bm25 = BM25Okapi(self.tokenized_corpus)
                return True
            return False
        except Exception:
            return False

    def search(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search corpus for top K matches using BM25 token matching, applying metadata filters."""
        if not self.bm25 or not self.chunks:
            # Try lazy load
            if not self.load():
                return []

        tokenized_query = self._tokenize(query)
        # Calculate BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Map back to chunks with scores
        hits = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            payload = chunk.get("payload", {})
            
            # Apply metadata filters
            match = True
            if filters:
                for k, v in filters.items():
                    if payload.get(k) != v:
                        match = False
                        break
            
            if match and score > 0:
                hits.append({
                    "id": chunk["id"],
                    "score": float(score),
                    "payload": payload,
                    "content": chunk["content"]
                })
        
        # Sort by score descending
        hits = sorted(hits, key=lambda x: x["score"], reverse=True)
        return hits[:limit]
