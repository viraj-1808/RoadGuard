import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import os

BASE_DIR = "C:/Users/viraj/Code_files/Github/RoadGuard AI"
MANIFEST_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/manifest.json")
GRAPH_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json")
ANNOT_DIR = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/train/annotations")

with open(MANIFEST_PATH) as f:
    manifest = json.load(f)
with open(GRAPH_PATH) as f:
    graph = json.load(f)

image_lookup = {}
for img in manifest['image_manifest']:
    stem = os.path.basename(img['normalized_image_path']).replace('.jpg', '')
    image_lookup[stem] = img

# Check specific stratum mappings
print("Checking stratum assignments for first few images:")
for i, (stem, img) in enumerate(list(image_lookup.items())[:10]):
    xml_path = os.path.join(ANNOT_DIR, f"{stem}.xml")
    classes = set()
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            for obj in tree.findall('object'):
                name = obj.find('name').text
                classes.add(name)
        except Exception as e:
            classes = set()
    
    cls = frozenset(classes)
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
    stratum = mapping.get(cls, "other")
    
    print(f"  {stem}: manifest retained={img['retained_object_count']}, classes={sorted(classes) if classes else 'none'}, stratum={stratum}")

# Let's look at the stratum distribution differences
print(f"\nStratum distribution from XML files:")
stratum_counts = Counter()
for stem, img in image_lookup.items():
    xml_path = os.path.join(ANNOT_DIR, f"{stem}.xml")
    classes = set()
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            for obj in tree.findall('object'):
                name = obj.find('name').text
                classes.add(name)
        except Exception as e:
            pass  # Use empty set on error
    
    cls = frozenset(classes)
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
    stratum = mapping.get(cls, "other")
    if stratum != "other":
        stratum_counts[stratum] += 1

print("Actual (from XML):")
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

print("\nExpected (from graph):")
expected_counts = graph['dataset_statistics']['class_presence_strata']
for s, c in sorted(expected_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

print("\nDifferences (Actual - Expected):")
for s in sorted(set(list(stratum_counts.keys()) + list(expected_counts.keys()))):
    actual = stratum_counts.get(s, 0)
    expected = expected_counts.get(s, 0)
    diff = actual - expected
    if diff != 0:
        print(f"  {s}: actual={actual}, expected={expected}, diff={diff:+d}")