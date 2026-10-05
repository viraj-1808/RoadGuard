import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BASE = PROJECT_ROOT
MANIFEST = BASE / 'experiments/dataset/normalized_rdd2022_india/manifest.json'
GRAPH = BASE / 'experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json'
ANNOT_DIR = BASE / 'experiments/dataset/normalized_rdd2022_india/train/annotations'

with open(MANIFEST) as f:
    manifest = json.load(f)
with open(GRAPH) as f:
    graph = json.load(f)

# Count TC objects from XML files
tc_total = 0
tc_images = set()
class_counts_per_image = {}
for img in manifest['image_manifest']:
    stem = img['normalized_image_path'].split('/')[-1].replace('.jpg', '')
    xml_path = ANNOT_DIR / f'{stem}.xml'
    counts = Counter()
    if xml_path.exists():
        tree = ET.parse(xml_path)
        for obj in tree.findall('object'):
            name = obj.find('name').text
            counts[name] += 1
    class_counts_per_image[stem] = dict(counts)
    if 'transverse_crack' in counts:
        tc_total += counts['transverse_crack']
        tc_images.add(stem)

print(f'TC objects from XML: {tc_total}')
print(f'TC images from XML: {len(tc_images)}')

# Check images_with_class from graph
print(f'images_with_class from graph: {graph["dataset_statistics"]["images_with_class"]}')

# Check object_totals from graph
print(f'object_totals from graph: {graph["dataset_statistics"]["object_totals"]}')

# Check strata
print(f'class_presence_strata from graph: {graph["dataset_statistics"]["class_presence_strata"]}')

# Verify total objects
total_objects = sum(sum(c.values()) for c in class_counts_per_image.values())
print(f'Total objects from XML: {total_objects}')
print(f'object_total_sum from graph: {graph["dataset_statistics"]["object_total_sum"]}')

# Check per-image class counts for a TC image
stem = 'India_000055'
print(f'\\nPer-image counts for {stem}: {class_counts_per_image[stem]}')