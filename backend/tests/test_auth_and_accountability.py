import time
import uuid
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.models.agent import AgentProfile, ComplaintAuditLog
from backend.app.models.complaint import Complaint
from backend.app.models.response import ResponseDraft, ReviewDecision


def create_token(
    sub: str = "clerk_agent_001",
    name: str = "Test Agent",
    email: str = "agent@test.internal",
    exp_offset: int = 3600,
    iss: str = "clerk-test-issuer",
) -> str:
    """Helper to generate JWT tokens recognized by ClerkTokenVerifier in test mode."""
    payload = {
        "iss": iss,
        "sub": sub,
        "name": name,
        "email": email,
        "exp": int(time.time() + exp_offset),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_unauthenticated_request_rejected_401(monkeypatch):
    """Verify endpoints reject requests without Clerk bearer token with HTTP 401."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    with TestClient(app) as unauthed_client:
        response = unauthed_client.get("/api/v1/agents/me")
        assert response.status_code == 401
        assert "detail" in response.json() or "error" in response.json()


def test_malformed_token_rejected_401(client: TestClient, monkeypatch):
    """Verify malformed tokens return HTTP 401."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    headers = {"Authorization": "Bearer not-a-valid-jwt-token"}
    response = client.get("/api/v1/agents/me", headers=headers)
    assert response.status_code == 401


def test_expired_token_rejected_401(client: TestClient, monkeypatch):
    """Verify expired tokens are rejected with HTTP 401."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    token = create_token(exp_offset=-120)  # Expired 2 minutes ago
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/agents/me", headers=headers)
    assert response.status_code == 401
    assert "expired" in response.text.lower()


def test_auto_provisioning_assigns_support_agent_role(client: TestClient, db_session: Session, monkeypatch):
    """
    Verify auto-provisioning creates an agent profile linked to Clerk user ID
    with strictly 'support_agent' role (never supervisor).
    """
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    clerk_id = f"clerk_user_{uuid.uuid4().hex[:8]}"
    token = create_token(sub=clerk_id, name="Alice Support", email="alice@test.internal")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/agents/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["clerk_user_id"] == clerk_id
    assert data["display_name"] == "Alice Support"
    assert data["role"] == "support_agent"
    assert data["is_active"] is True


def test_non_supervisor_cannot_update_roles_403(client: TestClient, monkeypatch):
    """Verify regular support agent cannot promote users or assign supervisor privileges."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    agent_id_str = f"agent_{uuid.uuid4().hex[:8]}"
    token = create_token(sub=agent_id_str, name="Regular Agent", email="regular@test.internal")
    headers = {"Authorization": f"Bearer {token}"}

    # First initialize profile
    profile_resp = client.get("/api/v1/agents/me", headers=headers)
    assert profile_resp.status_code == 200
    my_profile_id = profile_resp.json()["id"]

    # Attempt to self-promote to supervisor
    update_resp = client.patch(
        f"/api/v1/agents/{my_profile_id}/role",
        json={"role": "supervisor"},
        headers=headers,
    )
    assert update_resp.status_code == 403
    assert "Supervisor privileges required" in update_resp.text


def test_deactivated_agent_rejected_403(client: TestClient, monkeypatch):
    """Verify deactivated agents receive HTTP 403 Forbidden on all requests."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    supervisor_sub = f"sup_{uuid.uuid4().hex[:8]}"
    sup_token = create_token(sub=supervisor_sub, name="Head Supervisor", email="sup@test.internal")
    sup_headers = {"Authorization": f"Bearer {sup_token}"}

    # Initialize supervisor profile and promote in db factory
    from backend.app.core.database import get_session_factory
    factory = get_session_factory()
    if factory is not None:
        with factory() as db:
            sup = AgentProfile(
                clerk_user_id=supervisor_sub,
                email="sup@test.internal",
                display_name="Head Supervisor",
                role="supervisor",
                is_active=True,
            )
            db.add(sup)
            db.commit()

        # Initialize agent to deactivate
        agent_sub = f"agent_{uuid.uuid4().hex[:8]}"
        agent_token = create_token(sub=agent_sub, name="Deactivated Agent", email="deact@test.internal")
        client.get("/api/v1/agents/me", headers={"Authorization": f"Bearer {agent_token}"})

        with factory() as db:
            agent = db.query(AgentProfile).filter(AgentProfile.clerk_user_id == agent_sub).first()
            agent_id = str(agent.id)

        # Supervisor deactivates agent
        deact_resp = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"is_active": False},
            headers=sup_headers,
        )
        assert deact_resp.status_code == 200
        assert deact_resp.json()["is_active"] is False

        # Deactivated agent attempts request
        blocked_resp = client.get("/api/v1/agents/me", headers={"Authorization": f"Bearer {agent_token}"})
        assert blocked_resp.status_code == 403
        assert "deactivated" in blocked_resp.text.lower()


def test_supervisor_role_change_lifecycle(client: TestClient, monkeypatch):
    """Verify supervisor can promote support_agent and demote."""
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    from backend.app.core.database import get_session_factory
    factory = get_session_factory()
    if factory is None:
        pytest.skip("Database factory not available")

    sup_sub = f"sup_lifecycle_{uuid.uuid4().hex[:8]}"
    sup_token = create_token(sub=sup_sub, name="Lead Sup", email="leadsup@test.internal")
    sup_headers = {"Authorization": f"Bearer {sup_token}"}

    with factory() as db:
        sup_agent = AgentProfile(
            clerk_user_id=sup_sub,
            email="leadsup@test.internal",
            display_name="Lead Sup",
            role="supervisor",
            is_active=True,
        )
        db.add(sup_agent)
        db.commit()

    agent_sub = f"agent_sub_{uuid.uuid4().hex[:8]}"
    agent_token = create_token(sub=agent_sub, name="Bob Agent", email="bob@test.internal")
    agent_resp = client.get("/api/v1/agents/me", headers={"Authorization": f"Bearer {agent_token}"})
    agent_id = agent_resp.json()["id"]

    # Promote Bob to supervisor
    promote_resp = client.patch(
        f"/api/v1/agents/{agent_id}/role",
        json={"role": "supervisor"},
        headers=sup_headers,
    )
    assert promote_resp.status_code == 200
    assert promote_resp.json()["role"] == "supervisor"

    # Demote Bob back to support_agent
    demote_resp = client.patch(
        f"/api/v1/agents/{agent_id}/role",
        json={"role": "support_agent"},
        headers=sup_headers,
    )
    assert demote_resp.status_code == 200
    assert demote_resp.json()["role"] == "support_agent"


def test_audit_attribution_on_complaint_and_review(client: TestClient, monkeypatch):
    """
    Verify complaint creation, review decision, and assignment record
    immutable audit logs attributing the verified Clerk actor.
    """
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    from backend.app.core.database import get_session_factory
    factory = get_session_factory()
    if factory is None:
        pytest.skip("Database factory not available")

    agent_a_sub = f"agent_a_{uuid.uuid4().hex[:8]}"
    token_a = create_token(sub=agent_a_sub, name="Agent A", email="agenta@test.internal")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Agent A submits complaint
    complaint_payload = {
        "complaint_text": "I ordered headphones but the left earcup does not produce sound. I want a refund.",
        "response_tone": "professional",
        "generate_tone_variants": False,
    }
    create_resp = client.post("/api/v1/complaints", json=complaint_payload, headers=headers_a)
    assert create_resp.status_code == 201
    c_data = create_resp.json()
    complaint_id = c_data["complaint_id"]
    draft_id = c_data["draft"]["draft_id"]

    assert c_data["created_by_agent_name"] == "Agent A"

    # 2. Agent B assigns complaint to themselves
    agent_b_sub = f"agent_b_{uuid.uuid4().hex[:8]}"
    token_b = create_token(sub=agent_b_sub, name="Agent B", email="agentb@test.internal")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    b_profile = client.get("/api/v1/agents/me", headers=headers_b).json()
    agent_b_id = b_profile["id"]

    assign_resp = client.post(
        f"/api/v1/complaints/{complaint_id}/assign",
        json={"assigned_to_agent_id": agent_b_id},
        headers=headers_b,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_to_agent_id"] == agent_b_id
    assert assign_resp.json()["assigned_to_agent_name"] == "Agent B"

    # 3. Agent B records review decision with edited draft text
    review_resp = client.post(
        f"/api/v1/complaints/{complaint_id}/review",
        json={
            "draft_id": draft_id,
            "decision": "approved",
            "final_response_text": "We are issuing a return shipping label for your damaged headphones.",
            "reason": "Covered under return and replacement policy.",
        },
        headers=headers_b,
    )
    assert review_resp.status_code == 201
    rev_data = review_resp.json()
    assert rev_data["reviewer_name"] == "Agent B"

    # 4. Fetch audit logs and verify actor identities
    audit_resp = client.get(f"/api/v1/complaints/{complaint_id}/audit", headers=headers_a)
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 3

    event_types = [e["event_type"] for e in events]
    assert "complaint_created" in event_types
    assert "reassigned" in event_types or "assigned" in event_types
    assert "review_approved" in event_types

    # Find review_approved event and assert Agent B is actor
    approved_event = next(e for e in events if e["event_type"] == "review_approved")
    assert approved_event["actor_name"] == "Agent B"
