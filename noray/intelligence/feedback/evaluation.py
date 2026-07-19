"""
NORAY — Evaluation Framework

Provides online (lightweight) and offline (heavy LLM-as-a-judge) evaluations
for RAG and agent responses.
"""

from typing import Dict, Any

class OnlineEvaluator:
    def evaluate(self, query: str, context: str, response: str) -> Dict[str, float]:
        """Fast heuristic checks (e.g., length, basic keyword grounding)."""
        # Mock online evaluation
        return {
            "groundedness_score": 0.85,
            "latency_penalty": 0.0,
            "overall_health": 0.9
        }

class OfflineEvaluator:
    async def evaluate_async(self, query: str, context: str, response: str) -> Dict[str, Any]:
        """
        LLM-as-a-judge evaluation (RAGAS-like metrics).
        Requires expensive LLM calls so it runs in background tasks.
        """
        # Mock RAGAS metrics
        return {
            "faithfulness": 0.92,
            "answer_relevance": 0.88,
            "context_precision": 0.75,
            "hallucination_index": 0.05
        }
