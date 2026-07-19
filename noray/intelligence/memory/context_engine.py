"""
NORAY — Context Engine
Fuses inputs from multiple memory sources (Working, Conversation, Semantic, Episodic, Procedural, Workspace).
Ranks and compresses the context to fit within the dynamically selected model's constraints.
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from noray.intelligence.core.interfaces import IContextEngine
from noray.llm.memory_ranking import MemoryRanker
from noray.shared.profile_store import load_profile
from noray.rag.memory import ProfileMemoryManager
from noray.graph.postgres_store import PostgresGraphStore
from noray.graph.extractor import EntityRelationExtractor
from noray.graph.graph_rag import GraphRAGFuser

logger = logging.getLogger("noray.intelligence.context")


class ContextEngine(IContextEngine):
    """Gathers and ranks context from vector search, graph search, and user profile."""
    
    def __init__(self, memory_ranker: Optional[MemoryRanker] = None):
        self.memory_ranker = memory_ranker or MemoryRanker()

    async def build_context(self, query: str, session_id: str) -> str:
        """
        Queries all active storage layers and combines them using MemoryRanker.
        """
        # 1. Fetch Profile context
        semantic_memories = []
        try:
            profile_data = load_profile()
            pm = ProfileMemoryManager(profile_data.model_dump())
            summary = pm.get_profile_summary_prompt()
            semantic_memories.append(summary)
        except Exception as e:
            logger.debug(f"Failed to fetch profile memory: {e}")

        # 2. Fetch Vector DB search hits
        vector_hits = []
        try:
            from noray.agents.agent_router import AgentRouter
            router_legacy = AgentRouter(session_id=session_id)
            vector_hits = router_legacy._retrieve_hybrid_context(query, filters={})
        except Exception as e:
            logger.debug(f"Failed to retrieve vector search context: {e}")

        # 3. Fetch Graph Context triples
        kg_facts = []
        try:
            store = PostgresGraphStore()
            extractor = EntityRelationExtractor(use_llm=False)
            fuser = GraphRAGFuser(graph_store=store, extractor=extractor)
            graph_enriched = fuser.enrich_context(query, vector_hits)
            triples = graph_enriched.get("graph_triples", [])
            for t in triples:
                kg_facts.append(f"{t.get('subject')} -- {t.get('relation')} -> {t.get('object')}")
        except Exception as e:
            logger.debug(f"Failed to fetch graph context: {e}")

        # 4. Invoke memory ranker
        return self.memory_ranker.rank_context(
            query=query,
            semantic_memories=semantic_memories,
            kg_facts=kg_facts,
            vector_hits=vector_hits
        )
