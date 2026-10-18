"""Evidence file storage and validation service."""

from datetime import datetime, timezone
import io
import os
from pathlib import Path
import uuid
from typing import BinaryIO, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Evidence, PotholeEvent


ALLOWED_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class EvidenceStorageError(Exception):
    """Raised when evidence storage fails."""
    pass


class EvidenceService:
    """Service handling secure validation, storage, and retrieval of evidence files."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.evidence_storage_path
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def validate_and_save_upload(
        self,
        file: UploadFile,
        db: Session,
        pothole_event_id: Optional[str] = None,
        verified: bool = False,
    ) -> Evidence:
        """Validate an uploaded file, store it safely with a server-generated filename, and persist evidence record."""
        # 1. Check Content-Type header
        content_type = file.content_type or ""
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{content_type}'. Allowed: {settings.ALLOWED_IMAGE_TYPES}",
            )

        # 2. Read content and enforce maximum file size
        file_bytes = file.file.read()
        file_size = len(file_bytes)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size} bytes) exceeds limit ({settings.MAX_UPLOAD_SIZE_BYTES} bytes).",
            )

        # 3. Deep image integrity check using Pillow
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
                img_format = img.format.lower() if img.format else "jpeg"
        except (UnidentifiedImageError, Exception) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or corrupted image payload: {str(exc)}",
            )

        # 4. Generate safe server-side filename (never trust client filename)
        extension = ALLOWED_EXTENSIONS.get(content_type, f".{img_format}")
        evidence_id = f"ev_{uuid.uuid4().hex}"
        safe_filename = f"{evidence_id}{extension}"
        destination_path = (self.storage_dir / safe_filename).resolve()

        # Path traversal safeguard
        if not str(destination_path).startswith(str(self.storage_dir.resolve())):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid destination path calculation.",
            )

        # 5. Write file to disk
        try:
            with open(destination_path, "wb") as f:
                f.write(file_bytes)
        except OSError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist file to disk: {str(e)}",
            )

        # 6. Verify event existence if provided
        if pothole_event_id:
            event = db.query(PotholeEvent).filter(PotholeEvent.event_id == pothole_event_id).first()
            if not event:
                # Cleanup file if event not found
                if destination_path.exists():
                    destination_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PotholeEvent with ID '{pothole_event_id}' not found.",
                )

        # 7. Create database record
        relative_storage_path = os.path.relpath(destination_path, start=Path.cwd())
        evidence = Evidence(
            evidence_id=evidence_id,
            pothole_event_id=pothole_event_id,
            media_type="image",
            storage_path=str(relative_storage_path).replace("\\", "/"),
            captured_at=datetime.now(timezone.utc),
            verified=verified,
            file_size_bytes=file_size,
            mime_type=content_type,
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)
        return evidence

    def get_evidence_file_path(self, evidence: Evidence) -> Path:
        """Resolve evidence file path safely, preventing directory traversal."""
        resolved_path = Path(evidence.storage_path).resolve()
        if not resolved_path.exists():
            # Try resolving relative to storage dir
            filename = Path(evidence.storage_path).name
            resolved_path = (self.storage_dir / filename).resolve()

        if not resolved_path.exists() or not resolved_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence file artifact not found on disk.",
            )
        return resolved_path


evidence_service = EvidenceService()
