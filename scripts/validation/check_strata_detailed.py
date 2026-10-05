import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BASE_DIR = PROJECT_ROOT
MANIFEST_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/manifest.json"
GRAPH_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json"
ANNOT_DIR = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/train/annotations"

with open(MANIFEST_PATH) as f:
    manifest = json.load(f)
with open(GRAPH_PATH) as f:
    graph = json.load(f)

image_lookup = {}
for img in manifest['image_manifest']:
    stem = os.path.basename(img['normalized_image_path']).replace('.jpg', '')
    image_lookup[stem] = img

components = graph["component_manifest"]["components"]

# Check component strata vs per-image strata
print("Component vs per-image stratum comparison:")
for comp in components[:10]:
    members = comp["members"]
    
    # Get per-image strata
    image_strata = []
    for m in members:
        img = image_lookup.get(m)
        if img:
            stem = os.path.basename(img["normalized_image_path"]).replace(".jpg", "")
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
            image_strata.append(stratum)
    
    # Get component stratum
    class_counts = Counter()
    for m in members:
        img = image_lookup.get(m)
        if img:
            stem = os.path.basename(img["normalized_image_path"]).replace(".jpg", "")
            xml_path = os.path.join(ANNOT_DIR, f"{stem}.xml")
            if os.path.exists(xml_path):
                try:
                    tree = ET.parse(xml_path)
                    classes_in_img = set()
                    for obj in tree.findall('object'):
                        name = obj.find('name').text
                        classes_in_img.add(name)
                    for cls in classes_in_img:
                        class_counts[cls] += 1
                except Exception as e:
                    for cls, count in img.get("final_class_counts", {}).items():
                        class_counts[cls] += 1
            else:
                for cls, count in img.get("final_class_counts", {}).items():
                    class_counts[cls] += 1
    
    classes_present = sorted(class_counts.keys())
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
    comp_stratum = mapping.get(cls, "other")
    
    print(f"Component {comp['component_id']}: size={comp['size']}, comp_stratum={comp_stratum}")
    print(f"  Per-image strata: {Counter(image_strata)}")