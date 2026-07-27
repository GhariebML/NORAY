"""
NORAY — Smart Router API Endpoints

Provides real-time status of the AI provider routing system,
health monitoring, circuit breaker states, configuration controls,
task-aware routing decisions, analytics, conversation cache, and offline mode.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from noray.llm.local_model_registry import local_model_registry
from noray.llm.smart_router import RoutingMode, smart_router

logger = logging.getLogger("noray.api.routes.smart_router")

router = APIRouter(prefix="/api/ai", tags=["AI Router"])


class ModeRequest(BaseModel):
    mode: str


class ProviderToggleRequest(BaseModel):
    provider: str
    enabled: bool


class PreferredModelRequest(BaseModel):
    model: str


class OfflineModeRequest(BaseModel):
    enabled: bool


class RoutingQuery(BaseModel):
    query: str = ""
    context: str = ""


@router.get("/status")
async def get_router_status():
    """Get the current SmartRouter status for the UI status bar."""
    status = smart_router.get_status()
    health = smart_router.get_all_health()

    healthy_cloud = [
        p for p, h in health.items()
        if p != "ollama" and h["healthy"]
    ]
    active_mode = status["mode"]

    return {
        "status": status,
        "health": health,
        "active_provider": status["current_provider"],
        "active_model": status["current_model"],
        "mode": active_mode,
        "is_local": status["is_local"],
        "offline_mode": status["offline_mode"],
        "mode_label": status["mode_label"],
        "healthy_cloud_providers": healthy_cloud,
        "local_models": [
            {
                "name": m.name,
                "size_gb": m.size_gb,
                "family": m.family,
                "parameter_size": m.parameter_size,
                "available": m.available,
            }
            for m in local_model_registry.sorted_models
        ],
        "local_ollama_running": local_model_registry.is_ollama_running,
    }


@router.get("/providers")
async def get_providers_full_status():
    """Get detailed health and circuit breaker status for all providers."""
    health = smart_router.get_all_health()
    return {
        "providers": [
            {
                **h,
                "enabled": smart_router.is_provider_enabled(h["name"]),
            }
            for h in health.values()
        ]
    }


@router.post("/mode")
async def set_routing_mode(request: ModeRequest):
    """Set the routing mode: auto, cloud, or local."""
    try:
        mode = RoutingMode(request.mode.lower())
        smart_router.set_mode(mode)
        logger.info(f"Routing mode set to: {mode.value}")
        return {"status": "ok", "mode": mode.value}
    except ValueError:
        return {"status": "error", "message": f"Invalid mode: {request.mode}. Use: auto, cloud, local"}


@router.post("/toggle-provider")
async def toggle_provider(request: ProviderToggleRequest):
    """Enable or disable a specific provider."""
    name = request.provider.lower().strip()
    if request.enabled:
        smart_router.enable_provider(name)
        logger.info(f"Provider enabled: {name}")
    else:
        smart_router.disable_provider(name)
        logger.info(f"Provider disabled: {name}")
    return {"status": "ok", "provider": name, "enabled": request.enabled}


@router.post("/preferred-model")
async def set_preferred_local_model(request: PreferredModelRequest):
    """Set the preferred local Ollama model."""
    smart_router.set_preferred_local_model(request.model)
    logger.info(f"Preferred local model set to: {request.model}")
    return {"status": "ok", "model": request.model}


@router.get("/analytics")
async def get_provider_analytics():
    """Get provider analytics including request counts, tokens, costs, and latency."""
    analytics = smart_router.get_analytics()
    aggregated = smart_router.get_aggregated_analytics()
    return {
        "providers": analytics,
        "aggregated": aggregated,
    }


@router.post("/offline-mode")
async def set_offline_mode(request: OfflineModeRequest):
    """Enable or disable emergency offline mode."""
    smart_router.set_offline_mode(request.enabled)
    return {
        "status": "ok",
        "offline_mode": request.enabled,
        "message": "Running in Offline Knowledge Mode" if request.enabled else "Online mode restored",
    }


@router.get("/routing-decision")
async def get_routing_decision(query: str = "", context: str = ""):
    """Get the current routing decision with task analysis for a given query."""
    decision = smart_router.get_routing_decision(query, context)
    return decision


@router.post("/routing-decision")
async def analyze_routing(request: RoutingQuery):
    """Analyze a query and return the recommended routing decision."""
    decision = smart_router.get_routing_decision(request.query, request.context)
    return decision
