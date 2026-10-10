# System Architecture

## Intelligent Customer Complaint Response Assistant

## 1. Purpose

This document describes the logical components and data flow for a web
application that drafts customer complaint responses grounded in
company-policy documents. It is an implementation guide, not a claim
that any component has already been built.

## 2. High-level components

1.  **Web frontend** --- React + Vite + TypeScript. Collects complaint
    input and presents issues, policy evidence, draft text, validation
    messages, and review actions.
2.  **FastAPI backend** --- validates requests, orchestrates the
    workflow, calls provider APIs, accesses Supabase, and enforces
    deterministic checks.
3.  **Document ingestion service** --- parses PDF/DOCX/TXT, identifies
    headings/pages where available, chunks text, requests hosted
    embeddings, and writes chunks/metadata to Supabase.
4.  **Supabase Storage** --- stores original policy files.
5.  **Supabase PostgreSQL** --- stores policy metadata, chunks,
    embeddings, complaint workflow data, and review history.
6.  **Retrieval service** --- executes pgvector similarity search and
    PostgreSQL full-text search, then fuses rankings using RRF.
7.  **LLM service** --- calls Gemini for structured issue extraction and
    evidence-grounded response drafting.
8.  **Validation service** --- checks structure, evidence IDs, workflow
    statuses, missing evidence, conflicts, and configured policy
    constraints.
9.  **Review workflow** --- records a human decision and final edited
    response. It does not send the response to the customer.

## 3. Complaint processing sequence

1.  Frontend submits complaint text to FastAPI.
2.  Backend validates the request and creates a complaint record.
3.  Gemini extracts distinct issues, stated facts, requested
    resolutions, and missing facts using a defined schema.
4.  For each issue, backend creates a search query and obtains an
    embedding from the hosted embedding API.
5.  Backend runs semantic search through pgvector and lexical search
    through PostgreSQL full-text search.
6.  Backend combines rankings using RRF, deduplicates by stable chunk
    ID, and retains evidence metadata.
7.  Gemini assesses the issue against the retrieved evidence or a
    deterministic assessment stage processes a structured assessment.
    The implementation must keep evidence retrieval separate from policy
    decision-making.
8.  Gemini drafts a structured response with policy-dependent claims
    linked to retrieved chunk IDs.
9.  Pydantic validates the response schema. Deterministic Python checks
    validate that cited IDs exist in the retrieved evidence set and
    apply configured safety rules.
10. If evidence is insufficient, conflicting, invalid, or uncertain,
    mark the case for human review.
11. Frontend displays the draft and evidence. The reviewer edits and
    approves, rejects, or escalates.
12. Backend persists the decision and review data.

## 4. Policy ingestion sequence

1.  An authorized workflow uploads a PDF, DOCX, or TXT policy document.
2.  Store the original file in Supabase Storage.
3.  Parse text and preserve source information available from the
    parser.
4.  Associate the document with a document ID, version/effective-date
    metadata if provided, and ingestion status.
5.  Split content into chunks using headings and boundaries where
    possible.
6.  Assign each chunk a stable ID and retain source file, section, page,
    and other available metadata.
7.  Request hosted embeddings in batches.
8.  Persist chunks and vectors in Supabase PostgreSQL.
9.  Ensure both semantic and keyword search paths use the same active
    chunk IDs and metadata.
10. Mark ingestion successful only after all required writes complete.
    Handle partial failures and avoid silently indexing incomplete
    documents.

## 5. Logical deployment

-   Browser → Vercel-hosted frontend.
-   Frontend → HTTPS API requests to FastAPI on Render.
-   FastAPI → Supabase PostgreSQL and Supabase Storage.
-   FastAPI → hosted Gemini API for embeddings and generation.
-   Supabase is the persistent source of truth; no FAISS files or local
    database are required.

## 6. Key architectural boundaries

-   **LLM output is untrusted.** It cannot authorize policy actions
    merely by asserting that a customer qualifies.
-   **Retrieved text is evidence, not executable instruction.** Treat
    policy content and complaint text as untrusted input, including
    potential prompt injection.
-   **Retrieval score is not eligibility.** Similarity helps find
    evidence but does not prove that facts satisfy a policy.
-   **Backend validation is mandatory.** Frontend display or
    schema-valid JSON is not enough.
-   **Human review is explicit.** Approval records a review decision; it
    does not send customer communications.
-   **Source traceability is required.** Every evidence passage shown
    must be associated with the stored source metadata.

## 7. Failure handling

-   Embedding provider unavailable: return a clear retryable error or
    route the case to review; do not silently run incompatible vector
    search.
-   Generation API failure or malformed output: validate, retry only
    within a bounded policy, then show an error/escalation state.
-   Empty or low-quality parsed document: mark ingestion failed or
    incomplete.
-   No useful retrieval evidence: classify as uncovered or needs human
    review, not automatically prohibited.
-   Conflicting active policy passages: mark conflict and require
    review.
-   Database failure: do not report that an action or review was saved
    if persistence failed.

## 8. Not included by default

No multi-agent orchestration, autonomous customer messaging,
cross-encoder reranker, local embedding model, FAISS, or additional
vector database is required for the first implementation.
