# Database Schema and Persistence Plan

## Supabase PostgreSQL + pgvector

**Status:** Logical schema proposal. Confirm exact SQL, constraints,
access policies, and authentication integration during implementation.

## 1. Design principles

-   Supabase PostgreSQL is the persistent source of truth.
-   Supabase Storage stores original policy files.
-   Use stable identifiers for documents, chunks, complaints, issues,
    drafts and review decisions.
-   Preserve source metadata so policy evidence can be traced back to a
    document and page/section where available.
-   Store embeddings with a known model ID and dimension.
-   Do not mix embeddings from different models or dimensions in one
    vector search.
-   Use migrations for repeatable schema setup.
-   Do not store unnecessary personal data.

## 2. Suggested entities

### `policy_documents`

Represents an uploaded policy document and its version.

Suggested fields: - `id` --- UUID primary key. - `source_filename` ---
original filename. - `storage_path` --- path/key in Supabase Storage. -
`document_type` --- PDF, DOCX, or TXT. - `version_label` --- optional
version supplied by the uploader. - `effective_from` / `effective_to`
--- optional dates only if known from source or entered by an authorized
user. - `status` --- ingestion and activation state, with defined
allowed values. - `created_at` --- timestamp.

Do not invent effective dates. If policy applicability cannot be
determined, surface that uncertainty.

### `policy_chunks`

One row per searchable text chunk.

Suggested fields: - `id` --- stable UUID or other stable primary key. -
`document_id` --- foreign key to `policy_documents`. - `chunk_index` ---
ordering within a document. - `section_path` --- optional heading
hierarchy. - `page_number` --- nullable; not all formats provide
pages. - `content` --- chunk text. - `embedding` --- pgvector column
with dimension matching the configured hosted embedding model. -
`embedding_model` --- model identifier used to generate the vector. -
`content_hash` --- optional hash to detect unchanged content. -
`created_at` --- timestamp.

Add a uniqueness constraint for the document/chunk position or stable
chunk identity as appropriate.

### `complaints`

One row per submitted complaint.

Suggested fields: - `id` --- UUID primary key. - `complaint_text` ---
complaint input. - `processing_status` --- lifecycle status. -
`created_at` and `updated_at` --- timestamps. - Optional non-sensitive
metadata only when needed.

### `complaint_issues`

One row per extracted issue within a complaint.

Suggested fields: - `id` --- UUID primary key. - `complaint_id` ---
foreign key to `complaints`. - `issue_text` --- normalized description
of the issue. - `requested_resolution` --- if identified. -
`customer_facts` --- structured facts, only when required. -
`missing_facts` --- structured list or JSON. - `assessment_status` ---
one of the defined policy statuses. - `created_at` --- timestamp.

### `issue_evidence`

Links a complaint issue to a retrieved policy chunk.

Suggested fields: - `id` --- UUID primary key. - `issue_id` --- foreign
key to `complaint_issues`. - `chunk_id` --- foreign key to
`policy_chunks`. - `retrieval_source` --- e.g. vector or full-text
search. - `retrieval_rank` --- rank in the original result list. -
`fusion_score` --- optional RRF score, not a confidence or eligibility
score. - `created_at` --- timestamp.

### `response_drafts`

Stores generated and final draft versions.

Suggested fields: - `id` --- UUID primary key. - `complaint_id` ---
foreign key to `complaints`. - `draft_text` --- draft content. -
`structured_output` --- optional JSON output for issues, claims, and
citations. - `validation_status` --- result of backend validation. -
`created_at` --- timestamp.

### `review_decisions`

Stores reviewer actions.

Suggested fields: - `id` --- UUID primary key. - `complaint_id` ---
foreign key to `complaints`. - `draft_id` --- foreign key to the draft
reviewed. - `decision` --- approved, rejected, or escalated. -
`final_response_text` --- edited final text when applicable. - `reason`
--- optional reviewer explanation. - `reviewed_at` --- timestamp. -
`reviewer_id` --- nullable until authentication/role model is confirmed.

These names and fields are proposals, not a requirement to use exactly
this schema. Keep the initial schema focused and minimal
while retaining source traceability and review history.

## 3. Search design

### Semantic search

-   Enable the `vector` extension in Supabase.
-   Configure `policy_chunks.embedding` to the verified output dimension
    of the selected hosted embedding model.
-   Query using the same model and dimension used at ingestion.
-   Start with exact vector search for a small corpus; add an
    approximate index only if measured performance requires it.
-   Filter out inactive or inapplicable document versions when that
    information is reliable and available.

### Keyword search

Use PostgreSQL full-text search over chunk content. A generated
`tsvector` column and a GIN index are possible implementation choices.
Decide language configuration based on the policy corpus. The current
assumption is English, but this must be confirmed against the actual
files.

PostgreSQL full-text ranking is not BM25. Do not describe it as BM25 in
code, docs, or presentation.

### Fusion

-   Run the two searches independently.
-   Combine their ranked lists with Reciprocal Rank Fusion (RRF).
-   Deduplicate by stable chunk ID.
-   Preserve the original rank/source for diagnostics.
-   RRF scores are ranking values, not calibrated probabilities or
    eligibility judgments.

## 4. Supabase Storage

Store original policy files in a dedicated bucket. Keep the bucket
private unless a documented requirement says otherwise. Store the
storage key in `policy_documents`; do not expose service-role
credentials in the browser.

Access rules and Row Level Security (RLS) policies must be designed for
the actual authentication model. Do not assume that hiding a URL is
sufficient access control.

## 5. Migrations and environments

-   Apply schema changes through Alembic migrations or a clearly
    versioned SQL migration workflow.
-   Test migrations against the project Supabase database before
    deploying.
-   Store database connection strings as Render environment variables.
-   Use the appropriate Supabase connection/pooler configuration for the
    deployment environment.
-   Never commit secrets or production database dumps.

## 6. Open items

-   Confirm whether Clerk is required for the complaint assistant; it is
    not yet finalized for this project.
-   Decide whether reviewer identity is required in the first demo.
-   Confirm the embedding model, exact dimension, and pgvector type.
-   Confirm retention and deletion requirements.
-   Confirm policy version/effective-date workflow.
-   Define RLS policies before using real or sensitive customer data.
