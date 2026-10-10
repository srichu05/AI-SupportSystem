import uuid
import hashlib
from unittest.mock import patch
import pytest
from sqlalchemy.orm import Session

from backend.app.models.policy import PolicyDocument, PolicyChunk
from backend.app.services.ingestion import PolicyIngestionService
from backend.app.services.retrieval import HybridRetrievalService, RetrievedChunk
from backend.app.services.complaint_analyzer import complaint_analyzer
from backend.app.services.response_generator import response_generator
from backend.app.services.response_validator import response_validator


def test_ingestion_idempotency_skips_unchanged_document(db_session: Session):
    """Verify that re-ingesting an unchanged document skips re-chunking and retains stable records."""
    service = PolicyIngestionService()
    doc_id = uuid.uuid4()
    content = b"""# Source ID: SRC-ZAPPOS-008
# URL: https://www.zappos.com/c/price-match
# Title: Price Matching Policy
# ------------------------------------------------------------
### Price Matching Policy
We match competitor pricing on identical in-stock items.
"""
    mock_vec = [0.05] * 768

    with patch("backend.app.services.ingestion.gemini_service.embed_texts", return_value=[mock_vec]):
        with patch("backend.app.services.ingestion.supabase_service.upload_file", return_value="policy-documents/test.txt"):
            # First ingestion
            doc1 = service.ingest_document(
                doc_id=doc_id,
                filename="zappos_price_matching.txt",
                content=content,
                source_id="SRC-ZAPPOS-008",
                canonical_url="https://www.zappos.com/c/price-match",
                db=db_session,
            )
            count1 = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count()
            assert count1 == 1
            assert doc1.source_id == "SRC-ZAPPOS-008"
            assert doc1.canonical_url == "https://www.zappos.com/c/price-match"
            assert doc1.content_hash == hashlib.sha256(content).hexdigest()

            # Second ingestion with exact same content - must skip re-chunking
            doc2 = service.ingest_document(
                doc_id=doc_id,
                filename="zappos_price_matching.txt",
                content=content,
                source_id="SRC-ZAPPOS-008",
                canonical_url="https://www.zappos.com/c/price-match",
                db=db_session,
            )
            count2 = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count()
            assert count2 == 1
            assert doc2.id == doc1.id


def test_ingestion_safe_update_no_stale_chunks(db_session: Session):
    """Verify modifying a policy document safely updates chunks without leaving orphaned records."""
    service = PolicyIngestionService()
    doc_id = uuid.uuid4()
    content_v1 = b"# Policy\nSection 1 original."
    content_v2 = b"# Policy\nSection 1 updated with new terms."
    mock_vec = [0.05] * 768

    with patch("backend.app.services.ingestion.gemini_service.embed_texts", return_value=[mock_vec]):
        with patch("backend.app.services.ingestion.supabase_service.upload_file", return_value="policy-documents/test.txt"):
            service.ingest_document(doc_id=doc_id, filename="test.txt", content=content_v1, db=db_session)
            assert db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count() == 1

            service.ingest_document(doc_id=doc_id, filename="test.txt", content=content_v2, db=db_session)
            chunks = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).all()
            assert len(chunks) == 1
            assert "new terms" in chunks[0].content


def test_retrieval_preserves_provenance_and_source_id(db_session: Session):
    """Verify hybrid retrieval preserves document provenance (source_id, canonical_url, section_path)."""
    retriever = HybridRetrievalService()
    doc = PolicyDocument(
        id=uuid.uuid4(),
        source_id="SRC-ZAPPOS-008",
        canonical_url="https://www.zappos.com/c/price-match",
        source_filename="zappos_price_matching.txt",
        content_hash="mock_hash",
        document_type="TXT",
        status="active",
    )
    db_session.add(doc)
    db_session.flush()

    chunk = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        chunk_index=0,
        section_path="Price Guarantee Policy",
        content="If you find the price has dropped within 10 days, refund is issued.",
        embedding=[0.05] * 768,
    )
    db_session.add(chunk)
    db_session.commit()

    with patch("backend.app.services.retrieval.gemini_service.embed_query", return_value=[0.05] * 768):
        results = retriever.retrieve(query="price drop within 10 days", db=db_session)

    assert len(results) >= 1
    top = results[0]
    assert top.source_id == "SRC-ZAPPOS-008"
    assert top.canonical_url == "https://www.zappos.com/c/price-match"
    assert top.source_filename == "zappos_price_matching.txt"
    assert top.section_path == "Price Guarantee Policy"
    assert top.to_dict()["source_id"] == "SRC-ZAPPOS-008"


def test_price_matching_complaint_retrieves_price_matching_policy(db_session: Session):
    """Verify price-matching complaints retrieve the price-matching policy rather than general FAQ alone."""
    retriever = HybridRetrievalService()

    # Doc 1: FAQ general questions
    doc_faq = PolicyDocument(
        id=uuid.uuid4(),
        source_id="SRC-ZAPPOS-003",
        source_filename="zappos_general_questions.txt",
        document_type="TXT",
        status="active",
    )
    # Doc 2: Specific Price Match policy
    doc_pm = PolicyDocument(
        id=uuid.uuid4(),
        source_id="SRC-ZAPPOS-008",
        source_filename="zappos_price_matching.txt",
        document_type="TXT",
        status="active",
    )
    db_session.add_all([doc_faq, doc_pm])
    db_session.flush()

    vec_faq = [0.0, 1.0] + [0.0] * 766
    vec_pm = [1.0, 0.0] + [0.0] * 766

    c_faq = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_faq.id,
        chunk_index=0,
        section_path="General FAQ",
        content="General question: Do you match prices? Please see our price match page.",
        embedding=vec_faq,
    )
    c_pm = PolicyChunk(
        id=uuid.uuid4(),
        document_id=doc_pm.id,
        chunk_index=0,
        section_path="Price Guarantee Policy",
        content="Price Guarantee: If you find an item reduced within 10 calendar days, we refund the difference.",
        embedding=vec_pm,
    )
    db_session.add_all([c_faq, c_pm])
    db_session.commit()

    with patch("backend.app.services.retrieval.gemini_service.embed_query", return_value=vec_pm):
        results = retriever.retrieve(
            query="shoes bought 6 days ago dropped in price refund difference",
            db=db_session,
        )

    assert len(results) > 0
    # Top retrieved item should be the specific price match policy
    assert results[0].source_id == "SRC-ZAPPOS-008"
    assert results[0].source_filename == "zappos_price_matching.txt"


def test_eval_cases_classification_and_safety():
    """Verify that price adjustment (EVAL-013) is covered and unauthorized auction match (EVAL-014) is prohibited."""
    c13 = "I bought running shoes 6 days ago for $140. Today they are marked down to $110 on your website. Refund the difference?"
    issues13 = complaint_analyzer.decompose_complaint(c13, is_adversarial=False)
    st13, _ = complaint_analyzer.assess_issue_policy(issues13[0], [], c13)
    assert st13 == "covered"

    c14 = "I want to buy boots for $180, but found an unauthorized seller listing them on an auction marketplace for $110. Will you price match?"
    issues14 = complaint_analyzer.decompose_complaint(c14, is_adversarial=False)
    st14, _ = complaint_analyzer.assess_issue_policy(issues14[0], [], c14)
    assert st14 == "prohibited"


def test_response_generation_citation_grounding_and_validation():
    """Verify response generation strictly grounds claims in retrieved chunk IDs and blocks hallucinated citations."""
    chunk_id = str(uuid.uuid4())
    fake_chunk_id = str(uuid.uuid4())

    issue = {
        "issue_text": "Price adjustment within 10 days",
        "assessment_status": "covered",
        "retrieved_evidence": [
            {
                "chunk_id": chunk_id,
                "section_path": "Price Guarantee Policy",
                "content": "Eligible for refund of price difference within 10 calendar days.",
            }
        ],
    }

    # Generate draft with valid evidence
    draft, citations, val = response_generator.generate_draft(
        complaint_text="My shoes dropped $30 in price 6 days after buying.",
        issues=[issue],
        tone="professional",
    )
    assert val.valid is True
    assert chunk_id in citations

    # Validate that injecting a fake chunk ID triggers validation failure
    tampered_draft = f"{draft} Also refer to policy [{fake_chunk_id}]."
    val_tampered = response_validator.validate_draft(
        draft_text=tampered_draft,
        issues=[issue],
        allowed_chunk_ids={chunk_id},
    )
    assert val_tampered.valid is False
    assert any("Invalid citation ID" in err for err in val_tampered.errors)
