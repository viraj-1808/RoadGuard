"""Aggregate API router for RoadGuard AI."""

from fastapi import APIRouter

from backend.api.cameras import router as cameras_router
from backend.api.detections import router as detections_router
from backend.api.events import router as events_router
from backend.api.evidence import router as evidence_router
from backend.api.health import router as health_router
from backend.api.reports import router as reports_router

api_router = APIRouter(prefix="/api")

# Include individual sub-routers
api_router.include_router(health_router)
api_router.include_router(events_router)
api_router.include_router(reports_router)
api_router.include_router(detections_router)
api_router.include_router(evidence_router)
api_router.include_router(cameras_router)
