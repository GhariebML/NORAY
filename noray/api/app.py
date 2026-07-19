"""
NORAY — FastAPI Application

REST API for the NORAY platform.
Designed for future Next.js frontend integration.

Run with:
    uvicorn NORAY.api.app:app --reload --port 8000
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from noray.api.routes import profile, jobs, scholarships, cv, sop, applications, upskill, workspace, documents, health, system_diagnostics
from noray.database import engine, Base
import noray.models  # Load models to register metadata

# Middleware & error imports
from noray.api.middleware.tracing import RequestTracingMiddleware
from noray.api.errors import WorkspaceStageError, workspace_stage_error_handler

# We rely on Alembic for database migrations now.
app = FastAPI(
    title="NORAY API",
    description="AI Career & Scholarship Operating System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Custom exception handler registration
app.add_exception_handler(WorkspaceStageError, workspace_stage_error_handler)

# Request tracing middleware registration
app.add_middleware(RequestTracingMiddleware)

# CORS — allow the Next.js frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",
        "https://NORAY.ai",  # Future production domain
    ],
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


@app.get("/")
async def root():
    return {
        "name": "NORAY",
        "version": "0.1.0",
        "description": "AI Career & Scholarship Operating System",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
