"""
NORAY — Graph RAG Fuser

Implements hybrid retrieval that combines:
    1. Vector Search (Qdrant / FAISS) — semantic similarity matching.
    2. Graph Search (Knowledge Graph) — entity relationship traversal.

The fusion strategy enriches standard RAG chunks with structured knowledge
graph context, enabling the LLM to reason over entity connections rather
than isolated text fragments.

Architecture:
    1. Standard RAG retrieval produces a set of candidate chunks.
    2. Entity extraction identifies mentioned entities in the query.
    3. Graph traversal (1–2 hops) pulls connected nodes and edges.
    4. Graph context is formatted as relationship triples and appended
       to the retrieval context.
    5. The combined context (chunks + graph triples) is passed to the LLM.

Design Decisions:
    - Graph context is formatted as human-readable triples, not raw JSON,
      so the LLM can naturally reason over them.
    - Deduplication ensures graph facts already present in vector chunks
      are not repeated.
    - The fuser is stateless — it receives store instances via DI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from noray.graph.base import BaseGraphStore, GraphNode, GraphEdge
from noray.graph.extractor import EntityRelationExtractor


class GraphRAGFuser:
    """Fuses vector retrieval results with Knowledge Graph context.

    This is the core component that transforms standard RAG into Graph RAG.
    It takes vector search hits, extracts entities from the query, traverses
    the Knowledge Graph around those entities, and produces an enriched
    context combining both sources.

    Args:
        graph_store: A BaseGraphStore implementation (injected).
        extractor: An EntityRelationExtractor instance (injected).
        max_hops: Maximum graph traversal depth (default: 2).
        max_graph_triples: Maximum number of graph triples to include (default: 20).
    """

    def __init__(
        self,
        graph_store: BaseGraphStore,
        extractor: Optional[EntityRelationExtractor] = None,
        max_hops: int = 2,
        max_graph_triples: int = 20,
    ):
        self.graph_store = graph_store
        self.extractor = extractor or EntityRelationExtractor(use_llm=False)
        self.max_hops = max_hops
        self.max_graph_triples = max_graph_triples

    def enrich_context(
        self,
        query: str,
        vector_hits: List[Dict[str, Any]],
        *,
        include_graph_summary: bool = True,
    ) -> Dict[str, Any]:
        """Enrich RAG retrieval results with graph-derived context.

        Args:
            query: The user's original query.
            vector_hits: Standard vector search results
                (list of dicts with "id", "score", "payload", optional "content").
            include_graph_summary: Whether to include a natural language
                summary of graph relationships.

        Returns:
            Dict containing:
                - "chunks": Original vector hits (unmodified).
                - "graph_nodes": List of relevant graph node dicts.
                - "graph_edges": List of relevant graph edge dicts.
                - "graph_triples": Human-readable relationship triples.
                - "combined_context": Merged context string for LLM prompt.
                - "entity_mentions": Entities extracted from the query.
        """
        # Step 1: Extract entities from the query
        query_entities, _ = self.extractor.extract(query)
        entity_names = [e.name for e in query_entities]

        # Step 2: Also extract entities from vector hit contents
        hit_entity_names = set()
        for hit in vector_hits:
            content = hit.get("content") or hit.get("payload", {}).get("content", "")
            if content:
                hit_entities, _ = self.extractor.extract(content[:500])
                for e in hit_entities:
                    hit_entity_names.add(e.name)

        # Step 3: Find matching graph nodes for extracted entities
        seed_node_ids: List[str] = []
        all_query_entities = list(set(entity_names) | hit_entity_names)

        for entity_name in all_query_entities:
            matching_nodes = self.graph_store.find_nodes(
                name=entity_name, limit=3
            )
            for node in matching_nodes:
                seed_node_ids.append(node.id)

        # Step 4: Traverse graph around seed nodes
        graph_nodes: List[GraphNode] = []
        graph_edges: List[GraphEdge] = []

        if seed_node_ids:
            graph_nodes, graph_edges = self.graph_store.get_subgraph(
                node_ids=seed_node_ids[:10],  # Cap seed nodes to avoid explosion
                max_hops=self.max_hops,
            )

        # Step 5: Format graph triples as human-readable text
        triples = self._format_triples(graph_nodes, graph_edges)

        # Step 6: Build combined context
        combined_context = self._build_combined_context(
            vector_hits, triples, include_graph_summary
        )

        return {
            "chunks": vector_hits,
            "graph_nodes": [n.to_dict() for n in graph_nodes],
            "graph_edges": [e.to_dict() for e in graph_edges],
            "graph_triples": triples,
            "combined_context": combined_context,
            "entity_mentions": all_query_entities,
        }

    def _format_triples(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
    ) -> List[str]:
        """Format graph relationships as human-readable triples.

        Example output:
            "Python [Skill] --REQUIRED_FOR--> Machine Learning Engineer [Role]"
        """
        node_map = {n.id: n for n in nodes}
        triples: List[str] = []

        for edge in edges:
            source = node_map.get(edge.source_id)
            target = node_map.get(edge.target_id)

            if source and target:
                triple = (
                    f"{source.name} [{source.type}] "
                    f"--{edge.type}--> "
                    f"{target.name} [{target.type}]"
                )
                triples.append(triple)

        # Cap at max_graph_triples to avoid context overflow
        return triples[: self.max_graph_triples]

    def _build_combined_context(
        self,
        vector_hits: List[Dict[str, Any]],
        triples: List[str],
        include_summary: bool,
    ) -> str:
        """Build a unified context string combining vector chunks and graph facts."""
        parts: List[str] = []

        # Section 1: Retrieved Document Chunks
        if vector_hits:
            parts.append("=== Retrieved Document Context ===")
            for idx, hit in enumerate(vector_hits, 1):
                content = hit.get("content") or hit.get("payload", {}).get("content", "")
                source = hit.get("payload", {}).get("source", "Unknown")
                score = hit.get("score", 0.0)
                parts.append(
                    f"[Chunk {idx} | Source: {source} | Relevance: {score:.3f}]\n{content}"
                )

        # Section 2: Knowledge Graph Relationships
        if triples:
            parts.append("\n=== Knowledge Graph Relationships ===")
            parts.append(
                "The following structured relationships were found in the Knowledge Graph:"
            )
            for triple in triples:
                parts.append(f"  • {triple}")

            if include_summary:
                parts.append(
                    "\nUse these relationships to reason about connections between "
                    "entities mentioned in the query."
                )

        return "\n".join(parts)

    def search_graph_only(
        self,
        query: str,
        *,
        max_hops: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Search the Knowledge Graph only (no vector search).

        Useful for exploring entity connections, e.g.:
            "What skills are required for Machine Learning Engineer?"

        Args:
            query: Natural language query.
            max_hops: Override for traversal depth.

        Returns:
            Dict with graph_nodes, graph_edges, and graph_triples.
        """
        hops = max_hops or self.max_hops

        # Extract entities from query
        entities, _ = self.extractor.extract(query)

        seed_ids: List[str] = []
        for entity in entities:
            matches = self.graph_store.find_nodes(name=entity.name, limit=3)
            for m in matches:
                seed_ids.append(m.id)

        if not seed_ids:
            return {
                "graph_nodes": [],
                "graph_edges": [],
                "graph_triples": [],
            }

        nodes, edges = self.graph_store.get_subgraph(
            node_ids=seed_ids[:10], max_hops=hops
        )
        triples = self._format_triples(nodes, edges)

        return {
            "graph_nodes": [n.to_dict() for n in nodes],
            "graph_edges": [e.to_dict() for e in edges],
            "graph_triples": triples,
        }
