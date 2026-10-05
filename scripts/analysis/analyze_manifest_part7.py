import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== CRITICAL FINDING: CUMULATIVE vs PER-IMAGE COUNTS ===')
print()

# Check if final_class_counts is cumulative by comparing consecutive images
print('Checking if final_class_counts is cumulative:')
print()
prev_fcc = {}
for i, img in enumerate(manifest[:10]):
    fname = img['source_image_path'].split('\\')[-1]
    fcc = img['final_class_counts']
    occ = img['original_class_counts']
    
    # Compute per-image deltas
    delta_fcc = {}
    for k, v in fcc.items():
        delta = v - prev_fcc.get(k, 0)
        delta_fcc[k] = delta
    
    delta_occ = {}
    for k, v in occ.items():
        delta = v - prev_fcc.get(k.replace('D40','pothole').replace('D44','excluded').replace('D20','alligator_crack').replace('D00','longitudinal_crack').replace('D01','longitudinal_crack').replace('D10','transverse_crack').replace('D11','transverse_crack'), 0)
        # This is getting complicated, let me just check the sums
    
    print(f'Image {i+1} ({fname}):')
    print(f'  original_object_count: {img["original_object_count"]}, sum(original_class_counts): {sum(occ.values())}')
    print(f'  retained_object_count: {img["retained_object_count"]}, sum(final_class_counts): {sum(fcc.values())}')
    print(f'  excluded_object_count: {img["excluded_object_count"]}')
    print(f'  original_class_counts: {occ}')
    print(f'  final_class_counts: {fcc}')
    print(f'  Delta from prev: {delta_fcc}')
    print()
    
    prev_fcc = fcc.copy()

print()
print('=== CHECK: Last image vs global statistics ===')
last = manifest[-1]
print(f'Last image: {last["source_image_path"].split(chr(92))[-1]}')
print(f'Last image final_class_counts: {last["final_class_counts"]}')
print(f'Global final_class_counts: {data["statistics"]["final_class_counts"]}')
print(f'Match: {last["final_class_counts"] == data["statistics"]["final_class_counts"]}')

print()
print('=== COMPUTE PER-IMAGE COUNTS FROM CUMULATIVE ===')
# Compute per-image counts by taking differences
prev_fcc = {}
per_image_counts = []
for img in manifest:
    fcc = img['final_class_counts']
    delta = {}
    for k, v in fcc.items():
        delta[k] = v - prev_fcc.get(k, 0)
    per_image_counts.append(delta)
    prev_fcc = fcc.copy()

# Verify: sum of per-image counts should equal global statistics
sum_per_image = Counter()
for delta in per_image_counts:
    for k, v in delta.items():
        sum_per_image[k] += v

print(f'Sum of per-image final_class_counts: {dict(sum_per_image)}')
print(f'Global final_class_counts: {data["statistics"]["final_class_counts"]}')
print(f'Match: {dict(sum_per_image) == data["statistics"]["final_class_counts"]}')

print()
print('=== PER-IMAGE transverse_crack distribution ===')
tc_per_image = [d.get('transverse_crack', 0) for d in per_image_counts]
print(f'Total transverse_crack (sum of per-image): {sum(tc_per_image)}')
print(f'Images with transverse_crack > 0: {sum(1 for x in tc_per_image if x > 0)}')
print(f'Images with transverse_crack == 1: {sum(1 for x in tc_per_image if x == 1)}')
print(f'Images with transverse_crack == 2: {sum(1 for x in tc_per_image if x == 2)}')
print(f'Images with transverse_crack >= 3: {sum(1 for x in tc_per_image if x >= 3)}')
print(f'Min transverse_crack per image: {min(tc_per_image)}')
print(f'Max transverse_crack per image: {max(tc_per_image)}')
print(f'Avg transverse_crack per image (non-zero): {sum(x for x in tc_per_image if x > 0) / sum(1 for x in tc_per_image if x > 0):.2f}')

print()
print('=== PER-IMAGE pothole distribution ===')
p_per_image = [d.get('pothole', 0) for d in per_image_counts]
print(f'Total pothole (sum of per-image): {sum(p_per_image)}')
print(f'Images with pothole > 0: {sum(1 for x in p_per_image if x > 0)}')
print(f'Min pothole per image: {min(p_per_image)}')
print(f'Max pothole per image: {max(p_per_image)}')

print()
print('=== PER-IMAGE alligator_crack distribution ===')
a_per_image = [d.get('alligator_crack', 0) for d in per_image_counts]
print(f'Total alligator_crack (sum of per-image): {sum(a_per_image)}')
print(f'Images with alligator_crack > 0: {sum(1 for x in a_per_image if x > 0)}')
print(f'Min alligator_crack per image: {min(a_per_image)}')
print(f'Max alligator_crack per image: {max(a_per_image)}')

print()
print('=== PER-IMAGE longitudinal_crack distribution ===')
l_per_image = [d.get('longitudinal_crack', 0) for d in per_image_counts]
print(f'Total longitudinal_crack (sum of per-image): {sum(l_per_image)}')
print(f'Images with longitudinal_crack > 0: {sum(1 for x in l_per_image if x > 0)}')
print(f'Min longitudinal_crack per image: {min(l_per_image)}')
print(f'Max longitudinal_crack per image: {max(l_per_image)}')