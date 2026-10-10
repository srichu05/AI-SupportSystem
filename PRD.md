# Product Requirements Document (PRD)

## Intelligent Customer Complaint Response Assistant

**Status:** Working specification for implementation\
**Project context:** CBC 2.0 Intelligent Customer Complaint Response Assistant\
**Team:** TENSOR TITANS\
**Problem reference:** PS-40, as supplied in the project conversation\
**Domain:** AI & ML

> This document defines the intended product based on decisions
> currently made by the team. Any item marked **TBD** must be confirmed
> rather than guessed.

## 1. Product summary

Build a web application that helps customer-support staff draft accurate
responses to customer complaints using company policy documents as
evidence. The system should identify distinct issues in a complaint,
retrieve relevant policy passages, assess whether the available evidence
is sufficient, draft a response, validate its citations and commitments,
and present the draft to a human reviewer.

The system is a decision-support and drafting tool. It does **not**
autonomously send responses to customers.

## 2. Problem and intended users

### Problem

Support staff may need to interpret lengthy policy documents while
handling complaints that contain multiple issues, incomplete facts, or
requests that policy does not clearly cover. Manual lookup can be slow
and inconsistent. A generative model may also produce unsupported
promises if it is not constrained by policy evidence.

### Primary user

-   Customer-support agent or reviewer who reads a complaint, inspects
    policy evidence, edits a draft, and approves, rejects, or escalates
    it.

### Other stakeholders

-   A team lead or administrator who maintains policy documents and
    reviews past decisions, if these roles are included in the
    implemented scope.

Specific organization size, expected complaint volume, and business
impact are **TBD** and must not be invented.

## 3. Product goals

1.  Retrieve relevant company-policy evidence for each issue in a
    complaint.
2.  Draft a customer-friendly response that is grounded in retrieved
    evidence.
3.  Make sources and uncertainty visible to the reviewer.
4.  Avoid unsupported eligibility decisions, guarantees, refunds, or
    other commitments.
5.  Allow human editing and explicit approval, rejection, or escalation.
6.  Keep a basic record of drafts and review decisions.
7.  Deploy the application with a hosted frontend, backend, and
    database.

## 4. Non-goals for the initial system release

-   Automatically sending emails, chat messages, or other customer
    communications.
-   Replacing a human's final policy or eligibility decision.
-   Training a custom language model.
-   Building a multi-agent system.
-   Adding a reranker unless retrieval evaluation shows it is needed.
-   Supporting every possible file format or scanned document in the
    first version.
-   Claiming production-grade compliance, legal correctness, or
    guaranteed hallucination elimination.

## 5. Core user workflow

1.  A reviewer opens the application and submits a complaint.
2.  The backend extracts separate issues, requested resolutions, stated
    facts, and missing information.
3.  For each issue, the backend retrieves policy chunks using semantic
    vector search and PostgreSQL full-text search.
4.  The retrieval results are combined using Reciprocal Rank Fusion
    (RRF).
5.  The system assesses each issue using one of the defined policy
    statuses.
6.  The model generates a structured draft using the retrieved evidence.
7.  Backend validation checks the response structure, citation IDs,
    evidence references, and configured policy rules.
8.  If evidence is insufficient, policy is conflicting, or validation
    fails, the draft is flagged for human review rather than presented
    as an assured answer.
9.  The reviewer inspects the evidence, edits the draft, and approves,
    rejects, or escalates it.
10. The application stores the review outcome and relevant history.

## 6. Functional requirements

### FR-01: Complaint intake

-   Accept complaint text through the frontend.
-   Validate that required input is present.
-   Assign a stable complaint identifier.
-   Do not require or invent customer personal details that are not
    needed.

### FR-02: Policy document ingestion

-   Support PDF, DOCX, and TXT in the initial scope.
-   Extract text and preserve source filename, page where available,
    section/heading where available, document identifier/version, and
    chunk identifier.
-   Store original files in Supabase Storage and extracted
    chunks/metadata in Supabase PostgreSQL.
-   Detect documents that yield no usable text and report the issue. OCR
    is a later enhancement unless time permits.

### FR-03: Embedding generation

-   Use a hosted embedding API, not a locally loaded Sentence
    Transformers model.
-   Current candidate: Gemini Embedding 2 model ID `gemini-embedding-2`,
    with 768 dimensions.
-   This candidate is **not final until a real API test confirms model
    access, dimension output, quota, and account terms**.
-   Use the same embedding model and dimensions for indexed policy
    chunks and complaint queries.
-   Cache generated embeddings and avoid re-embedding unchanged content.

### FR-04: Hybrid retrieval

-   Semantic search uses Supabase PostgreSQL with pgvector.
-   Keyword search uses PostgreSQL full-text search.
-   Combine rankings with Reciprocal Rank Fusion (RRF).
-   Do not call PostgreSQL `ts_rank` BM25; it is PostgreSQL full-text
    ranking, not the BM25 algorithm.
-   Keep chunk identifiers consistent across both retrieval paths.
-   Initial tuning hypothesis: retrieve up to 10 candidates per path,
    fuse/deduplicate, and supply approximately 3--5 evidence chunks per
    issue. Validate these values against test cases.

### FR-05: Issue decomposition and assessment

-   Decompose multi-issue complaints into distinct issues.
-   Record the customer's stated facts, requested resolution, missing
    facts, and evidence chunk IDs.
-   Use these statuses: `covered`, `partially_covered`, `uncovered`,
    `prohibited`, `conflict`, `needs_human_review`.
-   `uncovered` means sufficient supporting policy evidence was not
    found. It does not mean the request is prohibited.
-   Do not infer customer eligibility from topical similarity alone.

### FR-06: Grounded draft generation

-   Use Gemini API for issue analysis and response drafting.
-   Prefer structured JSON output validated with Pydantic.
-   Require policy-dependent claims to cite retrieved chunk IDs.
-   Do not treat model-generated citations as valid until the backend
    checks that the IDs exist in the retrieved evidence set.
-   Do not invent policy details, deadlines, eligibility requirements,
    or commitments.

### FR-06A: Response tone stretch goal

- Generate alternative drafts in `professional`, `empathetic`, and `concise` tones.
- Tone changes may affect wording and style only; they must not change customer facts, policy interpretation, eligibility, commitments, escalation decisions, or supporting evidence.
- Validate each variant against the same retrieved evidence and factual constraints. Reuse the same valid citation references; reject or flag variants that introduce unsupported claims.
- Keep this as a stretch goal after the single grounded draft and validation flow works end to end.

### FR-07: Validation and escalation

-   Validate schema, status values, cited chunk IDs, and configured
    prohibited commitments/rules.
-   Treat keyword rules as supplementary safeguards, not the sole
    decision mechanism.
-   Flag insufficient evidence, conflicts, missing critical facts,
    invalid citations, or validation failures for human review.
-   A valid JSON object is not proof that the content is correct.

### FR-08: Human review

-   Display the complaint, extracted issues, policy evidence, draft, and
    validation/escalation messages.
-   Allow a reviewer to edit the draft.
-   Support approve, reject, and escalate actions.
-   Approval must not trigger automatic customer delivery in this
    system release.

### FR-09: Review history

-   Persist the original complaint, AI draft, final edited draft if any,
    review decision, timestamp, and optional reviewer reason.
-   Do not store unnecessary sensitive personal data.
-   Access-control details and retention policy are **TBD** and must be
    decided before real customer data is used.

## 7. Non-functional requirements

-   **Deployability:** Frontend on Vercel, FastAPI backend on Render,
    data and files in Supabase.
-   **Resilience:** Handle embedding/model API errors, timeouts, rate
    limits, and malformed model output without silently producing an
    unverified response.
-   **Traceability:** Every displayed policy passage must identify its
    source document and available page/section metadata.
-   **Security:** Keep secrets in environment variables; never commit
    credentials.
-   **Maintainability:** Keep parsing, retrieval, generation,
    validation, persistence, and API routing in separate modules.
-   **Performance:** Measure end-to-end latency during evaluation. No
    latency target is currently confirmed.
-   **Privacy:** Use synthetic or approved test complaints until
    provider data-use terms and organizational requirements are
    reviewed.

## 8. Acceptance criteria for the demo

The minimum demo is acceptable when: - A supported PDF/DOCX/TXT policy
can be ingested and searched. - A complaint can be submitted through the
frontend. - The backend decomposes a multi-issue complaint or clearly
returns one issue where appropriate. - Hybrid retrieval returns
traceable policy chunks. - The response draft cites valid retrieved
chunk IDs for policy-dependent claims. - Missing evidence and policy
conflicts lead to review/escalation rather than unsupported certainty. -
A reviewer can edit and approve/reject/escalate the draft. - Review
decisions are persisted in Supabase. - The deployed frontend
communicates with the deployed backend and Supabase. - No customer
message is sent automatically.

## 9. Success measures

Use a small manually labelled evaluation set (start with 8--12 cases).
Track: - Whether relevant evidence appears in the retrieved results. -
Issue coverage. - Citation-ID validity and human-assessed citation
support. - Unsupported commitments. - Correct escalation/abstention when
evidence is insufficient. - End-to-end latency. - Reviewer assessment of
usefulness.

Do not report numerical performance claims until measured.

## 10. Open decisions / TBD

-   Exact official problem-statement wording.
-   Exact Gemini generation model ID and API availability.
-   Confirmation that Gemini Embedding 2 is available to the project's
    API key and can return 768-dimensional vectors.
-   Supabase project configuration, region, quotas, and connection
    method.
-   Authentication and role model, if required by the organizers.
-   Exact frontend pages and visual design (owned by frontend teammate;
    separate UI/UX specification).
-   Data retention and privacy requirements.
-   Whether OCR is included in the first version.
