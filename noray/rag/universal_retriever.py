"""
NORAY — Universal Retriever

A unified interface consolidating Vector (Dense), BM25 (Sparse), Knowledge Graph,
Metadata, Memory, and SQL retrievals.
Supports Hybrid Fusion (Reciprocal Rank Fusion) and intent-based routing.
"""

import asyncio
from typing import Any


class UniversalRetriever:
    def __init__(self, vector_store: Any, graph_store: Any, sparse_index: Any):
        self.vector = vector_store
        self.graph = graph_store
        self.sparse = sparse_index

    async def retrieve(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Executes concurrent retrieval across all connected backends and fuses the results.
        """
        # 1. Intent Classification
        intent = self._classify_intent(query)

        # 2. Query Rewriting
        rewritten_queries = self._rewrite_query(query, intent)

        # 3. Concurrent Execution via asyncio.gather
        tasks = []
        for q in rewritten_queries:
            if intent in ["factual", "hybrid"]:
                tasks.append(self._fetch_vector(q, limit))
                tasks.append(self._fetch_sparse(q, limit))
            if intent in ["relational", "hybrid"]:
                tasks.append(self._fetch_graph(q, limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Hybrid Fusion (e.g., RRF - Reciprocal Rank Fusion)
        fused = self._fuse_results(*results)

        # 5. Reranking (CrossEncoder)
        reranked = self._rerank(query, fused, limit)

        return reranked

    def _classify_intent(self, query: str) -> str:
        """Determines if the query needs Graph, Vector, or Hybrid retrieval."""
        if "connects to" in query or "related to" in query or "depends on" in query:
            return "relational"
        if "what is" in query or "define" in query:
            return "factual"
        return "hybrid"

    def _rewrite_query(self, query: str, intent: str) -> list[str]:
        """Expands the query using synonyms or sub-queries to improve recall."""
        # Mock expansion
        return [query, f"{query} details", f"{query} relationships"]

    async def _fetch_vector(self, query: str, limit: int):
        # Mock
        return [{"source": "vector", "score": 0.9, "content": "Vector chunk"}]

    async def _fetch_graph(self, query: str, limit: int):
        # Mock
        return [{"source": "graph", "score": 0.85, "content": "Graph triple"}]

    async def _fetch_sparse(self, query: str, limit: int):
        # Mock
        return [{"source": "bm25", "score": 0.7, "content": "BM25 keyword match"}]

    def _fuse_results(self, *result_sets) -> list[dict[str, Any]]:
        # Simplified RRF mock
        combined = []
        for rset in result_sets:
            if isinstance(rset, list):
                combined.extend(rset)
        return combined

    def _rerank(self, query: str, results: list[dict[str, Any]], limit: int):
        # Mock rerank (just sort by score for now)
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:limit]
