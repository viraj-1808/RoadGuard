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

image_lookup = {}
for img in manifest['image_manifest']:
    stem = os.path.basename(img['normalized_image_path']).replace('.jpg', '')
    image_lookup[stem] = img

tc_total = 0
tc_image_counts = {}
for stem, img in image_lookup.items():
    xml_path = ANNOT_DIR / f'{stem}.xml'
    counts = Counter()
    if xml_path.exists():
        tree = ET.parse(xml_path)
        for obj in tree.findall('object'):
            name = obj.find('name').text
            counts[name] += 1
    tc_count = counts.get('transverse_crack', 0)
    if tc_count > 0:
        tc_total += tc_count
        tc_image_counts[stem] = tc_count

print(f'Total TC objects from XML: {tc_total}')
print(f'Images with TC: {len(tc_image_counts)}')
print(f'TC image counts (showing first 20): {dict(sorted(tc_image_counts.items(), key=lambda x: x[1], reverse=True)[:20])}')