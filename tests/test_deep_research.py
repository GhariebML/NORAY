"""
NORAY — Deep Research Engine Tests

Tests the multi-stage research pipeline, including query expansion,
evidence gathering, conflict detection, fact verification, and report synthesis.
"""

import pytest
from typing import List, Dict, Any
from noray.research import DeepResearchEngine, ResearchSession, ResearchStatus, EvidenceItem, ConflictItem

# Mock retriever and graph searcher functions
def mock_retriever(query: str) -> List[Dict[str, Any]]:
    query_lower = query.lower()
    if "chevening" in query_lower:
        return [
            {
                "id": "c1",
                "content": "Chevening Scholarship application deadline is November 5, 2026. Applicants need a Master's degree target.",
                "payload": {"source": "chevening_official.pdf"}
            },
            {
                "id": "c2",
                "content": "Chevening requires 2 years of work experience (equivalent to 2800 hours).",
                "payload": {"source": "chevening_faq.txt"}
            }
        ]
    elif "daad" in query_lower:
        return [
            {
                "id": "d1",
                "content": "DAAD Development-Related Postgraduate Courses (EPOS) deadline is August 31, 2026 for Munich TU.",
                "payload": {"source": "daad_guide.pdf"}
            },
            {
                "id": "d2",
                "content": "DAAD requires 2 years of professional work experience and a Bachelor's degree.",
                "payload": {"source": "daad_requirements.docx"}
            }
        ]
    return [
        {
            "id": "g1",
            "content": "General guidance: Always apply at least two months prior to deadlines.",
            "payload": {"source": "general_tips.md"}
        }
    ]

def mock_graph_searcher(query: str) -> Dict[str, Any]:
    return {
        "graph_triples": [
            "Chevening Scholarship [Scholarship] --LOCATED_IN--> United Kingdom [Country]",
            "DAAD Scholarship [Scholarship] --LOCATED_IN--> Germany [Country]"
        ]
    }

@pytest.fixture
def research_engine():
    # Disable LLM to run deterministic test assertions using standard text/rule fallbacks
    return DeepResearchEngine(
        retriever=mock_retriever,
        graph_searcher=mock_graph_searcher,
        use_llm=False
    )

def test_evidence_item_to_dict():
    item = EvidenceItem(
        claim="Chevening requires 2 years of experience.",
        source="chevening_faq.txt",
        source_type="document",
        confidence=0.9
    )
    d = item.to_dict()
    assert d["source"] == "chevening_faq.txt"
    assert d["confidence"] == 0.9
    assert len(d["id"]) == 8

def test_conflict_item_to_dict():
    item = ConflictItem(
        topic="Deadline Discrepancy",
        claim_a="November 5",
        claim_b="August 31",
        source_a="Source A",
        source_b="Source B",
        resolution="Different scholarships have different deadlines."
    )
    d = item.to_dict()
    assert d["topic"] == "Deadline Discrepancy"
    assert d["claim_a"] == "November 5"
    assert d["resolution"] == "Different scholarships have different deadlines."

def test_research_session_to_dict():
    session = ResearchSession(objective="Find scholarship deadlines")
    d = session.to_dict()
    assert d["objective"] == "Find scholarship deadlines"
    assert d["status"] == "planning"
    assert len(d["id"]) == 12

def test_query_expansion(research_engine):
    queries = research_engine._expand_queries("Chevening Scholarship info")
    assert len(queries) >= 2
    assert any("eligibility" in q for q in queries) or any("deadline" in q for q in queries)

def test_evidence_extraction(research_engine):
    chunks = mock_retriever("chevening")
    triples = mock_graph_searcher("chevening")["graph_triples"]
    
    evidence = research_engine._extract_evidence(chunks, triples)
    assert len(evidence) == 4 # 2 from chunks, 2 from triples
    sources = {e.source for e in evidence}
    assert "chevening_official.pdf" in sources
    assert "Knowledge Graph" in sources

def test_full_research_pipeline(research_engine):
    session = research_engine.research("DAAD Scholarship deadline and criteria")
    assert session.status == ResearchStatus.COMPLETED
    assert len(session.evidence) >= 2
    assert len(session.graph_context) == 2
    assert "Report" in session.report
    assert len(session.citations) >= 2
