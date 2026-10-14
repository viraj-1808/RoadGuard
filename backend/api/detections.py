"""Detection endpoints exposing image-based pothole detection through the service boundary."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas import DetectionResponse, PotholeEventCreate
from backend.services.detection_service import detection_service
from backend.services.event_service import event_service
from backend.services.evidence_service import evidence_service

router = APIRouter(prefix="/detect", tags=["Detection"])


@router.get(
    "/status",
    summary="Get model and inference readiness status",
)
def get_detection_status():
    """Return whether model checkpoint is present and inference engine is configured."""
    return detection_service.get_model_status()


@router.post(
    "/image",
    response_model=DetectionResponse,
    summary="Run detection on uploaded image",
    description=(
        "Executes object detection on an uploaded road image through the ModelAdapter boundary. "
        "If model weights are unconfigured or missing, returns HTTP 503 with explicit diagnostic details. "
        "Optionally auto-creates PotholeEvents and attaches saved evidence."
    ),
)
def detect_image(
    file: UploadFile = File(..., description="Road image file (JPEG, PNG, or WebP)"),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Confidence threshold"),
    iou: Optional[float] = Query(None, ge=0.0, le=1.0, description="NMS IoU threshold"),
    auto_create_event: bool = Query(False, description="Whether to automatically persist detected potholes as PotholeEvents"),
    camera_id: Optional[str] = Query(None, description="Optional camera ID to link with auto-created events"),
    db: Session = Depends(get_db),
):
    # 1. Validate file extension and MIME type
    content_type = file.content_type or ""
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type '{content_type}'. Allowed: {settings.ALLOWED_IMAGE_TYPES}",
        )

    # 2. Read bytes and validate size
    image_bytes = file.file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty (0 bytes).",
        )
    if len(image_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds limit ({settings.MAX_UPLOAD_SIZE_BYTES} bytes).",
        )

    # 3. Call detection service boundary
    filename = file.filename or "uploaded_image.jpg"
    result = detection_service.detect_on_image_bytes(
        image_bytes=image_bytes,
        filename=filename,
        confidence_threshold=confidence,
        iou_threshold=iou,
    )

    # 4. Optional auto-creation of PotholeEvents if detections were found
    if auto_create_event and result.detections:
        created_event_ids: List[str] = []
        for det in result.detections:
            if det.class_name.lower() == "pothole":
                event_payload = PotholeEventCreate(
                    source_id=camera_id or "upload_session",
                    camera_id=camera_id,
                    confidence=det.confidence,
                    bbox=det.bbox,
                    status="pending",
                )
                event, _ = event_service.ingest_event(db=db, payload=event_payload)
                created_event_ids.append(event.event_id)
        result.auto_event_ids = created_event_ids

    return result
