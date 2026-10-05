import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
stats = data['statistics']
manifest = data['image_manifest']

print('=== 1. GLOBAL TOTALS ===')
print(f'image_count: {stats["output_image_count"]}')
print(f'original_object_count: {stats["original_object_count"]}')
print(f'retained_object_count: {stats["retained_object_count"]}')
print(f'excluded_object_count: {stats["excluded_object_count"]}')
print()
print('--- final_class_counts (object totals per class) ---')
for k,v in stats['final_class_counts'].items():
    print(f'  {k}: {v}')
print()
print('--- original_class_counts ---')
for k,v in stats['original_class_counts'].items():
    print(f'  {k}: {v}')
print()
print('--- other stats ---')
for k in ['d01_to_d00_count','d11_to_d10_count','d43_exclusions','d44_exclusions','d50_exclusions','images_becoming_empty','skipped_image_count','empty_annotation_count','invalid_annotation_count']:
    print(f'  {k}: {stats[k]}')