"""
NORAY — Request Tracing Middleware

Generates a unique trace ID for each incoming request, stores it in a contextvar,
and appends it to response headers.

Uses pure ASGI middleware instead of BaseHTTPMiddleware to avoid
the known Starlette deadlock issue with BaseHTTPMiddleware.
"""

from __future__ import annotations

import uuid
import contextvars
from starlette.types import ASGIApp, Receive, Scope, Send

# Context variable to hold the trace ID for the current request context
request_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_trace_id", default="")


class RequestTracingMiddleware:
    """Pure ASGI middleware to inject a unique X-Trace-ID header and track request flows.
    
    This avoids the known BaseHTTPMiddleware deadlock issue in Starlette
    (https://github.com/encode/starlette/issues/1012).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate trace ID
        headers = dict(scope.get("headers", []))
        trace_id = headers.get(b"x-trace-id", b"").decode() or str(uuid.uuid4())

        # Store in scope state for downstream access
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["trace_id"] = trace_id

        # Set contextvar
        token = request_trace_id.set(trace_id)

        async def send_with_trace(message: dict) -> None:
            """Inject X-Trace-ID header into the HTTP response start message."""
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_trace)
        finally:
            request_trace_id.reset(token)


def get_current_trace_id() -> str:
    """Retrieve the trace ID of the active request context."""
    return request_trace_id.get()
