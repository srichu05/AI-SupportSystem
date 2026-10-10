import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import app
from backend.app.core.database import Base
from backend.app.models import (
    PolicyDocument,
    PolicyChunk,
    Complaint,
    ComplaintIssue,
    IssueEvidence,
    ResponseDraft,
    ReviewDecision,
)


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Test client fixture for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Isolated in-memory SQLite database session for unit testing models."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_complaint_payload() -> dict:
    return {
        "complaint_text": "I was promised a full refund within 14 days, but my account has not received the credit.",
        "response_tone": "professional",
        "generate_tone_variants": False,
    }


@pytest.fixture
def sample_review_payload() -> dict:
    return {
        "draft_id": "00000000-0000-0000-0000-000000000001",
        "decision": "approved",
        "final_response_text": "We apologize for the delay. Your refund has been escalated to billing.",
        "reason": "Customer is within the 14-day window per Refund Policy section 3.",
    }
