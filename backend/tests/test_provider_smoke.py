from unittest.mock import MagicMock, patch
from backend.app.services.gemini import GeminiService
from backend.app.services.supabase import SupabaseService


def test_gemini_service_unconfigured():
    """Verify Gemini service correctly reports unconfigured state without fabricating results."""
    service = GeminiService(api_key="")
    assert service.is_configured is False

    gen_res = service.verify_generation()
    assert gen_res["success"] is False
    assert gen_res["status"] == "unconfigured"
    assert "GEMINI_API_KEY is not configured" in gen_res["message"]

    emb_res = service.verify_embedding()
    assert emb_res["success"] is False
    assert emb_res["status"] == "unconfigured"

    err_res = service.verify_error_handling()
    assert err_res["success"] is False
    assert err_res["status"] == "unconfigured"


def test_gemini_service_dimension_mismatch_detected():
    """Verify embedding verification flags dimension mismatch rather than pretending."""
    service = GeminiService(api_key="mock_test_key")

    mock_client = MagicMock()
    # Mock embedding returning 1536 dimensions instead of expected 768
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 1536
    mock_response = MagicMock()
    mock_response.embedding = mock_embedding
    mock_client.models.embed_content.return_value = mock_response

    with patch.object(service, "get_client", return_value=mock_client):
        res = service.verify_embedding(model_id="gemini-embedding-2", expected_dim=768)
        assert res["success"] is False
        assert res["status"] == "dimension_mismatch"
        assert res["actual_dimensions"] == 1536
        assert res["expected_dimensions"] == 768


def test_gemini_service_exact_dimension_match_verified():
    """Verify embedding verification succeeds when dimensions match exactly 768."""
    service = GeminiService(api_key="mock_test_key")

    mock_client = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    mock_response = MagicMock()
    mock_response.embedding = mock_embedding
    mock_client.models.embed_content.return_value = mock_response

    with patch.object(service, "get_client", return_value=mock_client):
        res = service.verify_embedding(model_id="gemini-embedding-2", expected_dim=768)
        assert res["success"] is True
        assert res["status"] == "verified"
        assert res["actual_dimensions"] == 768


def test_supabase_service_unconfigured():
    """Verify Supabase service reports unconfigured state safely."""
    service = SupabaseService()
    service.url = None
    service.key = None

    assert service.is_configured is False
    status = service.check_storage_access()
    assert status["configured"] is False
    assert status["status"] == "not_configured"
