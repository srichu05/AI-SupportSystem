import io
import uuid
from fastapi.testclient import TestClient


def test_upload_policy_txt_success(client: TestClient):
    """Verify uploading a valid TXT policy succeeds and returns document_id."""
    content = b"All full refunds must be requested within 14 days of purchase."
    files = {"file": ("refund_policy.txt", io.BytesIO(content), "text/plain")}
    data = {"version_label": "v1.0"}

    response = client.post("/api/v1/policies", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert "document_id" in res_data
    assert res_data["status"] == "processing"


def test_upload_policy_pdf_success(client: TestClient):
    """Verify uploading a valid PDF policy succeeds."""
    content = b"%PDF-1.4 sample policy binary content..."
    files = {"file": ("terms.pdf", io.BytesIO(content), "application/pdf")}

    response = client.post("/api/v1/policies", files=files)
    assert response.status_code == 201
    assert "document_id" in response.json()


def test_upload_policy_unsupported_file_type(client: TestClient):
    """Verify uploading an unsupported file format is rejected with standard error."""
    content = b"executable code..."
    files = {"file": ("virus.exe", io.BytesIO(content), "application/octet-stream")}

    response = client.post("/api/v1/policies", files=files)
    assert response.status_code == 415
    res_data = response.json()
    assert "error" in res_data
    assert res_data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert res_data["error"]["retryable"] is False


def test_upload_policy_empty_file(client: TestClient):
    """Verify empty document upload is rejected."""
    content = b""
    files = {"file": ("empty.txt", io.BytesIO(content), "text/plain")}

    response = client.post("/api/v1/policies", files=files)
    assert response.status_code == 400
    res_data = response.json()
    assert "error" in res_data
    assert res_data["error"]["code"] == "EMPTY_DOCUMENT"


def test_list_policies(client: TestClient):
    """Verify listing policies returns 200 and a list."""
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_complaint_contract(client: TestClient, sample_complaint_payload: dict):
    """Verify POST /api/v1/complaints matches API_SPEC.md response contract."""
    response = client.post("/api/v1/complaints", json=sample_complaint_payload)
    assert response.status_code == 201
    data = response.json()

    assert "complaint_id" in data
    assert "status" in data
    assert "issues" in data
    assert "draft" in data
    assert "validation" in data

    # Verify draft sub-fields
    assert "draft_id" in data["draft"]
    assert "text" in data["draft"]
    assert "citations" in data["draft"]

    # Verify validation sub-fields
    assert "valid" in data["validation"]
    assert "errors" in data["validation"]
    assert "warnings" in data["validation"]


def test_post_complaint_invalid_validation_error(client: TestClient):
    """Verify invalid complaint triggers centralized 422 error handler."""
    response = client.post("/api/v1/complaints", json={"complaint_text": "too short"})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_INPUT"
    assert data["error"]["retryable"] is False


def test_record_review_decision_contract(client: TestClient, sample_review_payload: dict):
    """Verify recording a review decision contract."""
    complaint_id = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/complaints/{complaint_id}/review",
        json=sample_review_payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["decision"] == "approved"
    assert data["complaint_id"] == complaint_id
    assert "review_id" in data
    assert "reviewed_at" in data


def test_record_review_invalid_decision(client: TestClient):
    """Verify invalid review decision is rejected."""
    complaint_id = str(uuid.uuid4())
    payload = {
        "draft_id": str(uuid.uuid4()),
        "decision": "invalid_action_xyz",
    }
    response = client.post(f"/api/v1/complaints/{complaint_id}/review", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_INPUT"


def test_complaint_history_contract(client: TestClient):
    """Verify GET /api/v1/complaints/{id}/history returns history structure."""
    complaint_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/complaints/{complaint_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_id"] == complaint_id
    assert "drafts" in data
    assert "reviews" in data
