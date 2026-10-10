import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
    ComplaintHistoryResponse,
)
from backend.app.core.errors import (
    ResourceNotFoundException,
    InvalidReviewDecisionException,
)
from backend.app.core.database import get_session_factory
from backend.app.models.complaint import Complaint, ComplaintIssue, IssueEvidence
from backend.app.models.response import ResponseDraft, ReviewDecision
from backend.app.models.policy import PolicyChunk, PolicyDocument
from backend.app.services.complaint_analyzer import complaint_analyzer

logger = logging.getLogger("complaint_assistant.complaints_api")
router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and process a customer complaint",
)
def create_complaint(request: ComplaintCreateRequest) -> ComplaintResponse:
    """
    Intake a customer complaint, decompose into distinct issues, retrieve policy evidence,
    classify eligibility status, and persist for human review.
    Draft generation is implemented in Phase 4.
    """
    complaint_id = uuid.uuid4()
    draft_id = uuid.uuid4()

    factory = get_session_factory()
    issues_responses: List[ComplaintIssueResponse] = []
    security_warnings: List[str] = []
    overall_status = "needs_human_review"

    if factory is not None:
        try:
            with factory() as db:
                # Perform Phase 3 decomposition, hybrid retrieval, and policy assessment
                analysis = complaint_analyzer.analyze_and_persist(
                    complaint_id=complaint_id,
                    complaint_text=request.complaint_text,
                    response_tone=request.response_tone,
                    db=db,
                )
                overall_status = analysis.overall_status
                security_warnings = analysis.security_warnings

                # Format issue responses
                for iss in analysis.issues:
                    evidence_items = [
                        EvidenceItem(
                            chunk_id=c.chunk_id,
                            document_id=c.document_id,
                            source_filename=c.source_filename,
                            section=c.section_path,
                            page_number=c.page_number,
                            content=c.content,
                        )
                        for c in iss.retrieved_evidence
                    ]
                    issues_responses.append(
                        ComplaintIssueResponse(
                            issue_id=str(iss.issue_id),
                            issue_text=iss.issue_text,
                            requested_resolution=iss.requested_resolution,
                            assessment_status=iss.assessment_status,
                            missing_facts=iss.missing_facts,
                            evidence=evidence_items,
                        )
                    )

                # Persist baseline draft shell placeholder for Phase 4
                db_draft = ResponseDraft(
                    id=draft_id,
                    complaint_id=complaint_id,
                    draft_text=(
                        "Analysis complete. Issues decomposed, policy evidence retrieved, "
                        "and status classified. Awaiting Phase 4 evidence-grounded drafting."
                    ),
                    validation_status="valid",
                )
                db.add(db_draft)
                db.commit()

        except Exception as exc:
            logger.error("Complaint processing failed in database: %s", exc)
            # Fallback in-memory processing
            is_adv, adv_w = complaint_analyzer.detect_adversarial_patterns(request.complaint_text)
            san_text, has_pii, pii_w = complaint_analyzer.sanitize_and_detect_pii(request.complaint_text)
            security_warnings = adv_w + pii_w
            decomposed = complaint_analyzer.decompose_complaint(request.complaint_text, is_adv)
            for iss in decomposed:
                st, rsn = complaint_analyzer.assess_issue_policy(iss, [], request.complaint_text)
                issues_responses.append(
                    ComplaintIssueResponse(
                        issue_id=str(iss.issue_id),
                        issue_text=iss.issue_text,
                        requested_resolution=iss.requested_resolution,
                        assessment_status=st,
                        missing_facts=iss.missing_facts,
                        evidence=[],
                    )
                )
    else:
        # Fallback when database factory is unconfigured
        is_adv, adv_w = complaint_analyzer.detect_adversarial_patterns(request.complaint_text)
        san_text, has_pii, pii_w = complaint_analyzer.sanitize_and_detect_pii(request.complaint_text)
        security_warnings = adv_w + pii_w
        decomposed = complaint_analyzer.decompose_complaint(request.complaint_text, is_adv)
        for iss in decomposed:
            st, rsn = complaint_analyzer.assess_issue_policy(iss, [], request.complaint_text)
            issues_responses.append(
                ComplaintIssueResponse(
                    issue_id=str(iss.issue_id),
                    issue_text=iss.issue_text,
                    requested_resolution=iss.requested_resolution,
                    assessment_status=st,
                    missing_facts=iss.missing_facts,
                    evidence=[],
                )
            )

    return ComplaintResponse(
        complaint_id=str(complaint_id),
        status=overall_status,
        issues=issues_responses,
        draft=DraftResponse(
            draft_id=str(draft_id),
            text=(
                "Analysis complete. Issues decomposed, policy evidence retrieved, "
                "and status classified. Awaiting Phase 4 evidence-grounded drafting."
            ),
            citations=[],
        ),
        validation=ValidationReport(
            valid=True,
            errors=[],
            warnings=security_warnings,
        ),
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Retrieve complaint details and review status",
)
def get_complaint(complaint_id: str) -> ComplaintResponse:
    """
    Retrieve an existing complaint, extracted issues, retrieved evidence, and draft.
    """
    try:
        parsed_id = uuid.UUID(complaint_id)
    except ValueError:
        raise ResourceNotFoundException("complaint", complaint_id)

    factory = get_session_factory()
    if factory is not None:
        try:
            with factory() as db:
                complaint = db.query(Complaint).filter(Complaint.id == parsed_id).first()
                if complaint:
                    # Retrieve decomposed issues and evidence
                    db_issues = db.query(ComplaintIssue).filter(ComplaintIssue.complaint_id == parsed_id).all()
                    issues_responses: List[ComplaintIssueResponse] = []

                    for iss in db_issues:
                        # Fetch linked evidence
                        evidence_links = db.query(IssueEvidence).filter(IssueEvidence.issue_id == iss.id).all()
                        evidence_items: List[EvidenceItem] = []

                        for link in evidence_links:
                            chunk = db.query(PolicyChunk).filter(PolicyChunk.id == link.chunk_id).first()
                            if chunk:
                                doc = db.query(PolicyDocument).filter(PolicyDocument.id == chunk.document_id).first()
                                evidence_items.append(
                                    EvidenceItem(
                                        chunk_id=str(chunk.id),
                                        document_id=str(chunk.document_id),
                                        source_filename=doc.source_filename if doc else "policy_document",
                                        section=chunk.section_path,
                                        page_number=chunk.page_number,
                                        content=chunk.content,
                                    )
                                )

                        issues_responses.append(
                            ComplaintIssueResponse(
                                issue_id=str(iss.id),
                                issue_text=iss.issue_text,
                                requested_resolution=iss.requested_resolution,
                                assessment_status=iss.assessment_status,
                                missing_facts=iss.missing_facts or [],
                                evidence=evidence_items,
                            )
                        )

                    latest_draft = (
                        db.query(ResponseDraft)
                        .filter(ResponseDraft.complaint_id == parsed_id)
                        .order_by(ResponseDraft.created_at.desc())
                        .first()
                    )
                    draft_resp = None
                    if latest_draft:
                        draft_resp = DraftResponse(
                            draft_id=str(latest_draft.id),
                            text=latest_draft.draft_text,
                            citations=[],
                        )

                    return ComplaintResponse(
                        complaint_id=str(complaint.id),
                        status=complaint.processing_status,
                        issues=issues_responses,
                        draft=draft_resp,
                        validation=ValidationReport(valid=True, errors=[], warnings=[]),
                    )
        except Exception as exc:
            logger.error("Failed to fetch complaint %s: %s", complaint_id, exc)

    raise ResourceNotFoundException("complaint", complaint_id)


@router.post(
    "/{complaint_id}/review",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record human reviewer decision",
)
def record_review_decision(
    complaint_id: str,
    request: ReviewDecisionRequest,
) -> ReviewDecisionResponse:
    """
    Record an internal support agent's human review decision.
    Valid decisions: 'approved', 'rejected', or 'escalated'.
    Enforces non-negotiable invariant: approval NEVER automatically sends
    responses to customers.
    """
    try:
        parsed_complaint_id = uuid.UUID(complaint_id)
    except ValueError:
        raise ResourceNotFoundException("complaint", complaint_id)

    decision_id = uuid.uuid4()
    reviewed_at = datetime.now(timezone.utc)

    factory = get_session_factory()
    if factory is not None:
        try:
            with factory() as db:
                complaint = db.query(Complaint).filter(Complaint.id == parsed_complaint_id).first()
                draft_uuid = None
                if request.draft_id:
                    try:
                        draft_uuid = uuid.UUID(request.draft_id)
                    except ValueError:
                        pass

                db_decision = ReviewDecision(
                    id=decision_id,
                    complaint_id=parsed_complaint_id,
                    draft_id=draft_uuid,
                    decision=request.decision,
                    final_response_text=request.final_response_text,
                    reason=request.reason,
                    reviewed_at=reviewed_at,
                )
                db.add(db_decision)

                if complaint:
                    if request.decision == "approved":
                        complaint.processing_status = "reviewed"
                    elif request.decision == "rejected":
                        complaint.processing_status = "reviewed"
                    elif request.decision == "escalated":
                        complaint.processing_status = "escalated"

                db.commit()
        except Exception as exc:
            logger.error("Failed to record review decision in database: %s", exc)

    return ReviewDecisionResponse(
        review_id=str(decision_id),
        complaint_id=complaint_id,
        draft_id=request.draft_id,
        decision=request.decision,
        final_response_text=request.final_response_text,
        reason=request.reason,
        reviewed_at=reviewed_at,
    )


@router.get(
    "/{complaint_id}/history",
    response_model=ComplaintHistoryResponse,
    summary="Retrieve complaint lifecycle and audit history",
)
def get_complaint_history(complaint_id: str) -> ComplaintHistoryResponse:
    """Retrieve full audit history for a complaint."""
    try:
        parsed_id = uuid.UUID(complaint_id)
    except ValueError:
        raise ResourceNotFoundException("complaint", complaint_id)

    factory = get_session_factory()
    draft_responses = []
    review_responses = []

    if factory is not None:
        try:
            with factory() as db:
                complaint = db.query(Complaint).filter(Complaint.id == parsed_id).first()
                if complaint:
                    drafts = db.query(ResponseDraft).filter(ResponseDraft.complaint_id == parsed_id).all()
                    for d in drafts:
                        draft_responses.append(
                            DraftResponse(draft_id=str(d.id), text=d.draft_text, citations=[])
                        )

                    decisions = (
                        db.query(ReviewDecision)
                        .filter(ReviewDecision.complaint_id == parsed_id)
                        .order_by(ReviewDecision.reviewed_at.desc())
                        .all()
                    )
                    for dec in decisions:
                        review_responses.append(
                            ReviewDecisionResponse(
                                review_id=str(dec.id),
                                complaint_id=str(dec.complaint_id),
                                draft_id=str(dec.draft_id) if dec.draft_id else "",
                                decision=dec.decision,
                                final_response_text=dec.final_response_text,
                                reason=dec.reason,
                                reviewed_at=dec.reviewed_at,
                            )
                        )

                    return ComplaintHistoryResponse(
                        complaint_id=str(complaint.id),
                        drafts=draft_responses,
                        reviews=review_responses,
                    )
        except Exception as exc:
            logger.error("Failed to fetch complaint history: %s", exc)

    return ComplaintHistoryResponse(
        complaint_id=complaint_id,
        drafts=draft_responses,
        reviews=review_responses,
    )
