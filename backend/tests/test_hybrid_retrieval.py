import uuid
from unittest.mock import patch
import pytest
from sqlalchemy.orm import Session

from backend.app.models.policy import PolicyDocument, PolicyChunk
from backend.app.services.ingestion import PolicyIngestionService
from backend.app.services.retrieval import HybridRetrievalService, RetrievedChunk
from backend.app.core.errors import EmptyDocumentException


def test_reciprocal_rank_fusion_math():
    """Verify Reciprocal Rank Fusion formula and ranking mechanics."""
    retriever = HybridRetrievalService(rrf_k=60)

    # Document 1 appears in both lists: Rank 1 in semantic, Rank 1 in keyword
    # Fused score = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.032787
    doc1_cid = str(uuid.uuid4())
    sem_list = [
        {"chunk_id": doc1_cid, "document_id": "d1", "source_filename": "f1.txt", "content": "text 1", "rank": 1, "score": 0.9},
        {"chunk_id": "c2", "document_id": "d1", "source_filename": "f1.txt", "content": "text 2", "rank": 2, "score": 0.8},
    ]
    kw_list = [
        {"chunk_id": doc1_cid, "document_id": "d1", "source_filename": "f1.txt", "content": "text 1", "rank": 1, "score": 1.0},
        {"chunk_id": "c3", "document_id": "d1", "source_filename": "f1.txt", "content": "text 3", "rank": 2, "score": 0.5},
    ]

    fused = retriever._reciprocal_rank_fusion(
        semantic_results=sem_list,
        keyword_results=kw_list,
        rrf_k=60,
        final_top_k=3,
    )

    assert len(fused) == 3
    # Top chunk should be doc1_cid because it scored in both lists
    assert fused[0].chunk_id == doc1_cid
    expected_score = (1.0 / 61.0) + (1.0 / 61.0)
    assert abs(fused[0].rrf_score - expected_score) < 1e-6
    assert fused[0].semantic_rank == 1
    assert fused[0].keyword_rank == 1

    # Second chunk should have score 1/62 ≈ 0.016129
    assert abs(fused[1].rrf_score - (1.0 / 62.0)) < 1e-6


def test_ingestion_lifecycle_success(db_session: Session):
    """Verify ingestion creates active document, saves chunks, and generates 768-dim embeddings."""
    service = PolicyIngestionService()
    doc_id = uuid.uuid4()
    content = b"# Policy\nRefunds within 30 days are accepted."

    # Mock Gemini embedding service to return valid 768-dim vectors
    mock_vector = [0.05] * 768
    with patch("backend.app.services.ingestion.gemini_service.embed_texts", return_value=[mock_vector]):
        with patch("backend.app.services.ingestion.supabase_service.upload_file", return_value="policy-documents/test.txt"):
            doc = service.ingest_document(
                doc_id=doc_id,
                filename="test.txt",
                content=content,
                version_label="v1",
                db=db_session,
            )

    assert doc.status == "active"
    assert doc.source_filename == "test.txt"
    chunks = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).all()
    assert len(chunks) == 1
    assert chunks[0].content == "Refunds within 30 days are accepted."
    assert chunks[0].section_path == "Policy"
    assert chunks[0].embedding == mock_vector
    assert chunks[0].chunk_index == 0


def test_duplicate_ingestion_replaces_chunks(db_session: Session):
    """Verify re-ingesting an existing document updates chunks without creating duplicates or orphans."""
    service = PolicyIngestionService()
    doc_id = uuid.uuid4()

    mock_vec = [0.1] * 768
    with patch("backend.app.services.ingestion.gemini_service.embed_texts", return_value=[mock_vec]):
        with patch("backend.app.services.ingestion.supabase_service.upload_file", return_value="policy-documents/test.txt"):
            # Initial ingestion
            service.ingest_document(
                doc_id=doc_id,
                filename="test.txt",
                content=b"# Original\nInitial rule text.",
                db=db_session,
            )
            initial_count = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count()
            assert initial_count == 1

            # Second ingestion with updated text
            service.ingest_document(
                doc_id=doc_id,
                filename="test.txt",
                content=b"# Updated\nNew rule text.",
                db=db_session,
            )
            updated_count = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count()
            assert updated_count == 1
            chunk = db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).first()
            assert "New rule text" in chunk.content


def test_ingestion_failure_marks_document_failed(db_session: Session):
    """Verify ingestion errors safely mark document status as 'failed' and do not leave orphaned chunks."""
    service = PolicyIngestionService()
    doc_id = uuid.uuid4()

    with pytest.raises(EmptyDocumentException):
        service.ingest_document(
            doc_id=doc_id,
            filename="empty.txt",
            content=b"",
            db=db_session,
        )

    # Document record should exist with 'failed' status
    doc = db_session.query(PolicyDocument).filter(PolicyDocument.id == doc_id).first()
    assert doc is not None
    assert doc.status == "failed"
    # Zero chunks persisted
    assert db_session.query(PolicyChunk).filter(PolicyChunk.document_id == doc_id).count() == 0


def test_hybrid_retrieval_active_filter(db_session: Session):
    """Verify retrieval excludes chunks from documents that are not 'active'."""
    retriever = HybridRetrievalService()

    active_doc = PolicyDocument(id=uuid.uuid4(), source_filename="active.txt", document_type="TXT", status="active")
    inactive_doc = PolicyDocument(id=uuid.uuid4(), source_filename="old.txt", document_type="TXT", status="archived")
    db_session.add_all([active_doc, inactive_doc])

    c1 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=active_doc.id,
        chunk_index=0,
        content="Active policy return window 60 days.",
        embedding=[0.1] * 768,
    )
    c2 = PolicyChunk(
        id=uuid.uuid4(),
        document_id=inactive_doc.id,
        chunk_index=0,
        content="Archived policy return window 90 days.",
        embedding=[0.1] * 768,
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    with patch("backend.app.services.retrieval.gemini_service.embed_query", return_value=[0.1] * 768):
        results = retriever.retrieve(query="return window", db=db_session, filter_active_only=True)

    assert len(results) == 1
    assert results[0].document_id == str(active_doc.id)
    assert "Active policy" in results[0].content
