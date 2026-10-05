import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== 5. IMAGES WITH ONLY pothole in final_class_counts ===')
pothole_only = []
for img in manifest:
    fcc = img['final_class_counts']
    if len(fcc) == 1 and 'pothole' in fcc:
        pothole_only.append(img)

print(f'Total images with only pothole: {len(pothole_only)}')
print()
pothole_counts = [img['final_class_counts']['pothole'] for img in pothole_only]
print(f'Pothole count range: min={min(pothole_counts)}, max={max(pothole_counts)}')
print(f'Average pothole per image: {sum(pothole_counts)/len(pothole_counts):.2f}')
print()
print('Pothole-only images:')
for img in pothole_only:
    fname = img['source_image_path'].split('\\')[-1]
    print(f'  {fname}: pothole={img["final_class_counts"]["pothole"]}, original={img["original_class_counts"]}')