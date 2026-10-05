import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== TRANSFORMATION RULES SECTION ===')
print(f"transformation_version: {data.get('transformation_version')}")
print()
print('class_mapping:')
for class_key, mapping in data['transformation_rules']['class_mapping'].items():
    if isinstance(mapping, dict):
        print(f'  {class_key}:')
        for k, v in mapping.items():
            if k == 'action':
                print(f'    {k}: {v}')
            else:
                print(f'    {k}: {v}')
    else:
        print(f'  {class_key}: {mapping}')

print()
print('=== COMPUTE PER-IMAGE COUNTS TO CHECK TRANSFORMATION EFFECTS ===')
# Compute per-image counts by taking differences
prev_fcc = {}
prev_occ = {}
transformation_checks = []

for img in manifest:
    fname = img['source_image_path'].split('\\\\')[-1]
    fcc = img['final_class_counts']
    occ = img['original_class_counts']
    
    # Compute per-image deltas
    delta_fcc = {}
    for k, v in fcc.items():
        delta_fcc[k] = v - prev_fcc.get(k, 0)
    
    delta_occ = {}
    for k, v in occ.items():
        delta_occ[k] = v - prev_occ.get(k, 0)
    
    # Check transformations: D01->D00, D11->D10, D43/D44/D50 excluded
    d01_before = delta_occ.get('D01', 0)
    d00_after = delta_fcc.get('longitudinal_crack', 0)  # Note: longitudinal_crack includes both D00 and D01
    
    d11_before = delta_occ.get('D11', 0)
    d10_after = delta_fcc.get('transverse_crack', 0)  # Note: transverse_crack includes both D10 and D11
    
    d43_excl = delta_occ.get('D43', 0)
    d44_excl = delta_occ.get('D44', 0)
    d50_excl = delta_occ.get('D50', 0)
    
    transformation_checks.append({
        'image': fname,
        'd01_before': d01_before,
        'd11_before': d11_before,
        'd43_excluded': d43_excl,
        'd44_excluded': d44_excl,
        'd50_excluded': d50_excl,
        'original_object_count': img['original_object_count'],
        'retained_object_count': img['retained_object_count'],
        'excluded_object_count': img['excluded_object_count']
    })
    
    prev_fcc = fcc.copy()
    prev_occ = occ.copy()

print('Per-image transformation checks (first 10 images with activity):')
active_checks = [c for c in transformation_checks if 
                c['d01_before'] > 0 or c['d11_before'] > 0 or 
                c['d43_excluded'] > 0 or c['d44_excluded'] > 0 or c['d50_excluded'] > 0][:10]

for check in active_checks:
    print(f"  {check['image']}:")
    print(f"    Original counts: D01={check['d01_before']}, D11={check['d11_before']}, D43={check['d43_excluded']}, D44={check['d44_excluded']}, D50={check['d50_excluded']}")
    print(f"    Object counts: original={check['original_object_count']}, retained={check['retained_object_count']}, excluded={check['excluded_object_count']}")
    # Note: We can't directly map D01/D11 to final counts because they merge into longitudinal_crack/transverse_crack
    # But we can verify that excluded classes are properly handled
    total_excluded_from_occ = check['d43_excluded'] + check['d44_excluded'] + check['d50_excluded']
    if total_excluded_from_occ > 0:
        print(f"    Total excluded classes in original: {total_excluded_from_occ}")
        print(f"    excluded_object_count: {check['excluded_object_count']}")
        if total_excluded_from_occ != check['excluded_object_count']:
            print(f"    *** MISMATCH: excluded_object_count should be {total_excluded_from_occ} ***")
    print()

print()
print('=== EXCLUDED CLASS COUNTS (PER-IMAGE) ===')
# Sum up all excluded classes from per-image original_class_counts
total_d43 = sum(delta_occ.get('D43', 0) for delta_occ in 
                [{k: v - prev.get(k, 0) for k, v in img['original_class_counts'].items()} 
                 for img, prev in zip(manifest, [{}] + [img['original_class_counts'] for img in manifest[:-1]])])
total_d44 = sum(delta_occ.get('D44', 0) for delta_occ in 
                [{k: v - prev.get(k, 0) for k, v in img['original_class_counts'].items()} 
                 for img, prev in zip(manifest, [{}] + [img['original_class_counts'] for img in manifest[:-1]])])
total_d50 = sum(delta_occ.get('D50', 0) for delta_occ in 
                [{k: v - prev.get(k, 0) for k, v in img['original_class_counts'].items()} 
                 for img, prev in zip(manifest, [{}] + [img['original_class_counts'] for img in manifest[:-1]])])

print(f'Total D43 (road marking damage - white line blur) objects: {total_d43}')
print(f'Total D44 (road marking damage - crosswalk blur) objects: {total_d44}')
print(f'Total D50 (annotation artifact) objects: {total_d50}')
print(f'Sum of all excluded objects: {total_d43 + total_d44 + total_d50}')
print(f'Global excluded_object_count: {data["statistics"]["excluded_object_count"]}')
print(f'Match: {total_d43 + total_d44 + total_d50 == data["statistics"]["excluded_object_count"]}')

print()
print('=== MERGE COUNTS (D01->D00, D11->D10) ===')
total_d01 = sum(delta_occ.get('D01', 0) for delta_occ in 
                [{k: v - prev.get(k, 0) for k, v in img['original_class_counts'].items()} 
                 for img, prev in zip(manifest, [{}] + [img['original_class_counts'] for img in manifest[:-1]])])
total_d11 = sum(delta_occ.get('D11', 0) for delta_occ in 
                [{k: v - prev.get(k, 0) for k, v in img['original_class_counts'].items()} 
                 for img, prev in zip(manifest, [{}] + [img['original_class_counts'] for img in manifest[:-1]])])

print(f'Total D01 objects (to be merged to D00): {total_d01}')
print(f'Total D11 objects (to be merged to D10): {total_d11}')
print(f'Global d01_to_d00_count: {data["statistics"]["d01_to_d00_count"]}')
print(f'Global d11_to_d10_count: {data["statistics"]["d11_to_d10_count"]}')
print(f'D01 match: {total_d01 == data["statistics"]["d01_to_d00_count"]}')
print(f'D11 match: {total_d11 == data["statistics"]["d11_to_d10_count"]}')

print()
print('=== VALIDATE: Per-image excluded_object_count consistency ===')
# For each image, excluded_object_count should equal sum of excluded classes in that image's original_class_counts
mismatches = []
for img in manifest:
    fname = img['source_image_path'].split('\\\\')[-1]
    occ = img['original_class_counts']
    excluded_from_occ = sum(v for k, v in occ.items() if k in ['D43', 'D44', 'D50'])
    actual_excluded = img['excluded_object_count']
    if excluded_from_occ != actual_excluded:
        mismatches.append((fname, excluded_from_occ, actual_excluded))

print(f'Per-image excluded_object_count mismatches: {len(mismatches)}')
if mismatches[:5]:
    print('First 5 mismatches:')
    for fname, expected, actual in mismatches[:5]:
        print(f'  {fname}: expected {expected}, got {actual}')

print()
print('=== EXTRA: Check why excluded_object_count is 0 for all images ===')
print('Looking at the first few images:')
for i, img in enumerate(manifest[:5]):
    fname = img['source_image_path'].split('\\\\')[-1]
    occ = img['original_class_counts']
    excluded_from_occ = sum(v for k, v in occ.items() if k in ['D43', 'D44', 'D50'])
    print(f'  {fname}: original_class_counts={occ}, excluded_from_occ={excluded_from_occ}, excluded_object_count={img["excluded_object_count"]}')