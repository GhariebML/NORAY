"""
NORAY — Feedback Optimizer

Consumes learning signals from Evaluations and user UI actions (edits, thumbs up/down).
Generates Procedural Memory rules and adjusts retrieval weights.
"""

from typing import Dict, Any

class FeedbackOptimizer:
    def process_signal(self, execution_id: str, signal_type: str, payload: Dict[str, Any]) -> None:
        """
        signal_type: 'user_edit', 'thumbs_down', 'low_faithfulness'
        """
        if signal_type == "thumbs_down":
            self._adjust_prompt_weights(execution_id)
        elif signal_type == "user_edit":
            self._extract_procedural_rule(payload.get("original"), payload.get("edited"))

    def _adjust_prompt_weights(self, execution_id: str):
        # E.g., downgrade the specific prompt template version used
        pass

    def _extract_procedural_rule(self, original: str, edited: str):
        # Prompt an LLM to figure out WHY the user edited the text
        # Store the rule in Procedural Memory
        pass
