"""
NORAY — Workspace Exceptions

Defines stage-specific exceptions that identify which architectural layer
(e.g., Planner, Router, Graph, LLM, etc.) failed.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from noray.api.middleware.tracing import get_current_trace_id


class WorkspaceStageError(Exception):
    """Exception raised when a specific phase of the workspace RAG pipeline fails."""

    def __init__(self, stage: str, error: str, details: str, trace_id: str | None = None):
        self.stage = stage
        self.error = error
        self.details = details
        self.trace_id = trace_id or get_current_trace_id()
        super().__init__(f"[{stage}] {error}: {details}")

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "error": self.error,
            "details": self.details,
            "trace_id": self.trace_id
        }

async def workspace_stage_error_handler(request: Request, exc: WorkspaceStageError) -> JSONResponse:
    """FastAPI error handler to format WorkspaceStageError into descriptive JSON responses."""
    return JSONResponse(
        status_code=400, # Using 400 Bad Request to indicate a readable domain-level execution error
        content=exc.to_dict()
    )
