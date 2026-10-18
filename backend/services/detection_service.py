"""Model integration and detection service boundary.

In accordance with architectural requirements:
- Route handlers never import framework-specific model objects directly.
- Does not reimplement YOLO inference or duplicate model logic.
- Does not fabricate detections or silently report success when weights are missing.
- When model weights or inference are unconfigured/missing, returns a clear, documented error.
"""

from datetime import datetime, timezone
import io
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from fastapi import HTTPException, status
from PIL import Image

from backend.app.config import settings
from backend.app.schemas import Detection, DetectionResponse


class DetectionService:
    """Service boundary mediating between API routes and the project ModelAdapter."""

    def __init__(self):
        self._cached_adapter = None

    def is_model_available(self) -> bool:
        """Check if model checkpoint exists and is accessible."""
        checkpoint_path = Path(settings.MODEL_CHECKPOINT_PATH).resolve()
        return checkpoint_path.is_file() and checkpoint_path.stat().st_size > 0

    def get_model_status(self) -> Dict[str, Any]:
        """Return diagnostic status of model configuration."""
        checkpoint_path = Path(settings.MODEL_CHECKPOINT_PATH).resolve()
        is_available = checkpoint_path.is_file() and checkpoint_path.stat().st_size > 0
        return {
            "configured": is_available,
            "model_name": settings.MODEL_NAME,
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_exists": is_available,
        }

    def detect_on_image_bytes(
        self,
        image_bytes: bytes,
        filename: str,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> DetectionResponse:
        """Run object detection on an image payload through the model adapter boundary.

        Raises HTTPException(503) with documented error if model weights are missing or unconfigured.
        """
        # 1. Enforce model availability safeguard (never fabricate detections)
        if not self.is_model_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "InferenceNotConfigured",
                    "message": (
                        f"Inference cannot be executed because model checkpoint was not found at "
                        f"'{settings.MODEL_CHECKPOINT_PATH}'. Please configure MODEL_CHECKPOINT_PATH with valid weights."
                    ),
                    "model_name": settings.MODEL_NAME,
                    "target_path": settings.MODEL_CHECKPOINT_PATH,
                },
            )

        # 2. Decode image to verify geometry and dimensions
        try:
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                width, height = pil_img.size
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot decode image payload for detection: {str(exc)}",
            )

        # 3. Dynamic adapter invocation via project ModelAdapter interface
        conf = confidence_threshold or settings.DEFAULT_CONFIDENCE_THRESHOLD
        iou = iou_threshold or settings.DEFAULT_IOU_THRESHOLD

        try:
            # Dynamic import of project adapter if present on the python path
            from inference.adapters.yolo_adapter import YOLOAdapter  # type: ignore

            if self._cached_adapter is None:
                self._cached_adapter = YOLOAdapter(
                    model_path=settings.MODEL_CHECKPOINT_PATH,
                    conf=conf,
                    iou=iou,
                    imgsz=settings.DEFAULT_IMAGE_SIZE,
                )

            # Save temporary image for the adapter if file-path based
            temp_img_path = settings.evidence_storage_path / f"temp_{uuid.uuid4().hex}.jpg"
            with open(temp_img_path, "wb") as f:
                f.write(image_bytes)

            try:
                start_time = time.perf_counter()
                adapter_result = self._cached_adapter.predict(str(temp_img_path))
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                detections_list: List[Detection] = []
                for det in adapter_result.detections:
                    detections_list.append(
                        Detection(
                            class_name=det.class_name,
                            confidence=float(det.confidence),
                            bbox=list(det.bbox_xyxy),
                            frame_id=filename,
                            capture_timestamp=datetime.now(timezone.utc),
                        )
                    )
            finally:
                if temp_img_path.exists():
                    temp_img_path.unlink()

        except ImportError as err:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "InferenceRuntimeUnavailable",
                    "message": "The project ModelAdapter or its ML runtime dependencies (e.g. ultralytics) are not loaded in the backend environment.",
                    "cause": str(err),
                },
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "InferenceExecutionError",
                    "message": f"Inference execution failed: {str(exc)}",
                },
            )

        image_id = f"img_{uuid.uuid4().hex[:12]}"
        return DetectionResponse(
            image_id=image_id,
            filename=filename,
            image_width=width,
            image_height=height,
            inference_time_ms=round(elapsed_ms, 2),
            model_name=settings.MODEL_NAME,
            detections=detections_list,
            total_detections=len(detections_list),
            auto_event_ids=[],
        )


detection_service = DetectionService()
