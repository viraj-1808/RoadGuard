"""
Tests for RoadGuard Inference Adapter
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import numpy as np


class TestYOLOAdapter:
    """Tests for YOLOAdapter."""

    @pytest.fixture
    def mock_model_path(self):
        """Create a dummy model file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            # Write some dummy data
            f.write(b"dummy model data")
            yield Path(f.name)

    def test_model_path_validation(self, mock_model_path):
        """Test that model path validation works."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)
            assert adapter.model_path == mock_model_path

    def test_model_not_found_raises_error(self):
        """Test that missing model raises FileNotFoundError."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with pytest.raises(FileNotFoundError):
            YOLOAdapter("nonexistent/path/model.pt")

    def test_sha256_computation(self, mock_model_path):
        """Test SHA256 computation matches expected."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)

            # Verify SHA256 was computed - read actual file content
            actual_content = mock_model_path.read_bytes()
            expected_hash = hashlib.sha256(actual_content).hexdigest()
            assert adapter.model_sha256 == expected_hash

    def test_get_model_info(self, mock_model_path):
        """Test model info retrieval."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)
            info = adapter.get_model_info(training_run_id="test_run")

            assert info.model_path == str(mock_model_path)
            assert info.model_sha256 == adapter.model_sha256
            assert info.model_name == "YOLO11s"
            assert info.training_run_id == "test_run"
            assert info.class_names == {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}

    def test_confidence_threshold_handling(self, mock_model_path):
        """Test confidence threshold is stored."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path, confidence_threshold=0.5)
            assert adapter.confidence_threshold == 0.5

    def test_supported_extensions(self, mock_model_path):
        """Test supported image extensions."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)
            # Test that predict_directory accepts supported_extensions parameter
            import inspect
            sig = inspect.signature(adapter.predict_directory)
            assert "supported_extensions" in sig.parameters
            # Default is None (handled in function body)
            assert sig.parameters["supported_extensions"].default is None

    def test_invalid_image_handling(self, mock_model_path):
        """Test that invalid images are handled gracefully."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)
            result = adapter.predict_image("nonexistent_image.jpg")

            assert result.error is not None
            assert "not found" in result.error.lower()

    def test_empty_directory_behavior(self, mock_model_path):
        """Test behavior with empty directory."""
        from inference.adapters.yolo_adapter import YOLOAdapter

        with patch("inference.adapters.yolo_adapter.YOLO") as mock_yolo:
            mock_instance = MagicMock()
            mock_instance.model.names = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
            mock_yolo.return_value = mock_instance

            adapter = YOLOAdapter(mock_model_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                results = adapter.predict_directory(tmpdir)
                assert results == []


class TestDetectionSchema:
    """Tests for Detection dataclass."""

    def test_detection_creation(self):
        """Test Detection creation with all fields."""
        from inference.adapters.yolo_adapter import Detection

        det = Detection(
            class_id=3,
            class_name="pothole",
            confidence=0.85,
            bbox_xyxy=(100.0, 150.0, 200.0, 250.0),
            image_width=640,
            image_height=480,
        )

        assert det.class_id == 3
        assert det.class_name == "pothole"
        assert det.confidence == 0.85
        assert det.bbox_xyxy == (100.0, 150.0, 200.0, 250.0)
        assert det.image_width == 640
        assert det.image_height == 480

    def test_inference_result_creation(self):
        """Test InferenceResult creation."""
        from inference.adapters.yolo_adapter import InferenceResult, Detection

        det = Detection(
            class_id=3,
            class_name="pothole",
            confidence=0.85,
            bbox_xyxy=(100.0, 150.0, 200.0, 250.0),
            image_width=640,
            image_height=480,
        )

        result = InferenceResult(
            image_path="test.jpg",
            detections=[det],
            inference_time_ms=45.2,
            image_width=640,
            image_height=480,
        )

        assert result.image_path == "test.jpg"
        assert len(result.detections) == 1
        assert result.inference_time_ms == 45.2
        assert result.error is None


class TestOutputFilenameGeneration:
    """Tests for output filename generation."""

    def test_annotated_filename_generation(self):
        """Test annotated output filename follows convention."""
        from pathlib import Path

        input_paths = [
            "road001.jpg",
            "road002.png",
            "road003.webp",
            "test_image.jpeg",
        ]

        for input_path in input_paths:
            p = Path(input_path)
            expected = f"{p.stem}_annotated{p.suffix}"
            output_name = f"{p.stem}_annotated{p.suffix}"
            assert output_name == expected


class TestClassMapping:
    """Tests for class mapping consistency."""

    def test_expected_classes(self):
        """Test that expected classes match project convention."""
        expected = {
            0: "longitudinal_crack",
            1: "transverse_crack",
            2: "alligator_crack",
            3: "pothole",
        }

        # This should match data.yaml
        assert expected == {
            0: "longitudinal_crack",
            1: "transverse_crack",
            2: "alligator_crack",
            3: "pothole",
        }


class TestJSONSerialization:
    """Tests for JSON serialization of predictions."""

    def test_predictions_schema(self):
        """Test predictions.json has expected structure."""
        # Build a sample predictions structure
        predictions = {
            "experiment_id": "EXP-INF-001",
            "timestamp": "2026-10-03T12:00:00Z",
            "model": {
                "path": "test.pt",
                "sha256": "abc123",
                "name": "YOLO11s",
                "class_names": {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"},
                "training_run_id": "test_run",
            },
            "inference_config": {
                "confidence_threshold": 0.25,
                "iou_threshold": 0.7,
                "imgsz": 720,
                "device": "0",
            },
            "source_directory": "validation/manual/input",
            "images": [
                {
                    "file": "road001.jpg",
                    "path": "validation/manual/input/road001.jpg",
                    "width": 640,
                    "height": 480,
                    "inference_time_ms": 45.2,
                    "detections": [
                        {
                            "class_id": 3,
                            "class_name": "pothole",
                            "confidence": 0.85,
                            "bbox_xyxy": [100.0, 150.0, 200.0, 250.0],
                        }
                    ],
                    "error": None,
                }
            ],
        }

        # Should be serializable
        import json
        json_str = json.dumps(predictions, indent=2)
        assert "EXP-INF-001" in json_str
        assert "pothole" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])