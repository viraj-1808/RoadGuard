import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== 8. excluded_object_count PATTERNS ===')
excl_counts = Counter()
for img in manifest:
    excl_counts[img['excluded_object_count']] += 1

print('Distribution of excluded_object_count:')
for k in sorted(excl_counts.keys()):
    print(f'  {k}: {excl_counts[k]} images')

print()
print('=== 7. TRANSFORMATION RULES SECTION ===')
print(f"transformation_version: {data.get('transformation_version')}")
print()
print('class_mapping:')
for class_key, mapping in data['transformation_rules']['class_mapping'].items():
    if isinstance(mapping, dict):
        print(f'  {class_key}:')
        for k,v in mapping.items():
            if k == 'action':
                print(f'    {k}: {v}')
            else:
                print(f'    {k}: {v}')
    else:
        print(f'  {class_key}: {mapping}')

print()
print('=== EXTRA: IMAGES WITH EXCLUDED CLASSES (D43, D44, D50) ===')
excluded_class_images = []
for img in manifest:
    occ = img['original_class_counts']
    has_excluded = any(k in occ for k in ['D43','D44','D50'])
    if has_excluded:
        excluded_class_images.append(img)

print(f'Total images with D43/D44/D50 in original counts: {len(excluded_class_images)}')

if excluded_class_images:
    print()
    print('Examples with excluded classes:')
    for img in excluded_class_images[:10]:
        fname = img['source_image_path'].split('\\')[-1]
        occ = img['original_class_counts']
        fcc = img['final_class_counts']
        print(f'  {fname}: original={occ}, final={fcc}')
    
    # Check if these match excluded_object_count
    print()
    print('Checking excluded_object_count consistency:')
    mismatches = []
    for img in excluded_class_images:
        original_total = sum(img['original_class_counts'].values())
        final_total = sum(img['final_class_counts'].values())
        calculated_excluded = original_total - final_total
        actual_excluded = img['excluded_object_count']
        if calculated_excluded != actual_excluded:
            mismatches.append((img['source_image_path'].split('\\')[-1], actual_excluded, calculated_excluded))
    
    if mismatches:
        print(f'  MISMATCHES FOUND: {len(mismatches)}')
        for m in mismatches[:5]:
            print(f'    {m}')
    else:
        print('  All excluded_object_count values match calculated differences')
else:
    print('  No images with D43/D44/D50 in original counts')

print()
print('=== EXTRA: CHECK FOR TRANSFORMATION EFFECTS (D01->D00, D11->D10) ===')
# Check if there are any D01 or D11 in original counts
d01_images = []
d11_images = []
for img in manifest:
    occ = img['original_class_counts']
    if 'D01' in occ:
        d01_images.append(img)
    if 'D11' in occ:
        d11_images.append(img)

print(f'Images with D01 (longitudinal subclasses): {len(d01_images)}')
print(f'Images with D11 (transverse subclasses): {len(d11_images)}')

if d01_images:
    print()
    print('D01 examples:')
    for img in d01_images[:5]:
        fname = img['source_image_path'].split('\\')[-1]
        occ = img['original_class_counts']
        fcc = img['final_class_counts']
        print(f'  {fname}: original={occ}, final={fcc}')

if d11_images:
    print()
    print('D11 examples:')
    for img in d11_images[:5]:
        fname = img['source_image_path'].split('\\')[-1]
        occ = img['original_class_counts']
        fcc = img['final_class_counts']
        print(f'  {fname}: original={occ}, final={fcc}')