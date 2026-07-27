"""
NORAY — Knowledge Graph Abstract Base Interface

Defines the contract that all graph store backends must implement.
This abstraction allows the platform to evolve from PostgreSQL-backed
graph storage to Apache AGE, Neo4j, or any future graph database
without modifying business logic or calling code.

Design Decisions:
    - GraphNode and GraphEdge are plain dataclasses (not ORM-coupled) so they
      can be serialized, transported across services, and used in tests without
      a database connection.
    - The BaseGraphStore uses the Repository Pattern with explicit CRUD methods
      and graph traversal primitives (neighbors, shortest_path, subgraph).
    - All methods accept and return domain objects, never raw SQL rows.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Domain Value Objects
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    """Represents an entity node in the Knowledge Graph.

    Attributes:
        id: Unique identifier (UUID string).
        name: Human-readable label (e.g. "Python", "DAAD Scholarship").
        type: Entity category. One of: Skill, University, Scholarship, Company,
              Country, ResearchTopic, Project, Certificate, Technology, Role,
              JobRequirement, Applicant, Document.
        properties: Arbitrary key-value metadata bag.
        created_at: Timestamp of creation (UTC).
        updated_at: Timestamp of last modification (UTC).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphNode:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=data.get("type", ""),
            properties=data.get("properties", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )


@dataclass
class GraphEdge:
    """Represents a directed relationship edge between two nodes.

    Attributes:
        id: Unique identifier (UUID string).
        source_id: ID of the origin node.
        target_id: ID of the destination node.
        type: Relationship label (e.g. "REQUIRED_FOR", "LOCATED_IN", "OFFERED_BY").
        weight: Numeric strength/confidence of the relationship (0.0 – 1.0).
        properties: Arbitrary key-value metadata bag.
        created_at: Timestamp of creation (UTC).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    type: str = ""
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEdge:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            source_id=data.get("source_id", ""),
            target_id=data.get("target_id", ""),
            type=data.get("type", ""),
            weight=data.get("weight", 1.0),
            properties=data.get("properties", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )


# ---------------------------------------------------------------------------
# Supported Entity and Relationship Types (constants for validation)
# ---------------------------------------------------------------------------

ENTITY_TYPES: set[str] = {
    "Skill",
    "University",
    "Scholarship",
    "Company",
    "Country",
    "ResearchTopic",
    "Project",
    "Certificate",
    "Technology",
    "Role",
    "JobRequirement",
    "Applicant",
    "Document",
}

RELATIONSHIP_TYPES: set[str] = {
    "REQUIRED_FOR",       # Skill -> Role / JobRequirement
    "LOCATED_IN",         # University / Company / Scholarship -> Country
    "OFFERED_BY",         # Scholarship / Role -> University / Company
    "PREREQUISITE_OF",    # Skill -> Skill / Certificate -> Role
    "PART_OF",            # Technology -> Project / Skill -> ResearchTopic
    "RELATED_TO",         # Generic semantic similarity link
    "APPLIED_TO",         # Applicant -> Scholarship / Role
    "AUTHORED",           # Applicant -> Document / Project
    "FUNDED_BY",          # Scholarship -> Company / Country
    "TEACHES",            # University -> Skill / ResearchTopic
    "CERTIFIES",          # Certificate -> Skill
    "MENTIONS",           # Document -> Skill / University / Scholarship
    "RESEARCHES",         # Applicant / University -> ResearchTopic
    "EMPLOYS",            # Company -> Role
}


# ---------------------------------------------------------------------------
# Abstract Graph Store Interface
# ---------------------------------------------------------------------------

class BaseGraphStore(ABC):
    """Abstract interface for Knowledge Graph storage backends.

    All concrete implementations (PostgresGraphStore, Neo4jGraphStore, etc.)
    must implement every method in this class.  Business logic interacts
    exclusively through this interface, guaranteeing backend portability.
    """

    # --- Node CRUD ---

    @abstractmethod
    def add_node(self, node: GraphNode) -> GraphNode:
        """Insert or upsert a node.  Returns the persisted node."""
        ...

    @abstractmethod
    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a single node by its ID, or None if not found."""
        ...

    @abstractmethod
    def find_nodes(
        self,
        *,
        name: str | None = None,
        node_type: str | None = None,
        properties_filter: dict[str, Any] | None = None,
        limit: int = 50,
    ) -> list[GraphNode]:
        """Search for nodes matching given criteria."""
        ...

    @abstractmethod
    def update_node(self, node: GraphNode) -> GraphNode:
        """Update an existing node's name, type, or properties."""
        ...

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and all connected edges.  Returns True if deleted."""
        ...

    # --- Edge CRUD ---

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Insert or upsert an edge.  Returns the persisted edge."""
        ...

    @abstractmethod
    def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Retrieve a single edge by its ID."""
        ...

    @abstractmethod
    def find_edges(
        self,
        *,
        source_id: str | None = None,
        target_id: str | None = None,
        edge_type: str | None = None,
        min_weight: float = 0.0,
        limit: int = 100,
    ) -> list[GraphEdge]:
        """Search for edges matching given criteria."""
        ...

    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge.  Returns True if deleted."""
        ...

    # --- Graph Traversal ---

    @abstractmethod
    def get_neighbors(
        self,
        node_id: str,
        *,
        edge_type: str | None = None,
        direction: str = "both",  # "outgoing", "incoming", "both"
        max_hops: int = 1,
    ) -> list[tuple[GraphNode, GraphEdge]]:
        """Return neighboring nodes and their connecting edges.

        Args:
            node_id: Starting node.
            edge_type: Optional filter for edge relationship type.
            direction: "outgoing", "incoming", or "both".
            max_hops: Number of hops (1 = direct neighbors, 2 = two-hop, etc.).
        """
        ...

    @abstractmethod
    def get_subgraph(
        self,
        node_ids: list[str],
        *,
        max_hops: int = 1,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Extract a subgraph around a set of seed nodes.

        Returns all nodes and edges reachable within max_hops.
        """
        ...

    # --- Bulk Operations ---

    @abstractmethod
    def add_nodes_bulk(self, nodes: list[GraphNode]) -> int:
        """Bulk insert nodes.  Returns count of inserted nodes."""
        ...

    @abstractmethod
    def add_edges_bulk(self, edges: list[GraphEdge]) -> int:
        """Bulk insert edges.  Returns count of inserted edges."""
        ...

    # --- Statistics ---

    @abstractmethod
    def count_nodes(self, node_type: str | None = None) -> int:
        """Count nodes, optionally filtered by type."""
        ...

    @abstractmethod
    def count_edges(self, edge_type: str | None = None) -> int:
        """Count edges, optionally filtered by type."""
        ...
