from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from backend.app.schemas.complaint import DraftResponse

ReviewDecisionType = Literal["approved", "rejected", "escalated"]


class ReviewDecisionRequest(BaseModel):
    """POST /api/v1/complaints/{id}/review request body."""
    draft_id: str = Field(..., description="UUID of the draft being reviewed")
    decision: ReviewDecisionType = Field(
        ...,
        description="Review decision: approved | rejected | escalated"
    )
    final_response_text: Optional[str] = Field(
        default=None,
        description="Optional human-edited final response text"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional reviewer explanation or rationale"
    )


class ReviewDecisionResponse(BaseModel):
    """Review decision record response."""
    review_id: str
    complaint_id: str
    draft_id: str
    decision: ReviewDecisionType
    final_response_text: Optional[str] = None
    reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: datetime


class ComplaintHistoryResponse(BaseModel):
    """GET /api/v1/complaints/{id}/history response."""
    complaint_id: str
    drafts: List[DraftResponse] = Field(default_factory=list)
    reviews: List[ReviewDecisionResponse] = Field(default_factory=list)
