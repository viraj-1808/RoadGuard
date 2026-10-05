"""
Adapters module for inference.
"""

from inference.adapters.yolo_adapter import YOLOAdapter, Detection, InferenceResult, ModelInfo, create_annotated_image

__all__ = [
    "YOLOAdapter",
    "Detection",
    "InferenceResult",
    "ModelInfo",
    "create_annotated_image",
]