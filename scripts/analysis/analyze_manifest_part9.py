import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

# Compute per-image counts from cumulative
prev_fcc = {}
per_image_counts = []
for img in manifest:
    fcc = img['final_class_counts']
    delta = {}
    for k, v in fcc.items():
        delta[k] = v - prev_fcc.get(k, 0)
    per_image_counts.append(delta)
    prev_fcc = fcc.copy()

print('=== IMAGES WITH transverse_crack (PER-IMAGE) ===')
tc_images = []
for i, (img, delta) in enumerate(zip(manifest, per_image_counts)):
    tc_count = delta.get('transverse_crack', 0)
    if tc_count > 0:
        fname = img['source_image_path'].split('\\\\')[-1]
        tc_images.append((fname, tc_count, delta))

print(f'Total images with transverse_crack: {len(tc_images)}')
print(f'Total transverse_crack objects: {sum(x[1] for x in tc_images)}')
print()
print('Images with transverse_crack:')
for fname, tc_count, delta in tc_images:
    print(f'  {fname}: transverse_crack={tc_count}, full_delta={delta}')

print()
print('=== IMAGES WITH ONLY pothole (PER-IMAGE) ===')
pothole_only = []
for i, (img, delta) in enumerate(zip(manifest, per_image_counts)):
    if len(delta) == 1 and 'pothole' in delta:
        fname = img['source_image_path'].split('\\\\')[-1]
        pothole_only.append((fname, delta['pothole']))

print(f'Total pothole-only images: {len(pothole_only)}')
for fname, count in pothole_only:
    print(f'  {fname}: pothole={count}')

print()
print('=== CLASS COMBINATION PATTERNS (PER-IMAGE) ===')
combo_counter = Counter()
for delta in per_image_counts:
    combo = tuple(sorted(delta.keys()))
    combo_counter[combo] += 1

print('Unique per-image class combination patterns:')
for combo, count in combo_counter.most_common():
    print(f'  {combo}: {count} images')

print()
print('=== EXCLUDED_OBJECT_COUNT ANALYSIS ===')
# The per-image excluded_object_count is always 0, but it should be the sum of D43+D44+D50 in original_class_counts
# Let's verify the global counts
excl_occ = Counter()
for img in manifest:
    for k, v in img['original_class_counts'].items():
        if k in ['D43', 'D44', 'D50']:
            excl_occ[k] += v

print(f'D43 total: {excl_occ["D43"]}')
print(f'D44 total: {excl_occ["D44"]}')
print(f'D50 total: {excl_occ["D50"]}')
print(f'Total excluded: {sum(excl_occ.values())}')
print(f'Global excluded_object_count: {data["statistics"]["excluded_object_count"]}')
print(f'Match: {sum(excl_occ.values()) == data["statistics"]["excluded_object_count"]}')

print()
print('=== DISTRIBUTION OF per-image EXCLUDED OBJECT COUNTS ===')
excl_per_image = []
for img in manifest:
    occ = img['original_class_counts']
    excl = sum(v for k, v in occ.items() if k in ['D43', 'D44', 'D50'])
    excl_per_image.append(excl)

excl_dist = Counter(excl_per_image)
print('Per-image excluded_object_count distribution (calculated from original_class_counts):')
for k in sorted(excl_dist.keys()):
    print(f'  {k}: {excl_dist[k]} images')

print()
print('=== TRANSFORMATION SUMMARY ===')
# D01 and D11 are in original_class_counts
d01_total = sum(1 for img in manifest for k, v in img['original_class_counts'].items() if k == 'D01')
d11_total = sum(1 for img in manifest for k, v in img['original_class_counts'].items() if k == 'D11')
print(f'Images with D01 in original_class_counts: {d01_total}')
print(f'Images with D11 in original_class_counts: {d11_total}')
print(f'Global d01_to_d00_count: {data["statistics"]["d01_to_d00_count"]}')
print(f'Global d11_to_d10_count: {data["statistics"]["d11_to_d10_count"]}')

# Actually sum the counts properly
d01_count = sum(v for img in manifest for k, v in img['original_class_counts'].items() if k == 'D01')
d11_count = sum(v for img in manifest for k, v in img['original_class_counts'].items() if k == 'D11')
print(f'Total D01 objects: {d01_count}')
print(f'Total D11 objects: {d11_count}')