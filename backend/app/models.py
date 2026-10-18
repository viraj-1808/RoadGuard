"""SQLAlchemy domain models for RoadGuard AI matching docs/DATABASE_SCHEMA.md."""

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


class Camera(Base):
    """Camera entity representing a physical or logical image/video capture source."""

    __tablename__ = "cameras"

    camera_id = Column(String(64), primary_key=True, index=True)
    location = Column(JSON, nullable=True)  # {"latitude": float, "longitude": float}
    active = Column(Boolean, default=True, nullable=False)
    camera_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    events = relationship("PotholeEvent", back_populates="camera")


class ModelVersion(Base):
    """ModelVersion entity tracking provenance of models producing inferences."""

    __tablename__ = "model_versions"

    model_version_id = Column(String(64), primary_key=True, index=True)
    model_name = Column(String(64), nullable=False)
    weights_hash = Column(String(128), nullable=False)
    accuracy_metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    events = relationship("PotholeEvent", back_populates="model_version")


class PotholeEvent(Base):
    """PotholeEvent entity representing a logical, reportable occurrence."""

    __tablename__ = "pothole_events"

    event_id = Column(String(64), primary_key=True, index=True)
    source_id = Column(String(64), nullable=True, index=True)
    camera_id = Column(String(64), ForeignKey("cameras.camera_id"), nullable=True)
    model_version_id = Column(
        String(64),
        ForeignKey("model_versions.model_version_id"),
        nullable=True,
    )
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox = Column(JSON, nullable=True)  # [x1, y1, x2, y2]
    location = Column(JSON, nullable=True)  # {"latitude": float, "longitude": float}
    status = Column(String(32), default="pending", nullable=False, index=True)
    evidence_ref = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    camera = relationship("Camera", back_populates="events")
    model_version = relationship("ModelVersion", back_populates="events")
    evidence = relationship(
        "Evidence",
        back_populates="pothole_event",
        cascade="all, delete-orphan",
    )
    report = relationship(
        "Report",
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Evidence(Base):
    """Evidence entity storing references to media artifacts associated with events."""

    __tablename__ = "evidence"

    evidence_id = Column(String(64), primary_key=True, index=True)
    pothole_event_id = Column(
        String(64),
        ForeignKey("pothole_events.event_id"),
        nullable=True,
        index=True,
    )
    media_type = Column(String(32), default="image", nullable=False)
    storage_path = Column(String(512), nullable=False)
    captured_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)

    # Relationships
    pothole_event = relationship("PotholeEvent", back_populates="evidence")


class Report(Base):
    """Report entity representing a human- or agency-initiated action on an event."""

    __tablename__ = "reports"

    report_id = Column(String(64), primary_key=True, index=True)
    event_id = Column(
        String(64),
        ForeignKey("pothole_events.event_id"),
        unique=True,
        nullable=False,
        index=True,
    )
    submitted_by = Column(String(128), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    priority = Column(String(32), default="medium", nullable=False)  # low, medium, high, critical
    resolution = Column(Text, nullable=True)
    status = Column(String(32), default="pending", nullable=False)  # pending, approved, in_progress, resolved

    # Relationships
    event = relationship("PotholeEvent", back_populates="report")
