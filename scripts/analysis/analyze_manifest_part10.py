import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']
stats = data['statistics']

print('=== CRITICAL: original_class_counts and final_class_counts are CUMULATIVE ===')
print()

# Compute per-image deltas
prev_occ = {}
prev_fcc = {}
per_image_data = []

for img in manifest:
    fname = img['source_image_path'].split('\\\\')[-1]
    occ = img['original_class_counts']
    fcc = img['final_class_counts']
    
    # Per-image original_class_counts (delta)
    delta_occ = {}
    for k, v in occ.items():
        delta_occ[k] = v - prev_occ.get(k, 0)
    
    # Per-image final_class_counts (delta)
    delta_fcc = {}
    for k, v in fcc.items():
        delta_fcc[k] = v - prev_fcc.get(k, 0)
    
    # Check consistency
    sum_delta_occ = sum(delta_occ.values())
    sum_delta_fcc = sum(delta_fcc.values())
    orig_obj = img['original_object_count']
    ret_obj = img['retained_object_count']
    excl_obj = img['excluded_object_count']
    
    # Also compute excluded from original delta
    excluded_delta = sum(delta_occ.get(k, 0) for k in ['D43', 'D44', 'D50'])
    
    # Check if original_object_count matches sum of per-image original_class_counts
    # Note: original_object_count might include or exclude excluded objects
    match_occ = (sum_delta_occ == orig_obj)
    match_fcc = (sum_delta_fcc == ret_obj)
    match_excl = (excluded_delta == excl_obj)
    
    per_image_data.append({
        'fname': fname,
        'delta_occ': delta_occ,
        'delta_fcc': delta_fcc,
        'original_object_count': orig_obj,
        'retained_object_count': ret_obj,
        'excluded_object_count': excl_obj,
        'excluded_delta': excluded_delta,
        'match_occ': match_occ,
        'match_fcc': match_fcc,
        'match_excl': match_excl
    })
    
    prev_occ = occ.copy()
    prev_fcc = fcc.copy()

print('Checking consistency for first 20 images:')
print(f'{"Image":<25} {"orig_obj":>8} {"sum_delta_occ":>14} {"match":>6} {"ret_obj":>8} {"sum_delta_fcc":>14} {"match":>6} {"excl_obj":>9} {"excl_delta":>10} {"match":>6}')
for i in range(min(20, len(per_image_data))):
    d = per_image_data[i]
    print(f'{d["fname"][:24]:<25} {d["original_object_count"]:>8} {sum(d["delta_occ"].values()):>14} {str(d["match_occ"]):>6} {d["retained_object_count"]:>8} {sum(d["delta_fcc"].values()):>14} {str(d["match_fcc"]):>6} {d["excluded_object_count"]:>9} {d["excluded_delta"]:>10} {str(d["match_excl"]):>6}')

print()
print('=== Consistency Summary (All 1530 images) ===')
occ_match_count = sum(1 for d in per_image_data if d['match_occ'])
fcc_match_count = sum(1 for d in per_image_data if d['match_fcc'])
excl_match_count = sum(1 for d in per_image_data if d['match_excl'])

print(f'original_object_count matches sum(delta_occ): {occ_match_count}/{len(per_image_data)}')
print(f'retained_object_count matches sum(delta_fcc): {fcc_match_count}/{len(per_image_data)}')
print(f'excluded_object_count matches excl delta: {excl_match_count}/{len(per_image_data)}')

print()
print('=== Per-image excluded objects (from deltas) ===')
excl_nonzero = [d for d in per_image_data if d['excluded_delta'] > 0]
print(f'Images with per-image excluded objects > 0: {len(excl_nonzero)}')
print(f'Total excluded objects (from deltas): {sum(d["excluded_delta"] for d in per_image_data)}')
print(f'Global excluded_object_count: {stats["excluded_object_count"]}')
print(f'Match: {sum(d["excluded_delta"] for d in per_image_data) == stats["excluded_object_count"]}')

print()
print('=== Detailed per-image excluded (showing mismatches with manifest excluded_object_count) ===')
all_mismatched = [d for d in per_image_data if d['excluded_delta'] != d['excluded_object_count']]
print(f'Images where manifest excluded_object_count != calculated per-image excluded: {len(all_mismatched)}')
print(f'All manifest excluded_object_count values are 0: {all(d["excluded_object_count"] == 0 for d in per_image_data)}')
print(f'Images that actually have excluded objects: {len(excl_nonzero)}')

print()
print('=== Per-image excluded class breakdown ===')
excl_classes = Counter()
for d in per_image_data:
    for k in ['D43', 'D44', 'D50']:
        if k in d['delta_occ']:
            excl_classes[k] += d['delta_occ'][k]
print(f'D43 per-image total: {excl_classes["D43"]}')
print(f'D44 per-image total: {excl_classes["D44"]}')
print(f'D50 per-image total: {excl_classes["D50"]}')
print(f'Sum: {sum(excl_classes.values())}')
print(f'Global d43_exclusions: {stats["d43_exclusions"]}')
print(f'Global d44_exclusions: {stats["d44_exclusions"]}')
print(f'Global d50_exclusions: {stats["d50_exclusions"]}')

print()
print('=== Per-image merge counts (D01, D11) ===')
d01_total = sum(d['delta_occ'].get('D01', 0) for d in per_image_data)
d11_total = sum(d['delta_occ'].get('D11', 0) for d in per_image_data)
print(f'D01 per-image total: {d01_total} vs global d01_to_d00_count: {stats["d01_to_d00_count"]} => Match: {d01_total == stats["d01_to_d00_count"]}')
print(f'D11 per-image total: {d11_total} vs global d11_to_d10_count: {stats["d11_to_d10_count"]} => Match: {d11_total == stats["d11_to_d10_count"]}')

print()
print('=== FIRST 20 IMAGES - ACTUAL PER-IMAGE COUNTS ===')
for i, d in enumerate(per_image_data[:20]):
    print(f'[{i+1}] {d["fname"]}:')
    print(f'    original_object_count: {d["original_object_count"]}, sum(per-image original): {sum(d["delta_occ"].values())}')
    print(f'    retained_object_count: {d["retained_object_count"]}, sum(per-image final): {sum(d["delta_fcc"].values())}')
    print(f'    per-image original_class_counts: {d["delta_occ"]}')
    print(f'    per-image final_class_counts: {d["delta_fcc"]}')
    print(f'    per-image excluded objects: {d["excluded_delta"]} (manifest says: {d["excluded_object_count"]})')