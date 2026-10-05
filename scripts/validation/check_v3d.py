import json
import hashlib
import os
from collections import Counter
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BASE_DIR = PROJECT_ROOT
MANIFEST_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/manifest.json"
GRAPH_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json"
ANNOT_DIR = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/train/annotations"
SPLIT_MANIFEST_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/split_manifest.json"

with open(SPLIT_MANIFEST_PATH) as f:
    manifest = json.load(f)

assignments = manifest['assignments']
unit_lookup = manifest['split_statistics']  # won't work, need to reconstruct

# Actually, let me use the script's data
"