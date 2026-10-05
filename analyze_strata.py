#!/usr/bin/env python3
import json
import os
from collections import Counter

BASE_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
DATASET_DIR = os.path.join(BASE_DIR, "experiments", "dataset", "normalized_rdd2022_india")
MANIFEST_PATH = os.path.join(DATASET_DIR, "manifest.json")
GRAPH_PATH = os.path.join(DATASET_DIR, "group_analysis", "correlation_graph.json")

with open(MANIFEST_PATH, "r") as f:
    manifest = json.load(f)
with open(GRAPH_PATH, "r") as f:
    graph = json.load(f)

image_manifest = manifest["image_manifest"]

print("=" * 60)
print("First 5 image entries:")
print("=" * 60)
for i, img in enumerate(image_manifest[:5]):
    print(f"\nImage {i}:")
    print(json.dumps(img, indent=2))

def compute_per_image_class_counts(image_manifest):
    per_image_counts = []
    prev_counts = {"pothole": 0, "alligator_crack": 0, "longitudinal_crack": 0, "transverse_crack": 0}
    for img in image_manifest:
        curr_counts = img.get("final_class_counts", {})
        per_image = {}
        for cls in ["pothole", "alligator_crack", "longitudinal_crack", "transverse_crack"]:
            per_image[cls] = curr_counts.get(cls, 0) - prev_counts.get(cls, 0)
            if per_image[cls] < 0:
                per_image[cls] = curr_counts.get(cls, 0)
        per_image_counts.append({
            "stem": os.path.basename(img["normalized_image_path"]).replace(".jpg", ""),
            "per_image_counts": per_image
        })
        for cls in ["pothole", "alligator_crack", "longitudinal_crack", "transverse_crack"]:
            prev_counts[cls] = curr_counts.get(cls, 0)
    return per_image_counts

def _class_stratum(classes_present):
    cls = frozenset(classes_present)
    mapping = {
        frozenset(): "empty_no_defect",
        frozenset({"pothole"}): "pothole",
        frozenset({"longitudinal_crack"}): "longitudinal_crack",
        frozenset({"alligator_crack"}): "alligator_crack",
        frozenset({"transverse_crack"}): "transverse_crack",
        frozenset({"pothole", "longitudinal_crack"}): "longitudinal_crack+pothole",
        frozenset({"pothole", "alligator_crack"}): "alligator_crack+pothole",
        frozenset({"pothole", "transverse_crack"}): "transverse_crack+pothole",
        frozenset({"longitudinal_crack", "alligator_crack"}): "longitudinal_crack+alligator_crack",
        frozenset({"pothole", "longitudinal_crack", "alligator_crack"}): "longitudinal_crack+alligator_crack+pothole",
        frozenset({"pothole", "longitudinal_crack", "transverse_crack"}): "longitudinal_crack+transverse_crack+pothole",
        frozenset({"pothole", "alligator_crack", "transverse_crack"}): "transverse_crack+alligator_crack+pothole",
        frozenset({"longitudinal_crack", "alligator_crack", "transverse_crack"}): "longitudinal_crack+alligator_crack+transverse_crack",
        frozenset({"pothole", "longitudinal_crack", "alligator_crack", "transverse_crack"}): "longitudinal_crack+transverse_crack+alligator_crack+pothole",
    }
    return mapping.get(cls, "other")

per_image_data = compute_per_image_class_counts(image_manifest)
per_image_class_counts = {item["stem"]: item["per_image_counts"] for item in per_image_data}

print("\n" + "=" * 60)
print("Per-image class counts (first 5):")
print("=" * 60)
for item in per_image_data[:5]:
    print(f"  {item['stem']}: {item['per_image_counts']}")

stratum_counts = Counter()
for item in per_image_data:
    stem_counts = item["per_image_counts"]
    classes_present = [cls for cls, count in stem_counts.items() if count > 0]
    stratum = _class_stratum(classes_present)
    stratum_counts[stratum] += 1

print("\n" + "=" * 60)
print("Computed stratum distribution:")
print("=" * 60)
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

ground_truth = {
    "pothole": 760,
    "alligator_crack+pothole": 380,
    "longitudinal_crack+pothole": 198,
    "longitudinal_crack+alligator_crack+pothole": 163,
    "longitudinal_crack+transverse_crack+pothole": 14,
    "transverse_crack+pothole": 9,
    "longitudinal_crack+transverse_crack+alligator_crack+pothole": 5,
    "transverse_crack+alligator_crack+pothole": 1,
}

print("\n" + "=" * 60)
print("Ground truth from correlation_graph.json:")
print("=" * 60)
for s, c in sorted(ground_truth.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

print("\n" + "=" * 60)
print("Comparison:")
print("=" * 60)
print(f"  {'Stratum':<50} {'Computed':>10} {'Ground Truth':>13} {'Match':>8}")
print(f"  {'-'*50} {'-'*10} {'-'*13} {'-'*8}")
all_match = True
for s in sorted(set(list(stratum_counts.keys()) + list(ground_truth.keys()))):
    computed = stratum_counts.get(s, 0)
    truth = ground_truth.get(s, 0)
    match = "YES" if computed == truth else "NO"
    if computed != truth:
        all_match = False
    print(f"  {s:<50} {computed:>10} {truth:>13} {match:>8}")

total_computed = sum(stratum_counts.values())
total_truth = sum(ground_truth.values())
print(f"\n  Total computed images: {total_computed}")
print(f"  Total ground truth images: {total_truth}")
print(f"\n  All match: {all_match}")
