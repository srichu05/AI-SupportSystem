# Safety, Evidence Grounding, and Validation

## Complaint Response Assistant

## 1. Purpose

The system drafts customer-support responses from company-policy
evidence. It must not treat a language model's output as policy
authority. Policy text, customer text, retrieved chunks, and
model-generated claims are all inputs that require controlled handling.

## 2. Non-negotiable principles

1.  Do not send customer communications automatically.
2.  Do not claim a customer qualifies for a benefit merely because a
    similar policy passage was retrieved.
3.  Do not invent policy terms, deadlines, exceptions, or commitments.
4.  Do not treat missing evidence as proof that a request is prohibited.
5.  Require valid source references for policy-dependent claims.
6.  Escalate uncertain, conflicting, or insufficiently supported cases.
7.  Treat complaint and policy text as untrusted content; text in either
    must not override system instructions or safety rules.

## 3. Per-issue states

-   `covered`: available policy evidence appears to address the issue;
    any customer-specific eligibility conditions still need to be
    checked.
-   `partially_covered`: some aspects are supported but material parts
    remain unresolved.
-   `uncovered`: sufficient policy evidence was not found.
-   `prohibited`: evidence or an explicit authorized rule indicates the
    requested action is not permitted.
-   `conflict`: applicable evidence or policy sources materially
    disagree.
-   `needs_human_review`: uncertainty, missing facts, validation
    failure, or risk requires a reviewer.

These descriptions are intended semantics. Implement precise transitions
and decision criteria in code and tests.

## 4. Structured model output

Use Pydantic models for: - Issue extraction. - Requested resolution and
customer facts. - Missing information. - Per-issue assessment and
evidence IDs. - Draft response and claim/citation relationships. -
Validation warnings and review routing.

A model response that parses successfully is not necessarily true or
safe. Parsing is only the first validation layer.

## 5. Evidence validation

Backend checks should include: - All cited chunk IDs exist in the
retrieved evidence set for this request. - Cited chunks are associated
with the appropriate issue. - The stored source record resolves to a
document and available page/section metadata. - A response does not cite
a chunk that was not retrieved or supplied to the generation step. -
Unsupported promises or actions are not introduced by the draft. - If
evidence is missing, contradictory, or not applicable to customer facts,
route to review.

Citation-ID validation is necessary but not sufficient for semantic
support. Include human review and labelled test cases to judge whether
cited passages truly support the associated claim.

## 6. Policy and eligibility reasoning

Separate these questions: 1. Does a relevant policy passage exist? 2.
What does the passage say? 3. What customer facts are known? 4. Are all
required eligibility conditions established? 5. Is the requested action
permitted, disallowed, or unresolved? 6. Can the response be drafted
safely, or is review required?

Similarity scores are retrieval signals, not confidence probabilities.
Do not use a single global similarity threshold as proof of eligibility.
Calibrate retrieval settings on representative cases.

## 7. Prohibited commitments and rules

A small human-authored rules file may define explicit high-risk
restrictions or required escalation cases. Rules must be grounded in
approved policy or product requirements.

Do not block words such as "refund," "replacement," or "guarantee" in
isolation: policy may legitimately authorize some of these actions.
Validate the meaning and evidence for the actual claim. Keyword rules
supplement, but do not replace, structured intent analysis and evidence
checks.

## 8. Prompt injection and untrusted content

-   Clearly delimit customer complaint text and retrieved policy
    passages as data.
-   Tell the model to analyze the content, not follow instructions
    embedded inside it.
-   Do not allow retrieved text to change system policy, reveal secrets,
    or bypass validation.
-   Apply deterministic checks outside the model.
-   Include adversarial tests containing instructions embedded in
    complaint text and policy documents.

## 9. Human review UX requirements (functional, not visual)

Show the reviewer: - Original complaint. - Separate issues and requested
resolutions. - Retrieved evidence with source and page/section when
available. - Draft response and citations. - Missing facts, conflicts,
and validation warnings. - Edit controls and approve/reject/escalate
actions.

Do not make the UI imply that an unverified draft is already approved or
sent.

## 10. Failure routing

Escalate or stop safely when: - Embedding or generation provider
fails. - Model output is malformed after bounded retries. - No relevant
evidence is found. - Applicable policies conflict. - Eligibility depends
on missing facts. - A cited chunk ID is invalid. - A high-risk rule is
triggered. - Persistence of the review decision fails.

Do not display a success state when the underlying action failed to
persist.

## 11. Audit trail

Persist the original draft, final edited text where applicable, reviewer
decision, timestamp, and optional reason. Store only necessary data and
decide retention/access rules before using real customer data.

## 12. Limitations

This design reduces known failure modes but does not guarantee zero
hallucinations, complete policy coverage, or legal/compliance
correctness. Claims of reliability must be supported by evaluation.


## 10. Tone-variant validation (stretch goal)

- Generate tone variants only after the single-draft path is reliable.
- Supported tones: `professional`, `empathetic`, and `concise`.
- Treat tone as a style instruction, never as permission to change facts or policy interpretation.
- Validate each variant for unsupported claims, altered eligibility/commitments, changed escalation outcomes, and invalid or missing citation IDs.
- If a variant fails validation, do not present it as validated; return a warning or omit that variant.
