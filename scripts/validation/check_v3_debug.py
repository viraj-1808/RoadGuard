import json
import os
from collections import Counter
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BASE_DIR = PROJECT_ROOT
MANIFEST_PATH = PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/manifest.json'
GRAPH_PATH = PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json'
ANNOT_DIR = PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/train/annotations'
SPLIT_PATH = PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/split_manifest.json'

with open(MANIFEST_PATH) as f:
    manifest = json.load(f)
with open(GRAPH_PATH) as f:
    graph = json.load(f)
with open(SPLIT_PATH) as f:
    split_manifest = json.load(f)

image_lookup = {}
for img in manifest['image_manifest']:
    stem = os.path.basename(img['normalized_image_path']).replace('.jpg', '')
    image_lookup[stem] = img

# Per-image stratum from XML
per_image_strata = {}
for stem in image_lookup:
    xml_path = os.path.join(ANNOT_DIR, f'{stem}.xml')
    classes = set()
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            for obj in tree.findall('object'):
                name = obj.find('name').text
                classes.add(name)
        except Exception:
            pass
    
    mapping = {
        frozenset(): 'empty_no_defect',
        frozenset({'pothole'}): 'pothole',
        frozenset({'longitudinal_crack'}): 'longitudinal_crack',
        frozenset({'alligator_crack'}): 'alligator_crack',
        frozenset({'transverse_crack'}): 'transverse_crack',
        frozenset({'pothole', 'longitudinal_crack'}): 'longitudinal_crack+pothole',
        frozenset({'pothole', 'alligator_crack'}): 'alligator_crack+pothole',
        frozenset({'pothole', 'transverse_crack'}): 'transverse_crack+pothole',
        frozenset({'longitudinal_crack', 'alligator_crack'}): 'longitudinal_crack+alligator_crack',
        frozenset({'pothole', 'longitudinal_crack', 'alligator_crack'}): 'longitudinal_crack+alligator_crack+pothole',
        frozenset({'pothole', 'longitudinal_crack', 'transverse_crack'}): 'longitudinal_crack+transverse_crack+pothole',
        frozenset({'pothole', 'alligator_crack', 'transverse_crack'}): 'transverse_crack+alligator_crack+pothole',
        frozenset({'longitudinal_crack', 'alligator_crack', 'transverse_crack'}): 'longitudinal_crack+alligator_crack+transverse_crack',
        frozenset({'pothole', 'longitudinal_crack', 'alligator_crack', 'transverse_crack'}): 'longitudinal_crack+transverse_crack+alligator_crack+pothole',
    }
    per_image_strata[stem] = mapping.get(frozenset(classes), 'other')

stratum_image_counts = graph['dataset_statistics']['class_presence_strata']
RATIOS = {'train': 0.70, 'val': 0.15, 'test': 0.15}
splits = ['train', 'val', 'test']

# Reconstruct unit_lookup from split_manifest
components = graph['component_manifest']['components']
images_in_graph = set()
for comp in components:
    images_in_graph.update(comp['members'])

# Build unit_lookup manually
unit_lookup = {}
for comp in components:
    unit_lookup[comp['component_id']] = {'type': 'component', 'members': comp['members'], 'size': comp['size']}

for stem in set(image_lookup.keys()) - images_in_graph:
    unit_lookup[stem] = {'type': 'singleton', 'members': [stem], 'size': 1}

# V3 check with per-image strata
print('V3 Strata Balance (per-image strata):')
v3_pass = True
for split in splits:
    for strat in stratum_image_counts:
        target = int(stratum_image_counts[strat] * RATIOS[split])
        actual = 0
        for uid, sp in split_manifest['assignments'].items():
            if sp == split:
                unit = unit_lookup[uid]
                for member in unit['members']:
                    member_stratum = per_image_strata.get(member, 'other')
                    if member_stratum == strat:
                        actual += 1
        tolerance = max(1, int(target * 0.02))
        status = 'PASS' if abs(actual - target) <= tolerance else 'FAIL'
        if abs(actual - target) > tolerance:
            v3_pass = False
        print(f'  {split} {strat}: actual={actual}, target={target}, tol=±{tolerance} [{status}]')

print(f'V3 overall: {"PASS" if v3_pass else "FAIL"}')