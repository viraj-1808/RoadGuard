#!/usr/bin/env python3
"""
Independent validation of YOLO conversion for RDD2022 India Dataset.

Validates that the YOLO conversion correctly preserved all annotation data
by independently reading both the normalized XML annotations and the YOLO
output, then comparing them object-by-object.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import xml.etree.ElementTree as ET
from PIL import Image

# Configuration
BASE_DIR = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI")

# File paths
SPLIT_MANIFEST = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json")
CORRELATION_GRAPH = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json")

# Source annotation directory (normalized XML annotations, not YAML)
NORMALIZED_ANNOTATIONS_DIR = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/train/annotations")

# YOLO output directory
YOLO_DIR = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/yolo_rdd2022_india")
YOLO_IMAGES_DIR = YOLO_DIR / "images"
YOLO_LABELS_DIR = YOLO_DIR / "labels"

# Output paths
OUTPUT_JSON = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/yolo_rdd2022_india/conversion_validation.json")
OUTPUT_MD = Path("C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/yolo_rdd2022_india/conversion_validation_report.md")

# Locked class mapping (D-015)
CLASS_MAPPING = {
    "longitudinal_crack": 0,
    "transverse_crack": 1,
    "alligator_crack": 2,
    "pothole": 3,
}

ID_TO_CLASS = {v: k for k, v in CLASS_MAPPING.items()}

# Excluded classes
EXCLUDED_CLASSES = {"D43", "D44", "D50"}

# Image dimensions (should be 720x720)
EXPECTED_WIDTH = 720
EXPECTED_HEIGHT = 720

# Coordinate tolerance for geometric equivalence
COORD_TOLERANCE = 1e-5


def read_split_manifest():
    """Read and expand split manifest, including expanding CC_xxxx components."""
    with open(SPLIT_MANIFEST, 'r') as f:
        manifest = json.load(f)
    
    assignments = manifest.get("assignments", {})
    
    # Load component manifest to expand CC_xxxx entries
    with open(CORRELATION_GRAPH, 'r') as f:
        cg = json.load(f)
    
    component_manifest = cg.get("component_manifest", {})
    components = component_manifest.get("components", [])
    
    # Build mapping: CC_xxxx -> member image IDs
    members_map = {}
    for comp in components:
        comp_id = comp["component_id"]
        members_map[comp_id] = comp["members"]
    
    # Expand CC_xxxx entries into their constituent images
    expanded_assignments = {}
    for key, split in assignments.items():
        if key.startswith("CC_"):
            members = members_map.get(key, [])
            for img_stem in members:
                expanded_assignments[img_stem] = split
        elif key.startswith("India_"):
            expanded_assignments[key] = split
    
    split_counts = defaultdict(int)
    for img, split in expanded_assignments.items():
        split_counts[split] += 1
    
    return expanded_assignments, manifest, split_counts, members_map


def read_normalized_annotations():
    """Read all normalized annotation XML files."""
    annotations = {}
    
    for xml_path in NORMALIZED_ANNOTATIONS_DIR.glob("*.xml"):
        stem = xml_path.stem
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        filename_elem = root.find("filename")
        image_filename = filename_elem.text if filename_elem is not None else stem + ".jpg"
        
        size_elem = root.find("size")
        width = int(size_elem.find("width").text) if size_elem is not None else 0
        height = int(size_elem.find("height").text) if size_elem is not None else 0
        
        objects = []
        for obj in root.findall("object"):
            name_elem = obj.find("name")
            class_name = name_elem.text if name_elem is not None else ""
            
            if class_name in EXCLUDED_CLASSES:
                continue
            
            if class_name not in CLASS_MAPPING:
                continue
            
            bbox = obj.find("bndbox")
            if bbox is None:
                continue
            
            xmin = int(bbox.find("xmin").text)
            ymin = int(bbox.find("ymin").text)
            xmax = int(bbox.find("xmax").text)
            ymax = int(bbox.find("ymax").text)
            
            objects.append({
                "class_name": class_name,
                "class_id": CLASS_MAPPING[class_name],
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax
            })
        
        annotations[stem] = {
            "image_filename": image_filename,
            "width": width,
            "height": height,
            "objects": objects
        }
    
    return annotations


def read_yolo_labels():
    """Read all YOLO label files."""
    labels = {}
    
    for split_dir in YOLO_LABELS_DIR.iterdir():
        if not split_dir.is_dir() or split_dir.name not in ["train", "val", "test"]:
            continue
        
        for label_path in split_dir.glob("*.txt"):
            stem = label_path.stem
            
            objects = []
            if label_path.stat().st_size > 0:
                with open(label_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split()
                        if len(parts) != 5:
                            continue
                        
                        try:
                            class_id = int(parts[0])
                            x_center = float(parts[1])
                            y_center = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])
                        except ValueError:
                            continue
                        
                        class_name = ID_TO_CLASS.get(class_id, f"unknown_{class_id}")
                        
                        objects.append({
                            "class_id": class_id,
                            "class_name": class_name,
                            "x_center": x_center,
                            "y_center": y_center,
                            "width": width,
                            "height": height
                        })
            
            labels[stem] = {
                "split": split_dir.name,
                "objects": objects,
                "path": label_path
            }
    
    return labels


def read_yolo_images():
    """Read all YOLO image files."""
    images = {}
    
    for split_dir in YOLO_IMAGES_DIR.iterdir():
        if not split_dir.is_dir() or split_dir.name not in ["train", "val", "test"]:
            continue
        
        for image_path in split_dir.glob("*.jpg"):
            stem = image_path.stem
            
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    images[stem] = {
                        "split": split_dir.name,
                        "width": width,
                        "height": height,
                        "path": image_path
                    }
            except Exception:
                continue
    
    return images


def compute_expected_yolo_coords(voc_obj, image_width, image_height):
    """Compute expected YOLO coordinates from VOC bounding box."""
    x_center = (voc_obj["xmin"] + voc_obj["xmax"]) / 2.0 / image_width
    y_center = (voc_obj["ymin"] + voc_obj["ymax"]) / 2.0 / image_height
    width = (voc_obj["xmax"] - voc_obj["xmin"]) / image_width
    height = (voc_obj["ymax"] - voc_obj["ymin"]) / image_height
    
    return x_center, y_center, width, height


def validate_invariant_a(assignments, yolo_labels):
    """Invariant A: Every image in split_manifest_fixed.json appears exactly once"""
    errors = []
    
    for img_stem in assignments:
        if img_stem not in yolo_labels:
            errors.append(f"Image {img_stem} from split manifest is missing from YOLO output")
    
    yolo_extra = set(yolo_labels.keys()) - set(assignments.keys())
    if yolo_extra:
        errors.append(f"Images in YOLO output not in split manifest: {sorted(yolo_extra)}")
    
    return len(errors) == 0, errors


def validate_invariant_b(yolo_labels, yolo_images):
    """Invariant B: Every image has exactly one corresponding label file"""
    errors = []
    
    for img_stem, img_info in yolo_images.items():
        label_path = YOLO_LABELS_DIR / img_info["split"] / f"{img_stem}.txt"
        
        if not label_path.exists():
            errors.append(f"No label file found for image {img_stem} (expected {label_path})")
    
    for label_stem, label_info in yolo_labels.items():
        found = False
        for img_stem, img_info in yolo_images.items():
            if img_stem == label_stem:
                found = True
                break
        
        if not found:
            alt_path = YOLO_IMAGES_DIR / label_info["split"] / f"{label_stem}.jpg"
            if not alt_path.exists():
                errors.append(f"Label file {label_stem}.txt does not have corresponding image")
    
    return len(errors) == 0, errors


def validate_invariant_c(normalized_annotations, yolo_labels):
    """Invariant C: Every retained annotation object appears exactly once"""
    errors = []
    
    for img_stem in set(normalized_annotations.keys()) | set(yolo_labels.keys()):
        norm_objects = normalized_annotations.get(img_stem, {}).get("objects", [])
        norm_class_counts = defaultdict(int)
        for obj in norm_objects:
            norm_class_counts[obj["class_id"]] += 1
        
        yolo_objects = yolo_labels.get(img_stem, {}).get("objects", [])
        yolo_class_counts = defaultdict(int)
        for obj in yolo_objects:
            yolo_class_counts[obj["class_id"]] += 1
        
        all_class_ids = set(norm_class_counts.keys()) | set(yolo_class_counts.keys())
        for class_id in all_class_ids:
            norm_count = norm_class_counts.get(class_id, 0)
            yolo_count = yolo_class_counts.get(class_id, 0)
            if norm_count != yolo_count:
                class_name = ID_TO_CLASS.get(class_id, f"unknown_{class_id}")
                errors.append(f"Image {img_stem}, class {class_name}: source has {norm_count} objects, YOLO has {yolo_count} objects")
    
    return len(errors) == 0, errors


def validate_invariant_d(yolo_labels):
    """Invariant D: No excluded annotation appears"""
    errors = []
    
    for img_stem, data in yolo_labels.items():
        for obj in data["objects"]:
            if obj["class_name"] in ["D43", "D44", "D50"]:
                errors.append(f"Excluded annotation {obj['class_name']} found in image {img_stem}")
    
    return len(errors) == 0, errors


def validate_invariant_e(yolo_labels):
    """Invariant E: Class IDs are only 0,1,2,3"""
    errors = []
    
    for img_stem, data in yolo_labels.items():
        for obj in data["objects"]:
            if obj["class_id"] not in [0, 1, 2, 3]:
                errors.append(f"Invalid class ID {obj['class_id']} in image {img_stem}")
    
    return len(errors) == 0, errors


def validate_invariant_f(yolo_labels):
    """Invariant F: Every YOLO coordinate is valid"""
    errors = []
    
    for img_stem, data in yolo_labels.items():
        for obj in data["objects"]:
            x_center, y_center, width, height = obj["x_center"], obj["y_center"], obj["width"], obj["height"]
            
            if not (0 <= x_center <= 1):
                errors.append(f"Invalid x_center {x_center} in image {img_stem}")
            
            if not (0 <= y_center <= 1):
                errors.append(f"Invalid y_center {y_center} in image {img_stem}")
            
            if not (0 < width <= 1):
                errors.append(f"Invalid width {width} in image {img_stem}")
            
            if not (0 < height <= 1):
                errors.append(f"Invalid height {height} in image {img_stem}")
    
    return len(errors) == 0, errors


def validate_invariant_g(normalized_annotations, yolo_labels):
    """Invariant G: Bounding boxes remain geometrically equivalent"""
    errors = []
    
    for img_stem in set(normalized_annotations.keys()) & set(yolo_labels.keys()):
        norm_data = normalized_annotations[img_stem]
        yolo_data = yolo_labels[img_stem]
        
        norm_objects = norm_data["objects"]
        norm_width = norm_data["width"]
        norm_height = norm_data["height"]
        yolo_objects = yolo_data["objects"]
        
        for norm_obj in norm_objects:
            matches = [obj for obj in yolo_objects if obj["class_id"] == norm_obj["class_id"]]
            
            if len(matches) != 1:
                continue
            
            yolo_obj = matches[0]
            expected_xc, expected_yc, expected_w, expected_h = compute_expected_yolo_coords(
                norm_obj, norm_width, norm_height
            )
            
            actual_xc, actual_yc, actual_w, actual_h = (
                yolo_obj["x_center"], yolo_obj["y_center"],
                yolo_obj["width"], yolo_obj["height"]
            )
            
            if abs(expected_xc - actual_xc) > COORD_TOLERANCE:
                errors.append(f"X center mismatch in {img_stem}: expected {expected_xc:.6f}, got {actual_xc:.6f}")
            
            if abs(expected_yc - actual_yc) > COORD_TOLERANCE:
                errors.append(f"Y center mismatch in {img_stem}: expected {expected_yc:.6f}, got {actual_yc:.6f}")
            
            if abs(expected_w - actual_w) > COORD_TOLERANCE:
                errors.append(f"Width mismatch in {img_stem}: expected {expected_w:.6f}, got {actual_w:.6f}")
            
            if abs(expected_h - actual_h) > COORD_TOLERANCE:
                errors.append(f"Height mismatch in {img_stem}: expected {expected_h:.6f}, got {actual_h:.6f}")
    
    return len(errors) == 0, errors


def validate_invariant_h(assignments, yolo_images):
    """Invariant H: No image crosses train/val/test"""
    errors = []
    
    for img_stem, data in yolo_images.items():
        split = data["split"]
        
        if img_stem in assignments:
            assigned_split = assignments[img_stem]
            if assigned_split != split:
                errors.append(f"Image {img_stem} assigned to split '{assigned_split}' but found in YOLO split '{split}'")
        else:
            errors.append(f"Image {img_stem} found in YOLO but not in split manifest")
    
    return len(errors) == 0, errors


def validate_invariant_i(assignments, correlation_graph):
    """Invariant I: The 583 accepted correlation edges never cross splits"""
    errors = []
    
    component_manifest = correlation_graph.get("component_manifest", {})
    components = component_manifest.get("components", [])
    
    for comp in components:
        comp_id = comp["component_id"]
        members = comp["members"]
        
        if comp_id not in assignments:
            continue
        
        comp_split = assignments[comp_id]
        
        for member in members:
            if member in assignments:
                member_split = assignments[member]
                if member_split != comp_split:
                    errors.append(f"Component {comp_id} and member {member} cross splits: "
                                f"component in '{comp_split}', member in '{member_split}'")
    
    return len(errors) == 0, errors


def validate_invariant_j(yolo_images):
    """Invariant J: Image dimensions remain unchanged"""
    errors = []
    
    for img_stem, data in yolo_images.items():
        if data["width"] != EXPECTED_WIDTH or data["height"] != EXPECTED_HEIGHT:
            errors.append(f"Image {img_stem} has incorrect dimensions: {data['width']}x{data['height']} "
                        f"(expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT})")
    
    return len(errors) == 0, errors


def validate_invariant_k(yolo_labels, yolo_images):
    """Invariant K: Conversion is deterministic"""
    errors = []
    
    all_image_stems = list(yolo_images.keys())
    if len(all_image_stems) != len(set(all_image_stems)):
        seen = set()
        duplicates = set()
        for stem in all_image_stems:
            if stem in seen:
                duplicates.add(stem)
            else:
                seen.add(stem)
        errors.append(f"Duplicate image names found: {sorted(duplicates)}")
    
    all_label_stems = []
    for data in yolo_labels.values():
        all_label_stems.append(data["path"].stem)
    
    if len(all_label_stems) != len(set(all_label_stems)):
        seen = set()
        duplicates = set()
        for stem in all_label_stems:
            if stem in seen:
                duplicates.add(stem)
            else:
                seen.add(stem)
        errors.append(f"Duplicate label names found: {sorted(duplicates)}")
    
    return len(errors) == 0, errors


def validate_invariant_l(assignments, yolo_labels, split_manifest):
    """Invariant L: Expected totals"""
    errors = []
    
    expected_from_split_manifest = split_manifest.get("dataset", {}).get("class_counts", {})
    expected_total_objects = split_manifest.get("dataset", {}).get("total_objects", 0)
    expected_total_images = split_manifest.get("dataset", {}).get("total_images", 0)
    
    actual_class_counts = defaultdict(int)
    actual_split_counts = defaultdict(lambda: defaultdict(int))
    actual_total_images = len(yolo_labels)
    actual_total_objects = 0
    
    for img_stem, data in yolo_labels.items():
        split = data["split"]
        for obj in data["objects"]:
            class_name = obj["class_name"]
            actual_class_counts[class_name] += 1
            actual_split_counts[split][class_name] += 1
            actual_total_objects += 1
    
    if actual_total_images != expected_total_images:
        errors.append(f"Total images mismatch: expected {expected_total_images}, got {actual_total_images}")
    
    if actual_total_objects != expected_total_objects:
        errors.append(f"Total objects mismatch: expected {expected_total_objects}, got {actual_total_objects}")
    
    for class_name, expected_count in expected_from_split_manifest.items():
        actual_count = actual_class_counts.get(class_name, 0)
        if actual_count != expected_count:
            errors.append(f"Class count mismatch for {class_name}: expected {expected_count}, got {actual_count}")
    
    split_stats = split_manifest.get("split_statistics", {})
    for split in ["train", "val", "test"]:
        expected_count = split_stats.get(split, {}).get("image_count", 0)
        actual_count = len([img for img in yolo_labels.values() if img["split"] == split])
        if actual_count != expected_count:
            errors.append(f"Images in split {split} mismatch: expected {expected_count}, got {actual_count}")
        
        expected_objects = split_stats.get(split, {}).get("object_count", 0)
        actual_objects = sum(actual_split_counts[split].values())
        if actual_objects != expected_objects:
            errors.append(f"Objects in split {split} mismatch: expected {expected_objects}, got {actual_objects}")
    
    return len(errors) == 0, errors


def main():
    """Main validation function."""
    print("Starting YOLO conversion validation...")
    
    print("Reading split manifest...")
    assignments, split_manifest, split_counts, members_map = read_split_manifest()
    
    print("Reading normalized annotations...")
    normalized_annotations = read_normalized_annotations()
    
    print("Reading YOLO labels...")
    yolo_labels = read_yolo_labels()
    
    print("Reading YOLO images...")
    yolo_images = read_yolo_images()
    
    print("\nRunning validation checks...")
    
    checks = [
        ("A", "Every image in split_manifest_fixed.json appears exactly once",
         validate_invariant_a, [assignments, yolo_labels]),
        ("B", "Every image has exactly one corresponding label file",
         validate_invariant_b, [yolo_labels, yolo_images]),
        ("C", "Every retained annotation object appears exactly once",
         validate_invariant_c, [normalized_annotations, yolo_labels]),
        ("D", "No excluded annotation appears",
         validate_invariant_d, [yolo_labels]),
        ("E", "Class IDs are only 0,1,2,3",
         validate_invariant_e, [yolo_labels]),
        ("F", "Every YOLO coordinate is valid",
         validate_invariant_f, [yolo_labels]),
        ("G", "Bounding boxes remain geometrically equivalent",
         validate_invariant_g, [normalized_annotations, yolo_labels]),
        ("H", "No image crosses train/val/test",
         validate_invariant_h, [assignments, yolo_images]),
        ("I", "The 583 accepted correlation edges never cross splits",
         validate_invariant_i, [assignments, split_manifest]),
        ("J", "Image dimensions remain unchanged",
         validate_invariant_j, [yolo_images]),
        ("K", "Conversion is deterministic",
         validate_invariant_k, [yolo_labels, yolo_images]),
        ("L", "Expected totals",
         validate_invariant_l, [assignments, yolo_labels, split_manifest]),
    ]
    
    all_passed = True
    check_results = []
    
    for check_id, description, check_func, check_args in checks:
        passed, errors = check_func(*check_args)
        check_results.append({
            "check_id": check_id,
            "description": description,
            "passed": passed,
            "errors": errors
        })
        
        if not passed:
            all_passed = False
    
    # Calculate class counts correctly
    actual_class_counts = {}
    for class_name in CLASS_MAPPING.keys():
        actual_class_counts[class_name] = len([obj for data in yolo_labels.values() for obj in data["objects"]
                                             if obj["class_name"] == class_name])
    
    validation_report = {
        "validation_version": "1.0.0",
        "source_annotation_dir": str(NORMALIZED_ANNOTATIONS_DIR),
        "yolo_output_dir": str(YOLO_DIR),
        "total_images": len(yolo_images),
        "total_yolo_labels": len(yolo_labels),
        "total_normalized_annotations": len(normalized_annotations),
        "split_statistics": {
            "train": split_counts.get("train", 0),
            "val": split_counts.get("val", 0),
            "test": split_counts.get("test", 0)
        },
        "class_counts": actual_class_counts,
        "checks": check_results,
        "overall_status": "PASS" if all_passed else "FAIL"
    }
    
    OUTPUT_JSON.write_text(json.dumps(validation_report, indent=2, ensure_ascii=False))
    print(f"Validation report written to {OUTPUT_JSON}")
    
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("# YOLO Conversion Validation Report\n\n")
        
        if all_passed:
            f.write("## Overall Status: PASS\n\n")
        else:
            f.write("## Overall Status: FAIL\n\n")
        
        f.write("## Check Results\n\n")
        
        for result in check_results:
            status = "PASS" if result["passed"] else "FAIL"
            f.write(f"### {status} Check {result['check_id']}: {result['description']}\n\n")
            
            if not result["passed"]:
                f.write("Errors:\n")
                for error in result["errors"]:
                    f.write(f"- {error}\n")
                f.write("\n")
        
        f.write("## Summary Statistics\n\n")
        f.write(f"- Total images processed: {validation_report['total_images']}\n")
        f.write(f"- Total YOLO labels: {validation_report['total_yolo_labels']}\n")
        f.write(f"- Total normalized annotations: {validation_report['total_normalized_annotations']}\n\n")
        
        f.write("## Split Statistics\n\n")
        for split, count in validation_report["split_statistics"].items():
            f.write(f"- {split}: {count} images\n")
        f.write("\n")
        
        f.write("## Class Counts\n\n")
        for class_name, count in validation_report["class_counts"].items():
            f.write(f"- {class_name}: {count}\n")
    
    print(f"Validation report written to {OUTPUT_MD}")
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for result in check_results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] Check {result['check_id']}: {result['description']}")
        if not result["passed"]:
            print(f"  Errors ({len(result['errors'])}):")
            for error in result["errors"][:3]:
                print(f"    - {error}")
            if len(result["errors"]) > 3:
                print(f"    ... and {len(result['errors']) - 3} more")
    
    print("\n" + "="*60)
    print(f"OVERALL STATUS: {validation_report['overall_status']}")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)