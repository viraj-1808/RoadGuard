"""Event ingestion, query, and management endpoints per docs/API_CONTRACTS.md."""

from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    EvidenceResponse,
    PotholeEventCreate,
    PotholeEventResponse,
    PotholeEventStatusUpdate,
)
from backend.services.event_service import event_service
from backend.services.evidence_service import evidence_service

router = APIRouter(prefix="/events", tags=["Events"])


def _format_event_response(event) -> PotholeEventResponse:
    evidence_list = [
        EvidenceResponse.model_validate(ev) for ev in (event.evidence or [])
    ]
    return PotholeEventResponse(
        event_id=event.event_id,
        source_id=event.source_id,
        camera_id=event.camera_id,
        model_version_id=event.model_version_id,
        timestamp=event.timestamp,
        confidence=event.confidence,
        bbox=event.bbox,
        location=event.location,
        status=event.status,
        evidence_ref=event.evidence_ref,
        created_at=event.created_at,
        evidence=evidence_list,
        has_report=event.report is not None,
    )


@router.post(
    "",
    response_model=PotholeEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a PotholeEvent",
    description="Idempotent ingestion endpoint for PotholeEvents from inference pipeline or client.",
)
def ingest_event(
    payload: PotholeEventCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    event, created = event_service.ingest_event(db=db, payload=payload)
    if not created:
        response.status_code = status.HTTP_200_OK
    return _format_event_response(event)


@router.get(
    "",
    response_model=List[PotholeEventResponse],
    summary="List and filter PotholeEvents",
)
def list_events(
    status: Optional[str] = Query(None, description="Filter by event status (e.g. pending, approved, resolved)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    camera_id: Optional[str] = Query(None, description="Filter by source camera ID"),
    source_id: Optional[str] = Query(None, description="Filter by source identifier"),
    start_time: Optional[datetime] = Query(None, description="Start timestamp in UTC"),
    end_time: Optional[datetime] = Query(None, description="End timestamp in UTC"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    events = event_service.list_events(
        db=db,
        status_filter=status,
        min_confidence=min_confidence,
        camera_id=camera_id,
        source_id=source_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return [_format_event_response(e) for e in events]


@router.get(
    "/{event_id}",
    response_model=PotholeEventResponse,
    summary="Get PotholeEvent by ID",
)
def get_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    event = event_service.get_event(db=db, event_id=event_id)
    return _format_event_response(event)


@router.patch(
    "/{event_id}/status",
    response_model=PotholeEventResponse,
    summary="Update PotholeEvent status",
)
def update_event_status(
    event_id: str,
    update: PotholeEventStatusUpdate,
    db: Session = Depends(get_db),
):
    event = event_service.update_event_status(db=db, event_id=event_id, update=update)
    return _format_event_response(event)


@router.get(
    "/{event_id}/evidence",
    response_model=List[EvidenceResponse],
    summary="List evidence associated with event",
)
def get_event_evidence(
    event_id: str,
    db: Session = Depends(get_db),
):
    event = event_service.get_event(db=db, event_id=event_id)
    return [EvidenceResponse.model_validate(ev) for ev in event.evidence]


@router.post(
    "/{event_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload evidence image for event",
)
def upload_event_evidence(
    event_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    evidence = evidence_service.validate_and_save_upload(
        file=file,
        db=db,
        pothole_event_id=event_id,
    )
    return EvidenceResponse.model_validate(evidence)
