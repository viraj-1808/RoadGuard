"""System health and diagnostic endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas import HealthResponse
from backend.services.detection_service import detection_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """Health check validating application runtime, database connectivity, and model configuration."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    model_status = detection_service.get_model_status()

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="RoadGuard AI Backend",
        version="0.1.0",
        database=db_status,
        model_configured=model_status["configured"],
        model_name=settings.MODEL_NAME if model_status["configured"] else None,
        timestamp=datetime.now(timezone.utc),
    )
