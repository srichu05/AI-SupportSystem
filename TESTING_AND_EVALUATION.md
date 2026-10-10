# Testing and Evaluation Plan

## Complaint Response Assistant

## 1. Objective

Verify that the system retrieves relevant policy evidence, handles
multi-issue complaints, cites sources correctly, avoids unsupported
commitments, and escalates uncertain cases. Evaluation results must be
measured; do not invent success percentages.

## 2. Initial golden set

Start with 8--12 manually labelled cases. If time allows, expand to
20--30. Each case should include: - Complaint text. - Expected distinct
issues. - Expected relevant policy chunk(s), if present. - Expected
issue status. - Required missing facts, if any. - Whether human review
is required. - Expected unsafe or unsupported commitments to avoid.

Cover: 1. Clearly covered request. 2. Request not addressed by policy.
3. Explicitly prohibited request, supported by evidence or an approved
rule. 4. Multi-issue complaint with different outcomes. 5. Missing
eligibility facts. 6. Conflicting policy passages. 7. Outdated/inactive
policy versus active policy. 8. Relevant-looking but non-authorizing
passage. 9. Prompt injection in complaint text. 10. Prompt injection or
malicious instructions in a policy document. 11. Unreadable/empty
document or ingestion failure. 12. Provider timeout or malformed model
output.

Not all cases need to be built before the first end-to-end demo;
prioritize core covered, uncovered, multi-issue, conflict and review
paths.

## 3. Retrieval metrics

-   **Evidence Recall@k:** fraction of labelled cases where at least one
    expected relevant chunk appears in the top k results.
-   **Precision@k:** fraction of the returned top-k chunks judged
    relevant, with the denominator adjusted if fewer than k results are
    returned.
-   **MRR (optional):** reciprocal rank of the first relevant result,
    averaged across cases.

Label relevant evidence before reporting metrics. A small set gives
directional feedback, not proof of production reliability.

## 4. Workflow and safety metrics

-   Issue extraction recall: expected issues found by the system.
-   Citation ID validity: citations resolve to evidence supplied for
    that request.
-   Citation support: human assessment of whether the cited text
    supports the claim.
-   Unsupported commitment rate: policy-dependent commitments not
    supported by evidence.
-   Safe abstention/escalation: cases requiring review that were
    correctly routed.
-   Conflict handling: cases with conflicting applicable passages that
    were escalated.
-   Latency: end-to-end processing time and, where useful, per-stage
    time.
-   Reviewer usefulness: qualitative feedback on whether the draft and
    evidence help.

Aim for zero observed unsupported commitments in the small demo set, but
do not present that as a guarantee for unseen cases.

## 5. Retrieval comparison

If time permits, compare: - PostgreSQL full-text search only. - pgvector
semantic search only. - Hybrid retrieval with RRF.

Use the same labelled complaints and relevant-chunk annotations. Compare
evidence recall and false positives, not just the ranking score. Hybrid
retrieval is the current design hypothesis, not a proven winner until
tested.

## 6. Test layers

### Unit tests

-   Chunking preserves source metadata.
-   Embedding response dimensions match configuration.
-   RRF merges ranks correctly and deduplicates stable chunk IDs.
-   Pydantic rejects malformed output.
-   Citation validator rejects IDs not present in the evidence set.
-   Status validation rejects unknown values.
-   Missing evidence does not automatically become `prohibited`.

### Integration tests

-   Ingest a small PDF, DOCX, and TXT file.
-   Verify stored chunks and embeddings.
-   Run vector and full-text search.
-   Run hybrid fusion.
-   Submit a complaint and retrieve its evidence/draft.
-   Record a review decision and confirm persistence.

### End-to-end tests

-   Complete a supported complaint through review.
-   Complete an uncovered complaint with safe escalation.
-   Complete a multi-issue complaint.
-   Confirm no automatic message is sent.
-   Confirm the deployed frontend can reach Render and Supabase-backed
    endpoints.

## 7. Results record

Store a simple JSONL or CSV record per case with: - Case ID. - Expected
issues/status/evidence. - Actual issues/status/evidence. - Retrieved
chunk IDs and ranks from each retriever. - Fused order. - Draft and
citation IDs. - Validation errors/warnings. - Review decision. -
Latency. - Human evaluation notes.

Avoid adding an external evaluation platform unless the basic test
harness is already working.

## 8. Failure triage

For each failure, classify it as: - Parsing/chunking. - Embedding API. -
Retrieval/ranking. - Policy version/filtering. - Issue extraction. -
Eligibility assessment. - Draft generation. - Citation validation. -
Persistence. - Frontend/backend integration.

Fix the earliest failing stage before adding more model complexity.


## Tone-variant stretch-goal tests

For the same complaint and retrieved evidence, generate professional, empathetic, and concise drafts. Check that all preserve the same factual claims, policy decision, eligibility, commitments, escalation outcome, and valid citations. Include a deliberately faulty variant that introduces an unsupported promise and verify validation flags it. Report results only from tests actually run.
