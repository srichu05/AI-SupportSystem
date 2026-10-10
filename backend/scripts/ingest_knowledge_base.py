#!/usr/bin/env python3
"""
Ingest Initial Knowledge Base into Supabase for CBC 2.0 (PS-40)

Sources:
- data/policy_documents/zappos_shipping_and_returns.txt
- data/policy_documents/zappos_conditions_of_use.txt

This script:
1. Uploads original text files to Supabase Storage bucket 'policy-documents'
2. Parses text and generates heading-aware chunks with stable UUIDs
3. Computes 768-dim embeddings using verified 'gemini-embedding-2'
4. Persists document records and chunk vectors in Supabase PostgreSQL
5. Runs test queries using Hybrid Retrieval (pgvector + full-text search + RRF)
"""

import sys
import uuid
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.core.database import get_session_factory
from backend.app.services.ingestion import policy_ingestion_service
from backend.app.services.retrieval import hybrid_retrieval_service
from backend.app.models.policy import PolicyDocument, PolicyChunk

DATA_DIR = PROJECT_ROOT / "data" / "policy_documents"

SOURCES = [
    {
        "filename": "zappos_shipping_and_returns.txt",
        "source_id": "SRC-ZAPPOS-001",
        "canonical_url": "https://www.zappos.com/c/shipping-and-returns",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_shipping_and_returns.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos Shipping and Return Policies",
    },
    {
        "filename": "zappos_conditions_of_use.txt",
        "source_id": "SRC-ZAPPOS-002",
        "canonical_url": "https://www.zappos.com/terms-of-use",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_conditions_of_use.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos Conditions of Use & Terms",
    },
    {
        "filename": "zappos_general_questions.txt",
        "source_id": "SRC-ZAPPOS-003",
        "canonical_url": "https://www.zappos.com/c/general-questions",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_general_questions.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos General Questions & FAQ",
    },
    {
        "filename": "zappos_customer_service_hub.txt",
        "source_id": "SRC-ZAPPOS-004",
        "canonical_url": "https://www.zappos.com/c/customer-service",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_customer_service_hub.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos Customer Service Hub",
    },
    {
        "filename": "zappos_vip_terms.txt",
        "source_id": "SRC-ZAPPOS-005",
        "canonical_url": "https://www.zappos.com/c/vip-terms-and-conditions",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_vip_terms.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos VIP Program Terms and Conditions",
    },
    {
        "filename": "zappos_privacy_policy.txt",
        "source_id": "SRC-ZAPPOS-006",
        "canonical_url": "https://www.zappos.com/c/privacy-policy",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_privacy_policy.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos Privacy Policy",
    },
    {
        "filename": "zappos_price_matching.txt",
        "source_id": "SRC-ZAPPOS-008",
        "canonical_url": "https://www.zappos.com/c/price-match",
        "doc_id": uuid.uuid5(uuid.NAMESPACE_DNS, "zappos_price_matching.txt"),
        "version_label": "demo-v1.0",
        "description": "Zappos Price Matching and Price Guarantee Policy",
    },
]


def ingest_initial_corpus():
    print("=" * 70)
    print("Intelligent Customer Complaint Response Assistant (PS-40)")
    print("Phase 2 & Phase 3: Audited Policy Knowledge Base Ingestion")
    print("=" * 70)

    factory = get_session_factory()
    if factory is None:
        print("[FAIL] Database is not configured. Check DATABASE_URL in .env.")
        sys.exit(1)

    ingested_docs = []

    for src in SOURCES:
        file_path = DATA_DIR / src["filename"]
        if not file_path.exists():
            print(f"[FAIL] Required policy document not found: {file_path}")
            sys.exit(1)

        print(f"\nProcessing {src['filename']}...")
        print(f"  Stable Document ID: {src['doc_id']}")
        print(f"  Source ID: {src['source_id']} | Canonical URL: {src['canonical_url']}")
        content = file_path.read_bytes()
        print(f"  File size: {len(content)} bytes ({len(content.decode('utf-8', errors='ignore'))} characters)")

        try:
            with factory() as session:
                doc = policy_ingestion_service.ingest_document(
                    doc_id=src["doc_id"],
                    filename=src["filename"],
                    content=content,
                    source_id=src["source_id"],
                    canonical_url=src["canonical_url"],
                    version_label=src["version_label"],
                    db=session,
                )
                chunk_count = session.query(PolicyChunk).filter(PolicyChunk.document_id == src["doc_id"]).count()
                print(f"  [SUCCESS] Status: {doc.status}")
                print(f"  Storage Path: {doc.storage_path}")
                print(f"  Source ID: {doc.source_id}")
                print(f"  Persisted Chunks: {chunk_count}")
                ingested_docs.append((doc, chunk_count))
        except Exception as exc:
            print(f"  [ERROR] Ingestion failed: {exc}")
            raise

    # Verification checks
    print("\n" + "=" * 70)
    print("Verifying Hybrid Retrieval against Ingested Policies...")
    print("=" * 70)

    test_queries = [
        "What is the return window and what condition must shoes be in?",
        "Do you ship to military APO addresses and how long does it take?",
        "What happens if a product received does not match the product description?",
        "Can I get a price adjustment if the shoes I bought 6 days ago dropped in price?",
        "Will you price match boots sold by an unauthorized seller on an auction marketplace?",
        "Do my VIP loyalty points expire if I have not used my account for over a year?",
    ]

    with factory() as session:
        for idx, q in enumerate(test_queries, 1):
            print(f"\nQuery {idx}: '{q}'")
            results = hybrid_retrieval_service.retrieve(
                query=q,
                db=session,
                top_k_vector=5,
                top_k_keyword=5,
                final_top_k=3,
            )
            print(f"  Retrieved {len(results)} passages (RRF):")
            for rank, r in enumerate(results, 1):
                preview = r.content.replace("\n", " ")[:120]
                print(f"    [{rank}] Chunk ID: {r.chunk_id}")
                print(f"        Source: {r.source_filename} (Source ID: {r.source_id}) | Section: {r.section_path or 'N/A'}")
                print(f"        RRF Score: {r.rrf_score:.5f} | Sem Rank: {r.semantic_rank} | KW Rank: {r.keyword_rank}")
                print(f"        Preview: \"{preview}...\"")

    print("\n" + "=" * 70)
    print(f"[SUCCESS] Knowledge base ingestion complete. {len(ingested_docs)} documents indexed.")
    print("=" * 70)


if __name__ == "__main__":
    ingest_initial_corpus()
