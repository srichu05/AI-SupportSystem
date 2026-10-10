import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_agent, require_supervisor
from backend.app.core.database import get_db
from backend.app.core.errors import ResourceNotFoundException
from backend.app.models.agent import AgentProfile
from backend.app.schemas.agent import (
    AgentProfileResponse,
    AgentRoleUpdateRequest,
    AgentStatusUpdateRequest,
)

logger = logging.getLogger("complaint_assistant.agents_api")
router = APIRouter(prefix="/agents", tags=["Agents & Accountability"])


def _map_agent_response(agent: AgentProfile) -> AgentProfileResponse:
    return AgentProfileResponse(
        id=str(agent.id),
        clerk_user_id=agent.clerk_user_id,
        email=agent.email,
        display_name=agent.display_name,
        role=agent.role,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.get(
    "/me",
    response_model=AgentProfileResponse,
    summary="Get current authenticated agent profile",
)
def get_current_agent_profile(
    current_agent: AgentProfile = Depends(get_current_agent),
) -> AgentProfileResponse:
    """
    Retrieve profile and role information for the currently authenticated agent.
    Auto-provisions profile if this is the user's first request.
    """
    return _map_agent_response(current_agent)


@router.get(
    "",
    response_model=List[AgentProfileResponse],
    summary="List active agent profiles",
)
def list_agents(
    current_agent: AgentProfile = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> List[AgentProfileResponse]:
    """
    Retrieve a list of support agent profiles.
    Used for case assignment and reviewer attribution.
    """
    agents = db.query(AgentProfile).order_by(AgentProfile.display_name.asc()).all()
    return [_map_agent_response(a) for a in agents]


@router.patch(
    "/{agent_id}/role",
    response_model=AgentProfileResponse,
    summary="Update an agent's role (Supervisor only)",
)
def update_agent_role(
    agent_id: str,
    request: AgentRoleUpdateRequest,
    supervisor: AgentProfile = Depends(require_supervisor),
    db: Session = Depends(get_db),
) -> AgentProfileResponse:
    """
    Update an agent's role between 'support_agent' and 'supervisor'.
    Restricted strictly to supervisors. Users can never assign themselves supervisor privileges.
    """
    try:
        parsed_id = uuid.UUID(agent_id)
    except ValueError:
        raise ResourceNotFoundException("agent_profile", agent_id)

    target_agent = db.query(AgentProfile).filter(AgentProfile.id == parsed_id).first()
    if not target_agent:
        raise ResourceNotFoundException("agent_profile", agent_id)

    # Prevent demoting oneself if no other supervisor exists
    if str(target_agent.id) == str(supervisor.id) and request.role != "supervisor":
        other_supervisors = (
            db.query(AgentProfile)
            .filter(AgentProfile.role == "supervisor", AgentProfile.id != target_agent.id, AgentProfile.is_active.is_(True))
            .count()
        )
        if other_supervisors == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the sole active supervisor.",
            )

    target_agent.role = request.role
    db.commit()
    db.refresh(target_agent)

    logger.info(
        "Supervisor %s (%s) updated agent %s (%s) role to %s",
        supervisor.display_name,
        supervisor.id,
        target_agent.display_name,
        target_agent.id,
        target_agent.role,
    )
    return _map_agent_response(target_agent)


@router.patch(
    "/{agent_id}/status",
    response_model=AgentProfileResponse,
    summary="Activate or deactivate an agent profile (Supervisor only)",
)
def update_agent_status(
    agent_id: str,
    request: AgentStatusUpdateRequest,
    supervisor: AgentProfile = Depends(require_supervisor),
    db: Session = Depends(get_db),
) -> AgentProfileResponse:
    """
    Activate or deactivate an agent. Deactivated agents cannot access the API.
    Historical audit events are safely preserved.
    """
    try:
        parsed_id = uuid.UUID(agent_id)
    except ValueError:
        raise ResourceNotFoundException("agent_profile", agent_id)

    target_agent = db.query(AgentProfile).filter(AgentProfile.id == parsed_id).first()
    if not target_agent:
        raise ResourceNotFoundException("agent_profile", agent_id)

    # Invariant: Supervisors cannot deactivate themselves
    if str(target_agent.id) == str(supervisor.id) and not request.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supervisors cannot deactivate their own active account.",
        )

    target_agent.is_active = request.is_active
    db.commit()
    db.refresh(target_agent)

    logger.info(
        "Supervisor %s (%s) updated agent %s (%s) active status to %s",
        supervisor.display_name,
        supervisor.id,
        target_agent.display_name,
        target_agent.id,
        target_agent.is_active,
    )
    return _map_agent_response(target_agent)
