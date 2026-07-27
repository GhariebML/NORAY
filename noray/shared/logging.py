"""
NORAY — Structured Workspace Logger

Uses structlog for structured JSON logging. Injects trace IDs automatically.
"""

import structlog

from noray.api.middleware.tracing import get_current_trace_id


def add_trace_id(logger, method_name, event_dict):
    """Add the trace ID from the contextvar to the event dictionary."""
    trace_id = get_current_trace_id()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_id,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("noray.workspace")

def log_stage(stage: str, message: str, **kwargs) -> None:
    """Log workspace stage details with trace ID injection."""
    logger.info(message, stage=stage, **kwargs)
