#!/usr/bin/env python3
"""
Annotation validator for RoadGuard AI.

Validates annotations exported from the improved review tool v2.
Implements:
- Export JSON validation
- YOLO label validation
- Coordinate normalization checks
- Class mapping validation
- Negative image handling verification
"""

import json
import os
import sys
import argparse
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from pathlib import Path


# Class mapping from manifest.json
CLASS_MAPPING = {
    "0": "longitudinal_crack",
    "1": "transverse_crack", 
    "2": "alligator_crack",
    "3": "pothole"
}


@dataclass
class ValidationReport:
    """Report for validation results."""
    is_valid: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.stats is None:
            self.stats = {}
    
    def add_error(self, message: str):
        """Add an error to the report."""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning to the report."""
        self.warnings.append(message)
    
    def print_report(self):
        """Print the validation report to stdout."""
        print("=== ANNOTATION VALIDATION REPORT ===\n")
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        if self.stats:
            print("📊 STATISTICS:")
            for key, value in self.stats.items():
                print(f"  {key}: {value}")
            print()
        
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        print(f"FINAL STATUS: {status}")
        return self.is_valid


class AnnotationValidator:
    """Validator for RoadGuard AI annotations."""
    
    # Class mapping from manifest.json
    CLASS_MAPPING = CLASS_MAPPING
    
    def __init__(self):
        self.stats = {
            "total_images": 0,
            "total_boxes": 0,
            "by_class": {},
            "by_status": {},
            "images_with_boxes": 0,
            "images_confirmed_negative": 0,
            "images_uncertain": 0,
            "images_confirmed_positive": 0,
            "invalid_boxes": 0,
            "boundary_violations": 0,
            "empty_negative_files": 0
        }
        for class_id in self.CLASS_MAPPING.keys():
            self.stats["by_class"][class_id] = 0
        for status in ["CONFIRMED_POSITIVE", "CONFIRMED_NEGATIVE", "UNCERTAIN", "NEEDS_HUMAN_REVIEW"]:
            self.stats["by_status"][status] = 0
    
    def validate_export_json(self, export_path: str) -> ValidationReport:
        """Validate an export JSON from the review tool v2.
        
        Args:
            export_path: Path to export JSON file
            
        Returns:
            ValidationReport with results
        """
        report = ValidationReport()
        
        try:
            with open(export_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            report.add_error(f"Failed to load export JSON: {e}")
            return report
        
        # Validate required structure
        if "version" not in data:
            report.add_error("Missing 'version' field in export JSON")
        elif not data["version"].startswith("v2.0"):
            report.add_warning(f"Export version '{data['version']}' is not v2.0")
        
        if "class_mapping" not in data:
            report.add_error("Missing 'class_mapping' field")
        
        if "annotations" not in data:
            report.add_error("Missing 'annotations' field")
            return report
        
        annotations = data["annotations"]
        
        # Initialize image paths from export (for stats)
        self.stats["total_images"] = len(annotations)
        
        # Validate each image
        for image_path, image_data in annotations.items():
            self._validate_image_annotation(image_path, image_data, report)
        
        # Finalize stats
        report.stats = self.stats
        
        return report
    
    def _validate_image_annotation(self, image_path: str, image_data: Dict, report: ValidationReport):
        """Validate annotation for a single image."""
        # Validate required fields
        if "status" not in image_data:
            report.add_error(f"{image_path}: Missing 'status' field")
            return
        
        if "boxes" not in image_data:
            report.add_error(f"{image_path}: Missing 'boxes' field")
            return
        
        if "width" not in image_data or "height" not in image_data:
            report.add_error(f"{image_path}: Missing width/height")
            return
        
        status = image_data["status"]
        boxes = image_data["boxes"]
        width = image_data["width"]
        height = image_data["height"]
        
        # Update status stats
        if status in self.stats["by_status"]:
            self.stats["by_status"][status] += 1
        else:
            report.add_error(f"{image_path}: Invalid status '{status}'")
        
        # Update negative/positive stats
        if status == "CONFIRMED_NEGATIVE":
            self.stats["images_confirmed_negative"] += 1
            if boxes:
                self.stats["empty_negative_files"] += 1
                report.add_error(f"{image_path}: CONFIRMED_NEGATIVE should have empty boxes, got {len(boxes)}")
        elif status == "CONFIRMED_POSITIVE":
            self.stats["images_confirmed_positive"] += 1
        elif status == "UNCERTAIN":
            self.stats["images_uncertain"] += 1
        
        # Validate boxes
        for i, box in enumerate(boxes):
            self._validate_box(box, image_path, i, report, width, height)
        
        # Update overall stats
        if boxes:
            self.stats["images_with_boxes"] += 1
            self.stats["total_boxes"] += len(boxes)
    
    def _validate_box(self, box: Dict, image_path: str, box_index: int, report: ValidationReport, 
                     width: int, height: int):
        """Validate a single bounding box."""
        # Validate required fields
        required_fields = ["x1", "y1", "x2", "y2", "class_id", "class_name"]
        for field in required_fields:
            if field not in box:
                report.add_error(f"{image_path}: Box {box_index} missing '{field}'")
                return
        
        x1 = box["x1"]
        y1 = box["y1"] 
        x2 = box["x2"]
        y2 = box["y2"]
        class_id = box["class_id"]
        class_name = box["class_name"]
        
        # Validate coordinates
        if not isinstance(x1, (int, float)) or not isinstance(y1, (int, float)):
            report.add_error(f"{image_path}: Box {box_index} x1/y1 not numeric")
            return
        
        if not isinstance(x2, (int, float)) or not isinstance(y2, (int, float)):
            report.add_error(f"{image_path}: Box {image_path}: Box {box_index} x2/y2 not numeric")
            return
        
        # Validate box dimensions
        if x2 <= x1:
            report.add_error(f"{image_path}: Box {box_index} has x2 <= x1 ({x1} > {x2})")
            self.stats["invalid_boxes"] += 1
        
        if y2 <= y1:
            report.add_error(f"{image_path}: Box {box_index} has y2 <= y1 ({y1} > {y2})")
            self.stats["invalid_boxes"] += 1
        
        width_px = x2 - x1
        height_px = y2 - y1
        
        if width_px <= 0 or height_px <= 0:
            report.add_error(f"{image_path}: Box {box_index} has zero or negative dimensions ({width_px}x{height_px})")
        
        # Validate bounds
        if x1 < 0 or x2 > width:
            report.add_error(f"{image_path}: Box {box_index} x coordinates out of bounds [0, {width}] ({x1}, {x2})")
            self.stats["boundary_violations"] += 1
        
        if y1 < 0 or y2 > height:
            report.add_error(f"{image_path}: Box {box_index} y coordinates out of bounds [0, {height}] ({y1}, {y2})")
            self.stats["boundary_violations"] += 1
        
        # Validate class
        if not isinstance(class_id, int) and not (isinstance(class_id, str) and class_id.isdigit()):
            report.add_error(f"{image_path}: Box {box_index} class_id not integer: {class_id}")
        else:
            class_id_str = str(class_id)
            if class_id_str not in self.CLASS_MAPPING:
                report.add_error(f"{image_path}: Box {box_index} invalid class_id: {class_id}")
            elif self.CLASS_MAPPING[class_id_str] != class_name:
                report.add_error(f"{image_path}: Box {box_index} class_name '{class_name}' doesn't match class_id {class_id} (expected: {self.CLASS_MAPPING[class_id_str]})")
            else:
                self.stats["by_class"][class_id_str] += 1
    
    def validate_yolo_label(self, label_path: str, image_width: int, image_height: int) -> ValidationReport:
        """Validate a single YOLO label file.
        
        Args:
            label_path: Path to YOLO .txt file
            image_width: Width of corresponding image
            image_height: Height of corresponding image
            
        Returns:
            ValidationReport with results
        """
        report = ValidationReport()
        
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            report.add_error(f"Failed to read YOLO label: {e}")
            return report
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) != 5:
                report.add_error(f"{label_path}:{line_num} - Expected 5 values, got {len(parts)}")
                continue
            
            class_id, x_center, y_center, width_norm, height_norm = parts
            
            # Validate class
            if not class_id.isdigit():
                report.add_error(f"{label_path}:{line_num} - class_id not integer: {class_id}")
            elif int(class_id) not in [0, 1, 2, 3]:
                report.add_error(f"{label_path}:{line_num} - invalid class_id: {class_id}")
            
            # Validate normalized coordinates
            try:
                x_center = float(x_center)
                y_center = float(y_center)
                width_norm = float(width_norm)
                height_norm = float(height_norm)
            except ValueError:
                report.add_error(f"{label_path}:{line_num} - coordinates not numeric")
                continue
            
            # Validate range
            if not (0.0 <= x_center <= 1.0):
                report.add_error(f"{label_path}:{line_num} - x_center out of range [0,1]: {x_center}")
            
            if not (0.0 <= y_center <= 1.0):
                report.add_error(f"{label_path}:{line_num} - y_center out of range [0,1]: {y_center}")
            
            if not (0.0 <= width_norm <= 1.0):
                report.add_error(f"{label_path}:{line_num} - width out of range [0,1]: {width_norm}")
            
            if not (0.0 <= height_norm <= 1.0):
                report.add_error(f"{label_path}:{line_num} - height out of range [0,1]: {height_norm}")
            
            # Validate area (width*height should be > 0 for valid box)
            if width_norm * height_norm <= 0:
                report.add_error(f"{label_path}:{line_num} - invalid box area: {width_norm * height_norm}")
        
        # Update stats
        report.stats = {
            "lines_processed": len(lines),
            "image_width": image_width,
            "image_height": image_height,
            "boxes_count": sum(1 for line in lines if line.strip())
        }
        
        return report
    
    def convert_to_yolo(self, export_json: Dict, output_dir: str) -> Dict:
        """Convert export JSON to YOLO format.
        
        Args:
            export_json: Export JSON dictionary
            output_dir: Directory to save YOLO .txt files
            
        Returns:
            Dictionary with per-image validation results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for image_path, image_data in export_json["annotations"].items():
            if image_data["status"] != "CONFIRMED_POSITIVE":
                # Skip non-positive images
                results[image_path] = {
                    "converted": False,
                    "reason": "Not confirmed positive",
                    "boxes_count": len(image_data.get("boxes", []))
                }
                continue
            
            # Extract image dimensions
            filename = Path(image_path).name
            # Replace .jpg with .txt for YOLO format
            if filename.endswith('.jpg'):
                yolo_filename = filename.replace('.jpg', '.txt')
            elif filename.endswith('.webp'):
                yolo_filename = filename.replace('.webp', '.txt')
            else:
                yolo_filename = filename + '.txt'
            
            output_path = os.path.join(output_dir, yolo_filename)
            
            try:
                with open(output_path, 'w') as f:
                    for box in image_data.get("boxes", []):
                        # Convert to YOLO format
                        width = image_data["width"]
                        height = image_data["height"]
                        
                        x_center = ((box["x1"] + box["x2"]) / 2) / width
                        y_center = ((box["y1"] + box["y2"]) / 2) / height
                        box_width = (box["x2"] - box["x1"]) / width
                        box_height = (box["y2"] - box["y1"]) / height
                        
                        # Write YOLO line
                        f.write(f"{box['class_id']} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n")
                
                results[image_path] = {
                    "converted": True,
                    "output_path": output_path,
                    "boxes_count": len(image_data.get("boxes", [])),
                    "file_size": os.path.getsize(output_path)
                }
                
            except Exception as e:
                results[image_path] = {
                    "converted": False,
                    "reason": str(e),
                    "boxes_count": len(image_data.get("boxes", []))
                }
        
        return results
    
    def check_negative_handling(self, export_json: Dict) -> List[str]:
        """Check that confirmed negative images are handled correctly.
        
        Args:
            export_json: Export JSON dictionary
            
        Returns:
            List of issues found
        """
        issues = []
        
        for image_path, image_data in export_json["annotations"].items():
            if image_data["status"] == "CONFIRMED_NEGATIVE":
                boxes = image_data.get("boxes", [])
                if boxes:
                    issues.append(
                        f"{image_path}: CONFIRMED_NEGATIVE should have empty boxes, got {len(boxes)}: "
                        f"[{', '.join([f'({b['x1']},{b['y1']},{b['x2']},{b['y2']})' for b in boxes])}]"
                    )
            
            elif image_data["status"] == "UNCERTAIN":
                # Ensure uncertain status is explicit and not silently converted
                if image_data.get("boxes") is None:
                    issues.append(f"{image_path}: UNCERTAIN status without 'boxes' field")
        
        return issues


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate RoadGuard AI annotations")
    parser.add_argument("export_path", help="Path to export JSON file")
    parser.add_argument("--yolo-output-dir", help="Directory to save YOLO labels")
    parser.add_argument("--yolo-validate", action="store_true", help="Validate existing YOLO labels")
    parser.add_argument("--yolo-image-width", type=int, default=1920, help="Image width for YOLO validation")
    parser.add_argument("--yolo-image-height", type=int, default=1080, help="Image height for YOLO validation")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    validator = AnnotationValidator()
    
    if args.yolo_validate:
        # Validate YOLO label
        report = validator.validate_yolo_label(
            args.export_path, args.yolo_image_width, args.yolo_image_height
        )
        
        print(f"Validating YOLO label: {args.export_path}")
        report.print_report()
        sys.exit(0 if report.is_valid else 1)
    
    # Validate export JSON
    try:
        with open(args.export_path, 'r') as f:
            export_data = json.load(f)
    except Exception as e:
        print(f"Error loading export file: {e}")
        sys.exit(1)
    
    print(f"Validating export JSON: {args.export_path}")
    
    # Validate export JSON
    report = validator.validate_export_json(args.export_path)
    
    # Check negative handling
    negative_issues = validator.check_negative_handling(export_data)
    if negative_issues:
        report.errors.extend(negative_issues)
        report.is_valid = False
    
    # Convert to YOLO if requested
    yolo_results = {}
    if args.yolo_output_dir:
        print(f"Converting to YOLO format in: {args.yolo_output_dir}")
        yolo_results = validator.convert_to_yolo(export_data, args.yolo_output_dir)
    
    # Print validation report
    is_valid = report.print_report()
    
    # Print YOLO conversion results
    if args.yolo_output_dir and yolo_results:
        print("\n=== YOLO CONVERSION RESULTS ===")
        for image_path, result in yolo_results.items():
            status = "✅" if result["converted"] else "❌"
            print(f"{status} {image_path}: {result['boxes_count']} boxes -> {result.get('output_path', 'N/A')}")
    
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
