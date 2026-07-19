"""
NORAY — Self-Improving Feedback Loop Tests

Tests logging user ratings, clicked references, and executing automated parameter
weight adjustments.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from noray.database import Base
from noray.models.feedback import FeedbackModel, RetrievalParamsModel
from noray.feedback.tuner import RetrievalTuner

@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def tuner(test_session_factory, monkeypatch):
    # Monkeypatch the default SessionLocal inside noray.feedback.tuner
    monkeypatch.setattr("noray.feedback.tuner.SessionLocal", test_session_factory)
    return RetrievalTuner()

def test_record_feedback_logs_correctly(tuner):
    fb_id = tuner.record_feedback(
        session_id="session-123",
        query="Tell me about DAAD requirements",
        response="DAAD requires a Bachelor's degree and 2 years experience.",
        rating=5,
        clicks=["d1"],
        ignored_sources=["d2"]
    )
    assert len(fb_id) == 36
    
    params = tuner.get_retrieval_params()
    assert params["dense_weight"] == 0.5
    assert params["sparse_weight"] == 0.5

def test_auto_tune_parameters_sparse_shift(tuner):
    # Log some negative feedbacks where users clicked mostly sparse sources (e.g. non-UUID ids like "d1")
    tuner.record_feedback(
        session_id="session-1",
        query="Query 1",
        response="Response 1",
        rating=1,
        clicks=["d1"],
        ignored_sources=[]
    )
    tuner.record_feedback(
        session_id="session-2",
        query="Query 2",
        response="Response 2",
        rating=2,
        clicks=["d2"],
        ignored_sources=[]
    )

    res = tuner.auto_tune_parameters()
    assert res["status"] == "parameters optimized"
    assert res["new_sparse_weight"] > 0.5
    assert res["new_dense_weight"] < 0.5

def test_auto_tune_parameters_dense_shift(tuner):
    # Log some negative feedbacks where users clicked mostly dense sources (UUID like ids)
    tuner.record_feedback(
        session_id="session-1",
        query="Query 1",
        response="Response 1",
        rating=1,
        clicks=["550e8400-e29b-41d4-a716-446655440000"],
        ignored_sources=[]
    )
    tuner.record_feedback(
        session_id="session-2",
        query="Query 2",
        response="Response 2",
        rating=2,
        clicks=["123e4567-e89b-12d3-a456-426614174000"],
        ignored_sources=[]
    )

    res = tuner.auto_tune_parameters()
    assert res["status"] == "parameters optimized"
    assert res["new_dense_weight"] > 0.5
    assert res["new_sparse_weight"] < 0.5
