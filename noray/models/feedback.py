"""
NORAY — Feedback database models

Stores user interactions (ratings, clicks, corrected answers, ignored sources)
to enable self-improving retrieval optimization loops.
"""

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, func

from noray.database import Base


class FeedbackModel(Base):
    """Stores user ratings, click-through actions, and correction notes for LLM answers."""
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), index=True, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True) # 1 to 5 stars or binary 1/-1
    clicks = Column(JSON, nullable=True) # List of source ids clicked
    ignored_sources = Column(JSON, nullable=True) # List of sources shown but not clicked
    corrections = Column(Text, nullable=True) # User-provided corrected text
    created_at = Column(DateTime, default=func.now())

class RetrievalParamsModel(Base):
    """Stores dynamic hyperparameters for retrieval engines (dense weight vs sparse weight)."""
    __tablename__ = "retrieval_params"

    id = Column(String(50), primary_key=True, default="default")
    dense_weight = Column(Float, nullable=False, default=0.5)
    sparse_weight = Column(Float, nullable=False, default=0.5)
    chunk_size = Column(Integer, nullable=False, default=500)
    chunk_overlap = Column(Integer, nullable=False, default=100)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
