import json
import xml.etree.ElementTree as ET
from collections import Counter
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

components = graph["component_manifest"]["components"]
images_in_graph = set()
for comp in components:
    images_in_graph.update(comp["members"])

# Count strata from XML for all images (both components and singletons)
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
            pass
    
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

print("Stratum distribution from XML files (all images):")
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(stratum_counts.values())}")

print("\nExpected from graph:")
expected_counts = graph['dataset_statistics']['class_presence_strata']
for s, c in sorted(expected_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(expected_counts.values())}")

print("\nDifferences:")
for s in sorted(set(list(stratum_counts.keys()) + list(expected_counts.keys()))):
    actual = stratum_counts.get(s, 0)
    expected = expected_counts.get(s, 0)
    diff = actual - expected
    if diff != 0:
        print(f"  {s}: actual={actual}, expected={expected}, diff={diff:+d}")