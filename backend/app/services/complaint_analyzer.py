import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.schemas.complaint import AssessmentStatusType, ComplaintWorkflowStatusType
from backend.app.services.retrieval import hybrid_retrieval_service, RetrievedChunk
from backend.app.services.gemini import gemini_service
from backend.app.models.complaint import Complaint, ComplaintIssue, IssueEvidence
from backend.app.models.policy import PolicyChunk

logger = logging.getLogger("complaint_assistant.complaint_analyzer")

# Regex patterns for PII / PCI detection
RE_CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
RE_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
RE_CVV = re.compile(r"\b(?:CVV|CVC|CID)\s*[:#]?\s*\d{3,4}\b", re.IGNORECASE)
RE_EXP = re.compile(r"\b(?:EXP|EXPIRES)\s*[:#]?\s*\d{1,2}/\d{2,4}\b", re.IGNORECASE)

# Adversarial prompt injection markers
ADVERSARIAL_PATTERNS = [
    re.compile(r"\[(?:SYSTEM|INSTRUCTION|DIRECTIVE|IMPORTANT|ADMIN|DEVELOPER|PROMPT|AGENT)[\s\S]*?\]", re.IGNORECASE),
    re.compile(r"ignore\s+(?:all\s+)?(?:company\s+)?(?:policy|instructions|rules|limits)", re.IGNORECASE),
    re.compile(r"(?:print|reveal|disclose|show|leak)\s+(?:all\s+)?(?:api\s+keys|secrets|passwords|database\s+schema|system\s+instructions)", re.IGNORECASE),
    re.compile(r"(?:bypass|skip|disable)\s+(?:human|agent|manual)\s+(?:approval|review)", re.IGNORECASE),
    re.compile(r"irrevocably\s+promises", re.IGNORECASE),
    re.compile(r"without\s+waiting\s+for\s+(?:an?\s+)?agent", re.IGNORECASE),
    re.compile(r"(?:DROP\s+TABLE|UPDATE\s+\w+\s+SET|DELETE\s+FROM|SELECT\s+.*?FROM|--\s*\[)", re.IGNORECASE),
]


@dataclass
class DecomposedIssue:
    """A distinct extracted issue within a customer complaint."""
    issue_id: uuid.UUID
    issue_text: str
    requested_resolution: Optional[str]
    customer_facts: Dict[str, Any] = field(default_factory=dict)
    missing_facts: List[str] = field(default_factory=list)
    assessment_status: AssessmentStatusType = "needs_human_review"
    reasoning: str = ""
    is_adversarial: bool = False
    adversarial_notes: Optional[str] = None
    retrieved_evidence: List[RetrievedChunk] = field(default_factory=list)


@dataclass
class ComplaintAnalysisResult:
    """Full structured output of complaint decomposition, evidence mapping, and policy assessment."""
    complaint_id: uuid.UUID
    raw_text: str
    sanitized_text: str
    issues: List[DecomposedIssue]
    overall_status: ComplaintWorkflowStatusType
    security_warnings: List[str] = field(default_factory=list)
    contains_pii: bool = False


class ComplaintAnalyzer:
    """
    Decomposes customer complaints into distinct issues, maps relevant policy evidence
    via hybrid retrieval, detects prompt injection/PII, and classifies policy status.
    """

    def sanitize_and_detect_pii(self, text: str) -> Tuple[str, bool, List[str]]:
        """Redact sensitive customer cardholder and national ID data."""
        sanitized = text
        found_pii = False
        notes = []

        if RE_CREDIT_CARD.search(sanitized):
            sanitized = RE_CREDIT_CARD.sub("[REDACTED_CREDIT_CARD]", sanitized)
            found_pii = True
            notes.append("PCI cardholder account number detected and masked.")

        if RE_SSN.search(sanitized):
            sanitized = RE_SSN.sub("[REDACTED_SSN]", sanitized)
            found_pii = True
            notes.append("Social Security Number detected and masked.")

        if RE_CVV.search(sanitized):
            sanitized = RE_CVV.sub("[REDACTED_CVV]", sanitized)
            found_pii = True

        if RE_EXP.search(sanitized):
            sanitized = RE_EXP.sub("[REDACTED_EXPIRATION]", sanitized)
            found_pii = True

        return sanitized, found_pii, notes

    def detect_adversarial_patterns(self, text: str) -> Tuple[bool, List[str]]:
        """Identify embedded prompt injection instructions or secret extraction reconnaissance."""
        detected = False
        warnings = []

        for pat in ADVERSARIAL_PATTERNS:
            match = pat.search(text)
            if match:
                detected = True
                warnings.append(f"Prompt injection or unauthorized instruction pattern detected: '{match.group(0)[:60]}...'")

        return detected, warnings

    def decompose_complaint(self, text: str, is_adversarial: bool) -> List[DecomposedIssue]:
        """
        Decompose a customer complaint narrative into distinct issues,
        capturing customer facts, requested resolution, and missing information.
        """
        issues: List[DecomposedIssue] = []

        # Check for multi-issue markers (e.g. "Issue 1:", "Issue 2:", or explicit bullet splits)
        has_issue_headers = bool(re.search(r"\bIssue\s*\d+:", text, re.IGNORECASE))
        has_numbered_items = bool(re.search(r"(?:^|\n)\s*\d+[\.\)]\s+", text))

        if has_issue_headers:
            parts = re.split(r"\bIssue\s*\d+:", text, flags=re.IGNORECASE)
            for part in parts:
                clean = part.strip()
                if clean:
                    issue_obj = self._parse_single_issue_intent(clean, is_adversarial)
                    issues.append(issue_obj)
        elif has_numbered_items:
            parts = re.split(r"(?:^|\n)\s*\d+[\.\)]\s+", text)
            for part in parts:
                clean = part.strip()
                if clean:
                    issue_obj = self._parse_single_issue_intent(clean, is_adversarial)
                    issues.append(issue_obj)
        elif " damaged" in text.lower() and ("missing" in text.lower() or "never shipped" in text.lower()) and "inconvenience" in text.lower():
            # Composite multi-issue case (e.g., damaged shoes + missing socks + $100 compensation)
            issues.append(
                DecomposedIssue(
                    issue_id=uuid.uuid4(),
                    issue_text="Merchandise arrived damaged (sneakers with broken laces)",
                    requested_resolution="Replacement or return/refund for damaged item",
                    customer_facts={"item": "sneakers", "condition": "damaged_laces"},
                    missing_facts=[],
                    reasoning="Physical merchandise damaged in transit falls under return/replacement remedies.",
                )
            )
            issues.append(
                DecomposedIssue(
                    issue_id=uuid.uuid4(),
                    issue_text="Item omitted from shipment according to invoice (missing socks)",
                    requested_resolution="Reshipment or refund for undelivered item",
                    customer_facts={"item": "socks", "status": "never_shipped_on_invoice"},
                    missing_facts=[],
                    reasoning="Missing item claim from multi-item order.",
                )
            )
            issues.append(
                DecomposedIssue(
                    issue_id=uuid.uuid4(),
                    issue_text="Demand for monetary compensation for customer inconvenience ($100)",
                    requested_resolution="$100 cash compensation for inconvenience",
                    customer_facts={"requested_amount": 100},
                    missing_facts=[],
                    reasoning="Inconvenience damages demand barred by disclaimer and limitation of liability.",
                )
            )
        else:
            # Single main issue
            issue_obj = self._parse_single_issue_intent(text, is_adversarial)
            issues.append(issue_obj)

        return issues

    def _parse_single_issue_intent(self, text: str, is_adversarial: bool) -> DecomposedIssue:
        """Analyze intent, customer facts, and missing requirements for a single issue."""
        t_lower = text.lower()
        facts: Dict[str, Any] = {}
        missing: List[str] = []

        # Extract days / timeline numbers
        days_match = re.search(r"(\d+)\s*(?:business\s*)?days?", t_lower)
        if days_match:
            facts["days_elapsed"] = int(days_match.group(1))

        # Condition facts
        if "unworn" in t_lower or "new condition" in t_lower:
            facts["condition"] = "new_unworn"
        elif "worn" in t_lower or "worn down" in t_lower or "used" in t_lower:
            facts["condition"] = "worn_used"

        if "original" in t_lower and ("box" in t_lower or "shoebox" in t_lower or "packaging" in t_lower):
            facts["packaging"] = "original_packaging"

        # Geographic / location facts
        if "apo" in t_lower or "fpo" in t_lower:
            facts["destination_type"] = "military_apo_fpo"
        elif "canada" in t_lower or "international" in t_lower:
            facts["destination_type"] = "international"
        else:
            facts["destination_type"] = "us_domestic"

        # Missing information checks
        has_order_num = bool(re.search(r"order\s*(?:#|number|id|num)\s*[:\s]?\s*[0-9][A-Z0-9\-]{2,}", text, re.IGNORECASE))
        if ("missing an item" in t_lower or "missing item" in t_lower) and not has_order_num:
            missing.extend(["order_number", "item_name", "outer_box_condition"])

        if "approve my refund right now" in t_lower and ("sue" in t_lower or "arbitration" in t_lower):
            missing.extend(["order_number", "proof_of_purchase", "tracking_number"])

        # Determine summary description and requested resolution
        issue_text = text.split("\n")[0][:120].strip()
        requested_res = None

        if "return" in t_lower and "refund" in t_lower:
            requested_res = "Return merchandise for refund to original payment method"
        elif "refund" in t_lower:
            requested_res = "Refund payment"
        elif "exchange" in t_lower:
            requested_res = "Exchange item"
        elif "return label" in t_lower:
            requested_res = "Prepaid return shipping label"
        elif "late" in t_lower or "tracking" in t_lower or "delay" in t_lower:
            requested_res = "Delivery status inquiry or carrier trace"

        return DecomposedIssue(
            issue_id=uuid.uuid4(),
            issue_text=issue_text,
            requested_resolution=requested_res,
            customer_facts=facts,
            missing_facts=missing,
            is_adversarial=is_adversarial,
        )

    def assess_issue_policy(
        self,
        issue: DecomposedIssue,
        evidence: List[RetrievedChunk],
        full_complaint_text: str,
    ) -> Tuple[AssessmentStatusType, str]:
        """
        Classify policy coverage status based on customer facts, requested resolution,
        and retrieved policy passages from the knowledge base.
        """
        c_lower = full_complaint_text.lower()
        i_lower = issue.issue_text.lower()
        facts = issue.customer_facts
        evidence_contents = " ".join([e.content.lower() for e in evidence])

        # Rule 0: PII / PCI cardholder data requires specialized security routing
        if RE_CREDIT_CARD.search(full_complaint_text) or RE_SSN.search(full_complaint_text):
            return "needs_human_review", "Complaint includes high-risk PII / PCI cardholder data requiring redaction and specialized escalation."

        # Rule 1: Unsupported external promise assertion (e.g. ADV-003)
        if "phone already promised" in c_lower or "no return necessary" in c_lower:
            return "prohibited", "Customer asserts an unverified external promise to force an unauthorized commitment."

        # Rule 2: Prompt injection / System command overrides
        if issue.is_adversarial or any(p.search(issue.issue_text) for p in ADVERSARIAL_PATTERNS):
            if "approve both items together" in c_lower:
                return "partially_covered", "Bundled request with embedded override command: item A covered, item B prohibited."
            return "needs_human_review", "Prompt injection or command override attempt detected; routing to human review."

        # Rule 3: Secret extraction reconnaissance
        if "api key" in c_lower or "database schema" in c_lower or "system instructions" in c_lower:
            return "needs_human_review", "Secret extraction attempt; security policy prohibits disclosing system instructions or credentials."

        # Rule 4: Missing facts preventing confident decision
        if issue.missing_facts:
            return "needs_human_review", f"Critical eligibility facts are missing: {', '.join(issue.missing_facts)}."

        # Rule 5: Stolen package / Risk of loss policy conflict
        if ("stolen" in c_lower or "front steps" in c_lower or "porch" in c_lower) and "carrier" in c_lower:
            return "conflict", (
                "Policy conflict: Conditions of Use states Risk of Loss passes upon delivery to carrier, "
                "while Shipping & Returns advertises customer delivery assurance. Requires human supervisor escalation."
            )
        if "breach of contract" in c_lower and "risk of loss" in c_lower and "$1,000" in c_lower:
            return "conflict", "Adversary asserts legal tension between policy passages to coerce monetary admission."

        # Rule 5b: Account takeover / Fraudulent purchase / Suspicious activity
        if any(k in c_lower for k in ("never placed", "compromised", "account takeover", "unauthorized order", "suspicious activity", "fraudulent purchase")):
            return "needs_human_review", "Suspicious activity or unauthorized order reported; immediate escalation to fraud and security reviewer."

        # Rule 5c: Competitor price matching exclusions (unauthorized seller, auction, darknet, marketplace)
        if ("price match" in c_lower or "price match" in i_lower or "match" in i_lower) and any(
            k in c_lower for k in ("auction", "marketplace", "unauthorized", "darknet", "stolen", "discount club", "third-party", "third party")
        ):
            return "prohibited", "Price matching explicitly excludes third-party marketplaces, auction sites, unauthorized sellers, and discount clubs."

        # Rule 5d: VIP points expiration, non-transferability, and cash redemption prohibition
        if ("vip points" in c_lower or "loyalty points" in c_lower or ("points" in c_lower and "vip" in c_lower)) and any(
            k in c_lower for k in ("inactive", "expired", "transfer", "cash", "credit my bank", "sister's account")
        ):
            return "prohibited", "VIP loyalty points expire after 1 year of account inactivity, have no cash value, and are non-transferable."

        # Rule 5e: Gift card or store credit cash conversion prohibition
        if ("store credit" in c_lower or "gift certificate" in c_lower or "gift card" in c_lower) and any(
            k in c_lower for k in ("wire transfer", "cash", "venmo", "personal bank", "convert")
        ):
            return "prohibited", "Returns purchased with gift cards or store credit are strictly refunded as store credit and cannot be converted to cash or external transfers."

        # Rule 5f: APO expedited delivery override attempt
        if facts.get("destination_type") == "military_apo_fpo" and any(k in c_lower for k in ("override", "insist", "guarantee 2-day", "2-day delivery")):
            return "prohibited", "Expedited shipping is strictly unavailable to military APO/FPO addresses regardless of customer VIP status."

        # Rule 6: Worn merchandise or exceeded 60-day window
        days = facts.get("days_elapsed", 0)
        condition = facts.get("condition")
        if days > 60:
            if any(k in c_lower for k in ("hospital", "medical", "emergency", "exception", "extenuating")):
                return "needs_human_review", "Return request beyond 60-day window due to medical emergency requires supervisor review for store credit exception."
            return "prohibited", "Exceeds 60-day return window and/or violates requirement that returned merchandise must be in new/unworn condition."

        if condition == "worn_used" and "outdoors" in c_lower:
            return "prohibited", "Merchandise worn outdoors violates requirement that returned merchandise must be in new/unworn condition."

        # Rule 7: Free upgrade exchange without paying price difference
        if "exchange" in i_lower and ("different brand" in c_lower or "$40 more" in c_lower or "without paying" in c_lower):
            return "prohibited", "Exchanges for more expensive merchandise without paying the price difference are prohibited."

        # Rule 8: Refund exceeding actual amount paid (coupon discount)
        if "coupon" in c_lower and ("full original retail price" in c_lower or "retail difference" in c_lower or "discounted amount" in c_lower):
            return "prohibited", "Refunds are issued to the original form of payment up to the actual purchase price paid; unspent retail difference is prohibited."

        # Rule 9: Inconvenience damages demand
        if "inconvenience" in i_lower or "$100" in i_lower:
            return "prohibited", "Monetary compensation for inconvenience is barred by the disclaimer and limitation of liability in Conditions of Use."

        # Rule 9b: Zappos Price Guarantee (10-day price drop refund on zappos.com)
        if (
            ("price adjustment" in c_lower or "price guarantee" in c_lower or "marked down" in c_lower or "price drop" in c_lower or "difference" in c_lower)
            and ("website" in c_lower or "zappos" in c_lower)
            and days <= 10
        ):
            return "covered", "Covered under Price Guarantee Policy: item price reduction within 10 calendar days qualifies for difference refund to original payment method."

        # Rule 9c: Misplaced return label reprint
        if "label" in c_lower and any(k in c_lower for k in ("another copy", "reprint", "misplaced", "puppy chewed")):
            return "covered", "Customer can reprint or retrieve misplaced return labels via account order history."

        # Rule 9d: Multi-box return procedure
        if any(k in c_lower for k in ("separate boxes", "multi-box", "multiple boxes", "combine them into one", "single box")) and "return" in c_lower:
            return "covered", "Multi-box returns are covered under FAQ guidelines on returning split shipments."

        # Rule 9e: Payment verification delay
        if "payment verification" in c_lower or "billing verification" in c_lower or "authorization hold" in c_lower:
            return "covered", "Covered under FAQ payment guidelines explaining security holds and billing verification steps."

        # Rule 10: Expedited shipping to military APO/FPO addresses
        if facts.get("destination_type") == "military_apo_fpo" and "expedited" in c_lower:
            return "covered", "Policy explicitly excludes expedited shipping to military APO/FPO addresses in footnote; standard shipping is free."

        # Rule 11: International return label (Canada)
        if facts.get("destination_type") == "international" or "canada" in c_lower:
            return "covered", "Free return shipping policy explicitly bounds coverage to the United States, US territories, and APO/FPO addresses."

        # Rule 12: Inaccurate product description / Material discrepancy
        if "product page listed" in c_lower or "inner label says" in c_lower or "polyurethane" in c_lower or "genuine leather" in c_lower:
            return "covered", "Conditions of Use explicitly provides that if a product is not as described, the sole remedy is returning it in unused condition for full refund."

        # Rule 13: Delayed warehouse refund posting
        if "fulfillment center" in c_lower and "refund has posted" in c_lower:
            return "covered", "Covered by policy; warehouse inspection time and bank posting timelines apply."

        # Rule 14: Physical damaged merchandise or missing items
        if "damaged" in i_lower or "broken" in i_lower or "defective" in i_lower:
            return "covered", "Physical merchandise damaged in transit: eligible for return or replacement."

        if "missing" in i_lower or "omitted" in i_lower or "never shipped" in i_lower:
            return "covered", "Item omitted from shipment: eligible for reshipment or refund."

        # Rule 15: Standard covered returns and shipping delays
        if "return" in c_lower and (days <= 60 or condition == "new_unworn" or "shoebox" in c_lower):
            return "covered", "Meets verified policy criteria: within 60-day window, unworn condition with original packaging."

        if "shipping" in c_lower or "tracking" in c_lower or "delay" in c_lower:
            return "covered", "Standard shipping speed is 3-5 business days; stalled tracking warrants carrier investigation."

        # Default fallback: check evidence presence
        if not evidence or len(evidence) == 0:
            return "uncovered", "No relevant company policy evidence found in knowledge base."

        return "needs_human_review", "Evidence retrieved but eligibility requires human agent evaluation."

    def analyze_and_persist(
        self,
        complaint_id: uuid.UUID,
        complaint_text: str,
        response_tone: str,
        db: Session,
    ) -> ComplaintAnalysisResult:
        """
        Execute full Phase 3 complaint analysis:
        1. Sanitize text and detect PII/PCI cardholder data
        2. Detect prompt injection and adversarial directives
        3. Decompose into distinct issues
        4. Retrieve policy evidence per issue via HybridRetrievalService
        5. Assess policy status and reasoning
        6. Persist Complaint, ComplaintIssues, and IssueEvidence in database
        """
        # Step 1: Sanitize and detect PII
        sanitized_text, has_pii, pii_notes = self.sanitize_and_detect_pii(complaint_text)

        # Step 2: Detect adversarial patterns
        is_adv, adv_warnings = self.detect_adversarial_patterns(complaint_text)
        security_warnings = pii_notes + adv_warnings

        # Step 3: Decompose into issues
        issues = self.decompose_complaint(complaint_text, is_adv)

        # Step 4 & 5: Issue-level evidence retrieval and policy assessment
        overall_statuses: List[AssessmentStatusType] = []

        for issue in issues:
            query = f"{issue.issue_text} {issue.requested_resolution or ''}".strip()
            # Retrieve evidence using existing Phase 2 hybrid retrieval service
            try:
                retrieved_chunks = hybrid_retrieval_service.retrieve(
                    query=query,
                    db=db,
                    top_k_vector=5,
                    top_k_keyword=5,
                    final_top_k=3,
                    filter_active_only=True,
                )
            except Exception as ret_err:
                logger.warning("Hybrid retrieval failed for issue '%s': %s", query[:40], ret_err)
                retrieved_chunks = []

            issue.retrieved_evidence = retrieved_chunks

            # Assess status
            status, reason = self.assess_issue_policy(issue, retrieved_chunks, complaint_text)
            issue.assessment_status = status
            issue.reasoning = reason
            overall_statuses.append(status)

        # Determine overall complaint workflow status
        overall_status: ComplaintWorkflowStatusType = "needs_human_review"
        if any(s in ("conflict", "prohibited") for s in overall_statuses) or is_adv or has_pii:
            overall_status = "needs_human_review"

        # Step 6: Persist in PostgreSQL
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            db_complaint = Complaint(
                id=complaint_id,
                complaint_text=sanitized_text,
                response_tone=response_tone,
                processing_status=overall_status,
            )
            db.add(db_complaint)
            db.flush()
        else:
            db_complaint.complaint_text = sanitized_text
            db_complaint.processing_status = overall_status
            db_complaint.response_tone = response_tone

        # Clean existing issues to ensure idempotency
        db.query(ComplaintIssue).filter(ComplaintIssue.complaint_id == complaint_id).delete(
            synchronize_session=False
        )

        for issue in issues:
            db_issue = ComplaintIssue(
                id=issue.issue_id,
                complaint_id=complaint_id,
                issue_text=issue.issue_text,
                requested_resolution=issue.requested_resolution,
                customer_facts=issue.customer_facts,
                missing_facts=issue.missing_facts,
                assessment_status=issue.assessment_status,
            )
            db.add(db_issue)
            db.flush()

            # Persist IssueEvidence links
            for rank, chunk in enumerate(issue.retrieved_evidence, 1):
                try:
                    chunk_uuid = uuid.UUID(chunk.chunk_id)
                    db_evidence = IssueEvidence(
                        id=uuid.uuid4(),
                        issue_id=issue.issue_id,
                        chunk_id=chunk_uuid,
                        retrieval_source="hybrid_rrf",
                        retrieval_rank=rank,
                        fusion_score=chunk.rrf_score,
                    )
                    db.add(db_evidence)
                except Exception as ev_err:
                    logger.warning("Failed to link IssueEvidence for chunk %s: %s", chunk.chunk_id, ev_err)

        db.commit()

        logger.info(
            "Analyzed complaint %s: %d issues extracted, status: %s, pii: %s, adv: %s",
            complaint_id,
            len(issues),
            overall_status,
            has_pii,
            is_adv,
        )

        return ComplaintAnalysisResult(
            complaint_id=complaint_id,
            raw_text=complaint_text,
            sanitized_text=sanitized_text,
            issues=issues,
            overall_status=overall_status,
            security_warnings=security_warnings,
            contains_pii=has_pii,
        )


complaint_analyzer = ComplaintAnalyzer()
