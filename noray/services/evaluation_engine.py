"""
NORAY — Automated Evaluation Engine
Scores generation groundedness, completeness, and hallucination risk metrics.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.services.evaluation")


class EvaluationEngine:
    """Evaluates output response quality parameters, saving scoring traces in Redis."""
    
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or RedisCache(namespace="noray_evaluations")

    def evaluate(self, session_id: str, prompt: str, response: str, tools_used: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates groundedness, completeness, and quality scores."""
        # Groundedness matches citation lists present in the markdown
        has_citations = "Sources & Citations" in response
        groundedness = 0.95 if has_citations else 0.50
        
        # Completeness based on output length and structural layout
        completeness = min(len(response.split()) / 200.0, 1.0)
        
        # Hallucination risk calculations
        hallucination_risk = 0.05 if has_citations else 0.40
        
        # General response formatting checks
        has_headings = "#" in response
        has_code = "```" in response
        quality = 0.90 if (has_headings or has_code) else 0.60

        scores = {
            "groundedness": groundedness,
            "completeness": completeness,
            "hallucination_risk": hallucination_risk,
            "response_quality": quality,
            "confidence": min((groundedness + completeness + quality) / 3.0, 1.0)
        }
        
        self.cache.set(session_id, scores, ttl=604800)  # 7-day retention TTL
        logger.info(f"[Session: {session_id}] Evaluated output: confidence={scores['confidence']:.2f}")
        return scores
