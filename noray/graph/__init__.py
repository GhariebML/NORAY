"""
NORAY — Knowledge Graph Package

Provides a semantic Knowledge Graph layer for entity-relationship reasoning.
Supports Graph RAG: combining vector search with graph traversal for enriched
context retrieval.

Architecture:
    BaseGraphStore (abstract) ← PostgresGraphStore (default)
                               ← Future: Neo4jGraphStore, ApacheAGEGraphStore

The abstraction interface ensures the business logic is decoupled from the
storage backend, allowing migration to Neo4j or Apache AGE without changing
any calling code.
"""

from noray.graph.base import BaseGraphStore, GraphNode, GraphEdge
from noray.graph.postgres_store import PostgresGraphStore
from noray.graph.extractor import EntityRelationExtractor
from noray.graph.graph_rag import GraphRAGFuser

__all__ = [
    "BaseGraphStore",
    "GraphNode",
    "GraphEdge",
    "PostgresGraphStore",
    "EntityRelationExtractor",
    "GraphRAGFuser",
]
