import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple

logger = logging.getLogger("complaint_assistant.response_validator")

# Regex to find citation IDs enclosed in square brackets [chunk_id]
RE_CITATION = re.compile(
    r"\[([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[A-Za-z0-9_\-\.]+_[a-zA-Z0-9_\-\.]+|[A-Za-z0-9_-]{8,40})\]"
)

# Currency detection for invented monetary compensation
RE_DOLLAR_AMOUNT = re.compile(r"\$\s*(\d+(?:\.\d{2})?)")

# Unauthorized commitment patterns
RE_UNAUTHORIZED_REFUND = re.compile(
    r"\b(?:we\s+have\s+issued\s+a\s+refund|we\s+will\s+issue\s+a\s+(?:full\s+)?refund|full\s+refund\s+has\s+been\s+processed|refund\s+has\s+been\s+approved|we\s+promise\s+a\s+refund|refund\s+guaranteed)\b",
    re.IGNORECASE,
)
RE_UNAUTHORIZED_REPLACEMENT = re.compile(
    r"\b(?:replacement\s+has\s+been\s+dispatched|replacement\s+is\s+on\s+the\s+way|we\s+will\s+send\s+a\s+replacement\s+immediately|replacement\s+approved|guaranteed\s+replacement)\b",
    re.IGNORECASE,
)
RE_LIABILITY_ADMISSION = re.compile(
    r"\b(?:we\s+admit\s+(?:fault|liability)|our\s+carrier\s+was\s+negligent|we\s+accept\s+full\s+responsibility\s+for\s+the\s+stolen|we\s+take\s+full\s+legal\s+responsibility)\b",
    re.IGNORECASE,
)
RE_ADVERSARIAL_LEAKAGE = re.compile(
    r"\b(?:SYSTEM\s+OVERRIDE|IGNORE\s+POLICY|BYPASS\s+APPROVAL|ADMINISTRATIVE\s+OVERRIDE|DEVELOPER\s+MODE|ROOT\s+ACCESS)\b",
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    """Outcome of deterministic validation checks on a generated or edited draft."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)


def _get_issue_field(iss: Any, field_name: str, default: Any = None) -> Any:
    if hasattr(iss, field_name):
        val = getattr(iss, field_name)
        return val if val is not None else default
    if isinstance(iss, dict):
        return iss.get(field_name, default)
    return default


def _get_chunk_field(chunk: Any, field_name: str, default: Any = None) -> Any:
    if hasattr(chunk, field_name):
        val = getattr(chunk, field_name)
        return val if val is not None else default
    if isinstance(chunk, dict):
        return chunk.get(field_name, default)
    return default


class ResponseValidator:
    """
    Deterministic validation engine ensuring all response drafts are
    strictly grounded in retrieved policy evidence, free of hallucinated
    commitments, and resilient against adversarial instruction leakage.
    """

    def extract_citations(self, text: str) -> List[str]:
        """Extract all cited chunk identifiers from bracketed references."""
        matches = RE_CITATION.findall(text)
        # Preserve order while deduplicating
        seen = set()
        citations = []
        for m in matches:
            clean = m.strip()
            if clean and clean not in seen:
                seen.add(clean)
                citations.append(clean)
        return citations

    def validate_draft(
        self,
        draft_text: str,
        issues: List[Any],
        allowed_chunk_ids: Optional[Set[str]] = None,
        complaint_text: str = "",
        is_adversarial: bool = False,
    ) -> ValidationResult:
        """
        Validate draft text against issue statuses, allowed evidence chunk IDs,
        and safety rules.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not draft_text or not draft_text.strip():
            return ValidationResult(
                valid=False,
                errors=["Draft response text cannot be empty."],
                warnings=[],
                citations=[],
            )

        # 1. Extract and validate citations
        extracted_citations = self.extract_citations(draft_text)

        # Build allowed chunk IDs from issues if not provided
        if allowed_chunk_ids is None:
            allowed_chunk_ids = set()
            for iss in issues:
                evidence = _get_issue_field(iss, "retrieved_evidence") or _get_issue_field(iss, "evidence") or []
                for ev in evidence:
                    cid = _get_chunk_field(ev, "chunk_id")
                    if cid:
                        allowed_chunk_ids.add(str(cid).strip())

        # Check for invalid citations
        invalid_citations = [c for c in extracted_citations if c not in allowed_chunk_ids]
        if invalid_citations:
            for inv in invalid_citations:
                errors.append(f"Invalid citation ID not present in retrieved evidence: '{inv}'")

        # Check if citations are missing when policy determinations are made
        has_covered_or_prohibited = False
        has_conflict = False
        has_prohibited = False
        has_uncovered = False
        has_needs_review = False

        for iss in issues:
            st = _get_issue_field(iss, "assessment_status")
            if st in ("covered", "prohibited"):
                has_covered_or_prohibited = True
            if st == "prohibited":
                has_prohibited = True
            if st == "conflict":
                has_conflict = True
            if st == "uncovered":
                has_uncovered = True
            if st == "needs_human_review":
                has_needs_review = True

        if has_covered_or_prohibited and allowed_chunk_ids and not extracted_citations:
            warnings.append("Draft makes policy determinations but does not cite any retrieved evidence chunk IDs.")

        # 2. Check for unauthorized commitments based on issue statuses
        if has_prohibited:
            if RE_UNAUTHORIZED_REFUND.search(draft_text):
                errors.append("Draft promises refund for an issue explicitly classified as prohibited under policy.")
            if RE_UNAUTHORIZED_REPLACEMENT.search(draft_text):
                errors.append("Draft promises replacement for an issue explicitly classified as prohibited under policy.")

        if has_uncovered:
            if RE_UNAUTHORIZED_REFUND.search(draft_text):
                errors.append("Draft promises refund for an issue not covered under current store policy.")

        if has_conflict:
            if RE_LIABILITY_ADMISSION.search(draft_text):
                errors.append("Draft admits carrier fault or legal liability for an issue with conflicting policy rules.")
            if RE_UNAUTHORIZED_REFUND.search(draft_text):
                errors.append("Draft promises refund without supervisor review on a conflicting policy issue.")

        if has_needs_review and not (has_covered_or_prohibited):
            if RE_UNAUTHORIZED_REFUND.search(draft_text):
                errors.append("Draft makes unconditional refund commitment while issue requires human review.")

        # 3. Check for invented monetary amounts
        complaint_amounts = set(RE_DOLLAR_AMOUNT.findall(complaint_text))
        draft_amounts = set(RE_DOLLAR_AMOUNT.findall(draft_text))
        invented_amounts = draft_amounts - complaint_amounts
        if invented_amounts:
            for amt in invented_amounts:
                errors.append(f"Draft introduces unauthorized monetary commitment of ${amt} not present in complaint or policy.")

        # 4. Check for adversarial instruction leakage
        if RE_ADVERSARIAL_LEAKAGE.search(draft_text):
            errors.append("Draft contains leaked prompt injection directives or instruction overrides.")

        if is_adversarial and ("$500" in draft_text or re.search(r"\b(?:override\s+policy|bypass\s+approval)\b", draft_text, re.IGNORECASE)):
            errors.append("Draft echoes adversary override command.")

        # 5. Check if draft claims full resolution when escalation is required
        if (has_conflict or is_adversarial) and "resolved" in draft_text.lower() and "supervisor" not in draft_text.lower() and "review" not in draft_text.lower():
            warnings.append("Draft indicates issue is resolved despite requiring supervisor escalation.")

        is_valid = len(errors) == 0

        return ValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            citations=extracted_citations,
        )

    def validate_tone_variants(
        self,
        variants: Dict[str, str],
        issues: List[Any],
        allowed_chunk_ids: Set[str],
        complaint_text: str = "",
    ) -> Dict[str, ValidationResult]:
        """
        Independently validate each tone variant and check cross-variant consistency.
        """
        results: Dict[str, ValidationResult] = {}
        for tone_name, variant_text in variants.items():
            results[tone_name] = self.validate_draft(
                draft_text=variant_text,
                issues=issues,
                allowed_chunk_ids=allowed_chunk_ids,
                complaint_text=complaint_text,
            )

        # Cross-variant consistency check:
        # If any variant is valid while another has unauthorized commitments, warn or invalidate
        for t1, r1 in results.items():
            for t2, r2 in results.items():
                if t1 != t2 and r1.valid != r2.valid:
                    r1.warnings.append(f"Tone variant '{t1}' differs in validity status from variant '{t2}'.")

        return results


response_validator = ResponseValidator()
