"""Camera registration and query endpoints per docs/DATABASE_SCHEMA.md#Camera."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Camera
from backend.app.schemas import CameraCreate, CameraResponse

router = APIRouter(prefix="/cameras", tags=["Cameras"])


@router.get(
    "",
    response_model=List[CameraResponse],
    summary="List all registered cameras",
)
def list_cameras(db: Session = Depends(get_db)):
    cameras = db.query(Camera).order_by(Camera.created_at.desc()).all()
    return cameras


@router.post(
    "",
    response_model=CameraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new camera source",
)
def register_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(Camera.camera_id == payload.camera_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with ID '{payload.camera_id}' is already registered.",
        )

    cam = Camera(
        camera_id=payload.camera_id,
        location=payload.location,
        active=payload.active,
        camera_metadata=payload.camera_metadata,
    )
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


@router.get(
    "/{camera_id}",
    response_model=CameraResponse,
    summary="Get camera details by ID",
)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with ID '{camera_id}' not found.",
        )
    return cam
