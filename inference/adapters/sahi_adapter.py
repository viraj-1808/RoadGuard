"""
RoadGuard SAHI Tiled Inference Adapter

Provides sliced/tiled inference using SAHI (Slicing Aided Hyper Inference) for
large images where standard letterbox resize loses defect detail.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction
from ultralytics import YOLO


@dataclass(frozen=True)
class Detection:
    """Project-owned detection contract."""
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
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
    tile_count: int = 1
    error: str | None = None


@dataclass(frozen=True)
class ModelInfo:
    """Model provenance information."""
    model_path: str
    model_sha256: str
    model_name: str
    class_names: dict[int, str]
    training_run_id: str | None = None


class SAHIAdapter:
    """Adapter for SAHI tiled inference with Ultralytics YOLO model."""

    def __init__(
        self,
        model_path: str | Path,
        confidence_threshold: float = 0.05,
        iou_threshold: float = 0.7,
        slice_height: int = 640,
        slice_width: int = 640,
        overlap_height_ratio: float = 0.2,
        overlap_width_ratio: float = 0.2,
        device: str = "0",
        postprocess_type: str = "NMS",
        postprocess_match_metric: str = "IOU",
        postprocess_match_threshold: float = 0.5,
        postprocess_class_agnostic: bool = False,
    ):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.slice_height = slice_height
        self.slice_width = slice_width
        self.overlap_height_ratio = overlap_height_ratio
        self.overlap_width_ratio = overlap_width_ratio
        self.device = device
        self.postprocess_type = postprocess_type
        self.postprocess_match_metric = postprocess_match_metric
        self.postprocess_match_threshold = postprocess_match_threshold
        self.postprocess_class_agnostic = postprocess_class_agnostic

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        self.model_sha256 = self._compute_sha256(self.model_path)

        self._model = YOLO(str(self.model_path))

        self._detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov11",
            model_path=str(self.model_path),
            confidence_threshold=confidence_threshold,
            device=device,
            category_mapping=self._get_category_mapping(),
        )

        self.class_names = self._get_class_names()

    def _compute_sha256(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _get_class_names(self) -> dict[int, str]:
        if hasattr(self._model, "model") and hasattr(self._model.model, "names"):
            return {int(k): v for k, v in self._model.model.names.items()}
        return {}

    def _get_category_mapping(self) -> dict[str, str]:
        """Get category mapping for SAHI (requires string keys)."""
        if hasattr(self._model, "model") and hasattr(self._model.model, "names"):
            return {str(k): v for k, v in self._model.model.names.items()}
        return {}

    def get_model_info(self, training_run_id: str | None = None) -> ModelInfo:
        return ModelInfo(
            model_path=str(self.model_path),
            model_sha256=self.model_sha256,
            model_name="YOLO11s-SAHI",
            class_names=self.class_names,
            training_run_id=training_run_id,
        )

    def predict_image(self, image_path: str | Path) -> InferenceResult:
        """Run SAHI tiled inference on a single image."""
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

        try:
            result = get_sliced_prediction(
                img,
                self._detection_model,
                slice_height=self.slice_height,
                slice_width=self.slice_width,
                overlap_height_ratio=self.overlap_height_ratio,
                overlap_width_ratio=self.overlap_width_ratio,
                postprocess_type=self.postprocess_type,
                postprocess_match_metric=self.postprocess_match_metric,
                postprocess_match_threshold=self.postprocess_match_threshold,
                postprocess_class_agnostic=self.postprocess_class_agnostic,
                verbose=0,
            )

            detections = []
            object_predictions = result.object_prediction_list

            for pred in object_predictions:
                bbox = pred.bbox.to_xyxy()
                conf = pred.score.value
                cls_id = pred.category.id
                class_name = pred.category.name

                if conf >= self.confidence_threshold:
                    detections.append(Detection(
                        class_id=cls_id,
                        class_name=class_name,
                        confidence=float(conf),
                        bbox_xyxy=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                        image_width=width,
                        image_height=height,
                    ))

            tile_count = len(result.object_prediction_list) if hasattr(result, 'object_prediction_list') else 0

        except Exception as e:
            return InferenceResult(
                image_path=str(image_path),
                detections=[],
                inference_time_ms=0.0,
                image_width=width,
                image_height=height,
                error=f"SAHI inference failed: {e}",
            )

        inference_time_ms = (time.perf_counter() - start_time) * 1000

        return InferenceResult(
            image_path=str(image_path),
            detections=detections,
            inference_time_ms=inference_time_ms,
            image_width=width,
            image_height=height,
            tile_count=tile_count,
            error=None,
        )

    def predict_directory(
        self,
        source_dir: str | Path,
        recursive: bool = True,
        supported_extensions: set[str] | None = None,
    ) -> list[InferenceResult]:
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        if supported_extensions is None:
            supported_extensions = {".jpg", ".jpeg", ".png", ".webp"}

        pattern = "**/*" if recursive else "*"
        image_files = []
        for ext in supported_extensions:
            image_files.extend(source_dir.glob(pattern + ext.lower()))
            image_files.extend(source_dir.glob(pattern + ext.upper()))

        image_files = sorted(set(image_files))

        results = []
        for img_path in image_files:
            print(f"Processing: {img_path.name}")
            result = self.predict_image(img_path)
            results.append(result)

            if result.error:
                print(f"  WARNING: {result.error}")
            else:
                print(f"  Found {len(result.detections)} detections in {result.inference_time_ms:.1f}ms ({result.tile_count} tiles)")

        return results


def create_annotated_image(
    image_path: str | Path,
    result: InferenceResult,
    output_path: str | Path,
    color_map: dict[int, tuple[int, int, int]] | None = None,
) -> bool:
    """Create annotated image with bounding boxes and labels."""
    image_path = Path(image_path)
    output_path = Path(output_path)

    if color_map is None:
        color_map = {
            0: (0, 255, 255),
            1: (255, 0, 255),
            2: (255, 255, 0),
            3: (0, 0, 255),
        }

    if result.error:
        return False

    img = cv2.imread(str(image_path))
    if img is None:
        return False

    for det in result.detections:
        x1, y1, x2, y2 = map(int, det.bbox_xyxy)
        color = color_map.get(det.class_id, (0, 255, 0))

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        label = f"{det.class_name} {det.confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1 - label_h - 5), (x1 + label_w, y1), color, -1)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imwrite(str(output_path), img)
    return True