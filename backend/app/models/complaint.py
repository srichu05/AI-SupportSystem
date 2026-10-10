import uuid
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.policy import GUID


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    complaint_text = Column(Text, nullable=False)
    response_tone = Column(String(50), nullable=False, default="professional")
    processing_status = Column(
        String(50),
        nullable=False,
        default="received"
    )  # received, analyzing, drafted, needs_human_review, reviewed, escalated, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    created_by_agent_id = Column(GUID(), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_agent_id = Column(GUID(), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True, index=True)

    issues = relationship("ComplaintIssue", back_populates="complaint", cascade="all, delete-orphan")
    drafts = relationship("ResponseDraft", back_populates="complaint", cascade="all, delete-orphan")
    decisions = relationship("ReviewDecision", back_populates="complaint", cascade="all, delete-orphan")
    created_by = relationship("AgentProfile", back_populates="created_complaints", foreign_keys=[created_by_agent_id])
    assigned_to = relationship("AgentProfile", back_populates="assigned_complaints", foreign_keys=[assigned_to_agent_id])
    audit_logs = relationship("ComplaintAuditLog", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintIssue(Base):
    __tablename__ = "complaint_issues"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(GUID(), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_text = Column(Text, nullable=False)
    requested_resolution = Column(Text, nullable=True)
    customer_facts = Column(JSON, nullable=True)
    missing_facts = Column(JSON, nullable=True)
    assessment_status = Column(
        String(50),
        nullable=False,
        default="needs_human_review"
    )  # covered, partially_covered, uncovered, prohibited, conflict, needs_human_review
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="issues")
    evidence_links = relationship("IssueEvidence", back_populates="issue", cascade="all, delete-orphan")


class IssueEvidence(Base):
    __tablename__ = "issue_evidence"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    issue_id = Column(GUID(), ForeignKey("complaint_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(GUID(), ForeignKey("policy_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    retrieval_source = Column(String(50), nullable=False)  # vector, fulltext, hybrid_rrf
    retrieval_rank = Column(Integer, nullable=True)
    fusion_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    issue = relationship("ComplaintIssue", back_populates="evidence_links")
    chunk = relationship("PolicyChunk", back_populates="evidence_links")
