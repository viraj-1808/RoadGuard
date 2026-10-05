import json
import hashlib
import os
from collections import Counter
import xml.etree.ElementTree as ET

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

# Per-image stratum from XML data
per_image_strata = {}
for stem in image_lookup:
    xml_path = os.path.join(ANNOT_DIR, f"{stem}.xml")
    classes = set()
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            for obj in tree.findall('object'):
                name = obj.find('name').text
                classes.add(name)
        except Exception:
            pass
    else:
        classes = set(image_lookup[stem].get('final_class_counts', {}).keys())
    
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
    cls = frozenset(classes)
    per_image_strata[stem] = mapping.get(cls, "other")

stratum_image_counts = graph['dataset_statistics']['class_presence_strata']
RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
splits = ["train", "val", "test"]

print("Per-split stratum distribution (per-image strata):")
for split in splits:
    for strat in stratum_image_counts:
        target = int(stratum_image_counts[strat] * RATIOS[split])
        tolerance = max(1, int(target * 0.02))
        
        actual = 0
        for stem, stratum in per_image_strata.items():
            # We don't know the split assignment yet, so let's just check total
            pass
        print(f"  {split} {strat}: expected={target}, tolerance=±{tolerance}")

# Check total stratum distribution from XML
total_strata = Counter()
for stem, stratum in per_image_strata.items():
    total_strata[stratum] += 1

print("\nTotal stratum distribution from XML:")
for s, c in sorted(total_strata.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

print("\nExpected from graph:")
for s, c in sorted(stratum_image_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")