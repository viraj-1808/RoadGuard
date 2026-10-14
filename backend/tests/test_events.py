"""Automated tests for PotholeEvent ingestion, retrieval, idempotency, and status updates."""

from fastapi.testclient import TestClient


def test_ingest_event_success(client: TestClient):
    """Test successful ingestion of a new PotholeEvent."""
    payload = {
        "event_id": "evt_test_001",
        "source_id": "dashcam_front",
        "camera_id": "cam_highway_48",
        "confidence": 0.88,
        "bbox": [120.5, 340.0, 250.0, 410.5],
        "location": {"latitude": 19.076, "longitude": 72.8777},
        "status": "pending",
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == "evt_test_001"
    assert data["confidence"] == 0.88
    assert data["camera_id"] == "cam_highway_48"
    assert data["bbox"] == [120.5, 340.0, 250.0, 410.5]
    assert data["status"] == "pending"
    assert "timestamp" in data
    assert "created_at" in data


def test_ingest_event_idempotency(client: TestClient):
    """Test idempotent replay returns existing record with status 200."""
    payload = {
        "event_id": "evt_idempotent_test",
        "source_id": "camera_01",
        "confidence": 0.75,
        "bbox": [10.0, 20.0, 30.0, 40.0],
    }
    # First post creates record
    first_resp = client.post("/api/events", json=payload)
    assert first_resp.status_code == 201

    # Second post with identical event_id returns existing record without conflict
    second_resp = client.post("/api/events", json=payload)
    assert second_resp.status_code == 200
    assert second_resp.json()["event_id"] == "evt_idempotent_test"


def test_ingest_event_auto_assigns_id(client: TestClient):
    """Test event_id is auto-generated if omitted."""
    payload = {
        "confidence": 0.92,
        "bbox": [15.0, 25.0, 35.0, 45.0],
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"].startswith("evt_")
    assert data["confidence"] == 0.92


def test_ingest_event_validation_errors(client: TestClient):
    """Test validation rejection on invalid confidence (>1.0 or <0.0) or invalid bbox length."""
    # Invalid confidence > 1.0
    res1 = client.post("/api/events", json={"confidence": 1.5, "bbox": [1, 2, 3, 4]})
    assert res1.status_code == 422
    assert "ValidationError" in res1.json()["error"]

    # Invalid confidence < 0.0
    res2 = client.post("/api/events", json={"confidence": -0.2, "bbox": [1, 2, 3, 4]})
    assert res2.status_code == 422

    # Missing confidence
    res3 = client.post("/api/events", json={"bbox": [1, 2, 3, 4]})
    assert res3.status_code == 422


def test_get_event_by_id(client: TestClient):
    """Test fetching existing event and 404 for non-existent event."""
    client.post("/api/events", json={"event_id": "evt_fetch_test", "confidence": 0.81})

    # Fetch existing
    res = client.get("/api/events/evt_fetch_test")
    assert res.status_code == 200
    assert res.json()["event_id"] == "evt_fetch_test"

    # Fetch missing
    res_missing = client.get("/api/events/evt_nonexistent_xyz")
    assert res_missing.status_code == 404


def test_list_events_and_filtering(client: TestClient):
    """Test listing events with status and confidence filters."""
    client.post("/api/events", json={"event_id": "evt_f1", "confidence": 0.30, "status": "pending"})
    client.post("/api/events", json={"event_id": "evt_f2", "confidence": 0.85, "status": "approved"})
    client.post("/api/events", json={"event_id": "evt_f3", "confidence": 0.95, "status": "approved"})

    # Filter by status
    res_status = client.get("/api/events?status=approved")
    assert res_status.status_code == 200
    approved = res_status.json()
    assert len(approved) == 2
    assert all(e["status"] == "approved" for e in approved)

    # Filter by min_confidence
    res_conf = client.get("/api/events?min_confidence=0.80")
    assert res_conf.status_code == 200
    high_conf = res_conf.json()
    assert len(high_conf) == 2
    assert all(e["confidence"] >= 0.80 for e in high_conf)


def test_update_event_status(client: TestClient):
    """Test updating event status and rejecting invalid status."""
    client.post("/api/events", json={"event_id": "evt_stat_test", "confidence": 0.77, "status": "pending"})

    # Valid status transition
    update_res = client.patch("/api/events/evt_stat_test/status", json={"status": "approved"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "approved"

    # Invalid status value
    invalid_res = client.patch("/api/events/evt_stat_test/status", json={"status": "invalid_unknown_state"})
    assert invalid_res.status_code == 422
