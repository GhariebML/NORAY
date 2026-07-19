import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from noray.agents.planner import PlannerAgent
from noray.agents.router import RouterAgent
from noray.graph.postgres_store import PostgresGraphStore
from noray.graph.graph_rag import GraphRAGFuser
from noray.graph.extractor import EntityRelationExtractor
from noray.research import DeepResearchEngine
from noray.agents.agent_router import AgentRouter
from noray.shared.logging import log_stage
from noray.api.errors import WorkspaceStageError

router = APIRouter()

# --- Schemas ---

class ExplainabilityInfo(BaseModel):
    confidence_score: float = Field(default=0.0, description="Overall grounded confidence score.")
    retrieved_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant nodes retrieved.")
    retrieved_edges: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant edges retrieved.")
    retrieved_triples: List[str] = Field(default_factory=list, description="Human-readable triples.")
    reasoning_steps: List[str] = Field(default_factory=list, description="Decomposed plan tasks executed.")

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    temperature: Optional[float] = 0.3

class ChatResponse(BaseModel):
    session_id: str
    intent: str
    response: str
    citations: List[Dict[str, Any]]
    explainability: Optional[ExplainabilityInfo] = None

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]

class ResearchRequest(BaseModel):
    objective: str
    max_depth: Optional[int] = 2

class ResearchResponse(BaseModel):
    session_id: str
    objective: str
    status: str
    report: str
    citations: List[Dict[str, Any]]
    explainability: Optional[ExplainabilityInfo] = None


# --- Helper retrieval adapters ---

def get_graph_searcher_fn():
    store = PostgresGraphStore()
    extractor = EntityRelationExtractor(use_llm=False)
    fuser = GraphRAGFuser(graph_store=store, extractor=extractor)
    return fuser.search_graph_only

def get_hybrid_retriever_fn():
    router_instance = AgentRouter(session_id="temp_research")
    return lambda q: router_instance._retrieve_hybrid_context(q, filters={})


# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat_workspace(req: ChatRequest):
    """
    Processes chat requests using the central AIKernel.
    """
    import logging
    from noray.intelligence.core.di import get_kernel
    logger = logging.getLogger(__name__)

    session_id = req.session_id or str(uuid.uuid4())
    log_stage("Incoming Request", f"session_id={session_id} query='{req.query}'")

    try:
        kernel = get_kernel()
        result = await kernel.execute_request(goal=req.query, session_id=session_id)
        
        # Compile explainability
        explain = ExplainabilityInfo(
            confidence_score=result.get("confidence_score", 0.95),
            retrieved_nodes=[],
            retrieved_edges=[],
            retrieved_triples=[],
            reasoning_steps=result.get("reasoning_steps", [])
        )

        return ChatResponse(
            session_id=session_id,
            intent="general",
            response=result["response"],
            citations=result.get("citations", []),
            explainability=explain
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Unexpected workspace chat error: {e}\n{tb}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal assistant processing error: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_workspace(req: SearchRequest):
    """
    Runs global multi-index hybrid search over vector and BM25 indices, returning ranking list.
    """
    log_stage("Search Request", f"query='{req.query}'")
    try:
        router_instance = AgentRouter(session_id="temp_search_session")
        hits = router_instance._retrieve_hybrid_context(req.query, filters=req.filters or {})
        
        results = []
        for hit in hits:
            results.append({
                "id": hit.get("id"),
                "score": hit.get("rerank_score") or hit.get("score") or 0.0,
                "content": hit.get("content") or hit.get("payload", {}).get("content", ""),
                "payload": hit.get("payload", {})
            })
            
        log_stage("Search Output", f"Found {len(results)} hits")
        return SearchResponse(
            query=req.query,
            results=results[:req.limit]
        )
    except Exception as e:
        log_stage("Search Error", str(e))
        raise WorkspaceStageError(
            stage="Search",
            error="Search Retrieval failed",
            details=str(e)
        )


@router.post("/research", response_model=ResearchResponse)
async def research_workspace(req: ResearchRequest):
    """
    Runs an asynchronous multi-stage Deep Research pipeline on the given objective.
    """
    session_id = str(uuid.uuid4())
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
            report=session.report,
            citations=formatted_citations,
            explainability=explain
        )
    except Exception as e:
        log_stage("Research Error", str(e))
        raise WorkspaceStageError(
            stage="Research",
            error="Research Pipeline failed",
            details=str(e)
        )
