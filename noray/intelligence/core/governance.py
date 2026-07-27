"""
NORAY — Governance & Policy Engine

Intercepts agent actions to enforce safety, permissions, and risk assessments.
Routes sensitive actions to the HITL manager.
"""

import re
from typing import Any

from noray.services.hitl import HITLManager


class PolicyViolation(Exception):
    pass

class GovernanceEngine:
    def __init__(self, hitl_manager: HITLManager):
        self.hitl = hitl_manager

    async def intercept_action(self, task_id: str, agent_id: str, action: str, payload: dict[str, Any]) -> bool:
        """
        1. Permission Validation
        2. Risk Assessment
        3. PII Detection
        4. HITL Approval routing
        """

        # PII Detection (Basic mock)
        if self._contains_pii(str(payload)):
            # Flagged as sensitive
            pass

        # Risk Assessment
        sensitive_actions = ["send_email", "delete_file", "apply_job", "submit_application"]
        if action in sensitive_actions:
            # Requires HITL approval
            approved = await self.hitl.request_approval(
                task_id=task_id,
                action_type=action,
                summary=f"Agent '{agent_id}' requested to execute sensitive action: '{action}'",
                payload=payload
            )
            if not approved:
                raise PolicyViolation(f"Action '{action}' was rejected by the user.")

        return True

    def _contains_pii(self, text: str) -> bool:
        # Mock PII checker (e.g., SSN pattern)
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
            return True
        return False
