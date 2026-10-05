import os
import json
from collections import Counter
import glob

label_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\yolo_rdd2022_india\labels\test'
images_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\yolo_rdd2022_india\images\test'

# Check a few label files
label_files = glob.glob(os.path.join(label_dir, '*.txt'))[:3]
print('Label file format sample:')
for lf in label_files:
    fname = os.path.basename(lf)
    print(f'{fname}:')
    with open(lf, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:3]):
            print(f'  Line {i+1}: {line.strip()}')
    if len(lines) > 3:
        print(f'  ... and {len(lines)-3} more lines')
    print()

# Count total objects and per image
gt_counts = []
gt_per_img = Counter()
all_gt_objects = []
for lf in glob.glob(os.path.join(label_dir, '*.txt')):
    img_id = os.path.basename(lf).replace('.txt', '')
    with open(lf, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
        gt_per_img[img_id] = len(lines)
        gt_counts.append(len(lines))
        for line in lines:
            parts = line.split()
            class_id = int(parts[0])
            all_gt_objects.append((img_id, class_id))

print(f'Ground truth objects: {sum(gt_counts)} total')
print(f'Per image: min={min(gt_counts)}, max={max(gt_counts)}, mean={sum(gt_counts)/len(gt_counts):.1f}')
print(f'GT class distribution: {dict(Counter(c for _, c in all_gt_objects))}')

# Compare with manifest
manifest_path = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\normalized_rdd2022_india\split_manifest_fixed.json'
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

test_from_manifest = [k for k, v in manifest['assignments'].items() if v == 'test']
print(f'Test images from manifest: {len(test_from_manifest)}')
print(f'Test images from filesystem: {len([f for f in os.listdir(images_dir) if f.endswith(".jpg")])}')

# Check if they match
fs_images = set(os.path.splitext(f)[0] for f in os.listdir(images_dir) if f.endswith('.jpg'))
manifest_images = set(test_from_manifest)
print(f'Filesystem-manifest match: {fs_images == manifest_images}')
if fs_images != manifest_images:
    only_fs = fs_images - manifest_images
    only_man = manifest_images - fs_images
    print(f'  Only in FS: {len(only_fs)}')
    print(f'  Only in manifest: {len(only_man)}')

# Check GT images vs pred images
pred_path = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_dataset_v2_split_v2\test_eval\predictions.json'
with open(pred_path, 'r') as f:
    preds = json.load(f)
pred_images = set(p['image_id'] for p in preds)
print(f'GT images: {len(gt_per_img)}')
print(f'Pred images: {len(pred_images)}')
print(f'Intersection: {len(set(gt_per_img.keys()) & pred_images)}')
