"""Automated tests for backend health check and root endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns service identity and navigation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "RoadGuard AI API"
    assert data["status"] == "online"
    assert "health_check" in data


def test_health_check_api_endpoint(client: TestClient):
    """Test /api/health returns healthy status and DB connection."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert "model_configured" in data


def test_root_health_alias(client: TestClient):
    """Test top-level /health alias behaves identically."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
