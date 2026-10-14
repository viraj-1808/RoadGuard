"""Evidence retrieval and file serving endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Evidence
from backend.app.schemas import EvidenceResponse
from backend.services.evidence_service import evidence_service

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get evidence metadata by ID",
)
def get_evidence_metadata(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{evidence_id}' not found.",
        )
    return EvidenceResponse.model_validate(evidence)


@router.get(
    "/{evidence_id}/file",
    summary="Download or stream evidence media file",
)
def get_evidence_file(
    evidence_id: str,
    db: Session = Depends(get_db),
):
    evidence = db.query(Evidence).filter(Evidence.evidence_id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{evidence_id}' not found.",
        )

    file_path = evidence_service.get_evidence_file_path(evidence)
    return FileResponse(
        path=str(file_path),
        media_type=evidence.mime_type or "image/jpeg",
        filename=file_path.name,
    )
