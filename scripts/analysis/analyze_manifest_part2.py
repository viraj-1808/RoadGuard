import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
stats = data['statistics']
manifest = data['image_manifest']

print('=== 2. VERIFICATION ===')
fc = stats['final_class_counts']
print(f'longitudinal_crack == 498? {fc["longitudinal_crack"] == 498} (actual: {fc["longitudinal_crack"]})')
print(f'transverse_crack == 30? {fc["transverse_crack"] == 30} (actual: {fc["transverse_crack"]})')
print(f'alligator_crack == 645? {fc["alligator_crack"] == 645} (actual: {fc["alligator_crack"]})')
print(f'pothole == 3187? {fc["pothole"] == 3187} (actual: {fc["pothole"]})')
total = sum(fc.values())
print(f'total == 4360? {total == 4360} (actual: {total})')
print()
# Cross-check with original counts
oc = stats['original_class_counts']
print('--- Cross-check with original counts ---')
print(f'D00({oc["D00"]}) + D01({oc["D01"]}) = {oc["D00"]+oc["D01"]} vs longitudinal_crack {fc["longitudinal_crack"]}')
print(f'D10({oc["D10"]}) + D11({oc["D11"]}) = {oc["D10"]+oc["D11"]} vs transverse_crack {fc["transverse_crack"]}')
print(f'D20({oc["D20"]}) = {oc["D20"]} vs alligator_crack {fc["alligator_crack"]}')
print(f'D40({oc["D40"]}) = {oc["D40"]} vs pothole {fc["pothole"]}')
print(f'Sum of all original: {sum(oc.values())} vs original_object_count {stats["original_object_count"]}')
print(f'Sum of all final: {sum(fc.values())} vs retained_object_count {stats["retained_object_count"]}')
print(f'Excluded: {sum(oc.values()) - sum(fc.values())} vs excluded_object_count {stats["excluded_object_count"]}')

print()
print('=== 3. FIRST 20 IMAGES - final_class_counts ===')
for i, img in enumerate(manifest[:20]):
    fname = img['source_image_path'].split('\\')[-1]
    fcc = img['final_class_counts']
    occ = img['original_class_counts']
    excl = img['excluded_object_count']
    print(f'[{i+1}] {fname}: final={fcc} | original={occ} | excluded={excl} | retained={img["retained_object_count"]}')