"""Pytest fixtures for RoadGuard AI backend testing."""

import io
from pathlib import Path
import tempfile
from typing import Generator

from fastapi.testclient import TestClient
from PIL import Image
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.config import settings
settings.DATABASE_URL = "sqlite:///:memory:"

from backend.app.database import Base, get_db
import backend.app.database as db_module
from backend.main import app
from backend.services.evidence_service import evidence_service


@pytest.fixture(autouse=True)
def prevent_disk_db(monkeypatch):
    """Ensure init_db does not write to disk during testing."""
    monkeypatch.setattr(db_module, "init_db", lambda: None)


@pytest.fixture(scope="session")
def temp_storage_dir():
    """Create a temporary directory for evidence files during test execution."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        original_storage = evidence_service.storage_dir
        evidence_service.storage_dir = tmp_path
        yield tmp_path
        evidence_service.storage_dir = original_storage


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create an isolated in-memory SQLite database session for each test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session, temp_storage_dir: Path) -> Generator[TestClient, None, None]:
    """TestClient configured with the overridden test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a minimal valid JPEG image in bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(200, 50, 50))
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate a minimal valid PNG image in bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(0, 150, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()
