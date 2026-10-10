from fastapi.testclient import TestClient
from backend.app.core.errors import (
    DatabaseUnavailableException,
    ProviderUnavailableException,
    ProviderRateLimitException,
    CitationValidationException,
)


def test_custom_exception_response_shape(client: TestClient):
    """Verify AppException subclasses serialize to API_SPEC.md standard envelope."""
    exc = DatabaseUnavailableException()
    data = exc.to_dict()
    assert "error" in data
    assert data["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert data["error"]["retryable"] is True


def test_provider_unavailable_exception():
    """Verify provider unavailable exception code and retryable flag."""
    exc = ProviderUnavailableException(provider="Embedding")
    data = exc.to_dict()
    assert data["error"]["code"] == "EMBEDDING_PROVIDER_UNAVAILABLE"
    assert data["error"]["retryable"] is True


def test_provider_rate_limit_exception():
    """Verify provider rate limit exception code and retryable flag."""
    exc = ProviderRateLimitException(provider="Gemini")
    data = exc.to_dict()
    assert data["error"]["code"] == "PROVIDER_RATE_LIMIT"
    assert data["error"]["retryable"] is True


def test_citation_validation_exception():
    """Verify citation validation exception is non-retryable."""
    exc = CitationValidationException()
    data = exc.to_dict()
    assert data["error"]["code"] == "CITATION_VALIDATION_FAILURE"
    assert data["error"]["retryable"] is False


def test_not_found_route_error_envelope(client: TestClient):
    """Verify accessing undefined route returns structured error without server leaks."""
    response = client.get("/non_existent_route_abc123")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert data["error"]["retryable"] is False
