import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

MANIFEST_PATH = PROJECT_ROOT / "experiments/dataset/normalized_rdd2022_india/manifest.json"

with open(MANIFEST_PATH) as f:
    m = json.load(f)

tc = [img for img in m['image_manifest'] if img.get('final_class_counts', {}).get('transverse_crack', 0) > 0]
print(f'TC images: {len(tc)}')
print(f'Sum TC from final_class_counts: {sum(img["final_class_counts"]["transverse_crack"] for img in tc)}')

print('First 3 TC images:')
for img in tc[:3]:
    print(f'  {img["normalized_image_path"].split("/")[-1].replace(".jpg", "")}: orig={img["original_object_count"]}, retained={img["retained_object_count"]}, final_counts={img["final_class_counts"]}')

print(f'\nNon-TC images sample:')
non_tc = [img for img in m['image_manifest'] if 'transverse_crack' not in img.get('final_class_counts', {})][:3]
for img in non_tc:
    print(f'  {img["normalized_image_path"].split("/")[-1].replace(".jpg", "")}: orig={img["original_object_count"]}, retained={img["retained_object_count"]}, final_counts={img["final_class_counts"]}')

# Check original_class_counts vs final_class_counts
print(f'\nOriginal class counts for first TC image:')
img = tc[0]
print(f'  original_class_counts: {img.get("original_class_counts")}')
print(f'  final_class_counts: {img.get("final_class_counts")}')
print(f'  retained_object_count: {img.get("retained_object_count")}')