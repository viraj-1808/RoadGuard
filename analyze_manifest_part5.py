import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== 6. CLASS COMBINATION PATTERNS ===')
combo_counter = Counter()
for img in manifest:
    fcc = tuple(sorted(img['final_class_counts'].keys()))
    combo_counter[fcc] += 1

print('All unique class combination patterns:')
for combo, count in combo_counter.most_common():
    print(f'  {combo}: {count} images')

print()
print('=== COMBINATION ANALYSIS ===')
# Group by pattern type
for combo, count in combo_counter.items():
    if len(combo) == 1:
        print(f'Single-class pattern {combo}: {count} images')
    elif len(combo) == 2:
        print(f'Two-class pattern {combo}: {count} images')
    elif len(combo) == 3:
        print(f'Three-class pattern {combo}: {count} images')
    elif len(combo) == 4:
        print(f'Four-class pattern {combo}: {count} images')
    else:
        print(f'Other pattern {combo}: {count} images')

print()
print('=== DETAILED BREAKDOWN ===')
single_class = {k:v for k,v in combo_counter.items() if len(k)==1}
two_class = {k:v for k,v in combo_counter.items() if len(k)==2}
three_class = {k:v for k,v in combo_counter.items() if len(k)==3}
four_plus = {k:v for k,v in combo_counter.items() if len(k)>=4}

print(f'Total images: {len(manifest)}')
print(f'Single-class patterns: {len(single_class)}')
print(f'Two-class patterns: {len(two_class)}')
print(f'Three-class patterns: {len(three_class)}')
print(f'Four-class patterns: {len(four_plus)}')

print()
print('Single-class details:')
for combo, count in single_class.items():
    print(f'  {combo}: {count} images')

print()
print('Two-class details:')
for combo, count in two_class.items():
    print(f'  {combo}: {count} images')

print()
print('Three-class details:')
for combo, count in three_class.items():
    print(f'  {combo}: {count} images')

print()
print('Four-class details:')
for combo, count in four_plus.items():
    print(f'  {combo}: {count} images')