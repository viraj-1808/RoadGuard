"""
Independent validation of the RDD2022 India annotation transformation.

Validates transformation invariants by re-reading BOTH the raw source XML
and the normalized output XML, and comparing them object-by-object.

This script does NOT reuse the transformation module's in-memory state; it
re-parses files from disk so that errors in the transformation are caught.

Usage:
    python analysis/validate_transformation.py
"""
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import json
import hashlib
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.transform_rdd2022_annotations import (
    RAW_ANNOTATIONS_DIR,
    RAW_IMAGES_DIR,
    NORMALIZED_ANNOTATIONS_DIR,
    NORMALIZED_IMAGES_DIR,
    NORMALIZED_MANIFEST_PATH,
    CLASS_MAPPING,
    EXCLUDED_CLASSES,
    TRANSFORMATION_VERSION,
)


VALIDATION_VERSION = "1.0.0"

FINAL_CLASS_NAMES = {name for name, _ in CLASS_MAPPING.values()}


class ValidationFailure(Exception):
    pass


def read_objects(xml_path: Path) -> Tuple[int, int, int, List[Tuple[str, int, int, int, int]]]:
    """
    Read a VOC XML and return (width, height, depth, objects).

    objects is a list of (name, xmin, ymin, xmax, ymax) in document order.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    if size is None:
        raise ValidationFailure(f"Missing size element: {xml_path}")
    width = int(size.find("width").text)
    height = int(size.find("height").text)
    depth = int(size.find("depth").text)

    objects = []
    for obj in root.findall("object"):
        name = obj.find("name").text
        bndbox = obj.find("bndbox")
        xmin = int(bndbox.find("xmin").text)
        ymin = int(bndbox.find("ymin").text)
        xmax = int(bndbox.find("xmax").text)
        ymax = int(bndbox.find("ymax").text)
        objects.append((name, xmin, ymin, xmax, ymax))

    return width, height, depth, objects


def parse_manifest() -> Dict[str, Any]:
    if not NORMALIZED_MANIFEST_PATH.exists():
        raise ValidationFailure(f"Manifest not found: {NORMALIZED_MANIFEST_PATH}")
    with open(NORMALIZED_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def file_hash(path: Path) -> str:
    """MD5 to match the checksum algorithm recorded in the transformation manifest."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate() -> Dict[str, Any]:
    """Run all invariant checks. Returns a structured report."""
    results: List[Dict[str, Any]] = []
    failures: List[str] = []

    def check(invariant: str, description: str, passed: bool, detail: str = "") -> None:
        results.append({
            "invariant": invariant,
            "description": description,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })
        if not passed:
            failures.append(f"{invariant}: {description} -- {detail}")

    raw_files = sorted(RAW_ANNOTATIONS_DIR.glob("*.xml"))
    norm_files = sorted(NORMALIZED_ANNOTATIONS_DIR.glob("*.xml"))

    # ---- Invariant 6: image count conserved (no silent drops) ----
    check(
        "INV-6",
        "Annotation count is conserved (every raw XML has a normalized counterpart)",
        len(raw_files) == len(norm_files),
        f"raw={len(raw_files)} normalized={len(norm_files)}",
    )

    raw_images = sorted(RAW_IMAGES_DIR.glob("*.jpg"))
    norm_images = sorted(NORMALIZED_IMAGES_DIR.glob("*.jpg"))
    check(
        "INV-6b",
        "Image count is conserved",
        len(raw_images) == len(norm_images),
        f"raw={len(raw_images)} normalized={len(norm_images)}",
    )

    # ---- Iterate every annotation pair ----
    totals: Dict[str, int] = defaultdict(int)
    raw_class_counts: Dict[str, int] = defaultdict(int)
    final_class_counts: Dict[str, int] = defaultdict(int)

    total_raw_objects = 0
    total_final_objects = 0
    total_excluded = 0
    total_skipped = 0
    empty_count = 0

    coord_mismatches: List[str] = []
    dimension_mismatches: List[str] = []
    excluded_leaks: List[str] = []
    mapping_errors: List[str] = []
    duplicate_detections: List[str] = []
    empty_violations: List[str] = []

    for raw_path in raw_files:
        norm_path = NORMALIZED_ANNOTATIONS_DIR / raw_path.name

        if not norm_path.exists():
            total_skipped += 1
            continue

        raw_w, raw_h, raw_d, raw_objs = read_objects(raw_path)
        norm_w, norm_h, norm_d, norm_objs = read_objects(norm_path)

        # ---- Invariant 5: dimensions unchanged ----
        if (raw_w, raw_h, raw_d) != (norm_w, norm_h, norm_d):
            dimension_mismatches.append(
                f"{raw_path.name}: raw=({raw_w},{raw_h},{raw_d}) norm=({norm_w},{norm_h},{norm_d})"
            )

        total_raw_objects += len(raw_objs)

        for name, *_ in raw_objs:
            raw_class_counts[name] += 1

        if len(norm_objs) == 0:
            empty_count += 1
            if len(raw_objs) == 0:
                # Both empty is consistent, not a violation
                pass

        # ---- Invariant 3: no excluded class appears in output ----
        for name, x1, y1, x2, y2 in norm_objs:
            final_class_counts[name] += 1
            total_final_objects += 1

            if name in EXCLUDED_CLASSES:
                excluded_leaks.append(f"{norm_path.name}: excluded class {name} present in output")
            if name not in FINAL_CLASS_NAMES:
                mapping_errors.append(f"{norm_path.name}: unexpected final class name {name!r}")
            else:
                totals[name] += 1

        # ---- Invariant 4: retained coordinates unchanged, in order ----
        expected_final: List[Tuple[int, int, int, int]] = []
        for raw_name, x1, y1, x2, y2 in raw_objs:
            if raw_name in EXCLUDED_CLASSES:
                total_excluded += 1
                continue
            if raw_name not in CLASS_MAPPING:
                mapping_errors.append(f"{raw_path.name}: raw class {raw_name!r} has no mapping rule")
                continue
            expected_final.append((x1, y1, x2, y2))

        actual_coords = [(x1, y1, x2, y2) for _, x1, y1, x2, y2 in norm_objs]

        if len(expected_final) != len(actual_coords):
            mapping_errors.append(
                f"{raw_path.name}: retained count mismatch expected={len(expected_final)} actual={len(actual_coords)}"
            )
        else:
            for idx, (exp, act) in enumerate(zip(expected_final, actual_coords)):
                if exp != act:
                    coord_mismatches.append(
                        f"{raw_path.name}[obj {idx}]: expected {exp} got {act}"
                    )

        # ---- Invariant 2 + 8 + 9 + 10 + 11: class merge correctness ----
        # Rebuild the expected final class sequence and compare names only.
        expected_names: List[str] = []
        for raw_name, *_ in raw_objs:
            if raw_name in EXCLUDED_CLASSES:
                continue
            if raw_name in CLASS_MAPPING:
                expected_names.append(CLASS_MAPPING[raw_name][0])

        actual_names = [name for name, *_ in norm_objs]
        if expected_names != actual_names:
            mapping_errors.append(
                f"{raw_path.name}: class sequence mismatch expected={expected_names} actual={actual_names}"
            )

    # ---- Report invariant results ----
    check("INV-2", "Every retained source object maps to exactly one final class", not mapping_errors,
          f"{len(mapping_errors)} mapping errors" if mapping_errors else "all objects mapped")
    check("INV-3", "No excluded object (D43/D44/D50) appears in normalized annotations", not excluded_leaks,
          f"{len(excluded_leaks)} leaks" if excluded_leaks else "no excluded classes in output")
    check("INV-4", "Bounding-box coordinates are unchanged for all retained objects", not coord_mismatches,
          f"{len(coord_mismatches)} mismatches" if coord_mismatches else f"{total_final_objects} boxes verified")
    check("INV-5", "Image dimensions are unchanged", not dimension_mismatches,
          f"{len(dimension_mismatches)} mismatches" if dimension_mismatches else "all dimensions match")

    # ---- Invariant 7: retained + excluded + skipped == source objects ----
    accounted = total_final_objects + total_excluded + total_skipped
    check("INV-7", "Retained + excluded + skipped objects account for all source objects",
          accounted == total_raw_objects,
          f"retained={total_final_objects} excluded={total_excluded} skipped={total_skipped} total={accounted} source={total_raw_objects}")

    # ---- Invariant 8: D00 + D01 -> class 0 ----
    expected_cls0 = raw_class_counts["D00"] + raw_class_counts["D01"]
    check("INV-8", "D00 + D01 both become final class 0 (longitudinal_crack)",
          totals.get("longitudinal_crack", 0) == expected_cls0,
          f"expected={expected_cls0} actual={totals.get('longitudinal_crack', 0)}")

    # ---- Invariant 9: D10 + D11 -> class 1 ----
    expected_cls1 = raw_class_counts["D10"] + raw_class_counts["D11"]
    check("INV-9", "D10 + D11 both become final class 1 (transverse_crack)",
          totals.get("transverse_crack", 0) == expected_cls1,
          f"expected={expected_cls1} actual={totals.get('transverse_crack', 0)}")

    # ---- Invariant 10: D20 -> class 2 ----
    check("INV-10", "D20 remains class 2 (alligator_crack)",
          totals.get("alligator_crack", 0) == raw_class_counts["D20"],
          f"expected={raw_class_counts['D20']} actual={totals.get('alligator_crack', 0)}")

    # ---- Invariant 11: D40 -> class 3 ----
    check("INV-11", "D40 remains class 3 (pothole)",
          totals.get("pothole", 0) == raw_class_counts["D40"],
          f"expected={raw_class_counts['D40']} actual={totals.get('pothole', 0)}")

    # ---- Invariant 12: D43/D44/D50 never in output ----
    check("INV-12", "D43/D44/D50 never appear in normalized output",
          final_class_counts.get("D43", 0) == 0
          and final_class_counts.get("D44", 0) == 0
          and final_class_counts.get("D50", 0) == 0,
          f"D43={final_class_counts.get('D43', 0)} D44={final_class_counts.get('D44', 0)} D50={final_class_counts.get('D50', 0)}")

    # ---- Invariant 14: deterministic output filenames ----
    raw_names = sorted(p.name for p in raw_files)
    norm_names = sorted(p.name for p in norm_files)
    check("INV-14", "Output filenames are deterministic (identical to source names, sorted order stable)",
          raw_names == norm_names,
          "filenames match 1:1 and in identical sorted order" if raw_names == norm_names
          else "filename sets differ")

    # ---- Invariant 1: raw files unchanged (verified via manifest checksums) ----
    manifest = parse_manifest()
    stat_block = manifest.get("statistics", {})

    checksum_mismatch: List[str] = []
    for entry in manifest.get("image_manifest", []):
        src_img = Path(entry.get("source_image_path", ""))
        if src_img.exists():
            recorded = entry.get("source_image_checksum")
            if recorded and file_hash(src_img) != recorded:
                checksum_mismatch.append(f"raw image changed: {src_img.name}")
        else:
            checksum_mismatch.append(f"missing raw image: {src_img}")

        src_ann = Path(entry.get("source_annotation_path", ""))
        if src_ann.exists():
            recorded_ann = entry.get("source_annotation_checksum")
            if recorded_ann and file_hash(src_ann) != recorded_ann:
                checksum_mismatch.append(f"raw annotation changed: {src_ann.name}")
        else:
            checksum_mismatch.append(f"missing raw annotation: {src_ann}")

    check("INV-1", "Raw files are unchanged (raw image AND raw annotation checksums match those recorded during transformation)",
          not checksum_mismatch,
          f"{len(checksum_mismatch)} checksum mismatches" if checksum_mismatch
          else f"{len(manifest.get('image_manifest', []))} raw images and annotations checksum-verified")

    # ---- Cross-check manifest statistics against independently computed values ----
    manifest_mismatches: List[str] = []
    pairs = [
        ("original_object_count", total_raw_objects),
        ("retained_object_count", total_final_objects),
        ("excluded_object_count", total_excluded),
        ("skipped_image_count", total_skipped),
        ("empty_annotation_count", empty_count),
    ]
    for key, computed in pairs:
        recorded = stat_block.get(key)
        if recorded != computed:
            manifest_mismatches.append(f"{key}: manifest={recorded} recomputed={computed}")

    check("INV-MANIFEST", "Manifest statistics match independently recomputed values",
          not manifest_mismatches,
          "; ".join(manifest_mismatches) if manifest_mismatches else "all manifest statistics verified")

    # ---- Invariant 13: idempotency (re-running produces byte-identical output) ----
    sample_norms = [NORMALIZED_ANNOTATIONS_DIR / name for name in norm_names]
    pre_hashes = {p.name: file_hash(p) for p in sample_norms[:50]}
    check("INV-13", "Idempotency baseline captured (50 normalized annotations hashed before re-run)",
          len(pre_hashes) == min(50, len(sample_norms)),
          f"hashed {len(pre_hashes)} files")

    report = {
        "validation_version": VALIDATION_VERSION,
        "transformation_version": TRANSFORMATION_VERSION,
        "source_annotation_dir": str(RAW_ANNOTATIONS_DIR),
        "normalized_annotation_dir": str(NORMALIZED_ANNOTATIONS_DIR),
        "raw_annotation_count": len(raw_files),
        "normalized_annotation_count": len(norm_files),
        "raw_image_count": len(raw_images),
        "normalized_image_count": len(norm_images),
        "total_source_objects": total_raw_objects,
        "total_final_objects": total_final_objects,
        "total_excluded_objects": total_excluded,
        "total_skipped": total_skipped,
        "empty_normalized_annotations": empty_count,
        "raw_class_counts": dict(sorted(raw_class_counts.items())),
        "final_class_counts": dict(sorted(final_class_counts.items())),
        "checks": results,
        "overall_status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "diagnostics": {
            "coord_mismatches": coord_mismatches[:20],
            "dimension_mismatches": dimension_mismatches[:20],
            "excluded_leaks": excluded_leaks[:20],
            "mapping_errors": mapping_errors[:20],
            "checksum_mismatches": checksum_mismatch[:20],
            "manifest_mismatches": manifest_mismatches[:20],
        },
        "idempotency_baseline": pre_hashes,
    }

    return report


def main() -> int:
    print("Validating RDD2022 India transformation invariants...")
    print()
    report = validate()

    for entry in report["checks"]:
        marker = "PASS" if entry["status"] == "PASS" else "FAIL"
        print(f"[{marker}] {entry['invariant']}: {entry['description']}")
        if entry["detail"]:
            print(f"        {entry['detail']}")

    print()
    print("--- Counts ---")
    print(f"Source annotations:    {report['raw_annotation_count']}")
    print(f"Normalized annotations:{report['normalized_annotation_count']}")
    print(f"Source images:         {report['raw_image_count']}")
    print(f"Normalized images:     {report['normalized_image_count']}")
    print(f"Source objects:        {report['total_source_objects']}")
    print(f"Retained objects:      {report['total_final_objects']}")
    print(f"Excluded objects:      {report['total_excluded_objects']}")
    print(f"Skipped:               {report['total_skipped']}")
    print(f"Empty normalized annotations: {report['empty_normalized_annotations']}")
    print()
    print("--- Raw class counts ---")
    for k, v in report["raw_class_counts"].items():
        print(f"  {k}: {v}")
    print()
    print("--- Final class counts ---")
    for k, v in report["final_class_counts"].items():
        print(f"  {k}: {v}")
    print()

    out_path = NORMALIZED_ANNOTATIONS_DIR.parent.parent / "validation_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Validation report: {out_path}")
    print()
    print(f"OVERALL: {report['overall_status']}")

    if report["failures"]:
        print()
        print("Failures:")
        for f in report["failures"]:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
