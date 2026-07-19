"""
NORAY — Knowledge Graph Unit Tests

Tests the full graph layer: domain objects, PostgreSQL store (using SQLite
for test isolation), entity extraction, and Graph RAG fusion.
"""

import os
import pytest
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from noray.database import Base
from noray.graph.base import GraphNode, GraphEdge, ENTITY_TYPES, RELATIONSHIP_TYPES
from noray.graph.postgres_store import (
    PostgresGraphStore,
    GraphNodeModel,
    GraphEdgeModel,
)
from noray.graph.extractor import EntityRelationExtractor
from noray.graph.graph_rag import GraphRAGFuser


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_engine():
    """Create an in-memory SQLite engine for test isolation."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_session_factory(test_engine):
    """Session factory bound to the in-memory test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def graph_store(test_session_factory):
    """PostgresGraphStore wired to the in-memory test database."""
    return PostgresGraphStore(session_factory=test_session_factory)


@pytest.fixture
def extractor():
    """EntityRelationExtractor with LLM disabled for deterministic tests."""
    return EntityRelationExtractor(use_llm=False)


@pytest.fixture
def graph_rag_fuser(graph_store, extractor):
    """GraphRAGFuser wired to test graph store and rule-based extractor."""
    return GraphRAGFuser(graph_store=graph_store, extractor=extractor)


@pytest.fixture
def sample_nodes() -> List[GraphNode]:
    """A small knowledge graph with skills, roles, companies, and countries."""
    return [
        GraphNode(id="n1", name="Python", type="Technology"),
        GraphNode(id="n2", name="Machine Learning", type="Skill"),
        GraphNode(id="n3", name="ML Engineer", type="Role"),
        GraphNode(id="n4", name="Google", type="Company"),
        GraphNode(id="n5", name="United States", type="Country"),
        GraphNode(id="n6", name="TensorFlow", type="Technology"),
        GraphNode(id="n7", name="Deep Learning", type="Skill"),
        GraphNode(id="n8", name="DAAD Scholarship", type="Scholarship"),
        GraphNode(id="n9", name="Germany", type="Country"),
        GraphNode(id="n10", name="Technical University of Munich", type="University"),
    ]


@pytest.fixture
def sample_edges() -> List[GraphEdge]:
    """Relationships connecting the sample nodes."""
    return [
        GraphEdge(id="e1", source_id="n1", target_id="n3", type="REQUIRED_FOR", weight=0.9),
        GraphEdge(id="e2", source_id="n2", target_id="n3", type="REQUIRED_FOR", weight=0.95),
        GraphEdge(id="e3", source_id="n4", target_id="n3", type="EMPLOYS", weight=1.0),
        GraphEdge(id="e4", source_id="n4", target_id="n5", type="LOCATED_IN", weight=1.0),
        GraphEdge(id="e5", source_id="n6", target_id="n2", type="PART_OF", weight=0.8),
        GraphEdge(id="e6", source_id="n7", target_id="n2", type="RELATED_TO", weight=0.85),
        GraphEdge(id="e7", source_id="n8", target_id="n9", type="LOCATED_IN", weight=1.0),
        GraphEdge(id="e8", source_id="n8", target_id="n10", type="OFFERED_BY", weight=0.9),
        GraphEdge(id="e9", source_id="n10", target_id="n9", type="LOCATED_IN", weight=1.0),
        GraphEdge(id="e10", source_id="n1", target_id="n6", type="RELATED_TO", weight=0.7),
    ]


@pytest.fixture
def populated_store(graph_store, sample_nodes, sample_edges):
    """Graph store pre-populated with sample data."""
    graph_store.add_nodes_bulk(sample_nodes)
    graph_store.add_edges_bulk(sample_edges)
    return graph_store


# ---------------------------------------------------------------------------
# Domain Object Tests
# ---------------------------------------------------------------------------

class TestGraphDomainObjects:
    def test_graph_node_creation(self):
        node = GraphNode(name="Python", type="Technology")
        assert node.name == "Python"
        assert node.type == "Technology"
        assert len(node.id) == 36  # UUID format

    def test_graph_node_serialization(self):
        node = GraphNode(id="test-id", name="React", type="Technology", properties={"version": "18"})
        d = node.to_dict()
        assert d["id"] == "test-id"
        assert d["properties"]["version"] == "18"

        restored = GraphNode.from_dict(d)
        assert restored.name == "React"
        assert restored.properties["version"] == "18"

    def test_graph_edge_creation(self):
        edge = GraphEdge(source_id="a", target_id="b", type="REQUIRED_FOR", weight=0.9)
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.weight == 0.9

    def test_entity_types_defined(self):
        assert "Skill" in ENTITY_TYPES
        assert "University" in ENTITY_TYPES
        assert "Scholarship" in ENTITY_TYPES
        assert len(ENTITY_TYPES) >= 12

    def test_relationship_types_defined(self):
        assert "REQUIRED_FOR" in RELATIONSHIP_TYPES
        assert "LOCATED_IN" in RELATIONSHIP_TYPES
        assert "OFFERED_BY" in RELATIONSHIP_TYPES
        assert len(RELATIONSHIP_TYPES) >= 10


# ---------------------------------------------------------------------------
# PostgreSQL Graph Store Tests
# ---------------------------------------------------------------------------

class TestPostgresGraphStore:
    def test_add_and_get_node(self, graph_store):
        node = GraphNode(name="FastAPI", type="Technology")
        persisted = graph_store.add_node(node)
        assert persisted.name == "FastAPI"

        retrieved = graph_store.get_node(node.id)
        assert retrieved is not None
        assert retrieved.name == "FastAPI"
        assert retrieved.type == "Technology"

    def test_upsert_node(self, graph_store):
        node = GraphNode(id="upsert-test", name="React", type="Technology")
        graph_store.add_node(node)

        node.name = "React.js"
        node.properties = {"version": "19"}
        graph_store.add_node(node)

        retrieved = graph_store.get_node("upsert-test")
        assert retrieved.name == "React.js"
        assert retrieved.properties.get("version") == "19"

    def test_find_nodes_by_type(self, populated_store):
        skills = populated_store.find_nodes(node_type="Skill")
        assert len(skills) == 2  # Machine Learning, Deep Learning

    def test_find_nodes_by_name(self, populated_store):
        results = populated_store.find_nodes(name="Python")
        assert len(results) >= 1
        assert results[0].name == "Python"

    def test_find_nodes_partial_match(self, populated_store):
        results = populated_store.find_nodes(name="learn")
        assert len(results) >= 1  # Machine Learning, Deep Learning

    def test_update_node(self, graph_store):
        node = GraphNode(id="upd-1", name="Old Name", type="Skill")
        graph_store.add_node(node)

        node.name = "New Name"
        node.properties = {"level": "expert"}
        updated = graph_store.update_node(node)
        assert updated.name == "New Name"
        assert updated.properties["level"] == "expert"

    def test_delete_node_cascades_edges(self, graph_store):
        n1 = GraphNode(id="del-n1", name="A", type="Skill")
        n2 = GraphNode(id="del-n2", name="B", type="Role")
        graph_store.add_node(n1)
        graph_store.add_node(n2)

        edge = GraphEdge(id="del-e1", source_id="del-n1", target_id="del-n2", type="REQUIRED_FOR")
        graph_store.add_edge(edge)

        assert graph_store.delete_node("del-n1")
        assert graph_store.get_node("del-n1") is None
        assert graph_store.get_edge("del-e1") is None  # Cascade delete

    def test_add_and_get_edge(self, graph_store):
        n1 = GraphNode(id="eg-n1", name="Python", type="Technology")
        n2 = GraphNode(id="eg-n2", name="Backend Dev", type="Role")
        graph_store.add_node(n1)
        graph_store.add_node(n2)

        edge = GraphEdge(source_id="eg-n1", target_id="eg-n2", type="REQUIRED_FOR", weight=0.85)
        persisted = graph_store.add_edge(edge)
        assert persisted.type == "REQUIRED_FOR"

        retrieved = graph_store.get_edge(edge.id)
        assert retrieved is not None
        assert retrieved.weight == 0.85

    def test_find_edges_by_source(self, populated_store):
        edges = populated_store.find_edges(source_id="n1")
        assert len(edges) >= 2  # Python -> ML Engineer, Python -> TensorFlow

    def test_find_edges_by_type(self, populated_store):
        edges = populated_store.find_edges(edge_type="LOCATED_IN")
        assert len(edges) >= 3  # Google->US, DAAD->Germany, TUM->Germany

    def test_delete_edge(self, graph_store):
        n1 = GraphNode(id="de-n1", name="X", type="Skill")
        n2 = GraphNode(id="de-n2", name="Y", type="Role")
        graph_store.add_node(n1)
        graph_store.add_node(n2)

        edge = GraphEdge(id="de-e1", source_id="de-n1", target_id="de-n2", type="RELATED_TO")
        graph_store.add_edge(edge)

        assert graph_store.delete_edge("de-e1")
        assert graph_store.get_edge("de-e1") is None

    def test_bulk_operations(self, graph_store):
        nodes = [GraphNode(id=f"bulk-{i}", name=f"Node {i}", type="Skill") for i in range(50)]
        count = graph_store.add_nodes_bulk(nodes)
        assert count == 50
        assert graph_store.count_nodes(node_type="Skill") == 50

    def test_count_nodes_and_edges(self, populated_store):
        total_nodes = populated_store.count_nodes()
        assert total_nodes == 10

        tech_count = populated_store.count_nodes(node_type="Technology")
        assert tech_count == 2  # Python, TensorFlow

        total_edges = populated_store.count_edges()
        assert total_edges == 10

    def test_get_nonexistent_node(self, graph_store):
        assert graph_store.get_node("nonexistent-id") is None


# ---------------------------------------------------------------------------
# Graph Traversal Tests
# ---------------------------------------------------------------------------

class TestGraphTraversal:
    def test_direct_neighbors_outgoing(self, populated_store):
        neighbors = populated_store.get_neighbors("n1", direction="outgoing")
        neighbor_names = {n.name for n, _ in neighbors}
        assert "ML Engineer" in neighbor_names  # Python -> ML Engineer
        assert "TensorFlow" in neighbor_names   # Python -> TensorFlow

    def test_direct_neighbors_incoming(self, populated_store):
        neighbors = populated_store.get_neighbors("n3", direction="incoming")
        neighbor_names = {n.name for n, _ in neighbors}
        assert "Python" in neighbor_names       # Python -> ML Engineer
        assert "Machine Learning" in neighbor_names  # ML -> ML Engineer
        assert "Google" in neighbor_names        # Google -> ML Engineer

    def test_neighbors_both_directions(self, populated_store):
        neighbors = populated_store.get_neighbors("n2", direction="both")
        neighbor_names = {n.name for n, _ in neighbors}
        # Outgoing: ML -> ML Engineer
        assert "ML Engineer" in neighbor_names
        # Incoming: TensorFlow -> ML, Deep Learning -> ML
        assert "TensorFlow" in neighbor_names
        assert "Deep Learning" in neighbor_names

    def test_two_hop_traversal(self, populated_store):
        neighbors = populated_store.get_neighbors("n1", max_hops=2, direction="outgoing")
        neighbor_names = {n.name for n, _ in neighbors}
        # Hop 1: Python -> ML Engineer, Python -> TensorFlow
        assert "ML Engineer" in neighbor_names
        # Hop 2: ML Engineer -> Google (via EMPLOYS edge, incoming to n3)
        # TensorFlow -> Machine Learning (via PART_OF)
        assert "Machine Learning" in neighbor_names

    def test_neighbors_filtered_by_edge_type(self, populated_store):
        neighbors = populated_store.get_neighbors(
            "n1", direction="outgoing", edge_type="REQUIRED_FOR"
        )
        assert len(neighbors) == 1
        assert neighbors[0][0].name == "ML Engineer"

    def test_subgraph_extraction(self, populated_store):
        nodes, edges = populated_store.get_subgraph(
            node_ids=["n8"], max_hops=1
        )
        node_names = {n.name for n in nodes}
        assert "DAAD Scholarship" in node_names
        assert "Germany" in node_names
        assert "Technical University of Munich" in node_names
        assert len(edges) >= 2


# ---------------------------------------------------------------------------
# Entity Extraction Tests
# ---------------------------------------------------------------------------

class TestEntityExtraction:
    def test_rule_based_skill_extraction(self, extractor):
        text = "The applicant must know Python and TensorFlow for the Machine Learning role."
        nodes, edges = extractor.extract(text)
        names = {n.name for n in nodes}
        assert "Python" in names
        assert "TensorFlow" in names
        assert "Machine Learning" in names

    def test_scholarship_extraction(self, extractor):
        text = "Apply for the DAAD scholarship to study in Germany."
        nodes, edges = extractor.extract(text)
        names = {n.name for n in nodes}
        assert "DAAD Scholarship" in names
        assert "Germany" in names

    def test_country_normalization(self, extractor):
        text = "The fellowship is based in the UK and USA."
        nodes, _ = extractor.extract(text)
        names = {n.name for n in nodes}
        assert "United Kingdom" in names
        assert "United States" in names

    def test_degree_extraction(self, extractor):
        text = "Candidates must hold a PhD or MSc degree."
        nodes, _ = extractor.extract(text)
        types = {n.type for n in nodes}
        assert "Role" in types  # PhD and MSc are extracted as Role entities

    def test_document_mentions_edges(self, extractor):
        text = "Learn Python and React for web development."
        nodes, edges = extractor.extract(text, source_document_id="doc-123")
        mentions = [e for e in edges if e.type == "MENTIONS"]
        assert len(mentions) >= 2  # doc-123 MENTIONS Python, doc-123 MENTIONS React

    def test_normalization(self, extractor):
        assert extractor.normalize_entity_name("ml") == "Machine Learning"
        assert extractor.normalize_entity_name("uk") == "United Kingdom"
        assert extractor.normalize_entity_name("Custom Name") == "Custom Name"

    def test_empty_text(self, extractor):
        nodes, edges = extractor.extract("")
        assert nodes == []
        assert edges == []


# ---------------------------------------------------------------------------
# Graph RAG Fusion Tests
# ---------------------------------------------------------------------------

class TestGraphRAGFuser:
    def test_enrich_context_with_graph(self, graph_rag_fuser, populated_store):
        # Use the populated_store reference to ensure data is in place
        _ = populated_store

        vector_hits = [
            {
                "id": "chunk-1",
                "score": 0.92,
                "payload": {
                    "source": "job_desc.pdf",
                    "content": "We need a Python developer with Machine Learning experience.",
                },
            }
        ]

        result = graph_rag_fuser.enrich_context(
            query="What skills are needed for ML Engineer?",
            vector_hits=vector_hits,
        )

        assert "chunks" in result
        assert "graph_triples" in result
        assert "combined_context" in result
        assert "entity_mentions" in result
        assert len(result["entity_mentions"]) >= 1

    def test_combined_context_format(self, graph_rag_fuser, populated_store):
        _ = populated_store

        vector_hits = [
            {
                "id": "c1",
                "score": 0.85,
                "payload": {"source": "guide.md", "content": "Python is essential."},
            }
        ]

        result = graph_rag_fuser.enrich_context(
            query="Tell me about Python",
            vector_hits=vector_hits,
        )

        context = result["combined_context"]
        assert "Retrieved Document Context" in context
        assert "Python is essential" in context

    def test_graph_only_search(self, graph_rag_fuser, populated_store):
        _ = populated_store

        result = graph_rag_fuser.search_graph_only("DAAD scholarship in Germany")
        assert len(result["graph_nodes"]) >= 1
        assert len(result["graph_triples"]) >= 1

    def test_empty_vector_hits(self, graph_rag_fuser, populated_store):
        _ = populated_store

        result = graph_rag_fuser.enrich_context(
            query="Tell me about TensorFlow",
            vector_hits=[],
        )
        # Should still return graph context even without vector hits
        assert "combined_context" in result

    def test_no_matching_entities(self, graph_rag_fuser, populated_store):
        _ = populated_store

        result = graph_rag_fuser.enrich_context(
            query="Tell me about underwater basket weaving",
            vector_hits=[],
        )
        # Should return empty but valid structure
        assert result["graph_triples"] == []
        assert result["entity_mentions"] == []
