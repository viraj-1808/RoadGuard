import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import os

BASE = Path('C:/Users/viraj/Code_files/Github/RoadGuard AI')
MANIFEST = BASE / 'experiments/dataset/normalized_rdd2022_india/manifest.json'
GRAPH = BASE / 'experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json'
ANNOT_DIR = BASE / 'experiments/dataset/normalized_rdd2022_india/train/annotations'

with open(MANIFEST) as f:
    manifest = json.load(f)
with open(GRAPH) as f:
    graph = json.load(f)

image_lookup = {}
for img in manifest['image_manifest']:
    stem = os.path.basename(img['normalized_image_path']).replace('.jpg', '')
    image_lookup[stem] = img

# Count strata from XML files
stratum_counts = Counter()
for stem, img in image_lookup.items():
    xml_path = ANNOT_DIR / f'{stem}.xml'
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            classes = set()
            for obj in tree.findall('object'):
                name = obj.find('name').text
                classes.add(name)
        except:
            classes = set(img.get('final_class_counts', {}).keys())
    
    # Map classes to stratum
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
        frozenset({"pothole", "longitudinal_crack", "alligator_crack", "transverse_crack"}): "all_four_classes",
    }
    stratum = mapping.get(cls, "other")
    if stratum != "other":
        stratum_counts[stratum] += 1

print("Stratum distribution from XML files:")
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(stratum_counts.values())}")

print("\nExpected from graph:")
strata = graph['dataset_statistics']['class_presence_strata']
for s, c in sorted(strata.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")
print(f"Total: {sum(strata.values())}")

# Check which strata have mismatches
print("\nMismatch analysis:")
for s, c in sorted(stratum_counts.items(), key=lambda x: -x[1]):
    expected = strata.get(s, 0)
    diff = c - expected
    print(f"  {s}: actual={c}, expected={expected}, diff={diff}")