import logging
import os
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from noray.llm.factory import LLMProviderFactory
from noray.llm.health_monitor import ProviderHealthMonitor
from noray.llm.local_manager import local_runtime
from noray.llm.model_registry import model_registry
from noray.llm.router import ModelRouter, ModelRouteRequest

logger = logging.getLogger("noray.api.routes.system_diagnostics")

router = APIRouter(prefix="/api/system", tags=["System Diagnostics"])

class ModelPullRequest(BaseModel):
    model: str

async def run_model_pull_task(model_name: str):
    logger.info(f"Background task: pulling model '{model_name}' started.")
    await local_runtime.pull_model(model_name)
    logger.info(f"Background task: pulling model '{model_name}' completed.")


@router.get("/providers")
async def get_providers_status():
    """Retrieve detailed status, credentials configuration, and latency metric for all providers."""
    providers_list = ["openai", "anthropic", "gemini", "ollama", "openrouter", "deepseek", "mistral", "together"]
    results = []

    for name in providers_list:
        is_configured = ModelRouter.is_provider_configured(name)

        status = "Unconfigured"
        latency = 0.0
        healthy = False

        if is_configured:
            try:
                start_time = time.time()
                provider_inst = LLMProviderFactory.get_provider(name)
                is_healthy = provider_inst.health()
                latency = round((time.time() - start_time) * 1000, 2)

                if is_healthy:
                    status = "Healthy"
                    healthy = True
                else:
                    status = "Error"
            except Exception:
                status = "Error"

        # Lookup registered models for this provider
        models = model_registry.get_models_by_provider(name)
        model_names = [m.model for m in models]

        # Check support capabilities based on registry properties
        supports_streaming = any(m.supports_streaming for m in models)
        supports_embeddings = any(m.supports_embeddings for m in models)
        supports_tools = any(m.supports_tools for m in models)

        results.append({
            "provider": name.capitalize(),
            "status": status,
            "latency": latency,
            "available_models": model_names,
            "streaming": supports_streaming,
            "embeddings": supports_embeddings,
            "tools": supports_tools,
            "configured": is_configured,
            "healthy": healthy
        })

    return {"providers": results}


@router.get("/diagnostics")
async def get_diagnostics_report():
    """Run full checklist diagnostics across local models, LLM routing, streaming, and embeddings."""
    report = {
        "ollama_running": False,
        "models_downloaded": False,
        "api_keys_loaded": False,
        "router_healthy": False,
        "embeddings_healthy": False,
        "streaming_works": False,
        "memory_service_works": False,
        "details": {},
        "hardware": {}
    }

    # 1. Ollama status check
    ollama_active = await local_runtime.is_ollama_running()
    report["ollama_running"] = ollama_active
    report["details"]["ollama"] = "Running" if ollama_active else "Stopped"

    # 2. Hardware info
    hardware = local_runtime.get_hardware_info()
    report["hardware"] = hardware

    # 3. Models pull status
    downloaded_models = []
    if ollama_active:
        downloaded_models = await local_runtime.get_downloaded_models()
        model_names = {m["name"] for m in downloaded_models}

        # Strip tag if matched as fully tagged vs untagged
        clean_names = {n.split(":")[0] for n in model_names}.union(model_names)

        has_required = all(any(req in name for name in clean_names) for req in ["qwen2.5", "llama3.1", "nomic-embed-text"])
        report["models_downloaded"] = has_required
        report["details"]["downloaded_models"] = [m["name"] for m in downloaded_models]
    else:
        report["details"]["downloaded_models"] = []

    # 4. API keys count loading check
    configured_count = sum(
        1 for p in ["openai", "anthropic", "gemini", "openrouter", "mistral", "deepseek", "together"]
        if ModelRouter.is_provider_configured(p)
    )
    report["api_keys_loaded"] = configured_count > 0
    report["details"]["api_keys_configured_count"] = configured_count

    # 5. ModelRouter check
    router_inst = ModelRouter()
    req = ModelRouteRequest(query="Test system diagnostics router", complexity="low")
    try:
        model, provider, _, _ = router_inst.route(req)
        report["router_healthy"] = bool(model and provider)
        report["details"]["router_decision"] = f"{provider}:{model}"
    except Exception as e:
        report["details"]["router_error"] = str(e)

    # 6. Local Embeddings check
    try:
        provider_inst = LLMProviderFactory.get_provider("ollama")
        embed = provider_inst.embeddings("NORAY test embeddings latency ping")
        report["embeddings_healthy"] = len(embed) > 0
        report["details"]["embedding_dimension"] = len(embed)
    except Exception as e:
        report["details"]["embeddings_error"] = str(e)

    # 7. Streaming simulation
    try:
        from noray.llm.providers.base_provider import LLMConfig, LLMMessage
        provider_inst = LLMProviderFactory.get_provider("ollama")
        config = LLMConfig(model="qwen2.5:7b", max_tokens=5)
        messages = [LLMMessage(role="user", content="Ping")]

        if ollama_active:
            # Quick check generator
            gen = provider_inst.stream(messages, config)
            # Fetch first item to prove it streams
            async for item in gen:
                if item.content:
                    report["streaming_works"] = True
                    break
        else:
            report["streaming_works"] = False
            report["details"]["streaming"] = "Skipped (Ollama offline)"
    except Exception as e:
        report["details"]["streaming_error"] = str(e)

    # 8. Memory RAG check
    try:
        from noray.intelligence.memory.context_engine import ContextEngine
        context = ContextEngine()
        # Test mock/real memory ranking pipeline
        ranked = await context.build_context("ML jobs", "diagnostics_session")
        report["memory_service_works"] = True
        report["details"]["memory_context_length"] = len(ranked)
    except Exception as e:
        report["details"]["memory_error"] = str(e)

    return report


@router.get("/telemetry")
async def get_retrieval_telemetry(limit: int = 50):
    """Retrieve recent retrieval pipeline telemetry for diagnostics."""
    from noray.rag.telemetry import telemetry_store
    entries = telemetry_store.get_recent(limit=limit)
    return {"telemetry": entries}


@router.get("/ingestion-diagnostics")
async def get_ingestion_diagnostics():
    """Retrieve detailed operational status of document parsing, chunking, embeddings, and vector store components."""
    from noray.rag.embeddings import EmbeddingsManager
    from noray.rag.sparse_index import SparseBM25Index
    from noray.rag.vector_store import VectorStoreFactory

    diagnostics = {
        "ollama_status": "offline",
        "embedding_provider": os.getenv("EMBEDDINGS_PROVIDER", "local"),
        "embedding_model": os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2"),
        "vector_dimension": 384,
        "qdrant_status": "online",
        "qdrant_collections": [],
        "bm25_chunks_indexed": 0,
        "ocr_status": "available",
        "status": "healthy"
    }

    try:
        ollama_active = await local_runtime.is_ollama_running()
        diagnostics["ollama_status"] = "running" if ollama_active else "offline"
    except Exception:
        diagnostics["ollama_status"] = "offline"

    try:
        embedder = EmbeddingsManager.get_embedder()
        sample = embedder.embed(["Health ping"])
        diagnostics["vector_dimension"] = len(sample[0]) if sample else 384
    except Exception as e:
        diagnostics["status"] = "degraded"
        diagnostics["embedding_error"] = str(e)

    try:
        store = VectorStoreFactory.get_vector_store()
        store._lazy_init()
        if hasattr(store, "client") and store.client:
            colls = store.client.get_collections().collections
            diagnostics["qdrant_collections"] = [c.name for c in colls]
    except Exception as e:
        diagnostics["qdrant_status"] = "degraded"
        diagnostics["qdrant_error"] = str(e)

    try:
        bm25 = SparseBM25Index()
        if bm25.load():
            diagnostics["bm25_chunks_indexed"] = len(bm25.chunks)
    except Exception as e:
        diagnostics["bm25_error"] = str(e)

    return diagnostics


@router.post("/pull-model")
async def pull_model_endpoint(request: ModelPullRequest, background_tasks: BackgroundTasks):
    """Trigger background model pulling from Ollama registry."""
    if not await local_runtime.is_ollama_running():
        raise HTTPException(status_code=503, detail="Ollama local server is not running.")

    background_tasks.add_task(run_model_pull_task, request.model)
    return {"status": "started", "model": request.model}
