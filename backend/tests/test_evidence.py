"""Automated tests for evidence file upload, validation, safe filenames, and retrieval."""

import io
from fastapi.testclient import TestClient


def test_upload_valid_evidence_image(client: TestClient, sample_image_bytes: bytes):
    """Test uploading a valid JPEG image attached to an existing PotholeEvent."""
    client.post("/api/events", json={"event_id": "evt_with_evidence", "confidence": 0.91})

    files = {"file": ("dashcam_frame.jpg", sample_image_bytes, "image/jpeg")}
    response = client.post("/api/events/evt_with_evidence/evidence", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["evidence_id"].startswith("ev_")
    assert data["pothole_event_id"] == "evt_with_evidence"
    assert data["media_type"] == "image"
    assert data["file_size_bytes"] == len(sample_image_bytes)
    assert "storage_path" in data
    # Verify server filename does not use user's "dashcam_frame.jpg"
    assert "dashcam_frame.jpg" not in data["storage_path"]


def test_reject_unsupported_file_type(client: TestClient):
    """Test rejection with 415 when uploading an unsupported file type."""
    client.post("/api/events", json={"event_id": "evt_for_unsupported", "confidence": 0.8})

    files = {"file": ("malicious.sh", b"#!/bin/bash\necho hack", "application/x-sh")}
    response = client.post("/api/events/evt_for_unsupported/evidence", files=files)
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_reject_corrupted_image_payload(client: TestClient):
    """Test rejection with 400 when MIME type claims image but content is corrupted or spoofed."""
    client.post("/api/events", json={"event_id": "evt_corrupt", "confidence": 0.8})

    fake_image_bytes = b"This is not a real image header"
    files = {"file": ("fake.jpg", fake_image_bytes, "image/jpeg")}
    response = client.post("/api/events/evt_corrupt/evidence", files=files)
    assert response.status_code == 400
    assert "Invalid or corrupted image" in response.json()["detail"]


def test_reject_empty_file_upload(client: TestClient):
    """Test rejection with 400 when uploaded file is empty (0 bytes)."""
    client.post("/api/events", json={"event_id": "evt_empty", "confidence": 0.8})

    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/events/evt_empty/evidence", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_evidence_metadata_and_file_download(client: TestClient, sample_png_bytes: bytes):
    """Test retrieving evidence metadata and downloading the saved binary file."""
    client.post("/api/events", json={"event_id": "evt_download_test", "confidence": 0.88})

    files = {"file": ("pothole_crop.png", sample_png_bytes, "image/png")}
    upload_res = client.post("/api/events/evt_download_test/evidence", files=files)
    assert upload_res.status_code == 201
    evidence_id = upload_res.json()["evidence_id"]

    # 1. Fetch metadata
    meta_res = client.get(f"/api/evidence/{evidence_id}")
    assert meta_res.status_code == 200
    assert meta_res.json()["evidence_id"] == evidence_id

    # 2. Download file
    file_res = client.get(f"/api/evidence/{evidence_id}/file")
    assert file_res.status_code == 200
    assert file_res.content == sample_png_bytes
