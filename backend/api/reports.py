"""Maintenance report endpoints per docs/API_CONTRACTS.md."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import ReportCreate, ReportResponse, ReportUpdate
from backend.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create maintenance report",
    description="Creates a maintenance repair report derived from a confirmed PotholeEvent.",
)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
):
    report = report_service.create_report(db=db, payload=payload)
    return ReportResponse.model_validate(report)


@router.get(
    "",
    response_model=List[ReportResponse],
    summary="List maintenance reports",
)
def list_reports(
    status: Optional[str] = Query(None, description="Filter by status (pending, approved, in_progress, resolved)"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high, critical)"),
    event_id: Optional[str] = Query(None, description="Filter by originating PotholeEvent ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    reports = report_service.list_reports(
        db=db,
        status_filter=status,
        priority_filter=priority,
        event_id=event_id,
        limit=limit,
        offset=offset,
    )
    return [ReportResponse.model_validate(r) for r in reports]


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report by ID",
)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = report_service.get_report(db=db, report_id=report_id)
    return ReportResponse.model_validate(report)


@router.patch(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Update report details",
)
def update_report(
    report_id: str,
    update: ReportUpdate,
    db: Session = Depends(get_db),
):
    report = report_service.update_report(db=db, report_id=report_id, update=update)
    return ReportResponse.model_validate(report)
