from fastapi.testclient import TestClient


def test_root_health_check(client: TestClient):
    """Verify root GET /health endpoint per API_SPEC.md."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_api_v1_health_check(client: TestClient):
    """Verify v1 GET /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_health_check(client: TestClient):
    """Verify database health check endpoint returns structured status."""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "connected" in data
    assert "message" in data
    assert "database_url_configured" in data


def test_providers_health_check(client: TestClient):
    """Verify external provider health check returns structured status without failing process."""
    response = client.get("/health/providers")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "gemini" in data
    assert "supabase" in data
    assert "generation_model" in data["gemini"]
    assert "embedding_model" in data["gemini"]
    assert "embedding_dimensions" in data["gemini"]
