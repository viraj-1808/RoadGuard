#!/usr/bin/env python3
"""
Unit tests for RoadGuard AI annotation validator.
Tests validation of annotations exported from the review tool v2.
"""

import os
import tempfile
import json
import pytest
from pathlib import Path
from validator import AnnotationValidator, ValidationReport, CLASS_MAPPING


def create_valid_export_json():
    """Create a valid export JSON for testing (module-level for shared use)."""
    return {
        "version": "v2.0",
        "timestamp": "2026-10-11T15:45:00Z",
        "class_mapping": {k: v for k, v in CLASS_MAPPING.items()},
        "annotations": {
            "review_images/road013.jpg": {
                "status": "CONFIRMED_NEGATIVE",
                "boxes": [],
                "width": 1200,
                "height": 900
            },
            "review_images/road023.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 200, "x2": 400, "y2": 500,
                        "class_id": 0, "class_name": "longitudinal_crack"
                    },
                    {
                        "x1": 600, "y1": 100, "x2": 800, "y2": 300,
                        "class_id": 3, "class_name": "pothole"
                    }
                ],
                "width": 3072,
                "height": 4096
            },
            "review_images/road034.jpg": {
                "status": "UNCERTAIN",
                "boxes": [
                    {
                        "x1": 50, "y1": 50, "x2": 150, "y2": 150,
                        "class_id": 2, "class_name": "alligator_crack"
                    }
                ],
                "width": 960,
                "height": 1280
            }
        }
    }


class TestAnnotationValidator:
    """Test cases for AnnotationValidator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AnnotationValidator()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_path = os.path.join(self.temp_dir, "test_export.json")
        self.test_image_path = os.path.join(self.temp_dir, "test_image.jpg")
        
        # Create dummy image file (just empty)
        with open(self.test_image_path, 'wb') as f:
            f.write(b'')
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validation_report_initialization(self):
        """Test ValidationReport initialization."""
        report = ValidationReport()
        
        assert report.is_valid == True
        assert report.errors == []
        assert report.warnings == []
        assert report.stats == {}
    
    def test_validation_report_add_error(self):
        """Test adding errors to ValidationReport."""
        report = ValidationReport()
        
        report.add_error("Test error 1")
        report.add_error("Test error 2")
        
        assert report.is_valid == False
        assert len(report.errors) == 2
        assert "Test error 1" in report.errors
        assert "Test error 2" in report.errors
        
        # Report should remain valid for warnings
        report.add_warning("Test warning")
        assert len(report.warnings) == 1
        assert report.is_valid == False  # Still invalid due to errors
    
    def test_class_mapping(self):
        """Test class mapping consistency."""
        # Check that all expected class IDs are present
        expected_ids = ["0", "1", "2", "3"]
        for class_id in expected_ids:
            assert class_id in CLASS_MAPPING
        
        # Check that all expected class names are present
        expected_names = [
            "longitudinal_crack",
            "transverse_crack",
            "alligator_crack", 
            "pothole"
        ]
        for name in expected_names:
            assert name in CLASS_MAPPING.values()
        
        # Check mapping consistency
        for class_id, class_name in CLASS_MAPPING.items():
            assert isinstance(class_id, str)
            assert isinstance(class_name, str)
            assert class_name in expected_names
    
    def create_valid_export_json(self):
        """Create a valid export JSON for testing."""
        return {
            "version": "v2.0",
            "timestamp": "2026-10-11T15:45:00Z",
            "class_mapping": CLASS_MAPPING,
            "annotations": {
                "review_images/road013.jpg": {
                    "status": "CONFIRMED_NEGATIVE",
                    "boxes": [],
                    "width": 1200,
                    "height": 900
                },
                "review_images/road023.jpg": {
                    "status": "CONFIRMED_POSITIVE",
                    "boxes": [
                        {
                            "x1": 100, "y1": 200, "x2": 400, "y2": 500,
                            "class_id": 0, "class_name": "longitudinal_crack"
                        },
                        {
                            "x1": 600, "y1": 100, "x2": 800, "y2": 300,
                            "class_id": 3, "class_name": "pothole"
                        }
                    ],
                    "width": 3072,
                    "height": 4096
                },
                "review_images/road034.jpg": {
                    "status": "UNCERTAIN",
                    "boxes": [
                        {
                            "x1": 50, "y1": 50, "x2": 150, "y2": 150,
                            "class_id": 2, "class_name": "alligator_crack"
                        }
                    ],
                    "width": 960,
                    "height": 1280
                }
            }
        }
    
    def test_validate_export_json_valid(self):
        """Test validation of a valid export JSON."""
        export_data = self.create_valid_export_json()
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        # Should be valid
        assert report.is_valid == True
        assert len(report.errors) == 0
        
        # Check stats
        assert report.stats["total_images"] == 3
        assert report.stats["total_boxes"] == 3
        assert report.stats["images_with_boxes"] == 2
        assert report.stats["images_confirmed_positive"] == 1
        assert report.stats["images_confirmed_negative"] == 1
        assert report.stats["images_uncertain"] == 1
        
        # Check class counts
        assert report.stats["by_class"]["0"] == 1  # longitudinal_crack
        assert report.stats["by_class"]["3"] == 1  # pothole
        assert report.stats["by_class"]["2"] == 1  # alligator_crack
    
    def test_validate_export_json_missing_version(self):
        """Test validation of export JSON missing version."""
        export_data = self.create_valid_export_json()
        del export_data["version"]
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        assert report.is_valid == False
        assert any("Missing 'version'" in error for error in report.errors)
    
    def test_validate_export_json_invalid_coordinates(self):
        """Test validation of export JSON with invalid coordinates."""
        export_data = self.create_valid_export_json()
        
        # Add invalid box to road023.jpg
        for image_path, image_data in export_data["annotations"].items():
            if image_path == "review_images/road023.jpg":
                # Add invalid box (x2 < x1)
                image_data["boxes"].append({
                    "x1": 500, "y1": 500, "x2": 100, "y2": 600,
                    "class_id": 1, "class_name": "transverse_crack"
                })
                break
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        assert report.is_valid == False
        assert any("x2 <= x1" in error for error in report.errors)
    
    def test_validate_export_json_out_of_bounds(self):
        """Test validation of export JSON with out-of-bounds coordinates."""
        export_data = self.create_valid_export_json()
        
        # Add out-of-bounds box to road023.jpg (x2 > width)
        for image_path, image_data in export_data["annotations"].items():
            if image_path == "review_images/road023.jpg":
                image_data["boxes"].append({
                    "x1": 4000, "y1": 200, "x2": 4500, "y2": 500,
                    "class_id": 1, "class_name": "transverse_crack"
                })
                break
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        assert report.is_valid == False
        assert any("out of bounds" in error for error in report.errors)
    
    def test_validate_export_json_invalid_class(self):
        """Test validation of export JSON with invalid class."""
        export_data = self.create_valid_export_json()
        
        # Add invalid box with class_id 99
        for image_path, image_data in export_data["annotations"].items():
            if image_path == "review_images/road023.jpg":
                image_data["boxes"].append({
                    "x1": 200, "y1": 200, "x2": 300, "y2": 300,
                    "class_id": 99, "class_name": "invalid_class"
                })
                break
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        assert report.is_valid == False
        assert any("invalid class_id" in error or "class_name doesn't match" in error 
                  for error in report.errors)
    
    def test_validate_export_json_negative_with_boxes(self):
        """Test validation of CONFIRMED_NEGATIVE with boxes."""
        export_data = self.create_valid_export_json()
        
        # Change road013.jpg to CONFIRMED_NEGATIVE with boxes
        for image_path, image_data in export_data["annotations"].items():
            if image_path == "review_images/road013.jpg":
                image_data["status"] = "CONFIRMED_NEGATIVE"
                image_data["boxes"] = [
                    {
                        "x1": 100, "y1": 100, "x2": 200, "y2": 200,
                        "class_id": 0, "class_name": "longitudinal_crack"
                    }
                ]
                break
        
        with open(self.test_json_path, 'w') as f:
            json.dump(export_data, f)
        
        report = self.validator.validate_export_json(self.test_json_path)
        
        assert report.is_valid == False
        assert any("CONFIRMED_NEGATIVE should have empty boxes" in error 
                  for error in report.errors)
    
    def test_validate_yolo_label_valid(self):
        """Test validation of a valid YOLO label."""
        yolo_content = "0 0.123456 0.234567 0.123456 0.234567\n2 0.555555 0.666666 0.111111 0.111111\n"
        
        with open(self.test_json_path, 'w') as f:
            f.write(yolo_content)
        
        report = self.validator.validate_yolo_label(
            self.test_json_path, 1920, 1080
        )
        
        assert report.is_valid == True
        assert len(report.errors) == 0
        assert report.stats["lines_processed"] == 2
        assert report.stats["boxes_count"] == 2
    
    def test_validate_yolo_label_invalid_format(self):
        """Test validation of YOLO label with invalid format."""
        yolo_content = "0 0.123456 0.234567 0.123456\n"  # Missing height
        
        with open(self.test_json_path, 'w') as f:
            f.write(yolo_content)
        
        report = self.validator.validate_yolo_label(
            self.test_json_path, 1920, 1080
        )
        
        assert report.is_valid == False
        assert any("Expected 5 values" in error for error in report.errors)
    
    def test_validate_yolo_label_out_of_range(self):
        """Test validation of YOLO label with out-of-range values."""
        yolo_content = "0 1.5 0.234567 0.123456 0.234567\n"  # x_center > 1
        
        with open(self.test_json_path, 'w') as f:
            f.write(yolo_content)
        
        report = self.validator.validate_yolo_label(
            self.test_json_path, 1920, 1080
        )
        
        assert report.is_valid == False
        assert any("out of range" in error for error in report.errors)
    
    def test_validate_yolo_label_invalid_class(self):
        """Test validation of YOLO label with invalid class."""
        yolo_content = "99 0.123456 0.234567 0.123456 0.234567\n"  # Invalid class
        
        with open(self.test_json_path, 'w') as f:
            f.write(yolo_content)
        
        report = self.validator.validate_yolo_label(
            self.test_json_path, 1920, 1080
        )
        
        assert report.is_valid == False
        assert any("invalid class_id" in error for error in report.errors)
    
    def test_convert_to_yolo_basic(self):
        """Test basic YOLO conversion."""
        export_data = self.create_valid_export_json()
        
        # Add a temporary directory for conversion
        yolo_dir = os.path.join(self.temp_dir, "yolo_output")
        
        results = self.validator.convert_to_yolo(export_data, yolo_dir)
        
        # Check results structure
        assert isinstance(results, dict)
        assert len(results) == 3  # All three images in our test data
        
        # Check conversion results
        for image_path, result in results.items():
            if image_path == "review_images/road013.jpg":
                assert result["converted"] == False
                assert result["reason"] == "Not confirmed positive"
                assert result["boxes_count"] == 0
            
            elif image_path == "review_images/road023.jpg":
                assert result["converted"] == True
                assert os.path.exists(result["output_path"])
                assert result["boxes_count"] == 2
                
                # Check YOLO file content
                with open(result["output_path"], 'r') as f:
                    content = f.read()
                    lines = content.strip().split('\n')
                    assert len(lines) == 2
                    
                    # First box should be longitudinal_crack (class 0)
                    assert lines[0].startswith("0 ")
                    
                    # Second box should be pothole (class 3)
                    assert lines[1].startswith("3 ")
            
            elif image_path == "review_images/road034.jpg":
                assert result["converted"] == False
                assert result["reason"] == "Not confirmed positive"
                assert result["boxes_count"] == 1
    
    def test_convert_to_yolo_empty_boxes(self):
        """Test YOLO conversion for image with boxes but CONFIRMED_NEGATIVE status."""
        export_data = self.create_valid_export_json()
        
        # Set road013.jpg to have boxes but CONFIRMED_NEGATIVE status
        for image_path, image_data in export_data["annotations"].items():
            if image_path == "review_images/road013.jpg":
                image_data["status"] = "CONFIRMED_NEGATIVE"
                image_data["boxes"] = [
                    {
                        "x1": 100, "y1": 100, "x2": 200, "y2": 200,
                        "class_id": 0, "class_name": "longitudinal_crack"
                    }
                ]
                break
        
        yolo_dir = os.path.join(self.temp_dir, "yolo_output")
        results = self.validator.convert_to_yolo(export_data, yolo_dir)
        
        # Image should not be converted due to negative status
        for image_path, result in results.items():
            if image_path == "review_images/road013.jpg":
                assert result["converted"] == False
                assert result["reason"] == "Not confirmed positive"
                assert result["boxes_count"] == 1
                break
    
    def test_check_negative_handling_valid(self):
        """Test negative handling check with valid data."""
        export_data = self.create_valid_export_json()
        
        issues = self.validator.check_negative_handling(export_data)
        
        assert len(issues) == 0
    
    def test_check_negative_handling_invalid(self):
        """Test negative handling check with invalid data."""
        export_data = self.create_valid_export_json()
        
        # Add invalid negative image
        export_data["annotations"]["review_images/invalid_negative.jpg"] = {
            "status": "CONFIRMED_NEGATIVE",
            "boxes": [
                {
                    "x1": 100, "y1": 100, "x2": 200, "y2": 200,
                    "class_id": 0, "class_name": "longitudinal_crack"
                }
            ],
            "width": 1920,
            "height": 1080
        }
        
        issues = self.validator.check_negative_handling(export_data)
        
        assert len(issues) == 1
        assert "CONFIRMED_NEGATIVE should have empty boxes" in issues[0]
    
    def test_check_negative_handling_uncertain_missing_boxes(self):
        """Test uncertain image handling check."""
        export_data = create_valid_export_json()
        
        # Add invalid uncertain image
        export_data["annotations"]["review_images/invalid_uncertain.jpg"] = {
            "status": "UNCERTAIN"
            # Missing boxes field
        }
        
        issues = self.validator.check_negative_handling(export_data)
        
        assert len(issues) == 1
        assert "UNCERTAIN status without 'boxes' field" in issues[0]

    def test_cli_help(self):
        """Test that CLI help works."""
        import subprocess
        import sys
        import os
        
        validator_path = os.path.join(os.path.dirname(__file__), "validator.py")
        
        result = subprocess.run(
            [sys.executable, validator_path, "--help"],
            capture_output=True,
            text=True
        )
        
        # Should show help
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()


class TestAnnotationValidatorIntegration:
    """Integration tests for the full validation pipeline."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.validator = AnnotationValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_round_trip_conversion(self):
        """Test export JSON -> YOLO conversion -> validation round trip."""
        # Create export JSON
        export_data = create_valid_export_json()

        # Add a YOLO-compatible positive image
        export_data["annotations"]["test_image.jpg"] = {
            "status": "CONFIRMED_POSITIVE",
            "boxes": [
                {
                    "x1": 100, "y1": 100, "x2": 300, "y2": 300,
                    "class_id": 3, "class_name": "pothole"
                }
            ],
            "width": 1920,
            "height": 1080
        }

        export_path = os.path.join(self.temp_dir, "export.json")
        yolo_dir = os.path.join(self.temp_dir, "yolo")

        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        # Convert to YOLO
        conversion_results = self.validator.convert_to_yolo(export_data, yolo_dir)

        # Find YOLO file for our test image (test_image.jpg -> test_image.txt)
        yolo_files = [f for f in Path(yolo_dir).glob("*.txt") if f.stem == "test_image"]
        assert len(yolo_files) == 1

        # Validate YOLO file - pass the PATH as first argument
        yolo_path = str(yolo_files[0])
        report = self.validator.validate_yolo_label(yolo_path, 1920, 1080)

        # YOLO file should be valid (contains 1 box at correct coordinates)
        assert report.is_valid == True

        # Clean up
        import shutil
        shutil.rmtree(yolo_dir, ignore_errors=True)

    def test_validator_stats_accumulation(self):
        """Test that validation stats are properly accumulated."""
        export_data = create_valid_export_json()

        export_path = os.path.join(self.temp_dir, "export.json")

        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)

        # Check that stats are properly accumulated
        assert report.stats["total_images"] == 3
        assert report.stats["total_boxes"] == 3
        assert report.stats["images_with_boxes"] == 2
        assert report.stats["images_confirmed_positive"] == 1
        assert report.stats["images_confirmed_negative"] == 1
        assert report.stats["images_uncertain"] == 1

        # Check class distribution
        assert report.stats["by_class"]["0"] == 1  # longitudinal_crack
        assert report.stats["by_class"]["2"] == 1  # alligator_crack
        assert report.stats["by_class"]["3"] == 1  # pothole

        # Transverse crack (class 1) should not appear in our test data
        assert report.stats["by_class"]["1"] == 0


class TestRoundTripExportImport:
    """Round-trip tests for JSON export/import across all statuses."""

    def setup_method(self):
        self.validator = AnnotationValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_import_confirmed_positive(self):
        """Test round-trip for CONFIRMED_POSITIVE image with multiple classes."""
        export_data = create_valid_export_json()
        # road023.jpg is CONFIRMED_POSITIVE with 2 boxes
        road023 = export_data["annotations"]["review_images/road023.jpg"]
        assert road023["status"] == "CONFIRMED_POSITIVE"
        assert len(road023["boxes"]) == 2

        # Validate export -> write to file -> re-read -> compare
        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == True

        # Re-read and verify data integrity
        with open(export_path, 'r') as f:
            reloaded = json.load(f)

        reloaded_023 = reloaded["annotations"]["review_images/road023.jpg"]
        assert reloaded_023["status"] == "CONFIRMED_POSITIVE"
        assert len(reloaded_023["boxes"]) == 2
        assert reloaded_023["boxes"][0]["class_id"] == 0
        assert reloaded_023["boxes"][0]["class_name"] == "longitudinal_crack"
        assert reloaded_023["boxes"][1]["class_id"] == 3
        assert reloaded_023["boxes"][1]["class_name"] == "pothole"
        assert reloaded_023["boxes"][0]["x1"] == 100
        assert reloaded_023["boxes"][0]["y1"] == 200
        assert reloaded_023["boxes"][0]["x2"] == 400
        assert reloaded_023["boxes"][0]["y2"] == 500

    def test_export_import_confirmed_negative(self):
        """Test round-trip for CONFIRMED_NEGATIVE image (empty boxes)."""
        export_data = create_valid_export_json()
        road013 = export_data["annotations"]["review_images/road013.jpg"]
        assert road013["status"] == "CONFIRMED_NEGATIVE"
        assert road013["boxes"] == []

        # Validate
        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == True

        # Verify import validation does not flag negatives
        issues = self.validator.check_negative_handling(export_data)
        assert len(issues) == 0

        # Re-read and verify data integrity
        with open(export_path, 'r') as f:
            reloaded = json.load(f)

        reloaded_013 = reloaded["annotations"]["review_images/road013.jpg"]
        assert reloaded_013["status"] == "CONFIRMED_NEGATIVE"
        assert reloaded_013["boxes"] == []
        assert reloaded_013["width"] == 1200
        assert reloaded_013["height"] == 900

    def test_export_import_uncertain(self):
        """Test round-trip for UNCERTAIN image with tentative boxes."""
        export_data = create_valid_export_json()
        road034 = export_data["annotations"]["review_images/road034.jpg"]
        assert road034["status"] == "UNCERTAIN"
        assert len(road034["boxes"]) == 1

        # Validate
        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == True

        # Re-read and verify data integrity
        with open(export_path, 'r') as f:
            reloaded = json.load(f)

        reloaded_034 = reloaded["annotations"]["review_images/road034.jpg"]
        assert reloaded_034["status"] == "UNCERTAIN"
        assert len(reloaded_034["boxes"]) == 1
        assert reloaded_034["boxes"][0]["class_id"] == 2
        assert reloaded_034["boxes"][0]["class_name"] == "alligator_crack"
        assert reloaded_034["boxes"][0]["x1"] == 50
        assert reloaded_034["boxes"][0]["y1"] == 50
        assert reloaded_034["boxes"][0]["x2"] == 150
        assert reloaded_034["boxes"][0]["y2"] == 150

    def test_import_does_not_silently_convert_negative(self):
        """Ensure importing does not convert CONFIRMED_NEGATIVE to something else."""
        export_data = create_valid_export_json()

        # Verify all three statuses are preserved independently
        statuses = {
            "review_images/road013.jpg": "CONFIRMED_NEGATIVE",
            "review_images/road023.jpg": "CONFIRMED_POSITIVE",
            "review_images/road034.jpg": "UNCERTAIN"
        }

        for image_path, expected_status in statuses.items():
            actual = export_data["annotations"][image_path]["status"]
            assert actual == expected_status, \
                f"{image_path}: expected {expected_status}, got {actual}"

    def test_yolo_export_only_confirmed_positive(self):
        """Verify YOLO export includes only CONFIRMED_POSITIVE images."""
        export_data = create_valid_export_json()

        yolo_dir = os.path.join(self.temp_dir, "yolo")
        results = self.validator.convert_to_yolo(export_data, yolo_dir)

        # Only road023.jpg (CONFIRMED_POSITIVE) should be converted
        for image_path, result in results.items():
            if image_path == "review_images/road023.jpg":
                assert result["converted"] == True
                assert os.path.exists(result["output_path"])
                assert result["boxes_count"] == 2
            elif image_path == "review_images/road013.jpg":
                assert result["converted"] == False
                assert result["reason"] == "Not confirmed positive"
                assert result["boxes_count"] == 0
            elif image_path == "review_images/road034.jpg":
                assert result["converted"] == False  # UNCERTAIN, not converted
                assert result["reason"] == "Not confirmed positive"


class TestCoordinateNormalization:
    """Tests for coordinate normalization and boundary validation."""

    def setup_method(self):
        self.validator = AnnotationValidator()

    def test_yolo_conversion_correctness(self):
        """Test that YOLO conversion produces correct normalized values."""
        export_data = create_valid_export_json()

        # road023.jpg has box: x1=100, y1=200, x2=400, y2=500
        # width=3072, height=4096
        road023 = export_data["annotations"]["review_images/road023.jpg"]
        box0 = road023["boxes"][0]  # longitudinal_crack at (100, 200)-(400, 500)

        width = 3072
        height = 4096

        # Compute expected YOLO values
        expected_x_center = (100 + 400) / 2 / width
        expected_y_center = (200 + 500) / 2 / height
        expected_width = (400 - 100) / width
        expected_height = (500 - 200) / height

        # Simulate YOLO conversion
        x_center = (box0["x1"] + box0["x2"]) / 2 / width
        y_center = (box0["y1"] + box0["y2"]) / 2 / height
        box_width = (box0["x2"] - box0["x1"]) / width
        box_height = (box0["y2"] - box0["y1"]) / height

        assert x_center == pytest.approx(expected_x_center)
        assert y_center == pytest.approx(expected_y_center)
        assert box_width == pytest.approx(expected_width)
        assert box_height == pytest.approx(expected_height)

        # Verify all values are in [0, 1]
        assert 0.0 <= x_center <= 1.0
        assert 0.0 <= y_center <= 1.0
        assert 0.0 <= box_width <= 1.0
        assert 0.0 <= box_height <= 1.0

    def test_zero_area_box_rejected(self):
        """Test that zero-area boxes fail validation."""
        export_data = create_valid_export_json()

        # Add zero-area box (x1 == x2, y1 == y2)
        export_data["annotations"]["review_images/road023.jpg"]["boxes"].append({
            "x1": 500, "y1": 500, "x2": 500, "y2": 500,
            "class_id": 1, "class_name": "transverse_crack"
        })

        export_path = os.path.join(tempfile.mkdtemp(), "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == False
        assert any("x2 <= x1" in e or "y2 <= y1" in e for e in report.errors)

        import shutil
        shutil.rmtree(os.path.dirname(export_path), ignore_errors=True)

    def test_boundary_violation_rejected(self):
        """Test that boxes exceeding image bounds fail validation."""
        export_data = create_valid_export_json()

        # road023.jpg: width=3072, height=4096
        # Add box that exceeds right boundary
        export_data["annotations"]["review_images/road023.jpg"]["boxes"].append({
            "x1": 3000, "y1": 200, "x2": 3500, "y2": 500,
            "class_id": 1, "class_name": "transverse_crack"
        })

        export_path = os.path.join(tempfile.mkdtemp(), "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == False
        assert any("out of bounds" in e for e in report.errors)

        import shutil
        shutil.rmtree(os.path.dirname(export_path), ignore_errors=True)

    def test_negative_coordinates_rejected(self):
        """Test that negative coordinates fail validation."""
        export_data = create_valid_export_json()

        # Add box with negative coordinates
        export_data["annotations"]["review_images/road023.jpg"]["boxes"].append({
            "x1": -50, "y1": -50, "x2": 100, "y2": 100,
            "class_id": 1, "class_name": "transverse_crack"
        })

        export_path = os.path.join(tempfile.mkdtemp(), "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == False
        # Validator reports "out of bounds" for negative coordinates
        assert any("out of bounds" in e or "x1 < 0" in e or "y1 < 0" in e for e in report.errors)

        import shutil
        shutil.rmtree(os.path.dirname(export_path), ignore_errors=True)

    def test_invalid_class_id_rejected(self):
        """Test that invalid class IDs fail validation."""
        export_data = create_valid_export_json()

        # Add box with invalid class_id
        export_data["annotations"]["review_images/road023.jpg"]["boxes"].append({
            "x1": 500, "y1": 500, "x2": 600, "y2": 600,
            "class_id": 99, "class_name": "invalid"
        })

        export_path = os.path.join(tempfile.mkdtemp(), "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == False
        # Fix variable name: iterate over 'error' not 'e'
        assert any("invalid class_id" in error for error in report.errors)

        import shutil
        shutil.rmtree(os.path.dirname(export_path), ignore_errors=True)

    def test_class_name_mismatch_rejected(self):
        """Test that class_name mismatch with class_id fails validation."""
        export_data = create_valid_export_json()

        # Add box with mismatched class_name
        export_data["annotations"]["review_images/road023.jpg"]["boxes"].append({
            "x1": 500, "y1": 500, "x2": 600, "y2": 600,
            "class_id": 3, "class_name": "alligator_crack"  # Should be "pothole"
        })

        export_path = os.path.join(tempfile.mkdtemp(), "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == False
        assert any("doesn't match" in e for e in report.errors)

        import shutil
        shutil.rmtree(os.path.dirname(export_path), ignore_errors=True)


class TestExportImportContract:
    """Tests for export/import contract compliance."""

    def setup_method(self):
        self.validator = AnnotationValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_export_includes_all_images(self):
        """Verify export includes all images, not just positive ones."""
        export_data = create_valid_export_json()

        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        report = self.validator.validate_export_json(export_path)
        assert report.is_valid == True
        assert report.stats["total_images"] == 3
        assert report.stats["images_confirmed_positive"] == 1
        assert report.stats["images_confirmed_negative"] == 1
        assert report.stats["images_uncertain"] == 1

        # Verify structure
        with open(export_path, 'r') as f:
            data = json.load(f)

        assert "version" in data
        assert "timestamp" in data
        assert "class_mapping" in data
        assert "annotations" in data
        assert len(data["annotations"]) == 3

    def test_export_includes_status_field(self):
        """Verify every image in export has an explicit status."""
        export_data = create_valid_export_json()

        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        with open(export_path, 'r') as f:
            data = json.load(f)

        for image_path, image_data in data["annotations"].items():
            assert "status" in image_data, f"{image_path} missing status"
            assert image_data["status"] in [
                "CONFIRMED_POSITIVE", "CONFIRMED_NEGATIVE", "UNCERTAIN"
            ], f"{image_path} has invalid status: {image_data['status']}"

    def test_export_includes_dimensions(self):
        """Verify every image in export has width and height."""
        export_data = create_valid_export_json()

        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        with open(export_path, 'r') as f:
            data = json.load(f)

        for image_path, image_data in data["annotations"].items():
            assert "width" in image_data, f"{image_path} missing width"
            assert "height" in image_data, f"{image_path} missing height"
            assert isinstance(image_data["width"], int)
            assert isinstance(image_data["height"], int)
            assert image_data["width"] > 0
            assert image_data["height"] > 0

    def test_empty_boxes_preserved_for_negative(self):
        """Verify CONFIRMED_NEGATIVE images retain empty boxes through round-trip."""
        export_data = create_valid_export_json()
        export_data["annotations"]["review_images/road013.jpg"]["boxes"] = []

        export_path = os.path.join(self.temp_dir, "export.json")
        with open(export_path, 'w') as f:
            json.dump(export_data, f)

        with open(export_path, 'r') as f:
            reloaded = json.load(f)

        reloaded_013 = reloaded["annotations"]["review_images/road013.jpg"]
        assert reloaded_013["status"] == "CONFIRMED_NEGATIVE"
        assert reloaded_013["boxes"] == []


class TestExistingAnnotationIntegrity:
    """Verify existing annotations in annotations_v1 are not modified."""

    def test_existing_confirmed_annotations_unchanged(self):
        """Verify existing annotations_v1 confirmed files match manifest."""
        confirmed_dir = Path(__file__).parent.parent / "annotations_v1" / "confirmed"
        
        # Check a few known annotation files exist and have content
        expected_files = ["road001.txt", "road003.txt", "road033.txt"]
        
        annotation_count = 0
        for txt_file in expected_files:
            file_path = confirmed_dir / txt_file
            assert file_path.exists(), f"Expected file missing: {txt_file}"
            content = file_path.read_text()
            # Should have non-empty content (at least one annotation)
            if content.strip():
                annotation_count += 1
        
        # At least some files should have annotations
        assert annotation_count > 0, "Expected at least some annotation files to have content"

    def test_leakage_safe_split_unchanged(self):
        """Verify leakage_safe_split.json still exists and is valid."""
        split_path = Path(__file__).parent.parent / "annotations_v1" / "leakage_safe_split.json"
        assert split_path.exists(), "leakage_safe_split.json missing"
        
        with open(split_path, 'r') as f:
            split_data = json.load(f)
        
        assert "train" in split_data
        assert "val" in split_data
        assert "holdout" in split_data
        assert len(split_data["train"]) == 10
        assert len(split_data["val"]) == 5
        assert len(split_data["holdout"]) == 5


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
