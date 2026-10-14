#!/usr/bin/env python3
"""
Test script to verify the YOLO export contract for RoadGuard AI review tool v2.

This script validates that:
1. CONFIRMED_POSITIVE images → YOLO .txt files generated with correct normalized coordinates
2. CONFIRMED_NEGATIVE images → NOT exported to YOLO
3. UNCERTAIN images → NOT exported to YOLO
4. Coordinate normalization is correct for specified test case
5. Edge cases (zero-area boxes, boundary violations, invalid class IDs) are handled
6. Missing images (no metadata entry) are handled appropriately
7. CONFIRMED_POSITIVE with no boxes produces empty label files
"""

import os
import tempfile
import json
import sys
from pathlib import Path

# Add the current directory to path so we can import validator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validator import AnnotationValidator, ValidationReport, CLASS_MAPPING


def create_test_export_json():
    """Create test export JSON with various test cases."""
    return {
        "version": "v2.0",
        "timestamp": "2026-10-11T15:45:00Z",
        "class_mapping": CLASS_MAPPING,
        "annotations": {
            # CONFIRMED_POSITIVE with boxes - should be exported
            "review_images/positive_with_boxes.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 200, "x2": 400, "y2": 500,
                        "class_id": 0, "class_name": "longitudinal_crack"
                    }
                ],
                "width": 3072,
                "height": 4096
            },
            # CONFIRMED_POSITIVE with no boxes - should produce empty file
            "review_images/positive_no_boxes.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [],
                "width": 1920,
                "height": 1080
            },
            # CONFIRMED_NEGATIVE with boxes - should NOT be exported
            "review_images/negative_with_boxes.jpg": {
                "status": "CONFIRMED_NEGATIVE",
                "boxes": [
                    {
                        "x1": 50, "y1": 50, "x2": 150, "y2": 150,
                        "class_id": 1, "class_name": "transverse_crack"
                    }
                ],
                "width": 1200,
                "height": 900
            },
            # CONFIRMED_NEGATIVE with no boxes - should NOT be exported
            "review_images/negative_no_boxes.jpg": {
                "status": "CONFIRMED_NEGATIVE",
                "boxes": [],
                "width": 1200,
                "height": 900
            },
            # UNCERTAIN with boxes - should NOT be exported
            "review_images/uncertain_with_boxes.jpg": {
                "status": "UNCERTAIN",
                "boxes": [
                    {
                        "x1": 200, "y1": 300, "x2": 400, "y2": 400,
                        "class_id": 2, "class_name": "alligator_crack"
                    }
                ],
                "width": 960,
                "height": 1280
            },
            # UNCERTAIN with no boxes - should NOT be exported
            "review_images/uncertain_no_boxes.jpg": {
                "status": "UNCERTAIN",
                "boxes": [],
                "width": 800,
                "height": 600
            },
            # Test case for coordinate normalization verification
            "review_images/coordinate_test.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 200, "x2": 400, "y2": 500,
                        "class_id": 3, "class_name": "pothole"
                    }
                ],
                "width": 3072,
                "height": 4096
            }
        }
    }


def test_confirmed_positive_exported():
    """Test that CONFIRMED_POSITIVE images are exported to YOLO."""
    export_data = create_test_export_json()
    validator = AnnotationValidator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        # Check CONFIRMED_POSITIVE with boxes
        pos_with_boxes_result = results["review_images/positive_with_boxes.jpg"]
        assert pos_with_boxes_result["converted"] == True, \
            "CONFIRMED_POSITIVE with boxes should be exported"
        assert os.path.exists(pos_with_boxes_result["output_path"]), \
            "YOLO file should exist for CONFIRMED_POSITIVE with boxes"
        assert pos_with_boxes_result["boxes_count"] == 1, \
            "Should have 1 box"
        
        # Check CONFIRMED_POSITIVE with no boxes
        pos_no_boxes_result = results["review_images/positive_no_boxes.jpg"]
        assert pos_no_boxes_result["converted"] == True, \
            "CONFIRMED_POSITIVE with no boxes should be exported (empty file)"
        assert os.path.exists(pos_no_boxes_result["output_path"]), \
            "YOLO file should exist for CONFIRMED_POSITIVE with no boxes"
        assert pos_no_boxes_result["boxes_count"] == 0, \
            "Should have 0 boxes"
        
        # Verify the file is actually empty
        with open(pos_no_boxes_result["output_path"], 'r') as f:
            content = f.read().strip()
            assert content == "", \
                "YOLO file for CONFIRMED_POSITIVE with no boxes should be empty"


def test_confirmed_negative_not_exported():
    """Test that CONFIRMED_NEGATIVE images are NOT exported to YOLO."""
    export_data = create_test_export_json()
    validator = AnnotationValidator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        # Check CONFIRMED_NEGATIVE with boxes
        neg_with_boxes_result = results["review_images/negative_with_boxes.jpg"]
        assert neg_with_boxes_result["converted"] == False, \
            "CONFIRMED_NEGATIVE with boxes should NOT be exported"
        assert neg_with_boxes_result["reason"] == "Not confirmed positive", \
            "Reason should indicate not confirmed positive"
        assert neg_with_boxes_result["boxes_count"] == 1, \
            "Should still report box count"
        
        # Check CONFIRMED_NEGATIVE with no boxes
        neg_no_boxes_result = results["review_images/negative_no_boxes.jpg"]
        assert neg_no_boxes_result["converted"] == False, \
            "CONFIRMED_NEGATIVE with no boxes should NOT be exported"
        assert neg_no_boxes_result["reason"] == "Not confirmed positive", \
            "Reason should indicate not confirmed positive"
        assert neg_no_boxes_result["boxes_count"] == 0, \
            "Should report 0 boxes"


def test_uncertain_not_exported():
    """Test that UNCERTAIN images are NOT exported to YOLO."""
    export_data = create_test_export_json()
    validator = AnnotationValidator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        # Check UNCERTAIN with boxes
        unc_with_boxes_result = results["review_images/uncertain_with_boxes.jpg"]
        assert unc_with_boxes_result["converted"] == False, \
            "UNCERTAIN with boxes should NOT be exported"
        assert unc_with_boxes_result["reason"] == "Not confirmed positive", \
            "Reason should indicate not confirmed positive"
        assert unc_with_boxes_result["boxes_count"] == 1, \
            "Should still report box count"
        
        # Check UNCERTAIN with no boxes
        unc_no_boxes_result = results["review_images/uncertain_no_boxes.jpg"]
        assert unc_no_boxes_result["converted"] == False, \
            "UNCERTAIN with no boxes should NOT be exported"
        assert unc_no_boxes_result["reason"] == "Not confirmed positive", \
            "Reason should indicate not confirmed positive"
        assert unc_no_boxes_result["boxes_count"] == 0, \
            "Should report 0 boxes"


def test_coordinate_normalization():
    """Test coordinate normalization for specific test case."""
    export_data = create_test_export_json()
    validator = AnnotationValidator()
    
    # Extract the test case
    test_image = "review_images/coordinate_test.jpg"
    image_data = export_data["annotations"][test_image]
    box = image_data["boxes"][0]  # x1=100, y1=200, x2=400, y2=500
    width = image_data["width"]   # 3072
    height = image_data["height"] # 4096
    
    # Expected YOLO values (normalized)
    expected_x_center = (box["x1"] + box["x2"]) / 2 / width
    expected_y_center = (box["y1"] + box["y2"]) / 2 / height
    expected_width = (box["x2"] - box["x1"]) / width
    expected_height = (box["y2"] - box["y1"]) / height
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        result = results[test_image]
        assert result["converted"] == True, "Should be converted"
        
        # Read the YOLO file and verify values
        with open(result["output_path"], 'r') as f:
            line = f.read().strip()
            parts = line.split()
            
            # Format: class_id x_center y_center width height
            assert len(parts) == 5, f"Expected 5 parts, got {len(parts)}: {line}"
            
            class_id, x_center, y_center, w_norm, h_norm = parts
            x_center = float(x_center)
            y_center = float(y_center)
            w_norm = float(w_norm)
            h_norm = float(h_norm)
            
            # Check class ID
            assert int(class_id) == box["class_id"], \
                f"Class ID mismatch: expected {box['class_id']}, got {class_id}"
            
            # Check normalized coordinates (with small tolerance for floating point)
            tolerance = 1e-6
            assert abs(x_center - expected_x_center) < tolerance, \
                f"x_center mismatch: expected {expected_x_center}, got {x_center}"
            assert abs(y_center - expected_y_center) < tolerance, \
                f"y_center mismatch: expected {expected_y_center}, got {y_center}"
            assert abs(w_norm - expected_width) < tolerance, \
                f"width mismatch: expected {expected_width}, got {w_norm}"
            assert abs(h_norm - expected_height) < tolerance, \
                f"height mismatch: expected {expected_height}, got {h_norm}"


def test_edge_cases():
    """Test edge cases: zero-area boxes, boundary violations, invalid class IDs."""
    export_data = {
        "version": "v2.0",
        "timestamp": "2026-10-11T15:45:00Z",
        "class_mapping": CLASS_MAPPING,
        "annotations": {
            # Zero-area box (x1 == x2 or y1 == y2)
            "review_images/zero_area_box.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 100, "x2": 100, "y2": 200,  # Zero width
                        "class_id": 0, "class_name": "longitudinal_crack"
                    }
                ],
                "width": 640,
                "height": 480
            },
            # Boundary violation (x2 > width)
            "review_images/boundary_violation.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 600, "y1": 100, "x2": 700, "y2": 200,  # x2 > 640
                        "class_id": 1, "class_name": "transverse_crack"
                    }
                ],
                "width": 640,
                "height": 480
            },
            # Invalid class ID
            "review_images/invalid_class.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 100, "x2": 200, "y2": 200,
                        "class_id": 99, "class_name": "invalid_class"  # Not in mapping
                    }
                ],
                "width": 640,
                "height": 480
            }
        }
    }
    
    validator = AnnotationValidator()
    
    # Test validation catches these issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(export_data, f)
        temp_json_path = f.name
    
    try:
        report = validator.validate_export_json(temp_json_path)
        
        # Should be invalid due to edge cases
        assert report.is_valid == False, "Should detect validation errors"
        
        error_messages = ' '.join(report.errors)
        
        # Check for zero-area box detection
        assert "zero or negative dimensions" in error_messages or \
               "x2 <= x1" in error_messages or "y2 <= y1" in error_messages, \
               "Should detect zero-area box"
        
        # Check for boundary violation detection
        assert "out of bounds" in error_messages, \
               "Should detect boundary violation"
        
        # Check for invalid class ID detection
        assert "invalid class_id" in error_messages or \
               "class_name doesn't match" in error_messages, \
               "Should detect invalid class ID"
               
    finally:
        os.unlink(temp_json_path)


def test_missing_images():
    """Test handling of missing images (no metadata entry)."""
    # This test verifies that if an image file exists but has no metadata entry,
    # it's simply not processed (not an error condition in the export logic)
    export_data = {
        "version": "v2.0",
        "timestamp": "2026-10-11T15:45:00Z",
        "class_mapping": CLASS_MAPPING,
        "annotations": {
            # Only one image in metadata
            "review_images/existing_image.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [
                    {
                        "x1": 100, "y1": 100, "x2": 200, "y2": 200,
                        "class_id": 0, "class_name": "longitudinal_crack"
                    }
                ],
                "width": 640,
                "height": 480
            }
            # Note: "missing_image.jpg" is not in metadata - this should be ignored
        }
    }
    
    validator = AnnotationValidator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        # Only the image in metadata should be processed
        assert len(results) == 1, "Should only process images in metadata"
        assert "review_images/existing_image.jpg" in results, \
            "Should process the image that exists in metadata"
        assert "review_images/missing_image.jpg" not in results, \
            "Should not process images not in metadata"


def test_empty_label_files():
    """Test that CONFIRMED_POSITIVE with no boxes produces empty label files."""
    export_data = {
        "version": "v2.0",
        "timestamp": "2026-10-11T15:45:00Z",
        "class_mapping": CLASS_MAPPING,
        "annotations": {
            "review_images/empty_labels.jpg": {
                "status": "CONFIRMED_POSITIVE",
                "boxes": [],  # No boxes
                "width": 1280,
                "height": 720
            }
        }
    }
    
    validator = AnnotationValidator()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yolo_dir = os.path.join(temp_dir, "yolo_output")
        results = validator.convert_to_yolo(export_data, yolo_dir)
        
        result = results["review_images/empty_labels.jpg"]
        assert result["converted"] == True, "Should be exported"
        assert result["boxes_count"] == 0, "Should have 0 boxes"
        assert os.path.exists(result["output_path"]), "YOLO file should exist"
        
        # File should be empty
        with open(result["output_path"], 'r') as f:
            content = f.read()
            assert content.strip() == "", "YOLO file should be empty"


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        ("CONFIRMED_POSITIVE exported", test_confirmed_positive_exported),
        ("CONFIRMED_NEGATIVE not exported", test_confirmed_negative_not_exported),
        ("UNCERTAIN not exported", test_uncertain_not_exported),
        ("Coordinate normalization", test_coordinate_normalization),
        ("Edge cases", test_edge_cases),
        ("Missing images", test_missing_images),
        ("Empty label files", test_empty_label_files)
    ]
    
    passed = 0
    failed = 0
    
    print("Running YOLO export contract tests...")
    print("=" * 50)

    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}", end=" ")
            test_func()
            print("PASSED")
            passed += 1
        except Exception as e:
            print(f"FAILED - {str(e)}")
            failed += 1

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("All tests passed!")
        return True
    else:
        print("Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)