#!/usr/bin/env python3
"""
YOLO Conversion Script for RDD2022 India Dataset

Converts normalized Pascal VOC XML annotations to YOLO format,
respecting the stratified train/val/test split from split_manifest_fixed.json.

Locked class mapping (D-015):
    0 = longitudinal_crack
    1 = transverse_crack
    2 = alligator_crack
    3 = pothole

Image format: JPEG, 720x720 (standardized)
Truncated objects: RETAIN (per project decision)
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import hashlib
import shutil

# Configuration
SPLIT_MANIFEST = Path("experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json")
COMPONENT_MANIFEST = Path("experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json")
ANNOTATIONS_DIR = Path("experiments/dataset/normalized_rdd2022_india/train/annotations")
IMAGES_DIR = Path("experiments/dataset/normalized_rdd2022_india/train/images")
OUTPUT_DIR = Path("experiments/dataset/yolo_rdd2022_india")

# Locked class mapping (D-015)
CLASS_TO_ID = {
    "longitudinal_crack": 0,
    "transverse_crack": 1,
    "alligator_crack": 2,
    "pothole": 3,
}

ID_TO_CLASS = {v: k for k, v in CLASS_TO_ID.items()}

IMAGE_WIDTH = 720
IMAGE_HEIGHT = 720
COORD_PRECISION = 6

# Expected totals from validation_report.json
EXPECTED_CLASS_COUNTS = {
    "longitudinal_crack": 498,
    "transverse_crack": 30,
    "alligator_crack": 645,
    "pothole": 3187,
}
EXPECTED_TOTAL_OBJECTS = 4360
EXPECTED_TOTAL_IMAGES = 1530


def load_component_manifest():
    """Load component definitions from correlation_graph.json.
    
    Returns a dict mapping CC_xxxx component IDs to their member image IDs.
    """
    if not COMPONENT_MANIFEST.exists():
        print(f"WARNING: Component manifest not found at {COMPONENT_MANIFEST}")
        return {}
    
    with open(COMPONENT_MANIFEST) as f:
        cg = json.load(f)
    
    component_manifest = cg.get("component_manifest", {})
    components = component_manifest.get("components", [])
    
    # Build mapping: CC_xxxx -> member image IDs
    members_map = {}
    for comp in components:
        comp_id = comp["component_id"]
        members_map[comp_id] = comp["members"]
    
    print(f"Loaded {len(members_map)} component definitions from correlation_graph.json")
    return members_map


def load_split_manifest():
    """Load and parse the split manifest."""
    with open(SPLIT_MANIFEST) as f:
        manifest = json.load(f)
    assignments = manifest.get("assignments", {})
    print(f"Loaded {len(assignments)} image assignments from split manifest")
    
    # Also load component definitions
    members_map = load_component_manifest()
    
    # Expand CC_xxxx entries into their constituent images
    expanded_assignments = {}
    cc_to_split = {}  # Map CC_xxxx -> split assignment
    
    for key, split in assignments.items():
        if key.startswith("CC_"):
            # Store the split assignment for this component
            cc_to_split[key] = split
            # Expand to member images
            members = members_map.get(key, [])
            for img_stem in members:
                expanded_assignments[img_stem] = split
        elif key.startswith("India_"):
            # Individual image assignment
            expanded_assignments[key] = split
        else:
            print(f"WARNING: Unknown assignment key format: {key}")
    
    # Also add singleton images that might be in the component members but not in assignments
    # (These should already be covered, but let's be thorough)
    all_expanded = set(expanded_assignments.keys())
    print(f"Total expanded assignments: {len(all_expanded)} (CC expanded: {len(cc_to_split)})")
    
    # Check for any India_XXXXXX images that might be missing from assignments
    # but present in the component manifest members
    missing_images = []
    seen_stems = set()
    for key in assignments:
        if key.startswith("India_"):
            seen_stems.add(key)
    
    for comp_id, members in members_map.items():
        for img_stem in members:
            if img_stem not in seen_stems and img_stem not in all_expanded:
                missing_images.append(img_stem)
    
    if missing_images:
        print(f"WARNING: {len(missing_images)} images found in components but not in assignments")
        # Add them as singletons - but we need to figure out their split
        # For now, just warn
    
    return expanded_assignments, manifest, cc_to_split, members_map


def parse_voc_xml(xml_path):
    """Parse Pascal VOC XML and return list of objects with class and bbox."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Verify image size
    size_elem = root.find("size")
    if size_elem is not None:
        w = int(size_elem.find("width").text)
        h = int(size_elem.find("height").text)
        if w != IMAGE_WIDTH or h != IMAGE_HEIGHT:
            print(f"  WARNING: {xml_path.name} has size {w}x{h}, expected {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
    
    objects = []
    for obj in root.findall("object"):
        name = obj.find("name").text
        if name not in CLASS_TO_ID:
            print(f"  WARNING: Unknown class '{name}' in {xml_path.name}, skipping")
            continue
        
        class_id = CLASS_TO_ID[name]
        
        # Get bounding box
        bbox = obj.find("bndbox")
        xmin = int(bbox.find("xmin").text)
        ymin = int(bbox.find("ymin").text)
        xmax = int(bbox.find("xmax").text)
        ymax = int(bbox.find("ymax").text)
        
        # Get truncated flag
        truncated_elem = obj.find("truncated")
        truncated = int(truncated_elem.text) if truncated_elem is not None else 0
        
        # Get difficult flag
        difficult_elem = obj.find("difficult")
        difficult = int(difficult_elem.text) if difficult_elem is not None else 0
        
        objects.append({
            "class_id": class_id,
            "class_name": name,
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax,
            "truncated": truncated,
            "difficult": difficult,
        })
    
    return objects


def voc_to_yolo_bbox(xmin, ymin, xmax, ymax):
    """Convert VOC bbox to YOLO normalized format."""
    x_center = (xmin + xmax) / 2.0 / IMAGE_WIDTH
    y_center = (ymin + ymax) / 2.0 / IMAGE_HEIGHT
    width = (xmax - xmin) / IMAGE_WIDTH
    height = (ymax - ymin) / IMAGE_HEIGHT
    
    # Validate
    if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 < width <= 1 and 0 < height <= 1):
        raise ValueError(f"Invalid YOLO coordinates: x_center={x_center}, y_center={y_center}, width={width}, height={height}")
    
    return x_center, y_center, width, height


def main():
    print("=" * 60)
    print("YOLO Conversion for RDD2022 India Dataset")
    print("=" * 60)
    
    # Load split assignments with component expansion
    assignments, manifest, cc_to_split, members_map = load_split_manifest()
    
    # Verify manifest version
    print(f"Split version: {manifest.get('split_version', 'unknown')}")
    print(f"Total images in manifest: {manifest.get('dataset', {}).get('total_images', 'unknown')}")
    print(f"Total objects in manifest: {manifest.get('dataset', {}).get('total_objects', 'unknown')}")
    
    # Verify expected total images
    if len(assignments) != EXPECTED_TOTAL_IMAGES:
        print(f"ERROR: Expected {EXPECTED_TOTAL_IMAGES} image assignments, got {len(assignments)}")
    
    # Create output directories
    for split in ["train", "val", "test"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)
    
    # Statistics
    stats = {
        "total_images": 0,
        "total_objects": 0,
        "by_split": defaultdict(lambda: defaultdict(int)),
        "by_class": defaultdict(int),
        "empty_labels": 0,
        "errors": [],
        "warnings": [],
        "truncated_objects": 0,
        "images_with_truncated": set(),
    }
    
    # Process each assigned image
    for img_filename, split in assignments.items():
        # Extract image stem (without extension)
        img_stem = Path(img_filename).stem
        
        # Find annotation file
        xml_path = ANNOTATIONS_DIR / f"{img_stem}.xml"
        if not xml_path.exists():
            stats["errors"].append(f"Missing annotation: {xml_path}")
            continue
        
        # Find image file
        img_path = IMAGES_DIR / f"{img_stem}.jpg"
        if not img_path.exists():
            # Try other extensions
            found = False
            for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
                test_path = IMAGES_DIR / f"{img_stem}{ext}"
                if test_path.exists():
                    img_path = test_path
                    found = True
                    break
            if not found:
                stats["errors"].append(f"Missing image: {img_stem}")
                continue
        
        # Parse annotation
        try:
            objects = parse_voc_xml(xml_path)
        except Exception as e:
            stats["errors"].append(f"Failed to parse {xml_path.name}: {e}")
            continue
        
        # Copy image to output directory
        dst_img_dir = OUTPUT_DIR / "images" / split
        dst_img_path = dst_img_dir / img_path.name
        shutil.copy2(img_path, dst_img_path)
        
        # Create YOLO label file
        label_lines = []
        for obj in objects:
            x_center, y_center, width, height = voc_to_yolo_bbox(
                obj["xmin"], obj["ymin"], obj["xmax"], obj["ymax"]
            )
            
            # Format with 6 decimal places
            line = f"{obj['class_id']} {x_center:.{COORD_PRECISION}f} {y_center:.{COORD_PRECISION}f} {width:.{COORD_PRECISION}f} {height:.{COORD_PRECISION}f}"
            label_lines.append(line)
            
            # Update statistics
            stats["by_split"][split][obj["class_name"]] += 1
            stats["by_class"][obj["class_name"]] += 1
            stats["total_objects"] += 1
            
            if obj["truncated"] == 1:
                stats["truncated_objects"] += 1
                stats["images_with_truncated"].add(img_stem)
        
        # Write label file (even if empty)
        dst_label_dir = OUTPUT_DIR / "labels" / split
        dst_label_path = dst_label_dir / f"{img_stem}.txt"
        with open(dst_label_path, "w") as f:
            if label_lines:
                f.write("\n".join(label_lines) + "\n")
            else:
                # Empty label file for images with no retained objects
                pass
                stats["empty_labels"] += 1
        
        stats["total_images"] += 1
    
    # Create data.yaml
    data_yaml = {
        "path": str(OUTPUT_DIR),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": 4,
        "names": ["longitudinal_crack", "transverse_crack", "alligator_crack", "pothole"],
    }
    
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        import yaml
        yaml.dump(data_yaml, f, default_flow_style=False)
    
    # Create conversion_manifest.json
    conversion_manifest = {
        "conversion_version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": {
            "dataset": "RDD2022_CRDDC_India",
            "normalized_path": str(ANNOTATIONS_DIR.parent),
            "split_manifest": str(SPLIT_MANIFEST),
            "split_version": manifest.get("split_version"),
        },
        "class_mapping": {
            "0": "longitudinal_crack",
            "1": "transverse_crack",
            "2": "alligator_crack",
            "3": "pothole",
        },
        "statistics": {
            "total_images": stats["total_images"],
            "total_objects": stats["total_objects"],
            "empty_labels": stats["empty_labels"],
            "truncated_objects": stats["truncated_objects"],
            "images_with_truncated": len(stats["images_with_truncated"]),
            "by_split": {split: dict(counts) for split, counts in stats["by_split"].items()},
            "by_class": dict(stats["by_class"]),
        },
        "verification": {
            "expected_class_counts": EXPECTED_CLASS_COUNTS,
            "expected_total_objects": EXPECTED_TOTAL_OBJECTS,
            "expected_total_images": EXPECTED_TOTAL_IMAGES,
        },
        "invariant_checks": {
            "all_images_assigned": stats["total_images"] == EXPECTED_TOTAL_IMAGES,
            "all_objects_converted": stats["total_objects"] == EXPECTED_TOTAL_OBJECTS,
            "class_counts_match": dict(stats["by_class"]) == EXPECTED_CLASS_COUNTS,
            "no_errors": len(stats["errors"]) == 0,
        },
    }
    
    with open(OUTPUT_DIR / "conversion_manifest.json", "w") as f:
        json.dump(conversion_manifest, f, indent=2)
    
    # Create conversion_report.md
    report = [
        "# YOLO Conversion Report",
        "",
        f"**Conversion version**: 1.0.0",
        f"**Timestamp**: {datetime.utcnow().isoformat()}Z",
        f"**Split manifest**: {SPLIT_MANIFEST} (v{manifest.get('split_version', 'unknown')})",
        "",
        "## Class Mapping (D-015 Locked)",
        "",
        "| Class ID | Class Name | Source |",
        "|----------|------------|--------|",
        "| 0 | longitudinal_crack | D00 + D01 (merged) |",
        "| 1 | transverse_crack | D10 + D11 (merged) |",
        "| 2 | alligator_crack | D20 |",
        "| 3 | pothole | D40 |",
        "",
        "## Conversion Statistics",
        "",
        f"- Total images converted: {stats['total_images']} / {EXPECTED_TOTAL_IMAGES} expected",
        f"- Total objects converted: {stats['total_objects']} / {EXPECTED_TOTAL_OBJECTS} expected",
        f"- Empty label files: {stats['empty_labels']}",
        f"- Truncated objects retained: {stats['truncated_objects']}",
        f"- Images with truncated objects: {len(stats['images_with_truncated'])}",
        "",
        "### Objects per Class",
        "",
        "| Class | Converted | Expected | Match |",
        "|-------|-----------|----------|-------|",
    ]
    
    for cls_name, expected in EXPECTED_CLASS_COUNTS.items():
        converted = stats["by_class"].get(cls_name, 0)
        match = "✓" if converted == expected else "✗"
        report.append(f"| {cls_name} | {converted} | {expected} | {match} |")
    
    report.extend([
        "",
        "### Objects per Split",
        "",
        "| Split | longitudinal_crack | transverse_crack | alligator_crack | pothole | Total |",
        "|-------|--------------------|------------------|-----------------|---------|-------|",
    ])
    
    for split in ["train", "val", "test"]:
        counts = stats["by_split"][split]
        total = sum(counts.values())
        report.append(f"| {split} | {counts.get('longitudinal_crack', 0)} | {counts.get('transverse_crack', 0)} | {counts.get('alligator_crack', 0)} | {counts.get('pothole', 0)} | {total} |")
    
    report.extend([
        "",
        "## Invariant Checks",
        "",
        f"- All images assigned: {'PASS' if conversion_manifest['invariant_checks']['all_images_assigned'] else 'FAIL'} ({stats['total_images']} == {EXPECTED_TOTAL_IMAGES})",
        f"- All objects converted: {'PASS' if conversion_manifest['invariant_checks']['all_objects_converted'] else 'FAIL'} ({stats['total_objects']} == {EXPECTED_TOTAL_OBJECTS})",
        f"- Class counts match: {'PASS' if conversion_manifest['invariant_checks']['class_counts_match'] else 'FAIL'}",
        f"- No errors: {'PASS' if conversion_manifest['invariant_checks']['no_errors'] else 'FAIL'}",
        "",
    ])
    
    if stats["errors"]:
        report.append("## Errors")
        report.append("")
        for err in stats["errors"]:
            report.append(f"- {err}")
        report.append("")
    
    if stats["warnings"]:
        report.append("## Warnings")
        report.append("")
        for warn in stats["warnings"]:
            report.append(f"- {warn}")
        report.append("")
    
    report.append("## Output Structure")
    report.append("")
    report.append("```")
    report.append("experiments/dataset/yolo_rdd2022_india/")
    report.append("├── images/")
    report.append("│   ├── train/")
    report.append("│   ├── val/")
    report.append("│   └── test/")
    report.append("├── labels/")
    report.append("│   ├── train/")
    report.append("│   ├── val/")
    report.append("│   └── test/")
    report.append("├── data.yaml")
    report.append("├── conversion_manifest.json")
    report.append("└── conversion_report.md")
    report.append("```")
    
    with open(OUTPUT_DIR / "conversion_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    # Print summary
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    for line in report[5:30]:
        print(line)
    
    print("\nInvariant Checks:")
    for check, passed in conversion_manifest["invariant_checks"].items():
        print(f"  {check}: {'PASS' if passed else 'FAIL'}")
    
    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for e in stats["errors"]:
            print(f"  - {e}")
    
    return conversion_manifest, stats


if __name__ == "__main__":
    manifest, stats = main()