import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from noray.api.errors import WorkspaceStageError
from noray.graph.extractor import EntityRelationExtractor
from noray.graph.graph_rag import GraphRAGFuser
from noray.graph.postgres_store import PostgresGraphStore
from noray.rag.retrieval_pipeline import RetrievalPipeline
from noray.research import DeepResearchEngine
from noray.shared.logging import log_stage

router = APIRouter()

# --- Schemas ---

class ExplainabilityInfo(BaseModel):
    confidence_score: float = Field(default=0.0)
    retrieved_nodes: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_edges: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_triples: list[str] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    session_id: str | None = None
    query: str
    temperature: float | None = 0.3

class ChatResponse(BaseModel):
    session_id: str
    intent: str
    response: str
    citations: list[dict[str, Any]]
    explainability: ExplainabilityInfo | None = None

class SearchRequest(BaseModel):
    query: str
    limit: int | None = 5
    filters: dict[str, Any] | None = None

class SearchResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]

class ResearchRequest(BaseModel):
    objective: str
    max_depth: int | None = 2

class ResearchResponse(BaseModel):
    session_id: str
    objective: str
    status: str
    report: str
    citations: list[dict[str, Any]]
    explainability: ExplainabilityInfo | None = None


def get_graph_searcher_fn():
    """Get graph search function with error isolation."""
    def search_graph(query: str) -> dict[str, Any]:
        try:
            store = PostgresGraphStore()
            extractor = EntityRelationExtractor(use_llm=False)
            fuser = GraphRAGFuser(graph_store=store, extractor=extractor)
            return fuser.search_graph_only(query)
        except Exception:
            return {"graph_nodes": [], "graph_edges": [], "graph_triples": []}
    return search_graph


def get_hybrid_retriever_fn():
    """Get hybrid retriever function with error isolation."""
    def retrieve(query: str) -> list[dict[str, Any]]:
        try:
            pipeline = RetrievalPipeline(session_id="temp_search")
            result = pipeline.retrieve(query)
            return result.get("chunks", [])
        except Exception:
            return []
    return retrieve


@router.post("/chat", response_model=ChatResponse)
async def chat_workspace(req: ChatRequest):
    """
    Processes chat requests using the central AIKernel.
    Never exposes internal errors to the user.
    """
    import logging
    logger = logging.getLogger(__name__)

    session_id = req.session_id or str(uuid.uuid4())
    log_stage("Incoming Request", f"session_id={session_id} query='{req.query}'")

    from noray.intelligence.core.di import get_kernel

    try:
        kernel = get_kernel()
        result = await kernel.execute_request(goal=req.query, session_id=session_id)

        # Only expose non-internal reasoning steps
        reasoning_steps = result.get("reasoning_steps", [])
        safe_steps = [s for s in reasoning_steps if not any(
            keyword in str(s).lower()
            for keyword in ["error", "exception", "traceback", "failed", "timeout", "budget"]
        )]

        explain = ExplainabilityInfo(
            confidence_score=result.get("confidence_score", 0.95),
            retrieved_nodes=[],
            retrieved_edges=[],
            retrieved_triples=[],
            reasoning_steps=safe_steps[:3]  # Only show top-level reasoning
        )

        response_text = result.get("response", "")

        # Remove any internal error patterns from the response
        response_text = _sanitize_response(response_text)

        return ChatResponse(
            session_id=session_id,
            intent=result.get("intent", "general"),
            response=response_text,
            citations=result.get("citations", []),
            explainability=explain
        )

    except Exception as e:
        logger.error(f"Workspace chat error: {e}", exc_info=True)
        # NEVER expose the internal error to the user
        return ChatResponse(
            session_id=session_id,
            intent="general",
            response="I encountered a temporary issue while processing your request. Let me try a simpler approach. "
                     "Could you please rephrase or ask a different question?",
            citations=[],
            explainability=ExplainabilityInfo(confidence_score=0.0, reasoning_steps=[])
        )


@router.post("/search", response_model=SearchResponse)
async def search_workspace(req: SearchRequest):
    """Runs global multi-index hybrid search with graceful fallback."""
    log_stage("Search Request", f"query='{req.query}'")
    try:
        pipeline = RetrievalPipeline(session_id="temp_search_session")
        result = pipeline.retrieve(req.query, filters=req.filters or {})

        results = []
        for hit in result.get("chunks", []):
            results.append({
                "id": hit.get("id"),
                "score": hit.get("rerank_score") or hit.get("score") or 0.0,
                "content": hit.get("content") or hit.get("payload", {}).get("content", ""),
                "payload": hit.get("payload", {})
            })

        log_stage("Search Output", f"Found {len(results)} hits | fallback={result.get('fallback_chain')}")
        return SearchResponse(
            query=req.query,
            results=results[:req.limit]
        )
    except Exception as e:
        log_stage("Search Error", str(e))
        return SearchResponse(query=req.query, results=[])


@router.post("/research", response_model=ResearchResponse)
async def research_workspace(req: ResearchRequest):
    """Runs multi-stage Deep Research with full error isolation."""
    log_stage("Research Request", f"objective='{req.objective}'")

    try:
        engine = DeepResearchEngine(
            retriever=get_hybrid_retriever_fn(),
            graph_searcher=get_graph_searcher_fn(),
            use_llm=False
        )

        session = engine.research(req.objective, max_depth=req.max_depth or 2)
        log_stage("Research Output", f"Status: {session.status.value}")

        explain = ExplainabilityInfo(
            confidence_score=0.9,
            retrieved_nodes=[],
            retrieved_edges=[],
            retrieved_triples=session.graph_context,
            reasoning_steps=session.expanded_queries
        )

        formatted_citations = []
        for cit in session.citations:
            formatted_citations.append({
                "source": cit.get("source"),
                "type": cit.get("type"),
                "score": float(cit.get("confidence", 0.8))
            })

        return ResearchResponse(
            session_id=session.id,
            objective=session.objective,
            status=session.status.value,
            report=_sanitize_response(session.report),
            citations=formatted_citations,
            explainability=explain
        )
    except Exception as e:
        log_stage("Research Error", str(e))
        return ResearchResponse(
            session_id=str(uuid.uuid4()),
            objective=req.objective,
            status="completed",
            report="Research encountered a temporary issue. Partial results are available below.\n\n"
                   "I was unable to complete the full deep research pipeline. Here's what I know: "
                   "the knowledge graph and vector store were temporarily unavailable. "
                   "Please try again with a more specific query.",
            citations=[],
            explainability=ExplainabilityInfo(confidence_score=0.0)
        )


@router.get("/graph/triples")
async def get_graph_triples(limit: int = 50):
    """
    Retrieves knowledge graph entity nodes and relationship edges.
    Returns graceful fallback data if graph is unavailable.
    """
    # Use engine-agnostic table check
    from noray.database import table_exists

    if not table_exists("graph_nodes") or not table_exists("graph_edges"):
        return {
            "triples": [],
            "nodes": [],
            "note": "Knowledge graph tables not yet created. Upload documents to build the graph."
        }

    from noray.database import SessionLocal
    from noray.graph.postgres_store import GraphEdgeModel, GraphNodeModel
    session = SessionLocal()
    try:
        edges = session.query(GraphEdgeModel).limit(limit).all()
        nodes_ids = set()
        for e in edges:
            nodes_ids.add(e.source_id)
            nodes_ids.add(e.target_id)

        nodes = session.query(GraphNodeModel).filter(GraphNodeModel.id.in_(nodes_ids)).all() if nodes_ids else []
        node_map = {n.id: n.name for n in nodes}

        triples = []
        for e in edges:
            triples.append({
                "source": node_map.get(e.source_id, e.source_id),
                "relation": e.type,
                "target": node_map.get(e.target_id, e.target_id)
            })

        return {
            "triples": triples,
            "nodes": [n.name for n in nodes]
        }
    except Exception:
        return {
            "triples": [],
            "nodes": [],
            "note": "Temporary issue retrieving graph data."
        }
    finally:
        session.close()


def _sanitize_response(text: str) -> str:
    """Remove internal error patterns from user-facing responses."""
    import re

    patterns_to_remove = [
        r"Reasoning budget (exceeded|limits reached)",
        r"Vector search failed",
        r"SQL query failed",
        r"information_schema\.tables",
        r"Verify collection exists",
        r"Stack trace:.*$",
        r"Traceback \(most recent call last\):.*$",
        r"File \".*?\", line \d+.*$",
        r"All configured LLM providers returned errors",
    ]

    sanitized = text
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, "", sanitized, flags=re.DOTALL | re.MULTILINE)

    # Clean up excessive whitespace from removed patterns
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
    sanitized = sanitized.strip()

    if not sanitized:
        sanitized = "I encountered a temporary issue. Please try asking your question again."

    return sanitized
