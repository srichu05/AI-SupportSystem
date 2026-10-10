# Policy Ingestion and Hybrid Retrieval Pipeline

## RAG design for the Complaint Response Assistant

## 1. Objective

Retrieve traceable, relevant policy evidence for each distinct issue in
a customer complaint. Retrieval supplies evidence for downstream
assessment and drafting; it does not independently determine
eligibility.

## 2. Ingestion

### Supported inputs

-   PDF: PyMuPDF.
-   DOCX: python-docx.
-   TXT: Python built-ins.

Scanned PDFs may not yield usable text. OCR is an optional later
enhancement; do not claim scanned-PDF support until implemented and
tested.

### Extraction requirements

Preserve as available: - Original filename and document ID. - Document
version/effective-date metadata only when known. - Page number for
page-based formats. - Heading/section path when extractable. - Extracted
text and stable chunk ID. - Ingestion status and errors.

DOCX may not have page numbers in a stable way. Do not fabricate them.

### Chunking

-   Prefer heading-aware splitting.
-   Keep chunks small enough to retrieve a specific policy rule,
    condition, exception, or procedure.
-   Preserve heading/section context in chunk text or metadata.
-   Initial experiment: roughly 350--500 tokens per chunk with 50--75
    tokens of overlap, adjusted to the actual document structure.
-   Do not split tables or numbered conditions in a way that destroys
    their meaning.
-   Store chunk metadata alongside each chunk.

These chunk sizes are starting hypotheses, not universal rules. Inspect
sample chunks before indexing the whole corpus.

## 3. Hosted embeddings

The project must not load a local Sentence Transformers model in Render.

Current candidate: - Gemini Embedding 2, model ID
`gemini-embedding-2`. - Target output dimension: 768.

Before indexing, run an API smoke test to confirm model access, quota,
request/response format, and output dimensions. Keep model ID and
dimensions configurable. If the selected model changes, regenerate all
vectors; do not mix incompatible vector spaces.

Batch embedding requests where supported. Cache embeddings and use
content hashes or another stable change-detection method to avoid
repeated work on unchanged policy chunks. Apply bounded retries and
handle rate limits/timeouts.

## 4. Hybrid retrieval

### Semantic path

1.  Normalize the issue/query text consistently.
2.  Request a hosted query embedding using the same embedding model as
    the indexed policy chunks.
3.  Query Supabase pgvector for the nearest eligible chunks.
4.  Return chunk ID, document/version metadata, page/section, content,
    and semantic rank or distance.

### Keyword path

1.  Convert issue/query text to PostgreSQL full-text search
    representation using a consistent text-search configuration.
2.  Search chunk content.
3.  Return the same stable chunk identifiers and source metadata, along
    with keyword rank.

PostgreSQL full-text search is not strict BM25. This project uses
PostgreSQL full-text search for the initial implementation.

### Fusion

Use Reciprocal Rank Fusion:

`RRF(d) = sum over result lists of 1 / (k + rank(d))`

A conventional starting value is `k = 60`. Ranks should be one-based. A
document absent from a list contributes nothing from that list.
Deduplicate by chunk ID after fusion.

Initial candidate settings: - Retrieve up to 10 chunks from each search
path. - Fuse and deduplicate. - Pass approximately 3--5 chunks per issue
to the assessment/drafting stage.

Tune with labelled test cases. A fused score is not a probability, a
policy confidence score, or proof of eligibility.

## 5. Filtering and policy versions

When policy status/version is known and trustworthy: - Exclude
inactive/revoked documents from normal current-policy retrieval. -
Prefer applicable versions according to explicit metadata/rules. -
Retain version and source metadata for reviewer display. - If two
applicable policy passages conflict or applicability is unclear, mark
the issue for review rather than arbitrarily choosing one.

Do not invent effective dates or infer that the newest uploaded file is
necessarily authoritative unless an explicit rule establishes this.

## 6. Issue-by-issue retrieval

A single complaint can include unrelated requests. Do not rely
exclusively on one query for the entire complaint.

For each extracted issue: - Preserve issue text and requested
resolution. - Identify missing customer facts. - Search for the issue
and its key terms. - Retrieve evidence independently. - Associate
evidence IDs with that issue. - Assess each issue separately, then
compose a coherent response that does not merge unsupported conclusions.

## 7. Evidence and citations

Every retrieved chunk shown to a reviewer should expose its source
document and available section/page information. Each policy-dependent
claim in the draft must refer to valid retrieved chunk IDs.

Backend validation must check: - Every cited chunk ID exists in the
evidence set for this request. - The evidence actually belongs to the
relevant issue/retrieval context. - Citations can be rendered to a real
source record. - Missing or conflicting evidence triggers review.

Valid IDs alone do not prove that a claim is semantically supported.
Include human spot checks in evaluation.

## 8. Failure cases

-   Empty query embedding or provider failure: do not run incompatible
    vector search; return a retryable failure or review state.
-   No relevant passage: mark `uncovered` or `needs_human_review`, not
    automatically `prohibited`.
-   Search results conflict: mark `conflict`.
-   Top-ranked passage discusses the same topic but not eligibility: do
    not claim eligibility.
-   Malformed/empty source document: fail or flag ingestion.
-   Partial ingestion: do not mark the document fully indexed until all
    required steps succeed.
-   Prompt injection in a policy file or complaint: treat text as
    untrusted data; it must not override system instructions or
    validation rules.

## 9. Evaluation

Create manually labelled complaint-to-evidence examples. Compare hybrid
retrieval against vector-only or keyword-only on a small sample if time
allows. Track whether the relevant policy chunk appears in the top
results and inspect false positives. Do not assume hybrid retrieval is
always better without testing.
