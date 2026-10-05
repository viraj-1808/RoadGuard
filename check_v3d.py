import json
import hashlib
import os
from collections import Counter
import xml.etree.ElementTree as ET

BASE_DIR = "C:/Users/viraj/Code_files/Github/RoadGuard AI"
MANIFEST_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized: true
原文主体中提到的大部分内容我都有)

MANIFEST_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/manifest.json")
GRAPH_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json")
ANNOT_DIR = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/train/annotations")
SPLIT_MANIFEST_PATH = os.path.join(BASE_DIR, "experiments/dataset/normalized_rdd2022_india/split_manifest.json")

with open(SPLIT_MANIFEST_PATH) as f:
    manifest = json.load(f)

assignments = manifest['assignments']
unit_lookup = manifest['split_statistics']  # won't work, need to reconstruct

# Actually, let me use the script's data
"