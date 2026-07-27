"""
NORAY — Health & Dependency Diagnostics Endpoints

Provides fine-grained checks of PostgreSQL database, Qdrant vector store,
Graph Store, LLM credentials, and MCP adapter servers.
"""

import os

from fastapi import APIRouter
from sqlalchemy import text

from noray.agents.tools.mcp_adapter import McpClientAdapter
from noray.database import SessionLocal
from noray.rag.vector_store import VectorStoreFactory

router = APIRouter()

@router.get("")
async def get_general_health():
    """Aggregated health status of all subsystems."""
    from noray.gateway.facade import AIGateway
    gateway = AIGateway()

    db_ok = check_database()
    vec_ok = check_vector()
    graph_ok = check_graph()
    llm_ok = check_llm()
    mcp_ok = check_mcp()

    overall = "healthy"
    if not (db_ok and vec_ok and graph_ok and llm_ok):
        overall = "degraded"
    if not db_ok:
        overall = "unhealthy"

    # Fetch provider state details
    provider_states = gateway.get_provider_health_states()

    return {
        "status": overall,
        "details": {
            "database": "healthy" if db_ok else "unhealthy",
            "vector_store": "healthy" if vec_ok else "unhealthy",
            "graph_store": "healthy" if graph_ok else "unhealthy",
            "llm": "configured" if llm_ok else "not_configured",
            "mcp": "active" if mcp_ok else "inactive"
        },
        "gateway": {
            "metrics": gateway.metrics,
            "provider_states": provider_states,
            "models": [name for name in gateway.registry.list_models().keys()],
            "active_provider": "local" if not llm_ok else "hybrid (local/cloud)"
        }
    }

@router.get("/database")
async def get_database_health():
    """Specific check for PostgreSQL database."""
    ok = check_database()
    return {"status": "healthy" if ok else "unhealthy", "dependency": "PostgreSQL"}

@router.get("/vector")
async def get_vector_health():
    """Specific check for Qdrant/FAISS vector store."""
    ok = check_vector()
    return {"status": "healthy" if ok else "unhealthy", "dependency": "Qdrant"}

@router.get("/graph")
async def get_graph_health():
    """Specific check for Graph store database tables."""
    ok = check_graph()
    return {"status": "healthy" if ok else "unhealthy", "dependency": "PostgresGraphStore"}

@router.get("/llm")
async def get_llm_health():
    """Specific check for Anthropic/OpenAI API configuration."""
    ok = check_llm()
    return {
        "status": "healthy" if ok else "degraded",
        "api_keys": {
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY"))
        }
    }

@router.get("/mcp")
async def get_mcp_health():
    """Specific check for MCP external adapter servers."""
    # Instantiates adapter and checks active client list
    adapter = McpClientAdapter()
    servers = list(adapter.servers.keys())
    tools = list(adapter.discovered_tools.keys())
    return {
        "status": "healthy" if len(servers) > 0 or os.getenv("MCP_TEST_MODE") == "true" else "inactive",
        "connected_servers": servers,
        "discovered_tools_count": len(tools)
    }

# --- Check Helpers ---

def check_database() -> bool:
    from noray.database import detect_database_engine
    try:
        engine_type = detect_database_engine()
        session = SessionLocal()
        try:
            if engine_type == "postgresql":
                session.execute(text("SELECT 1"))
            else:
                session.execute(text("SELECT 1"))
            return True
        finally:
            session.close()
    except Exception:
        return False

def check_vector() -> bool:
    try:
        store = VectorStoreFactory.get_vector_store()
        # Ping collection check if supported, or list check
        if hasattr(store, "indexes"):
            return True # FAISS mock is always healthy
        if hasattr(store, "_lazy_init"):
            store._lazy_init()
        if hasattr(store, "client") and store.client:
            store.client.get_collections()
            return True
        return False
    except Exception:
        return False

def check_graph() -> bool:
    from noray.database import table_exists
    try:
        return table_exists("graph_nodes") and table_exists("graph_edges")
    except Exception:
        return False

def check_llm() -> bool:
    # Check if either API key is configured
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))

def check_mcp() -> bool:
    try:
        adapter = McpClientAdapter()
        return len(adapter.servers) > 0 or os.getenv("MCP_TEST_MODE") == "true"
    except Exception:
        return False

# --- Hardware Detection & Installer Endpoints ---

@router.get("/setup")
async def get_hardware_setup_recommendation():
    """Detects system hardware parameters and returns the optimal local model recommendation."""
    from noray.gateway.installer import detect_hardware, recommend_model
    hw = detect_hardware()
    rec = recommend_model(hw)
    return {
        "hardware": hw,
        "recommended_model": rec,
        "description": f"Recommended local model is {rec} based on detected system hardware."
    }

@router.post("/setup/install")
async def trigger_local_model_installation():
    """Triggers the automated Ollama installation, pulls the recommended model, and runs verification."""
    from noray.gateway.installer import (
        detect_hardware,
        install_ollama_if_missing,
        pull_and_verify_model,
        recommend_model,
    )

    hw = detect_hardware()
    rec_model = recommend_model(hw)

    # 1. Install Ollama if missing
    ollama_ok = install_ollama_if_missing()
    if not ollama_ok:
        return {
            "success": False,
            "error": "Failed to install Ollama executable.",
            "details": "Check admin permissions or download manually from https://ollama.com"
        }

    # 2. Pull and verify the recommended model
    pulled_ok, verify_msg = pull_and_verify_model(rec_model)

    return {
        "success": pulled_ok,
        "model": rec_model,
        "verification": verify_msg
    }
