"""
NORAY — Self-Improving Retrieval Tuner

Implements the optimization loop:
1. Records user ratings, click-through citations, and manual corrections.
2. Analyzes performance trends (e.g. clicked vs ignored citation indices).
3. Automatically tunes retrieval weights (dense vs sparse) and chunking limits
   without manual code updates.
"""

from __future__ import annotations

import uuid
from typing import Any

from noray.database import SessionLocal
from noray.models.feedback import FeedbackModel, RetrievalParamsModel


class RetrievalTuner:
    """Manages recording feedback and tuning RAG retrieval hyperparameters dynamically."""

    def __init__(self):
        self._ensure_params_exist()

    def _ensure_params_exist(self) -> None:
        """Verify default parameters row is registered in database."""
        session = SessionLocal()
        try:
            params = session.query(RetrievalParamsModel).filter_by(id="default").first()
            if not params:
                params = RetrievalParamsModel(
                    id="default",
                    dense_weight=0.5,
                    sparse_weight=0.5,
                    chunk_size=500,
                    chunk_overlap=100
                )
                session.add(params)
                session.commit()
        except Exception:
            pass
        finally:
            session.close()

    def record_feedback(
        self,
        session_id: str,
        query: str,
        response: str,
        rating: int | None = None,
        clicks: list[str] | None = None,
        ignored_sources: list[str] | None = None,
        corrections: str | None = None
    ) -> str:
        """Log a user interaction event to the database."""
        session = SessionLocal()
        feedback_id = str(uuid.uuid4())
        try:
            model = FeedbackModel(
                id=feedback_id,
                session_id=session_id,
                query=query,
                response=response,
                rating=rating,
                clicks=clicks or [],
                ignored_sources=ignored_sources or [],
                corrections=corrections
            )
            session.add(model)
            session.commit()
            return feedback_id
        finally:
            session.close()

    def get_retrieval_params(self) -> dict[str, Any]:
        """Fetch current active weights and chunk configurations."""
        session = SessionLocal()
        try:
            params = session.query(RetrievalParamsModel).filter_by(id="default").first()
            if params:
                return {
                    "dense_weight": params.dense_weight,
                    "sparse_weight": params.sparse_weight,
                    "chunk_size": params.chunk_size,
                    "chunk_overlap": params.chunk_overlap
                }
        except Exception:
            pass
        finally:
            session.close()

        # Fallback defaults
        return {
            "dense_weight": 0.5,
            "sparse_weight": 0.5,
            "chunk_size": 500,
            "chunk_overlap": 100
        }

    def auto_tune_parameters(self) -> dict[str, Any]:
        """
        Analyzes recent feedback ratings and adjusts retrieval parameters:
        - If ratings are low (<3) and user clicks mostly sparse sources, shift weight to sparse.
        - If ratings are low (<3) and user clicks mostly dense sources, shift weight to dense.
        - Cap values between 0.1 and 0.9.
        """
        session = SessionLocal()
        try:
            # Query recent negative feedback
            feedbacks = session.query(FeedbackModel).filter(FeedbackModel.rating < 3).all()
            if not feedbacks:
                return {"status": "no negative feedback trends to optimize, weights retained."}

            dense_clicks = 0
            sparse_clicks = 0

            for fb in feedbacks:
                clicks = fb.clicks or []
                # Simple heuristic: inspect click IDs (dense IDs might be UUIDs, sparse IDs contain text keys)
                for click in clicks:
                    if "-" in click and len(click) > 20: # matches UUID format typical of dense search hits
                        dense_clicks += 1
                    else:
                        sparse_clicks += 1

            params = session.query(RetrievalParamsModel).filter_by(id="default").first()
            if not params:
                return {"status": "parameters record missing"}

            old_dense = params.dense_weight
            old_sparse = params.sparse_weight

            adjustment_step = 0.05
            if sparse_clicks > dense_clicks:
                # Sparse search yields better click matching, increase sparse weight
                params.sparse_weight = min(params.sparse_weight + adjustment_step, 0.9)
                params.dense_weight = max(params.dense_weight - adjustment_step, 0.1)
            elif dense_clicks > sparse_clicks:
                # Dense search yields better click matching, increase dense weight
                params.dense_weight = min(params.dense_weight + adjustment_step, 0.9)
                params.sparse_weight = max(params.sparse_weight - adjustment_step, 0.1)

            session.commit()

            return {
                "status": "parameters optimized",
                "old_dense_weight": old_dense,
                "new_dense_weight": params.dense_weight,
                "old_sparse_weight": old_sparse,
                "new_sparse_weight": params.sparse_weight
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            session.close()
