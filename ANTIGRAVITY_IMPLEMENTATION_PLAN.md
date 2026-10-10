# Antigravity Implementation Plan

## Intelligent Customer Complaint Response Assistant

Follow this sequence. Read `PRD.md`, `TECH_STACK.md`, `ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `RAG_PIPELINE.md`, `API_SPEC.md`, `SAFETY_AND_VALIDATION.md`, `TESTING_AND_EVALUATION.md`, and `DEPLOYMENT.md`. The frontend teammate owns the separate UI/UX specification. Keep the API contract stable for their branch.

## Working rules

- Inspect the existing repository before changing files; preserve working code.
- Do not invent provider model IDs, endpoints, schemas, policy content, or secrets. Verify provider IDs/access with a smoke test.
- Use FastAPI, Supabase PostgreSQL + pgvector + PostgreSQL full-text search + RRF, Supabase Storage, and hosted Gemini APIs as documented. No Streamlit, local embedding model, local PostgreSQL dependency, or FAISS.
- Keep API routing, parsing, retrieval, generation, validation, and persistence in separate modules.
- Never automatically send customer messages. Never claim persistence succeeded if it failed.
- Keep secrets in environment variables; never commit `.env`, API keys, service-role keys, or customer data.
- The tone-variation stretch goal must not delay the core grounded draft and review flow.

## Phase 1 — Foundation, provider verification, and database

1. Inspect the repo and existing runtime versions.
2. Confirm Gemini generation model ID and test generation. Verify `gemini-embedding-2` access, output dimension, quota, request format, and terms; do not assume the candidate is available until tested.
3. Verify Supabase connectivity, pgvector, and Storage access. Record settings in `.env.example` using placeholders.
4. Create repeatable migrations for policy documents/chunks, complaints, issues, evidence, drafts, and review history. Configure vector dimension only after verifying the embedding output. Add full-text indexes and constraints.
5. Implement FastAPI app setup, CORS configuration, `/health`, Pydantic schemas, consistent errors, and API contract tests.

**Exit criteria:** Supabase and both provider calls have passed smoke tests; migrations apply; `/health` works; no secrets are committed.

## Phase 2 — Policy ingestion and knowledge base

1. Accept PDF, DOCX, and TXT policy files with size/type limits.
2. Parse text, preserve page/section/source metadata, and use stable chunk IDs with heading-aware chunking.
3. Store original files in Supabase Storage.
4. Generate hosted embeddings in batches and persist vectors plus metadata. Cache unchanged content where practical.
5. Track ingestion status and safely handle empty/unreadable files, duplicate uploads, provider failures, and partial writes.

**Exit criteria:** A sample policy handbook can be ingested; source metadata survives; failed/partial ingestion is not marked successful.

## Phase 3 — Complaint analysis and hybrid retrieval

1. Implement issue decomposition into separate issues, stated facts, requested resolution, and missing facts.
2. Embed each issue/query using the same verified model used for policy chunks.
3. Implement pgvector similarity search and PostgreSQL full-text search; combine results with tested RRF and stable-ID deduplication.
4. Return evidence with chunk ID, document, page/section, and text. Apply only trusted policy status/version filters.
5. Implement the issue statuses `covered`, `partially_covered`, `uncovered`, `prohibited`, `conflict`, and `needs_human_review`.

**Exit criteria:** Single-issue and multi-issue complaints retrieve inspectable evidence; no-result, conflicting-policy, and missing-fact cases are represented safely. `uncovered` is not treated as `prohibited`.

## Phase 4 — Grounded response, validation, review, and tone stretch goal

1. Generate a structured response draft using only customer facts and retrieved evidence. Require policy-dependent claims to cite retrieved chunk IDs.
2. Validate schemas, citation membership, unsupported commitments, missing facts, conflicts, and escalation conditions with deterministic backend rules. Pydantic validity alone is not factual validation.
3. Persist complaint, issues, evidence references, original draft, edited draft, and review decision. Implement edit/approve/reject/escalate; approval must not send the response.
4. Only after the single-draft path passes, add professional, empathetic, and concise variants. Validate each variant independently to ensure facts, policy decisions, commitments, escalation, and citations remain unchanged.

**Exit criteria:** Core draft is evidence-grounded and invalid cases are flagged; review decisions persist; tone variants are optional and individually validated.

## Phase 5 — Evaluation, frontend integration, and deployment

1. Build an initial labelled suite of 10–15 complaints, expanding toward 20–30 if time permits. Cover supported, uncovered, prohibited, multi-issue, conflicting policy, missing facts, prompt injection, unreadable files, and provider failures.
2. Track issue coverage, evidence relevance/recall, citation validity and support, unsupported commitments, safe escalation, latency, and reviewer usefulness. Test tone consistency if implemented. Do not invent metrics.
3. Keep endpoint names and JSON schemas synchronized with `API_SPEC.md` and the frontend teammate. Use `/docs` and contract tests during integration; frontend mocks must be clearly labelled.
4. Deploy FastAPI to Render and frontend to Vercel; configure Supabase, environment variables, CORS, and HTTPS. Test the deployed end-to-end flow and inspect logs for secrets.

**Exit criteria:** The frontend can submit a complaint, show issue-level evidence and a validated draft, and save a human review decision. At least one safe escalation case is demonstrated. No automatic customer sending.

## Project Milestones and Priorities

**Must have:** provider/Supabase verification, policy ingestion, hybrid retrieval, issue decomposition, evidence-backed draft, citation validation, safe escalation, human review, persistence, and one deployed end-to-end flow.

**Stretch:** professional/empathetic/concise response variants with factual-equivalence validation.

**Only if time remains:** OCR for scanned documents, advanced policy versioning, expanded role management, or reranking.
