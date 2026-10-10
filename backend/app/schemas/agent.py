from typing import Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class AgentProfileResponse(BaseModel):
    id: str
    clerk_user_id: str
    email: str
    display_name: str
    role: Literal["support_agent", "supervisor"]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AgentRoleUpdateRequest(BaseModel):
    role: Literal["support_agent", "supervisor"]


class AgentStatusUpdateRequest(BaseModel):
    is_active: bool


class ComplaintAssignRequest(BaseModel):
    assigned_to_agent_id: str = Field(..., description="Target AgentProfile ID to assign complaint to")


class ComplaintAuditLogResponse(BaseModel):
    id: str
    complaint_id: str
    actor_agent_id: Optional[str] = None
    actor_name: Optional[str] = None
    event_type: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
