"""Event persistence and query service."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app.models import Camera, PotholeEvent
from backend.app.schemas import (
    PotholeEventCreate,
    PotholeEventResponse,
    PotholeEventStatusUpdate,
)

VALID_STATUSES = {"candidate", "pending", "approved", "rejected", "resolved", "closed"}


class EventService:
    """Service handling PotholeEvent ingestion, retrieval, status progression, and queries."""

    def ingest_event(
        self,
        db: Session,
        payload: PotholeEventCreate,
    ) -> Tuple[PotholeEvent, bool]:
        """Ingest a PotholeEvent.

        Returns (event, created):
        - If event_id exists, returns (existing_event, False) for idempotency.
        - Otherwise returns (new_event, True).
        """
        # 1. Idempotency check if client provided event_id
        if payload.event_id:
            existing = (
                db.query(PotholeEvent)
                .options(joinedload(PotholeEvent.evidence), joinedload(PotholeEvent.report))
                .filter(PotholeEvent.event_id == payload.event_id)
                .first()
            )
            if existing:
                return existing, False

        # 2. Assign unique ID if not provided
        event_id = payload.event_id or f"evt_{uuid.uuid4().hex}"

        # 3. Ensure camera exists if camera_id is given
        if payload.camera_id:
            cam = db.query(Camera).filter(Camera.camera_id == payload.camera_id).first()
            if not cam:
                cam = Camera(
                    camera_id=payload.camera_id,
                    location=payload.location,
                    active=True,
                )
                db.add(cam)
                db.flush()

        event_timestamp = payload.timestamp or datetime.now(timezone.utc)
        initial_status = (payload.status or "pending").lower()
        if initial_status not in VALID_STATUSES:
            initial_status = "pending"

        new_event = PotholeEvent(
            event_id=event_id,
            source_id=payload.source_id,
            camera_id=payload.camera_id,
            model_version_id=payload.model_version_id,
            timestamp=event_timestamp,
            confidence=payload.confidence,
            bbox=payload.bbox,
            location=payload.location,
            status=initial_status,
            evidence_ref=payload.evidence_ref,
            created_at=datetime.now(timezone.utc),
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event, True

    def get_event(self, db: Session, event_id: str) -> PotholeEvent:
        """Retrieve a single PotholeEvent by ID with evidence and report."""
        event = (
            db.query(PotholeEvent)
            .options(joinedload(PotholeEvent.evidence), joinedload(PotholeEvent.report))
            .filter(PotholeEvent.event_id == event_id)
            .first()
        )
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PotholeEvent with ID '{event_id}' not found.",
            )
        return event

    def list_events(
        self,
        db: Session,
        status_filter: Optional[str] = None,
        min_confidence: Optional[float] = None,
        camera_id: Optional[str] = None,
        source_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PotholeEvent]:
        """List PotholeEvents with multi-parameter filtering and pagination."""
        query = db.query(PotholeEvent).options(
            joinedload(PotholeEvent.evidence),
            joinedload(PotholeEvent.report),
        )

        if status_filter:
            query = query.filter(PotholeEvent.status == status_filter.lower())
        if min_confidence is not None:
            query = query.filter(PotholeEvent.confidence >= min_confidence)
        if camera_id:
            query = query.filter(PotholeEvent.camera_id == camera_id)
        if source_id:
            query = query.filter(PotholeEvent.source_id == source_id)
        if start_time:
            query = query.filter(PotholeEvent.timestamp >= start_time)
        if end_time:
            query = query.filter(PotholeEvent.timestamp <= end_time)

        query = query.order_by(PotholeEvent.timestamp.desc())
        return query.offset(offset).limit(limit).all()

    def update_event_status(
        self,
        db: Session,
        event_id: str,
        update: PotholeEventStatusUpdate,
    ) -> PotholeEvent:
        """Update the status of an existing PotholeEvent."""
        event = self.get_event(db, event_id)
        normalized_status = update.status.lower()
        if normalized_status not in VALID_STATUSES:
            http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
            raise HTTPException(
                status_code=http_422,
                detail=f"Invalid status '{update.status}'. Allowed: {sorted(list(VALID_STATUSES))}",
            )

        event.status = normalized_status
        db.commit()
        db.refresh(event)
        return event


event_service = EventService()
