import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from backend.app.core.database import Base
from backend.app.models.policy import GUID


class AgentProfile(Base):
    """
    Support agent profile linked to Clerk authentication identity.
    Provides role-based access control (support_agent vs supervisor)
    and accountability tracking.
    """
    __tablename__ = "agent_profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="support_agent")  # 'support_agent' or 'supervisor'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    created_complaints = relationship(
        "Complaint",
        back_populates="created_by",
        foreign_keys="Complaint.created_by_agent_id",
    )
    assigned_complaints = relationship(
        "Complaint",
        back_populates="assigned_to",
        foreign_keys="Complaint.assigned_to_agent_id",
    )
    created_drafts = relationship(
        "ResponseDraft",
        back_populates="created_by",
        foreign_keys="ResponseDraft.created_by_agent_id",
    )
    reviews = relationship(
        "ReviewDecision",
        back_populates="reviewer_profile",
        foreign_keys="ReviewDecision.reviewer_profile_id",
    )
    audit_events = relationship(
        "ComplaintAuditLog",
        back_populates="actor",
        foreign_keys="ComplaintAuditLog.actor_agent_id",
    )


class ComplaintAuditLog(Base):
    """
    Audit log record capturing agent accountability events.
    Preserves historical identity even if agents are deactivated.
    """
    __tablename__ = "complaint_audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(GUID(), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_agent_id = Column(GUID(), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # complaint_created, assigned, reassigned, draft_edited, review_approved, review_rejected, case_escalated
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="audit_logs")
    actor = relationship("AgentProfile", back_populates="audit_events")
