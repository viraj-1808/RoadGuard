"""Maintenance report service handling report lifecycle per docs/EVENT_SCHEMAS.md#Report."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models import PotholeEvent, Report
from backend.app.schemas import ReportCreate, ReportUpdate

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_REPORT_STATUSES = {"pending", "approved", "in_progress", "resolved"}


class ReportService:
    """Service handling maintenance report creation, queries, and updates."""

    def create_report(self, db: Session, payload: ReportCreate) -> Report:
        """Create a new maintenance report linked to a PotholeEvent."""
        # 1. Validate that the parent PotholeEvent exists
        event = db.query(PotholeEvent).filter(PotholeEvent.event_id == payload.event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cannot create report: PotholeEvent with ID '{payload.event_id}' does not exist.",
            )

        # 2. Check 1-to-1 or 1-to-0 constraint (one report per event)
        existing_report = db.query(Report).filter(Report.event_id == payload.event_id).first()
        if existing_report:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A report already exists for PotholeEvent '{payload.event_id}' (report_id: '{existing_report.report_id}').",
            )

        # 3. Validate priority and status
        http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
        priority = (payload.priority or "medium").lower()
        if priority not in VALID_PRIORITIES:
            raise HTTPException(
                status_code=http_422,
                detail=f"Invalid priority '{payload.priority}'. Allowed: {sorted(list(VALID_PRIORITIES))}",
            )

        report_status = (payload.status or "pending").lower()
        if report_status not in VALID_REPORT_STATUSES:
            raise HTTPException(
                status_code=http_422,
                detail=f"Invalid report status '{payload.status}'. Allowed: {sorted(list(VALID_REPORT_STATUSES))}",
            )

        report_id = payload.report_id or f"rep_{uuid.uuid4().hex}"

        report = Report(
            report_id=report_id,
            event_id=payload.event_id,
            submitted_by=payload.submitted_by,
            submitted_at=datetime.now(timezone.utc),
            priority=priority,
            resolution=payload.resolution,
            status=report_status,
        )

        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def get_report(self, db: Session, report_id: str) -> Report:
        """Retrieve a report by ID."""
        report = db.query(Report).filter(Report.report_id == report_id).first()
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with ID '{report_id}' not found.",
            )
        return report

    def list_reports(
        self,
        db: Session,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        event_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Report]:
        """List reports with filtering and pagination."""
        query = db.query(Report)
        if status_filter:
            query = query.filter(Report.status == status_filter.lower())
        if priority_filter:
            query = query.filter(Report.priority == priority_filter.lower())
        if event_id:
            query = query.filter(Report.event_id == event_id)

        query = query.order_by(Report.submitted_at.desc())
        return query.offset(offset).limit(limit).all()

    def update_report(
        self,
        db: Session,
        report_id: str,
        update: ReportUpdate,
    ) -> Report:
        """Update priority, resolution, or status of an existing report."""
        report = self.get_report(db, report_id)

        http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
        if update.priority is not None:
            p = update.priority.lower()
            if p not in VALID_PRIORITIES:
                raise HTTPException(
                    status_code=http_422,
                    detail=f"Invalid priority '{update.priority}'. Allowed: {sorted(list(VALID_PRIORITIES))}",
                )
            report.priority = p

        if update.status is not None:
            s = update.status.lower()
            if s not in VALID_REPORT_STATUSES:
                raise HTTPException(
                    status_code=http_422,
                    detail=f"Invalid status '{update.status}'. Allowed: {sorted(list(VALID_REPORT_STATUSES))}",
                )
            report.status = s

        if update.resolution is not None:
            report.resolution = update.resolution

        db.commit()
        db.refresh(report)
        return report


report_service = ReportService()
