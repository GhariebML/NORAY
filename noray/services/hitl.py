"""
NORAY — Human-In-The-Loop (HITL) Service

Manages pausing workflows for human approval via WebSockets + Database.
"""

from typing import Dict, Any, Awaitable, Callable
from pydantic import BaseModel
import asyncio
import uuid

class ApprovalRequest(BaseModel):
    request_id: str
    task_id: str
    action_type: str  # e.g., 'send_email', 'execute_code'
    summary: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending, approved, rejected

class HITLManager:
    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}
        # Futures used to block task execution until UI resolves the approval
        self._pending_futures: Dict[str, asyncio.Future] = {}

    async def request_approval(self, task_id: str, action_type: str, summary: str, payload: Dict[str, Any]) -> bool:
        """Called by an agent to block execution until user approves."""
        req = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            task_id=task_id,
            action_type=action_type,
            summary=summary,
            payload=payload
        )
        self._requests[req.request_id] = req
        
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_futures[req.request_id] = future
        
        # Trigger WebSocket event to UI here (mocked for now)
        # await websocket_manager.broadcast_approval_needed(req)
        
        # Wait for the UI to resolve the future
        approved = await future
        return approved

    def resolve_approval(self, request_id: str, approved: bool) -> None:
        """Called by the API endpoint when the user clicks Approve/Reject."""
        req = self._requests.get(request_id)
        if req and req.status == "pending":
            req.status = "approved" if approved else "rejected"
            future = self._pending_futures.get(request_id)
            if future and not future.done():
                future.set_result(approved)
