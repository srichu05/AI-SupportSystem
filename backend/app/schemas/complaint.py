from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, field_validator


# Valid domain status constants defined across ARCHITECTURE.md and SAFETY_AND_VALIDATION.md
ResponseToneType = Literal["professional", "empathetic", "concise"]

AssessmentStatusType = Literal[
    "covered",
    "partially_covered",
    "uncovered",
    "prohibited",
    "conflict",
    "needs_human_review"
]

ComplaintWorkflowStatusType = Literal[
    "received",
    "analyzing",
    "drafted",
    "needs_human_review",
    "reviewed",
    "escalated",
    "failed"
]


class ComplaintCreateRequest(BaseModel):
    """POST /api/v1/complaints request body."""
    complaint_text: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="The customer complaint text to be analyzed"
    )
    response_tone: ResponseToneType = Field(
        default="professional",
        description="Desired primary tone for the drafted response"
    )
    generate_tone_variants: bool = Field(
        default=False,
        description="Whether to generate stretch-goal tone variants (professional, empathetic, concise)"
    )

    @field_validator("complaint_text")
    @classmethod
    def validate_complaint_text_non_empty(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Complaint text cannot be empty or whitespace only.")
        return trimmed


class EvidenceItem(BaseModel):
    """Retrieved policy passage chunk linked to an issue."""
    chunk_id: str = Field(..., description="Stable chunk identifier")
    document_id: str = Field(..., description="Parent policy document UUID")
    source_filename: str = Field(..., description="Original policy file name")
    section: Optional[str] = Field(default=None, description="Heading or section hierarchy")
    page_number: Optional[int] = Field(default=None, description="Page number if extractable")
    content: str = Field(..., description="Policy passage text")


class ComplaintIssueResponse(BaseModel):
    """Decomposed issue within a complaint."""
    issue_id: str = Field(..., description="Unique issue UUID")
    issue_text: str = Field(..., description="Summary of one distinct issue")
    requested_resolution: Optional[str] = Field(default=None, description="Requested outcome, if identified")
    assessment_status: AssessmentStatusType = Field(
        default="needs_human_review",
        description="One of: covered, partially_covered, uncovered, prohibited, conflict, needs_human_review"
    )
    missing_facts: List[str] = Field(default_factory=list, description="Missing customer facts needed for eligibility")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Retrieved policy evidence for this issue")


class DraftResponse(BaseModel):
    """Generated or edited draft response."""
    draft_id: str = Field(..., description="Unique draft UUID")
    text: str = Field(..., description="Draft response text")
    citations: List[str] = Field(default_factory=list, description="List of cited stable chunk IDs")


class ValidationReport(BaseModel):
    """Backend deterministic and safety validation report."""
    valid: bool = Field(default=True, description="Whether all validation checks passed")
    errors: List[str] = Field(default_factory=list, description="Validation blocking errors")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking validation warnings")


class ToneVariantDraft(BaseModel):
    """Tone variant response (Phase 4 stretch goal)."""
    draft_id: str
    tone: ResponseToneType
    text: str
    citations: List[str] = Field(default_factory=list)
    valid: bool = True
    warnings: List[str] = Field(default_factory=list)


class ComplaintResponse(BaseModel):
    """POST /api/v1/complaints and GET /api/v1/complaints/{id} response shape."""
    complaint_id: str = Field(..., description="Unique complaint UUID")
    status: ComplaintWorkflowStatusType = Field(..., description="Overall case workflow status")
    issues: List[ComplaintIssueResponse] = Field(default_factory=list, description="Extracted distinct issues")
    draft: Optional[DraftResponse] = Field(default=None, description="Primary drafted response")
    validation: Optional[ValidationReport] = Field(default=None, description="Validation report")
    draft_variants: Optional[Dict[str, ToneVariantDraft]] = Field(
        default=None,
        description="Optional tone variants if requested and generated"
    )
    created_by_agent_id: Optional[str] = Field(default=None, description="Agent who submitted complaint")
    created_by_agent_name: Optional[str] = Field(default=None, description="Display name of creating agent")
    assigned_to_agent_id: Optional[str] = Field(default=None, description="Agent currently assigned")
    assigned_to_agent_name: Optional[str] = Field(default=None, description="Display name of assigned agent")
