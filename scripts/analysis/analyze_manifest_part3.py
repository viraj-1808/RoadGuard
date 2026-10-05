import json
from collections import Counter

data = json.load(open('experiments/dataset/normalized_rdd2022_india/manifest.json'))
manifest = data['image_manifest']

print('=== 4. IMAGES WITH transverse_crack ===')
tc_images = []
for img in manifest:
    fcc = img['final_class_counts']
    if 'transverse_crack' in fcc and fcc['transverse_crack'] > 0:
        tc_images.append(img)

print(f'Total images with transverse_crack: {len(tc_images)}')
print()
# Get image names and counts
tc_data = []
for img in tc_images:
    fname = img['source_image_path'].split('\\')[-1]
    fcc = img['final_class_counts']
    tc_data.append((fname, fcc))
    print(f'  {fname}: {fcc}')

print()
print('--- Summary of transverse_crack images ---')
tc_counts = [fcc.get('transverse_crack', 0) for _, fcc in tc_data]
print(f'Transverse_crack counts per image: min={min(tc_counts)}, max={max(tc_counts)}, avg={sum(tc_counts)/len(tc_counts):.2f}')
print(f'Images with 1 transverse_crack: {sum(1 for x in tc_counts if x==1)}')
print(f'Images with 2 transverse_crack: {sum(1 for x in tc_counts if x==2)}')
print(f'Images with 3 transverse_crack: {sum(1 for x in tc_counts if x==3)}')

# Count total transverse_crack objects
total_tc = sum(fcc.get('transverse_crack', 0) for _, fcc in tc_data)
print(f'Total transverse_crack objects: {total_tc}')
print(f'Expected: 30')
print(f'Match: {total_tc == 30}')