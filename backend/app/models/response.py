import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.policy import GUID


class ResponseDraft(Base):
    __tablename__ = "response_drafts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(GUID(), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_text = Column(Text, nullable=False)
    structured_output = Column(JSON, nullable=True)  # { "issues": [...], "claims": [...], "citations": [...] }
    validation_status = Column(String(50), nullable=False, default="valid")  # valid, invalid, warnings
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="drafts")
    review_decisions = relationship("ReviewDecision", back_populates="draft", cascade="all, delete-orphan")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(GUID(), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_id = Column(GUID(), ForeignKey("response_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # approved, rejected, escalated
    final_response_text = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="decisions")
    draft = relationship("ResponseDraft", back_populates="review_decisions")
