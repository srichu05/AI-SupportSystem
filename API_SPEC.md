# API Contract

## FastAPI backend for the Complaint Response Assistant

**Status:** Proposed API contract. Endpoint names and exact schemas must
be implemented and kept consistent with the frontend. This is not a
claim that these endpoints already exist.

## 1. Conventions

-   JSON request and response bodies unless a file upload is specified.
-   Use standard HTTP status codes and consistent error objects.
-   Generate and return stable IDs for persisted records.
-   Validate requests and structured model responses with Pydantic.
-   Do not expose provider API keys, Supabase service-role keys, or raw
    internal secrets.
-   Every API call that triggers external model use should have bounded
    timeouts and error handling.

## 2. Proposed endpoints

### `GET /health`

Purpose: Basic process health check.

Example response:

``` json
{
  "status": "ok"
}
```

This endpoint should not expose credentials or sensitive infrastructure
details.

### `POST /api/v1/policies`

Purpose: Upload and ingest a PDF, DOCX, or TXT policy document.

Request: `multipart/form-data` with a file and optional metadata fields
such as a version label. Effective dates must only be accepted as
supplied/verified metadata.

Possible response:

``` json
{
  "document_id": "uuid",
  "status": "processing"
}
```

If ingestion is synchronous in the first version, the response may
instead report completed/failed status. Choose one behaviour and
document it; do not return `processing` unless background processing is
actually implemented.

### `GET /api/v1/policies`

Purpose: List policy documents and their ingestion/activation status.

Response fields may include document ID, source filename, type, version
label, status, and created timestamp. Do not expose private storage
credentials.

### `POST /api/v1/complaints`

Purpose: Submit a complaint and process it through issue extraction,
retrieval, assessment, draft generation, and validation.

Proposed request:

``` json
{
  "complaint_text": "The customer complaint text goes here.",
  "response_tone": "professional",
  "generate_tone_variants": false
}
```

The exact request may include optional non-sensitive metadata if
required. Avoid collecting unnecessary customer personal information.

Proposed response shape:

``` json
{
  "complaint_id": "uuid",
  "status": "needs_human_review",
  "issues": [
    {
      "issue_id": "uuid",
      "issue_text": "Summary of one distinct issue",
      "requested_resolution": "Requested outcome, if identified",
      "assessment_status": "covered",
      "missing_facts": [],
      "evidence": [
        {
          "chunk_id": "stable-chunk-id",
          "document_id": "uuid",
          "source_filename": "policy.pdf",
          "section": "Refund eligibility",
          "page_number": 3,
          "content": "Retrieved policy text"
        }
      ]
    }
  ],
  "draft": {
    "draft_id": "uuid",
    "text": "Draft response text",
    "citations": ["stable-chunk-id"]
  },
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  }
}
```

This is illustrative, not a fixed final schema. Ensure `status`
represents the overall case state and each issue's `assessment_status`
represents that issue's state.

Optional tone fields are a stretch goal. `response_tone` may be `professional`, `empathetic`, or `concise`; default to `professional`. If `generate_tone_variants` is true, the response may include a `draft_variants` object keyed by those tone names. Every variant must retain the same facts, policy decisions, commitments, escalation outcome, and valid evidence citations. Validate every variant independently; do not imply tone variation guarantees factual equivalence without checks.

### `GET /api/v1/complaints/{complaint_id}`

Purpose: Retrieve a complaint, its issues, evidence, draft and review
status.

### `POST /api/v1/complaints/{complaint_id}/review`

Purpose: Record a reviewer decision.

Proposed request:

``` json
{
  "draft_id": "uuid",
  "decision": "approved",
  "final_response_text": "Optional edited response",
  "reason": "Optional reviewer reason"
}
```

Allowed decision values: `approved`, `rejected`, `escalated`. Validate
them server-side. An approved review must not send a customer message.

### `GET /api/v1/complaints/{complaint_id}/history`

Purpose: Retrieve permitted draft/review history for a complaint.

Implement only if the UI needs it within the initial scope; otherwise
history may be returned through the complaint detail endpoint.

## 3. Error shape

Use a consistent structure such as:

``` json
{
  "error": {
    "code": "EMBEDDING_PROVIDER_UNAVAILABLE",
    "message": "Policy search is temporarily unavailable.",
    "retryable": true
  }
}
```

Do not return stack traces, API keys, database URLs, or raw provider
credentials to the client.

Suggested error categories: - Invalid input. - Unsupported file type. -
Empty/unreadable document. - Provider rate limit or unavailable. -
Invalid model output. - Policy not ingested. - Database unavailable. -
Complaint or draft not found. - Invalid review decision. - Citation
validation failure.

## 4. Validation and status semantics

Issue statuses: - `covered` - `partially_covered` - `uncovered` -
`prohibited` - `conflict` - `needs_human_review`

Keep the distinction between `uncovered` and `prohibited`. Define
overall complaint workflow states separately from per-issue policy
states.

## 5. API security

-   Configure CORS for known frontend origins.
-   Store secrets only in server-side environment variables.
-   Add authentication/authorization if required by the final product
    scope; the auth provider is not yet finalized.
-   Apply upload size and file-type limits.
-   Do not assume UUIDs alone are access control.
-   Enforce reviewer permissions on the backend.
-   Avoid logging full complaints or sensitive text unless necessary and
    appropriately protected.

## 6. Implementation instruction

Before frontend integration, create typed request/response models and a
small API contract test suite. If endpoint names or response shapes
change, update this document and the frontend types together.
