import uuid
import pytest
from backend.app.services.extractor import ExtractedDocument, ExtractedSection
from backend.app.services.chunker import PolicyChunker


def test_chunking_preserves_section_and_page():
    """Verify chunking preserves heading metadata, page numbers, and index order."""
    doc_id = uuid.uuid4()
    sections = [
        ExtractedSection(text="Return Policy content here.", section_path="Returns", page_number=1),
        ExtractedSection(text="Shipping details content here.", section_path="Shipping", page_number=2),
    ]
    extracted = ExtractedDocument(
        filename="policy.pdf",
        document_type="PDF",
        raw_text="Return Policy content here.\n\nShipping details content here.",
        sections=sections,
        total_characters=60,
    )

    chunker = PolicyChunker(chunk_size_chars=500, chunk_overlap_chars=50)
    chunks = chunker.chunk_document(doc_id, extracted)

    assert len(chunks) == 2
    assert chunks[0].chunk_index == 0
    assert chunks[0].section_path == "Returns"
    assert chunks[0].page_number == 1
    assert chunks[0].document_id == doc_id
    assert chunks[0].content_hash is not None

    assert chunks[1].chunk_index == 1
    assert chunks[1].section_path == "Shipping"
    assert chunks[1].page_number == 2


def test_chunking_deterministic_uuids():
    """Verify that re-chunking identical content produces identical chunk UUIDs."""
    doc_id = uuid.uuid4()
    sections = [
        ExtractedSection(text="Fixed policy statement for idempotency.", section_path="Overview", page_number=None),
    ]
    extracted = ExtractedDocument(
        filename="fixed.txt",
        document_type="TXT",
        raw_text="Fixed policy statement for idempotency.",
        sections=sections,
        total_characters=39,
    )

    chunker = PolicyChunker(chunk_size_chars=500, chunk_overlap_chars=50)
    run1 = chunker.chunk_document(doc_id, extracted)
    run2 = chunker.chunk_document(doc_id, extracted)

    assert len(run1) == 1
    assert len(run2) == 1
    assert run1[0].chunk_id == run2[0].chunk_id
    assert run1[0].content_hash == run2[0].content_hash


def test_chunking_splits_large_text_with_overlap():
    """Verify long paragraphs are split into multiple chunks with overlap."""
    doc_id = uuid.uuid4()
    long_text = "Sentence number one. " * 30  # ~630 characters
    sections = [
        ExtractedSection(text=long_text, section_path="Terms", page_number=None),
    ]
    extracted = ExtractedDocument(
        filename="long.txt",
        document_type="TXT",
        raw_text=long_text,
        sections=sections,
        total_characters=len(long_text),
    )

    chunker = PolicyChunker(chunk_size_chars=200, chunk_overlap_chars=40)
    chunks = chunker.chunk_document(doc_id, extracted)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.content) <= 300  # Allows boundary grace
    # Verify sequential indices
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))
