import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from backend.app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintIssueResponse,
    EvidenceItem,
    DraftResponse,
    ValidationReport,
    ToneVariantDraft,
)
from backend.app.schemas.review import (
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ComplaintHistoryResponse,
)
from backend.app.schemas.agent import (
    ComplaintAssignRequest,
    ComplaintAuditLogResponse,
)
from backend.app.core.errors import (
    ResourceNotFoundException,
    InvalidReviewDecisionException,
)
from backend.app.core.database import get_session_factory, get_db
from backend.app.core.auth import get_current_agent
from backend.app.models.agent import AgentProfile, ComplaintAuditLog
from backend.app.models.complaint import Complaint, ComplaintIssue, IssueEvidence
from backend.app.models.response import ResponseDraft, ReviewDecision
from backend.app.models.policy import PolicyChunk, PolicyDocument
from backend.app.services.complaint_analyzer import complaint_analyzer
from backend.app.services.response_generator import response_generator
from backend.app.services.response_validator import response_validator

logger = logging.getLogger("complaint_assistant.complaints_api")
router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and process a customer complaint",
)
def create_complaint(
    request: ComplaintCreateRequest,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> ComplaintResponse:
    """
    Intake a customer complaint, decompose into distinct issues, retrieve policy evidence,
    classify eligibility status, generate an evidence-grounded draft response, validate
    commitments and citations deterministically, and persist for human review.
    Attributed to the authenticated agent derived from Clerk credentials.
    """
    complaint_id = uuid.uuid4()
    draft_id = uuid.uuid4()

    factory = get_session_factory()
    issues_responses: List[ComplaintIssueResponse] = []
    security_warnings: List[str] = []
    overall_status = "needs_human_review"
    draft_text = ""
    citations: List[str] = []
    variants_dict: Optional[dict] = None
    val_valid = True
    val_errors: List[str] = []
    val_warnings: List[str] = []

    if factory is not None:
        try:
            with factory() as db:
                # Perform decomposition, hybrid retrieval, and policy assessment
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

                # Generate grounded draft in requested primary tone
                is_adv = any(iss.is_adversarial for iss in analysis.issues)
                draft_text, citations, val_result = response_generator.generate_draft(
                    complaint_text=request.complaint_text,
                    issues=analysis.issues,
                    tone=request.response_tone,
                    is_adversarial=is_adv,
                )
                val_valid = val_result.valid
                val_errors = val_result.errors
                val_warnings = val_result.warnings

                # Generate stretch-goal tone variants if requested
                if request.generate_tone_variants:
                    variants_dict = response_generator.generate_variants(
                        complaint_text=request.complaint_text,
                        issues=analysis.issues,
                        is_adversarial=is_adv,
                    )

                variants_json = (
                    {k: v.model_dump() for k, v in variants_dict.items()}
                    if variants_dict
                    else None
                )

                # Persist generated draft with creator attribution
                db_draft = ResponseDraft(
                    id=draft_id,
                    complaint_id=complaint_id,
                    draft_text=draft_text,
                    structured_output={
                        "citations": citations,
                        "tone": request.response_tone,
                        "variants": variants_json,
                    },
                    validation_status="valid" if val_valid else "invalid",
                    created_by_agent_id=current_agent.id,
                )
                db.add(db_draft)

                # Set workflow status based on validation and policy assessment
                if not val_valid or is_adv or overall_status in ("needs_human_review", "conflict"):
                    overall_status = "needs_human_review"
                elif overall_status == "covered":
                    overall_status = "drafted"

                complaint_rec = db.query(Complaint).filter(Complaint.id == complaint_id).first()
                if complaint_rec:
                    complaint_rec.processing_status = overall_status
                    complaint_rec.created_by_agent_id = current_agent.id
                    complaint_rec.assigned_to_agent_id = current_agent.id

                # Record immutable audit event for creation
                db_audit = ComplaintAuditLog(
                    id=uuid.uuid4(),
                    complaint_id=complaint_id,
                    actor_agent_id=current_agent.id,
                    event_type="complaint_created",
                    details={
                        "tone": request.response_tone,
                        "overall_status": overall_status,
                        "agent_name": current_agent.display_name,
                    },
                )
                db.add(db_audit)
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
                iss.assessment_status = st
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

            draft_text, citations, val_result = response_generator.generate_draft(
                complaint_text=request.complaint_text,
                issues=decomposed,
                tone=request.response_tone,
                is_adversarial=is_adv,
            )
            val_valid = val_result.valid
            val_errors = val_result.errors
            val_warnings = val_result.warnings

            if request.generate_tone_variants:
                variants_dict = response_generator.generate_variants(
                    complaint_text=request.complaint_text,
                    issues=decomposed,
                    is_adversarial=is_adv,
                )
    else:
        # Fallback when database factory is unconfigured
        is_adv, adv_w = complaint_analyzer.detect_adversarial_patterns(request.complaint_text)
        san_text, has_pii, pii_w = complaint_analyzer.sanitize_and_detect_pii(request.complaint_text)
        security_warnings = adv_w + pii_w
        decomposed = complaint_analyzer.decompose_complaint(request.complaint_text, is_adv)
        for iss in decomposed:
            st, rsn = complaint_analyzer.assess_issue_policy(iss, [], request.complaint_text)
            iss.assessment_status = st
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

        draft_text, citations, val_result = response_generator.generate_draft(
            complaint_text=request.complaint_text,
            issues=decomposed,
            tone=request.response_tone,
            is_adversarial=is_adv,
        )
        val_valid = val_result.valid
        val_errors = val_result.errors
        val_warnings = val_result.warnings

        if request.generate_tone_variants:
            variants_dict = response_generator.generate_variants(
                complaint_text=request.complaint_text,
                issues=decomposed,
                is_adversarial=is_adv,
            )

    return ComplaintResponse(
        complaint_id=str(complaint_id),
        status=overall_status,
        issues=issues_responses,
        draft=DraftResponse(
            draft_id=str(draft_id),
            text=draft_text,
            citations=citations,
        ),
        validation=ValidationReport(
            valid=val_valid,
            errors=val_errors,
            warnings=security_warnings + val_warnings,
        ),
        draft_variants=variants_dict,
        created_by_agent_id=str(current_agent.id),
        created_by_agent_name=current_agent.display_name,
        assigned_to_agent_id=str(current_agent.id),
        assigned_to_agent_name=current_agent.display_name,
    )


@router.get(
    "",
    response_model=List[ComplaintResponse],
    summary="List complaints and their current review status",
)
def list_complaints(
    limit: int = 50,
    offset: int = 0,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> List[ComplaintResponse]:
    """
    List complaints and their current review status.
    Protected by Clerk authentication.
    """
    factory = get_session_factory()
    results: List[ComplaintResponse] = []
    if factory is not None:
        try:
            with factory() as db:
                complaints = (
                    db.query(Complaint)
                    .order_by(Complaint.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
                for comp in complaints:
                    latest_draft = (
                        db.query(ResponseDraft)
                        .filter(ResponseDraft.complaint_id == comp.id)
                        .order_by(ResponseDraft.created_at.desc())
                        .first()
                    )
                    draft_resp = None
                    if latest_draft:
                        so = latest_draft.structured_output or {}
                        draft_resp = DraftResponse(
                            draft_id=str(latest_draft.id),
                            text=latest_draft.draft_text,
                            citations=so.get("citations", []),
                        )

                    results.append(
                        ComplaintResponse(
                            complaint_id=str(comp.id),
                            status=comp.processing_status,
                            issues=[
                                ComplaintIssueResponse(
                                    issue_id=str(iss.id),
                                    issue_text=iss.issue_text,
                                    requested_resolution=iss.requested_resolution,
                                    assessment_status=iss.assessment_status,
                                    missing_facts=iss.missing_facts or [],
                                    evidence=[],
                                )
                                for iss in comp.issues
                            ],
                            draft=draft_resp,
                            validation=ValidationReport(valid=True, errors=[], warnings=[]),
                            created_by_agent_id=str(comp.created_by_agent_id) if comp.created_by_agent_id else None,
                            created_by_agent_name=comp.created_by.display_name if comp.created_by else None,
                            assigned_to_agent_id=str(comp.assigned_to_agent_id) if comp.assigned_to_agent_id else None,
                            assigned_to_agent_name=comp.assigned_to.display_name if comp.assigned_to else None,
                        )
                    )
        except Exception as exc:
            logger.error("Failed to list complaints: %s", exc)
    return results


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Retrieve complaint details and review status",
)
def get_complaint(
    complaint_id: str,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> ComplaintResponse:
    """
    Retrieve an existing complaint, extracted issues, retrieved evidence, and draft.
    Includes ownership and assignment accountability attributes.
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
                    draft_variants = None
                    val_report = ValidationReport(valid=True, errors=[], warnings=[])

                    if latest_draft:
                        so = latest_draft.structured_output or {}
                        cites = so.get("citations", [])
                        raw_vars = so.get("variants")
                        if raw_vars:
                            draft_variants = {
                                k: ToneVariantDraft(**v) if isinstance(v, dict) else v
                                for k, v in raw_vars.items()
                            }
                        draft_resp = DraftResponse(
                            draft_id=str(latest_draft.id),
                            text=latest_draft.draft_text,
                            citations=cites,
                        )
                        is_valid = latest_draft.validation_status == "valid"
                        val_report = ValidationReport(
                            valid=is_valid,
                            errors=[] if is_valid else ["Validation flagged draft as invalid."],
                            warnings=[],
                        )

                    creator_name = complaint.created_by.display_name if complaint.created_by else None
                    assignee_name = complaint.assigned_to.display_name if complaint.assigned_to else None

                    return ComplaintResponse(
                        complaint_id=str(complaint.id),
                        status=complaint.processing_status,
                        issues=issues_responses,
                        draft=draft_resp,
                        validation=val_report,
                        draft_variants=draft_variants,
                        created_by_agent_id=str(complaint.created_by_agent_id) if complaint.created_by_agent_id else None,
                        created_by_agent_name=creator_name,
                        assigned_to_agent_id=str(complaint.assigned_to_agent_id) if complaint.assigned_to_agent_id else None,
                        assigned_to_agent_name=assignee_name,
                    )
        except Exception as exc:
            logger.error("Failed to fetch complaint %s: %s", complaint_id, exc)

    raise ResourceNotFoundException("complaint", complaint_id)


@router.post(
    "/{complaint_id}/assign",
    response_model=ComplaintResponse,
    summary="Assign or reassign complaint to a support agent",
)
def assign_complaint(
    complaint_id: str,
    request: ComplaintAssignRequest,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> ComplaintResponse:
    """
    Reassign complaint to a target agent profile.
    Derives actor identity exclusively from verified Clerk token and records audit event.
    """
    try:
        parsed_complaint_id = uuid.UUID(complaint_id)
    except ValueError:
        raise ResourceNotFoundException("complaint", complaint_id)

    try:
        target_agent_id = uuid.UUID(request.assigned_to_agent_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid assigned_to_agent_id format.",
        )

    factory = get_session_factory()
    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database factory is unconfigured.",
        )

    with factory() as db:
        complaint = db.query(Complaint).filter(Complaint.id == parsed_complaint_id).first()
        if not complaint:
            raise ResourceNotFoundException("complaint", complaint_id)

        target_agent = db.query(AgentProfile).filter(AgentProfile.id == target_agent_id).first()
        if not target_agent or not target_agent.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target agent does not exist or has been deactivated.",
            )

        prev_agent_id = complaint.assigned_to_agent_id
        complaint.assigned_to_agent_id = target_agent.id

        event_name = "reassigned" if prev_agent_id else "assigned"
        db_audit = ComplaintAuditLog(
            id=uuid.uuid4(),
            complaint_id=parsed_complaint_id,
            actor_agent_id=current_agent.id,
            event_type=event_name,
            details={
                "from_agent_id": str(prev_agent_id) if prev_agent_id else None,
                "to_agent_id": str(target_agent.id),
                "to_agent_name": target_agent.display_name,
                "assigned_by": current_agent.display_name,
            },
        )
        db.add(db_audit)
        db.commit()

    return get_complaint(complaint_id=complaint_id, current_agent=current_agent)


@router.post(
    "/{complaint_id}/review",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record human reviewer decision",
)
def record_review_decision(
    complaint_id: str,
    request: ReviewDecisionRequest,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> ReviewDecisionResponse:
    """
    Record an internal support agent's human review decision.
    Valid decisions: 'approved', 'rejected', or 'escalated'.
    Enforces non-negotiable invariant: approval NEVER automatically sends responses to customers.
    Derives reviewer identity exclusively from Clerk session token.
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

                # If reviewer edited the final response text, record the edited draft with agent identity
                if request.final_response_text:
                    edited_draft_id = uuid.uuid4()
                    db_edited_draft = ResponseDraft(
                        id=edited_draft_id,
                        complaint_id=parsed_complaint_id,
                        draft_text=request.final_response_text,
                        structured_output={"edited_by": current_agent.display_name},
                        validation_status="valid",
                        created_by_agent_id=current_agent.id,
                    )
                    db.add(db_edited_draft)

                    # Log audit event for draft edit
                    db.add(
                        ComplaintAuditLog(
                            id=uuid.uuid4(),
                            complaint_id=parsed_complaint_id,
                            actor_agent_id=current_agent.id,
                            event_type="draft_edited",
                            details={
                                "draft_id": str(edited_draft_id),
                                "editor_name": current_agent.display_name,
                            },
                        )
                    )

                db_decision = ReviewDecision(
                    id=decision_id,
                    complaint_id=parsed_complaint_id,
                    draft_id=draft_uuid,
                    decision=request.decision,
                    final_response_text=request.final_response_text,
                    reason=request.reason,
                    reviewer_profile_id=current_agent.id,
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

                # Log audit event for review decision
                action_type = "case_escalated" if request.decision == "escalated" else f"review_{request.decision}"
                db.add(
                    ComplaintAuditLog(
                        id=uuid.uuid4(),
                        complaint_id=parsed_complaint_id,
                        actor_agent_id=current_agent.id,
                        event_type=action_type,
                        details={
                            "decision": request.decision,
                            "reason": request.reason,
                            "reviewer_name": current_agent.display_name,
                        },
                    )
                )

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
        reviewer_id=str(current_agent.id),
        reviewer_name=current_agent.display_name,
        reviewed_at=reviewed_at,
    )


@router.get(
    "/{complaint_id}/audit",
    response_model=List[ComplaintAuditLogResponse],
    summary="Retrieve immutable audit events for a complaint",
)
def get_complaint_audit_logs(
    complaint_id: str,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> List[ComplaintAuditLogResponse]:
    """
    Retrieve audit trail for a complaint, showing actor identity, timestamps, and action details.
    """
    try:
        parsed_id = uuid.UUID(complaint_id)
    except ValueError:
        raise ResourceNotFoundException("complaint", complaint_id)

    factory = get_session_factory()
    results: List[ComplaintAuditLogResponse] = []

    if factory is not None:
        with factory() as db:
            logs = (
                db.query(ComplaintAuditLog)
                .filter(ComplaintAuditLog.complaint_id == parsed_id)
                .order_by(ComplaintAuditLog.created_at.asc())
                .all()
            )
            for log in logs:
                results.append(
                    ComplaintAuditLogResponse(
                        id=str(log.id),
                        complaint_id=str(log.complaint_id),
                        actor_agent_id=str(log.actor_agent_id) if log.actor_agent_id else None,
                        actor_name=log.actor.display_name if log.actor else "System",
                        event_type=log.event_type,
                        details=log.details,
                        created_at=log.created_at,
                    )
                )

    return results


@router.get(
    "/{complaint_id}/history",
    response_model=ComplaintHistoryResponse,
    summary="Retrieve complaint lifecycle and audit history",
)
def get_complaint_history(
    complaint_id: str,
    current_agent: AgentProfile = Depends(get_current_agent),
) -> ComplaintHistoryResponse:
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
                        so = d.structured_output or {}
                        draft_responses.append(
                            DraftResponse(
                                draft_id=str(d.id),
                                text=d.draft_text,
                                citations=so.get("citations", []),
                            )
                        )

                    decisions = (
                        db.query(ReviewDecision)
                        .filter(ReviewDecision.complaint_id == parsed_id)
                        .order_by(ReviewDecision.reviewed_at.desc())
                        .all()
                    )
                    for dec in decisions:
                        rev_name = dec.reviewer_profile.display_name if dec.reviewer_profile else None
                        review_responses.append(
                            ReviewDecisionResponse(
                                review_id=str(dec.id),
                                complaint_id=str(dec.complaint_id),
                                draft_id=str(dec.draft_id) if dec.draft_id else "",
                                decision=dec.decision,
                                final_response_text=dec.final_response_text,
                                reason=dec.reason,
                                reviewer_id=str(dec.reviewer_profile_id) if dec.reviewer_profile_id else None,
                                reviewer_name=rev_name,
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
