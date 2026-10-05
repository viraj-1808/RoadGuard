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

# Process components exactly as the script does
for i, comp in enumerate(components[:5]):
    members = comp["members"]
    class_counts = Counter()
    tc_count_in_comp = 0
    has_tc = False
    
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
                        if name == "transverse_crack":
                            tc_count_in_comp += 1
                            has_tc = True
                    for cls in classes_in_img:
                        class_counts[cls] += 1
                except Exception as e:
                    for cls, count in img.get("final_class_counts", {}).items():
                        class_counts[cls] += count
                    has_tc = "transverse_crack" in img.get("final_class_counts", {})
                    tc_count_in_comp = img.get("final_class_counts", {}).get("transverse_crack", 0)
            else:
                for cls, count in img.get("final_class_counts", {}).items():
                    class_counts[cls] += count
                has_tc = "transverse_crack" in img.get("final_class_counts", {})
                tc_count_in_comp = img.get("final_class_counts", {}).get("transverse_crack", 0)
    
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
    stratum = mapping.get(cls, "other")
    
    print(f"Component {comp['component_id']}: size={comp['size']}, members={len(members)}, classes={classes_present}, stratum={stratum}, class_counts={dict(class_counts)}")
    if i < 3:
        print(f"  First 5 members: {members[:5]}")