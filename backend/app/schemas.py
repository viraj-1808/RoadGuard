"""Pydantic schemas for request validation and response serialization.

Follows definitions from:
- docs/EVENT_SCHEMAS.md
- docs/API_CONTRACTS.md
- docs/DATABASE_SCHEMA.md
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Base / Shared Schemas
# ---------------------------------------------------------------------------

class Location(BaseModel):
    """Geographic location coordinates."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    address: Optional[str] = None
    accuracy_m: Optional[float] = None


class HealthResponse(BaseModel):
    """System health-check response model."""
    status: str
    service: str
    version: str
    database: str
    model_configured: bool
    model_name: Optional[str] = None
    timestamp: datetime


# ---------------------------------------------------------------------------
# Camera Schemas
# ---------------------------------------------------------------------------

class CameraBase(BaseModel):
    camera_id: str = Field(..., min_length=1, max_length=64)
    location: Optional[Dict[str, Any]] = None
    active: bool = True
    camera_metadata: Optional[Dict[str, Any]] = None


class CameraCreate(CameraBase):
    pass


class CameraResponse(CameraBase):
    created_at: datetime
    last_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Detection & Inference Schemas (contracts/detection/ boundary)
# ---------------------------------------------------------------------------

class Detection(BaseModel):
    """Single frame-level observation per contracts/detection/."""
    class_name: str = Field(default="pothole", description="Detected class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0-1]")
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2] coordinates")
    frame_id: Optional[str] = None
    capture_timestamp: Optional[datetime] = None


class DetectionResponse(BaseModel):
    """Response returned from image detection endpoint."""
    image_id: str
    filename: str
    image_width: int
    image_height: int
    inference_time_ms: float
    model_name: str
    detections: List[Detection]
    total_detections: int
    auto_event_ids: List[str] = Field(default_factory=list, description="IDs of auto-created PotholeEvents if requested")


# ---------------------------------------------------------------------------
# Evidence Schemas
# ---------------------------------------------------------------------------

class EvidenceCreate(BaseModel):
    evidence_id: Optional[str] = None
    pothole_event_id: Optional[str] = None
    media_type: str = "image"
    storage_path: str
    captured_at: Optional[datetime] = None
    verified: bool = False
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class EvidenceResponse(BaseModel):
    evidence_id: str
    pothole_event_id: Optional[str] = None
    media_type: str
    storage_path: str
    captured_at: datetime
    verified: bool
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# PotholeEvent Schemas (docs/EVENT_SCHEMAS.md#PotholeEvent)
# ---------------------------------------------------------------------------

class PotholeEventCreate(BaseModel):
    """Payload for ingesting a PotholeEvent."""
    event_id: Optional[str] = Field(None, max_length=64, description="Unique event identifier (client or server generated)")
    source_id: Optional[str] = Field(None, max_length=64, description="Identifier of capture source")
    camera_id: Optional[str] = Field(None, max_length=64, description="Foreign key to Camera")
    model_version_id: Optional[str] = Field(None, max_length=64, description="Foreign key to ModelVersion")
    timestamp: Optional[datetime] = Field(None, description="Time event was finalized")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Aggregated confidence score")
    bbox: Optional[List[float]] = Field(None, description="[x1, y1, x2, y2] bounding box")
    location: Optional[Dict[str, Any]] = Field(None, description="GPS/location metadata")
    status: Optional[str] = Field(default="pending", description="Event state (pending, approved, rejected, resolved, closed)")
    evidence_ref: Optional[str] = Field(None, max_length=256, description="Reference to evidence media")


class PotholeEventStatusUpdate(BaseModel):
    """Payload for updating event status."""
    status: str = Field(..., min_length=1, max_length=32, description="Target status (e.g. pending, approved, rejected, resolved, closed)")


class PotholeEventResponse(BaseModel):
    """Response schema for a PotholeEvent."""
    event_id: str
    source_id: Optional[str] = None
    camera_id: Optional[str] = None
    model_version_id: Optional[str] = None
    timestamp: datetime
    confidence: float
    bbox: Optional[List[float]] = None
    location: Optional[Dict[str, Any]] = None
    status: str
    evidence_ref: Optional[str] = None
    created_at: datetime
    evidence: List[EvidenceResponse] = []
    has_report: bool = False

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Report Schemas (docs/EVENT_SCHEMAS.md#Report)
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    """Payload for creating a maintenance Report derived from a PotholeEvent."""
    report_id: Optional[str] = Field(None, max_length=64)
    event_id: str = Field(..., max_length=64, description="Link to originating PotholeEvent")
    submitted_by: str = Field(..., min_length=1, max_length=128)
    priority: Optional[str] = Field(default="medium", description="low, medium, high, critical")
    resolution: Optional[str] = None
    status: Optional[str] = Field(default="pending", description="pending, approved, in_progress, resolved")


class ReportUpdate(BaseModel):
    """Payload for updating an existing Report."""
    priority: Optional[str] = Field(None, description="low, medium, high, critical")
    resolution: Optional[str] = None
    status: Optional[str] = Field(None, description="pending, approved, in_progress, resolved")


class ReportResponse(BaseModel):
    """Response schema for a maintenance Report."""
    report_id: str
    event_id: str
    submitted_by: str
    submitted_at: datetime
    priority: str
    resolution: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# ModelVersion Schemas
# ---------------------------------------------------------------------------

class ModelVersionCreate(BaseModel):
    model_version_id: str = Field(..., max_length=64)
    model_name: str = Field(..., max_length=64)
    weights_hash: str = Field(..., max_length=128)
    accuracy_metrics: Optional[Dict[str, Any]] = None
    is_active: bool = False


class ModelVersionResponse(BaseModel):
    model_version_id: str
    model_name: str
    weights_hash: str
    accuracy_metrics: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
