"""Automated tests for image detection endpoint and model boundary safeguards."""

from fastapi.testclient import TestClient


def test_detection_status_endpoint(client: TestClient):
    """Test /api/detect/status reports model configuration state."""
    response = client.get("/api/detect/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "model_name" in data
    assert "checkpoint_path" in data


def test_detection_fails_cleanly_when_model_weights_missing(client: TestClient, sample_image_bytes: bytes):
    """Test safeguard: when weights are missing, never fabricate detections; return documented 503 error."""
    files = {"file": ("road_sample.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post("/api/detect/image", files=files)

    # In our local test environment where the model weights file does not exist,
    # the server must return 503 Service Unavailable with explicit error details.
    assert response.status_code == 503
    error_data = response.json()["detail"]
    assert error_data["error"] == "InferenceNotConfigured"
    assert "model checkpoint was not found" in error_data["message"]
    assert "model_name" in error_data


def test_detection_rejects_unsupported_media_type(client: TestClient):
    """Test detection endpoint rejects non-image file uploads with 415."""
    files = {"file": ("script.py", b"print('hello')", "text/x-python")}
    response = client.post("/api/detect/image", files=files)
    assert response.status_code == 415
    assert "Unsupported image type" in response.json()["detail"]


def test_detection_rejects_empty_file(client: TestClient):
    """Test detection endpoint rejects empty image file with 400."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/detect/image", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]
