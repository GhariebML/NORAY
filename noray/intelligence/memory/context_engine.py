"""
NORAY — Context Engine

Fuses inputs from multiple memory sources (retrieval, graph, profile).
Every step is optional — failure never terminates execution.

Uses the graceful RetrievalPipeline with automatic fallback chain:
Dense Vector → BM25 → Conversation Memory → LLM Only.
"""

from __future__ import annotations

import logging
from typing import Any

from noray.database import detect_database_engine, table_exists
from noray.intelligence.core.interfaces import IContextEngine
from noray.llm.memory_ranking import MemoryRanker
from noray.rag.retrieval_pipeline import build_pipeline_context
from noray.shared.profile_store import load_profile

logger = logging.getLogger("noray.intelligence.context")

_GRAPH_TABLES = {"graph_nodes", "graph_edges"}


class ContextEngine(IContextEngine):
    """Gathers and ranks context from retrieval, graph search, and user profile.
    
    Every retrieval method is wrapped in try/except — failure of any single
    source never prevents the system from producing a response.
    """

    def __init__(self, memory_ranker: MemoryRanker | None = None):
        self.memory_ranker = memory_ranker or MemoryRanker()

    async def build_context(self, query: str, session_id: str) -> str:
        """
        Build a unified context string by gathering data from all available sources.
        
        Fallback order:
            1. RAG Retrieval (vector → BM25 → conversation memory → LLM only)
            2. Knowledge Graph (entity relationships)
            3. User Profile
            4. Memory Ranker consolidation
        
        Returns a context string. Never raises an exception.
        """
        parts: list[str] = []

        # 1. Run graceful retrieval pipeline
        retrieval_result = self._safe_retrieve(query, session_id)
        context = retrieval_result.get("context", "")
        user_notice = retrieval_result.get("user_notice", "")
        fallback_chain = retrieval_result.get("fallback_chain", [])

        if context:
            parts.append(context)

        # 2. Run Knowledge Graph enrichment (optional, never blocks)
        kg_facts = self._safe_graph_query(query, retrieval_result.get("chunks", []))
        if kg_facts:
            parts.append("\n=== Knowledge Graph Context ===\n" + "\n".join(kg_facts))

        # 3. Profile context (always available)
        profile_context = self._safe_profile_context()
        if profile_context:
            parts.append("\n=== User Profile ===\n" + profile_context)

        # 4. Consolidate with MemoryRanker
        combined = "\n\n".join(filter(None, parts))

        ranked = self._safe_rank(query, combined)
        if ranked:
            combined = ranked

        # Prepend user notice if retrieval was degraded
        if user_notice and not context:
            combined = f"[System Notice: {user_notice}]\n\n" + combined

        logger.info(
            f"Context built: len={len(combined)} fallback={' > '.join(fallback_chain) if fallback_chain else 'direct'} "
            f"notice={bool(user_notice)}"
        )

        return combined

    def _safe_retrieve(self, query: str, session_id: str) -> dict[str, Any]:
        """Run retrieval pipeline with full error isolation."""
        try:
            return build_pipeline_context(query=query, session_id=session_id)
        except Exception as e:
            logger.error(f"Retrieval pipeline crashed: {e}")
            return {
                "context": "",
                "chunks": [],
                "user_notice": "Knowledge source unavailable. Generating answer using available context.",
                "fallback_chain": ["pipeline_crash"],
            }

    def _safe_graph_query(
        self, query: str, chunks: list[dict[str, Any]]
    ) -> list[str]:
        """Query knowledge graph with engine-agnostic table checks."""
        try:
            # Check if graph tables exist in current database engine
            all_exist = all(table_exists(t) for t in _GRAPH_TABLES)
            if not all_exist:
                logger.debug("Graph tables not found — skipping graph enrichment")
                return []

            from noray.graph.extractor import EntityRelationExtractor
            from noray.graph.graph_rag import GraphRAGFuser
            from noray.graph.postgres_store import PostgresGraphStore

            store = PostgresGraphStore()
            extractor = EntityRelationExtractor(use_llm=False)
            fuser = GraphRAGFuser(graph_store=store, extractor=extractor)

            graph_enriched = fuser.enrich_context(query, chunks)
            triples = graph_enriched.get("graph_triples", [])
            return [f"  \u2022 {t}" for t in triples]

        except Exception as e:
            logger.debug(f"Graph enrichment skipped: {e}")
            return []

    def _safe_profile_context(self) -> str:
        """Load user profile context gracefully."""
        try:
            from noray.rag.memory import ProfileMemoryManager

            profile_data = load_profile()
            pm = ProfileMemoryManager(profile_data.model_dump())
            return pm.get_profile_summary_prompt()
        except Exception as e:
            logger.debug(f"Profile context unavailable: {e}")
            return ""

    def _safe_rank(self, query: str, context: str) -> str | None:
        """Rank and compress context using MemoryRanker."""
        try:
            if self.memory_ranker and context:
                return self.memory_ranker.rank_context(
                    query=query,
                    semantic_memories=[context],
                    kg_facts=[],
                    vector_hits=[],
                )
            return None
        except Exception as e:
            logger.debug(f"Memory ranking skipped: {e}")
            return None
