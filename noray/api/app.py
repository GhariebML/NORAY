"""
NORAY — FastAPI Application

REST API for the NORAY platform.
Designed for future Next.js frontend integration.

Run with:
    uvicorn NORAY.api.app:app --reload --port 8000
"""

import logging
import os

os.environ["HF_HUB_OFFLINE"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("noray.api.app")

from noray.api.errors import WorkspaceStageError, workspace_stage_error_handler

# Middleware & error imports
from noray.api.middleware.tracing import RequestTracingMiddleware
from noray.api.routes import (
    applications,
    cv,
    documents,
    health,
    jobs,
    profile,
    scholarships,
    smart_router,
    sop,
    system_diagnostics,
    upskill,
    workspace,
)
from noray.observability import stream_router

# We rely on Alembic for database migrations now.
app = FastAPI(
    title="NORAY API",
    description="AI Career & Scholarship Operating System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def start_smart_router_services():
    """Start SmartRouter background monitoring and model warm-up on app startup."""
    from noray.llm.smart_router import smart_router

    await smart_router.start_background_monitoring()
    await smart_router.start_warm_up()
    logger.info("SmartRouter services started: monitoring + warm-up")


@app.on_event("shutdown")
async def stop_smart_router_services():
    """Stop SmartRouter background monitoring on app shutdown."""
    from noray.llm.smart_router import smart_router

    await smart_router.stop_background_monitoring()
    logger.info("SmartRouter services stopped")

# Custom exception handler registration
app.add_exception_handler(WorkspaceStageError, workspace_stage_error_handler)

# Request tracing middleware registration
app.add_middleware(RequestTracingMiddleware)

# CORS — allow the Next.js frontend to connect
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://noray.ai",
    "https://noray-frontend.vercel.app",
    "https://noray-academic.streamlit.app",
]
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(scholarships.router, prefix="/api/scholarships", tags=["Scholarships"])
app.include_router(cv.router, prefix="/api/cv", tags=["CV"])
app.include_router(sop.router, prefix="/api/sop", tags=["SOP & Documents"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(upskill.router, prefix="/api/upskill", tags=["Upskill"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(system_diagnostics.router)
app.include_router(smart_router.router)
app.include_router(stream_router, prefix="/api", tags=["Observability Stream"])


@app.get("/")
async def root():
    return {
        "name": "NORAY",
        "version": "1.0.0",
        "description": "AI Career & Scholarship Operating System",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
