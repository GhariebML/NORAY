"""
NORAY — PostgreSQL Knowledge Graph Store

Implements BaseGraphStore using PostgreSQL as the storage backend.
Uses SQLAlchemy ORM for table definitions and queries, sharing the same
engine/session configuration as the rest of the NORAY platform.

Design Decisions:
    - Uses the existing `noray.database` engine and session factory to avoid
      creating a second connection pool.
    - Graph tables (graph_nodes, graph_edges) are defined as SQLAlchemy models
      registered with the shared `Base`, so they participate in the same
      `create_all()` migration lifecycle.
    - Multi-hop traversal uses recursive CTEs for PostgreSQL and iterative
      Python loops for SQLite (development fallback).
    - Bulk operations use `session.bulk_save_objects()` for throughput.

Future Migration Path:
    To evolve to Apache AGE or Neo4j, implement a new class inheriting from
    BaseGraphStore and swap via dependency injection. No business logic changes.
"""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import Column, String, Float, Text, DateTime, func, Index, and_, or_
from sqlalchemy.orm import Session

from noray.database import Base, SessionLocal
from noray.graph.base import BaseGraphStore, GraphNode, GraphEdge


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models for Graph Tables
# ---------------------------------------------------------------------------

class GraphNodeModel(Base):
    """Relational model for Knowledge Graph entity nodes."""
    __tablename__ = "graph_nodes"

    id = Column(String(36), primary_key=True)
    name = Column(String(512), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    properties = Column(Text, nullable=False, default="{}")  # JSON-encoded
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Composite index for type+name lookups
    __table_args__ = (
        Index("ix_graph_nodes_type_name", "type", "name"),
    )


class GraphEdgeModel(Base):
    """Relational model for Knowledge Graph relationship edges."""
    __tablename__ = "graph_edges"

    id = Column(String(36), primary_key=True)
    source_id = Column(String(36), nullable=False, index=True)
    target_id = Column(String(36), nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    properties = Column(Text, nullable=False, default="{}")  # JSON-encoded
    created_at = Column(DateTime, default=func.now())

    # Composite indexes for traversal queries
    __table_args__ = (
        Index("ix_graph_edges_source_type", "source_id", "type"),
        Index("ix_graph_edges_target_type", "target_id", "type"),
    )


# ---------------------------------------------------------------------------
# Conversion Helpers
# ---------------------------------------------------------------------------

def _node_model_to_domain(model: GraphNodeModel) -> GraphNode:
    """Convert ORM model to domain dataclass."""
    props = {}
    if model.properties:
        try:
            props = json.loads(model.properties)
        except (json.JSONDecodeError, TypeError):
            props = {}

    return GraphNode(
        id=model.id,
        name=model.name,
        type=model.type,
        properties=props,
        created_at=model.created_at.isoformat() if model.created_at else "",
        updated_at=model.updated_at.isoformat() if model.updated_at else "",
    )


def _edge_model_to_domain(model: GraphEdgeModel) -> GraphEdge:
    """Convert ORM model to domain dataclass."""
    props = {}
    if model.properties:
        try:
            props = json.loads(model.properties)
        except (json.JSONDecodeError, TypeError):
            props = {}

    return GraphEdge(
        id=model.id,
        source_id=model.source_id,
        target_id=model.target_id,
        type=model.type,
        weight=model.weight,
        properties=props,
        created_at=model.created_at.isoformat() if model.created_at else "",
    )


# ---------------------------------------------------------------------------
# PostgreSQL Graph Store Implementation
# ---------------------------------------------------------------------------

class PostgresGraphStore(BaseGraphStore):
    """Knowledge Graph store backed by PostgreSQL (or SQLite for dev).

    Uses the shared NORAY database engine and session factory.
    Supports dependency-injected sessions for testability.
    """

    def __init__(self, session_factory=None):
        """
        Args:
            session_factory: Callable that returns a new SQLAlchemy Session.
                             Defaults to noray.database.SessionLocal.
        """
        self._session_factory = session_factory or SessionLocal

    def _get_session(self) -> Session:
        return self._session_factory()

    # --- Node CRUD ---

    def add_node(self, node: GraphNode) -> GraphNode:
        session = self._get_session()
        try:
            existing = session.query(GraphNodeModel).filter_by(id=node.id).first()
            if existing:
                existing.name = node.name
                existing.type = node.type
                existing.properties = json.dumps(node.properties)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                model = GraphNodeModel(
                    id=node.id,
                    name=node.name,
                    type=node.type,
                    properties=json.dumps(node.properties),
                )
                session.add(model)
            session.commit()

            persisted = session.query(GraphNodeModel).filter_by(id=node.id).first()
            return _node_model_to_domain(persisted)
        finally:
            session.close()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        session = self._get_session()
        try:
            model = session.query(GraphNodeModel).filter_by(id=node_id).first()
            return _node_model_to_domain(model) if model else None
        finally:
            session.close()

    def find_nodes(
        self,
        *,
        name: Optional[str] = None,
        node_type: Optional[str] = None,
        properties_filter: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[GraphNode]:
        session = self._get_session()
        try:
            query = session.query(GraphNodeModel)

            if node_type:
                query = query.filter(GraphNodeModel.type == node_type)
            if name:
                # Case-insensitive partial match
                query = query.filter(GraphNodeModel.name.ilike(f"%{name}%"))

            results = query.limit(limit).all()

            nodes = [_node_model_to_domain(m) for m in results]

            # Post-filter by properties if requested
            if properties_filter:
                filtered = []
                for n in nodes:
                    match = all(
                        n.properties.get(k) == v
                        for k, v in properties_filter.items()
                    )
                    if match:
                        filtered.append(n)
                nodes = filtered

            return nodes
        finally:
            session.close()

    def update_node(self, node: GraphNode) -> GraphNode:
        session = self._get_session()
        try:
            model = session.query(GraphNodeModel).filter_by(id=node.id).first()
            if not model:
                raise ValueError(f"Node {node.id} not found")
            model.name = node.name
            model.type = node.type
            model.properties = json.dumps(node.properties)
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            return _node_model_to_domain(model)
        finally:
            session.close()

    def delete_node(self, node_id: str) -> bool:
        session = self._get_session()
        try:
            # Delete all connected edges first (cascade)
            session.query(GraphEdgeModel).filter(
                or_(
                    GraphEdgeModel.source_id == node_id,
                    GraphEdgeModel.target_id == node_id,
                )
            ).delete(synchronize_session=False)

            deleted = session.query(GraphNodeModel).filter_by(id=node_id).delete(
                synchronize_session=False
            )
            session.commit()
            return deleted > 0
        finally:
            session.close()

    # --- Edge CRUD ---

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        session = self._get_session()
        try:
            existing = session.query(GraphEdgeModel).filter_by(id=edge.id).first()
            if existing:
                existing.source_id = edge.source_id
                existing.target_id = edge.target_id
                existing.type = edge.type
                existing.weight = edge.weight
                existing.properties = json.dumps(edge.properties)
            else:
                model = GraphEdgeModel(
                    id=edge.id,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    type=edge.type,
                    weight=edge.weight,
                    properties=json.dumps(edge.properties),
                )
                session.add(model)
            session.commit()

            persisted = session.query(GraphEdgeModel).filter_by(id=edge.id).first()
            return _edge_model_to_domain(persisted)
        finally:
            session.close()

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        session = self._get_session()
        try:
            model = session.query(GraphEdgeModel).filter_by(id=edge_id).first()
            return _edge_model_to_domain(model) if model else None
        finally:
            session.close()

    def find_edges(
        self,
        *,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        edge_type: Optional[str] = None,
        min_weight: float = 0.0,
        limit: int = 100,
    ) -> List[GraphEdge]:
        session = self._get_session()
        try:
            query = session.query(GraphEdgeModel)

            if source_id:
                query = query.filter(GraphEdgeModel.source_id == source_id)
            if target_id:
                query = query.filter(GraphEdgeModel.target_id == target_id)
            if edge_type:
                query = query.filter(GraphEdgeModel.type == edge_type)
            if min_weight > 0.0:
                query = query.filter(GraphEdgeModel.weight >= min_weight)

            results = query.limit(limit).all()
            return [_edge_model_to_domain(m) for m in results]
        finally:
            session.close()

    def delete_edge(self, edge_id: str) -> bool:
        session = self._get_session()
        try:
            deleted = session.query(GraphEdgeModel).filter_by(id=edge_id).delete(
                synchronize_session=False
            )
            session.commit()
            return deleted > 0
        finally:
            session.close()

    # --- Graph Traversal ---

    def get_neighbors(
        self,
        node_id: str,
        *,
        edge_type: Optional[str] = None,
        direction: str = "both",
        max_hops: int = 1,
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        """BFS traversal up to max_hops from the starting node."""
        session = self._get_session()
        try:
            visited_nodes: Set[str] = {node_id}
            result: List[Tuple[GraphNode, GraphEdge]] = []
            frontier: deque = deque([node_id])
            current_hop = 0

            while frontier and current_hop < max_hops:
                next_frontier: List[str] = []
                batch_size = len(frontier)

                for _ in range(batch_size):
                    current_id = frontier.popleft()

                    # Build edge query based on direction
                    edge_query = session.query(GraphEdgeModel)
                    if direction == "outgoing":
                        edge_query = edge_query.filter(
                            GraphEdgeModel.source_id == current_id
                        )
                    elif direction == "incoming":
                        edge_query = edge_query.filter(
                            GraphEdgeModel.target_id == current_id
                        )
                    else:  # "both"
                        edge_query = edge_query.filter(
                            or_(
                                GraphEdgeModel.source_id == current_id,
                                GraphEdgeModel.target_id == current_id,
                            )
                        )

                    if edge_type:
                        edge_query = edge_query.filter(
                            GraphEdgeModel.type == edge_type
                        )

                    edges = edge_query.all()

                    for edge_model in edges:
                        # Determine the neighbor node ID
                        neighbor_id = (
                            edge_model.target_id
                            if edge_model.source_id == current_id
                            else edge_model.source_id
                        )

                        if neighbor_id not in visited_nodes:
                            visited_nodes.add(neighbor_id)
                            node_model = (
                                session.query(GraphNodeModel)
                                .filter_by(id=neighbor_id)
                                .first()
                            )
                            if node_model:
                                result.append((
                                    _node_model_to_domain(node_model),
                                    _edge_model_to_domain(edge_model),
                                ))
                                next_frontier.append(neighbor_id)

                frontier.extend(next_frontier)
                current_hop += 1

            return result
        finally:
            session.close()

    def get_subgraph(
        self,
        node_ids: List[str],
        *,
        max_hops: int = 1,
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Extract a subgraph around a set of seed node IDs."""
        all_nodes: Dict[str, GraphNode] = {}
        all_edges: Dict[str, GraphEdge] = {}

        for seed_id in node_ids:
            # Include the seed node itself
            seed_node = self.get_node(seed_id)
            if seed_node:
                all_nodes[seed_node.id] = seed_node

            # Get neighbors
            neighbors = self.get_neighbors(seed_id, max_hops=max_hops)
            for node, edge in neighbors:
                all_nodes[node.id] = node
                all_edges[edge.id] = edge

        return list(all_nodes.values()), list(all_edges.values())

    # --- Bulk Operations ---

    def add_nodes_bulk(self, nodes: List[GraphNode]) -> int:
        session = self._get_session()
        try:
            models = [
                GraphNodeModel(
                    id=n.id,
                    name=n.name,
                    type=n.type,
                    properties=json.dumps(n.properties),
                )
                for n in nodes
            ]
            session.bulk_save_objects(models)
            session.commit()
            return len(models)
        finally:
            session.close()

    def add_edges_bulk(self, edges: List[GraphEdge]) -> int:
        session = self._get_session()
        try:
            models = [
                GraphEdgeModel(
                    id=e.id,
                    source_id=e.source_id,
                    target_id=e.target_id,
                    type=e.type,
                    weight=e.weight,
                    properties=json.dumps(e.properties),
                )
                for e in edges
            ]
            session.bulk_save_objects(models)
            session.commit()
            return len(models)
        finally:
            session.close()

    # --- Statistics ---

    def count_nodes(self, node_type: Optional[str] = None) -> int:
        session = self._get_session()
        try:
            query = session.query(GraphNodeModel)
            if node_type:
                query = query.filter(GraphNodeModel.type == node_type)
            return query.count()
        finally:
            session.close()

    def count_edges(self, edge_type: Optional[str] = None) -> int:
        session = self._get_session()
        try:
            query = session.query(GraphEdgeModel)
            if edge_type:
                query = query.filter(GraphEdgeModel.type == edge_type)
            return query.count()
        finally:
            session.close()
