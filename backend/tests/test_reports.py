"""Automated tests for maintenance Report creation, constraints, queries, and updates."""

from fastapi.testclient import TestClient


def test_create_report_success(client: TestClient):
    """Test successful creation of a maintenance report linked to an event."""
    # First ingest event
    client.post("/api/events", json={"event_id": "evt_for_rep_1", "confidence": 0.89})

    report_payload = {
        "report_id": "rep_001",
        "event_id": "evt_for_rep_1",
        "submitted_by": "Inspector Jane Doe",
        "priority": "high",
        "status": "pending",
    }
    response = client.post("/api/reports", json=report_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["report_id"] == "rep_001"
    assert data["event_id"] == "evt_for_rep_1"
    assert data["submitted_by"] == "Inspector Jane Doe"
    assert data["priority"] == "high"
    assert data["status"] == "pending"
    assert "submitted_at" in data


def test_create_report_for_nonexistent_event_fails(client: TestClient):
    """Test report creation fails with 404 when target event does not exist."""
    report_payload = {
        "event_id": "evt_nonexistent_999",
        "submitted_by": "Officer Smith",
        "priority": "medium",
    }
    response = client.post("/api/reports", json=report_payload)
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_create_duplicate_report_for_same_event_rejected(client: TestClient):
    """Test 1-to-1 invariant: only one report can be created per PotholeEvent."""
    client.post("/api/events", json={"event_id": "evt_single_rep", "confidence": 0.90})

    # First report succeeds
    res1 = client.post("/api/reports", json={
        "event_id": "evt_single_rep",
        "submitted_by": "Crew A",
    })
    assert res1.status_code == 201

    # Second report for same event must be rejected with 409 Conflict
    res2 = client.post("/api/reports", json={
        "event_id": "evt_single_rep",
        "submitted_by": "Crew B",
    })
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_list_and_filter_reports(client: TestClient):
    """Test listing reports with priority and status filtering."""
    client.post("/api/events", json={"event_id": "evt_r1", "confidence": 0.8})
    client.post("/api/events", json={"event_id": "evt_r2", "confidence": 0.8})

    client.post("/api/reports", json={"event_id": "evt_r1", "submitted_by": "A", "priority": "critical"})
    client.post("/api/reports", json={"event_id": "evt_r2", "submitted_by": "B", "priority": "low"})

    # Filter critical priority
    res = client.get("/api/reports?priority=critical")
    assert res.status_code == 200
    crit = res.json()
    assert len(crit) == 1
    assert crit[0]["priority"] == "critical"


def test_update_report(client: TestClient):
    """Test updating priority, resolution, and status on an existing report."""
    client.post("/api/events", json={"event_id": "evt_up_rep", "confidence": 0.85})
    create_res = client.post("/api/reports", json={
        "report_id": "rep_update_me",
        "event_id": "evt_up_rep",
        "submitted_by": "Supervisor Lee",
        "priority": "medium",
    })
    assert create_res.status_code == 201

    # Update status and resolution
    update_res = client.patch("/api/reports/rep_update_me", json={
        "status": "resolved",
        "resolution": "Pothole filled with cold mix asphalt on 2026-10-13",
        "priority": "low",
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["status"] == "resolved"
    assert "cold mix asphalt" in updated["resolution"]
    assert updated["priority"] == "low"


def test_invalid_report_priority_or_status_rejected(client: TestClient):
    """Test rejection with 422 for invalid priority or status."""
    client.post("/api/events", json={"event_id": "evt_inv_rep", "confidence": 0.85})

    # Invalid priority
    res1 = client.post("/api/reports", json={
        "event_id": "evt_inv_rep",
        "submitted_by": "User",
        "priority": "invalid_priority_level",
    })
    assert res1.status_code == 422
