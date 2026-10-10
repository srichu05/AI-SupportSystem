import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import (
    PolicyDocument,
    PolicyChunk,
    Complaint,
    ComplaintIssue,
    IssueEvidence,
    ResponseDraft,
    ReviewDecision,
)


def test_create_policy_document_and_chunks(db_session: Session):
    """Test policy document and chunk models with cascade delete."""
    doc_id = uuid.uuid4()
    doc = PolicyDocument(
        id=doc_id,
        source_filename="customer_support_policy.pdf",
        document_type="PDF",
        version_label="v1.0",
        status="active",
    )
    db_session.add(doc)
    db_session.flush()

    chunk1 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        section_path="Refunds / Digital Goods",
        page_number=2,
        content="Digital items are non-refundable once downloaded.",
        embedding=[0.0] * 768,
        embedding_model="gemini-embedding-2",
    )
    chunk2 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=1,
        section_path="Refunds / Physical Goods",
        page_number=3,
        content="Physical items may be returned within 30 days.",
        embedding=[0.1] * 768,
        embedding_model="gemini-embedding-2",
    )
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    # Query back
    fetched_doc = db_session.query(PolicyDocument).filter(PolicyDocument.id == doc_id).first()
    assert fetched_doc is not None
    assert len(fetched_doc.chunks) == 2

    # Cascade delete verification
    db_session.delete(fetched_doc)
    db_session.commit()
    remaining_chunks = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).all()
    assert len(remaining_chunks) == 0


def test_policy_chunk_unique_constraint(db_session: Session):
    """Test unique constraint on (document_id, chunk_index)."""
    doc_id = uuid.uuid4()
    doc = PolicyDocument(
        id=doc_id,
        source_filename="test.txt",
        document_type="TXT",
        status="active",
    )
    db_session.add(doc)
    db_session.flush()

    c1 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        content="First chunk",
    )
    c2 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,  # Duplicate chunk_index
        content="Duplicate index chunk",
    )
    db_session.add(c1)
    db_session.flush()

    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_complaint_workflow_entities_and_relationships(db_session: Session):
    """Test end-to-end complaint, issue, evidence, draft, and review entities."""
    complaint_id = uuid.uuid4()
    complaint = Complaint(
        id=complaint_id,
        complaint_text="I was charged twice for order #12345.",
        response_tone="professional",
        processing_status="needs_human_review",
    )
    db_session.add(complaint)
    db_session.flush()

    # Policy chunk for evidence link
    doc_id = uuid.uuid4()
    doc = PolicyDocument(
        id=doc_id,
        source_filename="billing.pdf",
        document_type="PDF",
        status="active",
    )
    chunk = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        content="Duplicate billing errors must be refunded immediately.",
    )
    db_session.add_all([doc, chunk])
    db_session.flush()

    # Issue
    issue = ComplaintIssue(
        id=uuid.uuid4(),
        complaint_id=complaint_id,
        issue_text="Double charge for single order",
        requested_resolution="Refund second charge",
        assessment_status="covered",
        missing_facts=[],
    )
    db_session.add(issue)
    db_session.flush()

    # Issue Evidence link
    evidence = IssueEvidence(
        id=uuid.uuid4(),
        issue_id=issue.id,
        chunk_id=chunk.id,
        retrieval_source="hybrid_rrf",
        retrieval_rank=1,
        fusion_score=0.032,
    )
    db_session.add(evidence)
    db_session.flush()

    # Draft
    draft = ResponseDraft(
        id=uuid.uuid4(),
        complaint_id=complaint_id,
        draft_text="We have reviewed your account and confirmed the duplicate charge.",
        structured_output={"citations": [str(chunk.id)]},
        validation_status="valid",
    )
    db_session.add(draft)
    db_session.flush()

    # Review Decision
    review = ReviewDecision(
        id=uuid.uuid4(),
        complaint_id=complaint_id,
        draft_id=draft.id,
        decision="approved",
        final_response_text="We have reversed the duplicate charge immediately.",
        reason="Evidence clearly supports refund for billing duplicate.",
    )
    db_session.add(review)
    db_session.commit()

    # Assert relations
    loaded = db_session.query(Complaint).filter(Complaint.id == complaint_id).first()
    assert loaded is not None
    assert len(loaded.issues) == 1
    assert len(loaded.drafts) == 1
    assert len(loaded.decisions) == 1
    assert loaded.decisions[0].decision == "approved"
