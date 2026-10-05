"""
RoadGuard YOLO Model Adapter

Provides a clean interface around Ultralytics YOLO for inference.
Hides framework-specific details and exposes project-owned detection contracts.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from ultralytics import YOLO


@dataclass(frozen=True)
class Detection:
    """Project-owned detection contract."""
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel coordinates
    image_width: int
    image_height: int


@dataclass(frozen=True)
class InferenceResult:
    """Result of inference on a single image."""
    image_path: str
    detections: list[Detection]
    inference_time_ms: float
    image_width: int
    image_height: int
    error: str | None = None


@dataclass(frozen=True)
class ModelInfo:
    """Model provenance information."""
    model_path: str
    model_sha256: str
    model_name: str
    class_names: dict[int, str]
    training_run_id: str | None = None


class YOLOAdapter:
    """Adapter for Ultralytics YOLO model."""

    def __init__(
        self,
        model_path: str | Path,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.7,
        imgsz: int = 720,
        device: str = "0",
    ):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.device = device

        # Verify model exists
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        # Compute SHA256
        self.model_sha256 = self._compute_sha256(self.model_path)

        # Load model
        self._model = YOLO(str(self.model_path))

        # Warm up
        self._warmup()

        # Get class names from model
        self.class_names = self._get_class_names()

    def _compute_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of model file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_class_names(self) -> dict[int, str]:
        """Extract class names from model."""
        if hasattr(self._model, "model") and hasattr(self._model.model, "names"):
            return {int(k): v for k, v in self._model.model.names.items()}
        return {}

    def _warmup(self) -> None:
        """Warm up model with a dummy inference."""
        import cv2
        dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
        try:
            self._model.predict(dummy, imgsz=self.imgsz, device=self.device, verbose=False)
        except Exception:
            pass  # Warmup failure is non-fatal

    def get_model_info(self, training_run_id: str | None = None) -> ModelInfo:
        """Get model provenance information."""
        return ModelInfo(
            model_path=str(self.model_path),
            model_sha256=self.model_sha256,
            model_name="YOLO11s",
            class_names=self.class_names,
            training_run_id=training_run_id,
        )

    def predict_image(self, image_path: str | Path) -> InferenceResult:
        """Run inference on a single image."""
        import cv2

        image_path = Path(image_path)
        start_time = time.perf_counter()

        if not image_path.exists():
            return InferenceResult(
                image_path=str(image_path),
                detections=[],
                inference_time_ms=0.0,
                image_width=0,
                image_height=0,
                error=f"File not found: {image_path}",
            )

        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return InferenceResult(
                image_path=str(image_path),
                detections=[],
                inference_time_ms=0.0,
                image_width=0,
                image_height=0,
                error=f"Failed to read image: {image_path}",
            )

        height, width = img.shape[:2]

        # Run inference
        try:
            results = self._model.predict(
                img,
                imgsz=self.imgsz,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False,
            )
        except Exception as e:
            return InferenceResult(
                image_path=str(image_path),
                detections=[],
                inference_time_ms=0.0,
                image_width=width,
                image_height=height,
                error=f"Inference failed: {e}",
            )

        inference_time_ms = (time.perf_counter() - start_time) * 1000

        # Extract detections
        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
                confs = result.boxes.conf.cpu().numpy()
                cls_ids = result.boxes.cls.cpu().numpy().astype(int)

                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    if conf >= self.confidence_threshold:
                        class_name = self.class_names.get(cls_id, f"class_{cls_id}")
                        detections.append(Detection(
                            class_id=cls_id,
                            class_name=class_name,
                            confidence=float(conf),
                            bbox_xyxy=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                            image_width=width,
                            image_height=height,
                        ))

        return InferenceResult(
            image_path=str(image_path),
            detections=detections,
            inference_time_ms=inference_time_ms,
            image_width=width,
            image_height=height,
            error=None,
        )

    def predict_directory(
        self,
        source_dir: str | Path,
        recursive: bool = True,
        supported_extensions: set[str] | None = None,
    ) -> list[InferenceResult]:
        """Run inference on all images in a directory."""
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        if supported_extensions is None:
            supported_extensions = {".jpg", ".jpeg", ".png", ".webp"}

        # Find image files
        pattern = "**/*" if recursive else "*"
        image_files = []
        for ext in supported_extensions:
            image_files.extend(source_dir.glob(pattern + ext.lower()))
            image_files.extend(source_dir.glob(pattern + ext.upper()))

        # Deduplicate and sort
        image_files = sorted(set(image_files))

        results = []
        for img_path in image_files:
            print(f"Processing: {img_path.name}")
            result = self.predict_image(img_path)
            results.append(result)

            if result.error:
                print(f"  WARNING: {result.error}")
            else:
                print(f"  Found {len(result.detections)} detections in {result.inference_time_ms:.1f}ms")

        return results


def create_annotated_image(
    image_path: str | Path,
    result: InferenceResult,
    output_path: str | Path,
    color_map: dict[int, tuple[int, int, int]] | None = None,
) -> bool:
    """Create annotated image with bounding boxes and labels."""
    import cv2

    image_path = Path(image_path)
    output_path = Path(output_path)

    if color_map is None:
        # Default colors per class (BGR for OpenCV)
        color_map = {
            0: (0, 255, 255),    # longitudinal_crack - cyan
            1: (255, 0, 255),    # transverse_crack - magenta
            2: (255, 255, 0),    # alligator_crack - yellow
            3: (0, 0, 255),      # pothole - red
        }

    if result.error:
        return False

    img = cv2.imread(str(image_path))
    if img is None:
        return False

    for det in result.detections:
        x1, y1, x2, y2 = map(int, det.bbox_xyxy)
        color = color_map.get(det.class_id, (0, 255, 0))

        # Draw bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Draw label
        label = f"{det.class_name} {det.confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1 - label_h - 5), (x1 + label_w, y1), color, -1)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imwrite(str(output_path), img)
    return True