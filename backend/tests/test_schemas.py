import pytest
from pydantic import ValidationError

from backend.app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintIssueResponse,
    EvidenceItem,
    DraftResponse,
    ValidationReport,
)
from backend.app.schemas.review import (
    ReviewDecisionRequest,
    ReviewDecisionResponse,
)
from backend.app.schemas.errors import ErrorResponse, ErrorDetail


def test_complaint_create_request_valid():
    """Verify valid complaint request parses correctly."""
    req = ComplaintCreateRequest(
        complaint_text="My order arrived damaged and customer support did not respond.",
        response_tone="empathetic",
        generate_tone_variants=False,
    )
    assert req.response_tone == "empathetic"
    assert "damaged" in req.complaint_text


def test_complaint_create_request_invalid_tone():
    """Verify invalid tone raises ValidationError."""
    with pytest.raises(ValidationError):
        ComplaintCreateRequest(
            complaint_text="Valid complaint text that is long enough.",
            response_tone="aggressive",  # type: ignore
        )


def test_complaint_create_request_too_short():
    """Verify complaint text shorter than minimum length fails."""
    with pytest.raises(ValidationError):
        ComplaintCreateRequest(
            complaint_text="Too short",
        )


def test_complaint_create_request_empty():
    """Verify whitespace-only complaint text fails."""
    with pytest.raises(ValidationError):
        ComplaintCreateRequest(
            complaint_text="             ",
        )


def test_complaint_issue_allowed_statuses():
    """Verify all 6 documented issue assessment statuses are accepted."""
    allowed = [
        "covered",
        "partially_covered",
        "uncovered",
        "prohibited",
        "conflict",
        "needs_human_review",
    ]
    for status in allowed:
        issue = ComplaintIssueResponse(
            issue_id="issue-1",
            issue_text="Issue text",
            assessment_status=status,  # type: ignore
        )
        assert issue.assessment_status == status


def test_complaint_issue_invalid_status():
    """Verify unknown status is rejected."""
    with pytest.raises(ValidationError):
        ComplaintIssueResponse(
            issue_id="issue-1",
            issue_text="Issue text",
            assessment_status="unsupported_custom_status",  # type: ignore
        )


def test_review_decision_request_allowed():
    """Verify allowed review decisions: approved, rejected, escalated."""
    for decision in ["approved", "rejected", "escalated"]:
        req = ReviewDecisionRequest(
            draft_id="00000000-0000-0000-0000-000000000001",
            decision=decision,  # type: ignore
            reason="Reviewer note",
        )
        assert req.decision == decision


def test_review_decision_request_invalid():
    """Verify invalid review decision is rejected."""
    with pytest.raises(ValidationError):
        ReviewDecisionRequest(
            draft_id="00000000-0000-0000-0000-000000000001",
            decision="auto_send",  # type: ignore
        )


def test_error_response_shape():
    """Verify ErrorResponse conforms to API_SPEC.md."""
    err = ErrorResponse(
        error=ErrorDetail(
            code="EMBEDDING_PROVIDER_UNAVAILABLE",
            message="Policy search is temporarily unavailable.",
            retryable=True,
        )
    )
    data = err.model_dump()
    assert "error" in data
    assert data["error"]["code"] == "EMBEDDING_PROVIDER_UNAVAILABLE"
    assert data["error"]["retryable"] is True
