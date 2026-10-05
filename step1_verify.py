import random
from datasets import load_from_disk
from PIL import Image
import os

# Load dataset
ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")
test_ds = ds['test']
print(f"Test split: {len(test_ds)} examples")

# Count class ids in test split
from collections import Counter
test_cat_counts = Counter()
for ex in test_ds:
    for cat in ex['objects']['categories']:
        test_cat_counts[cat] += 1
print(f"Test Arrow category counts: {dict(sorted(test_cat_counts.items()))}")

# Build filename -> Arrow record map for test
arrow_map = {}
for ex in test_ds:
    arrow_map[ex['file_name']] = ex['objects']

# Find repo label files for test
labels_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022\data\labels\test"
label_files = []
for shard in os.listdir(labels_root):
    shard_path = os.path.join(labels_root, shard)
    if os.path.isdir(shard_path):
        for f in os.listdir(shard_path):
            if f.endswith('.txt'):
                label_files.append(os.path.join(shard_path, f))

print(f"Test repo label files found: {len(label_files)}")

# Sample 200 deterministically (seed 42)
random.seed(42)
sampled = random.sample(label_files, min(200, len(label_files)))
print(f"Sampled {len(sampled)} test images")

# Compare
agreement_seq = 0
agreement_multiset = 0
total_compared = 0
class_id_out_of_range = Counter()
empty_labels = 0
absent_labels = 0
bbox_token_issues = 0

for label_path in sampled:
    fname = os.path.basename(label_path)
    # Map label file to image name
    # Label could be X.jpg.txt or X.txt
    if fname.endswith('.jpg.txt'):
        img_name = fname[:-4]  # remove .txt
    else:
        img_name = fname[:-4] + '.jpg'  # add .jpg
    
    # Read repo label
    repo_classes = []
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                bbox_token_issues += 1
                continue
            try:
                class_id = int(float(parts[0]))
                repo_classes.append(class_id)
                if class_id not in {0, 1, 2, 3}:
                    class_id_out_of_range[class_id] += 1
            except ValueError:
                bbox_token_issues += 1
    
    if not repo_classes:
        empty_labels += 1
    
    # Get Arrow record
    arrow_obj = arrow_map.get(img_name)
    if arrow_obj is None:
        absent_labels += 1
        continue
    
    arrow_classes = arrow_obj['categories']
    
    # Compare sequence (order-sensitive)
    if repo_classes == arrow_classes:
        agreement_seq += 1
    
    # Compare multiset (order-insensitive)
    if Counter(repo_classes) == Counter(arrow_classes):
        agreement_multiset += 1
    
    total_compared += 1

print(f"\n=== STEP 1 RESULTS (Test split, n={total_compared}) ===")
print(f"Sequence agreement: {agreement_seq}/{total_compared} = {agreement_seq/total_compared*100:.2f}%")
print(f"Multiset agreement: {agreement_multiset}/{total_compared} = {agreement_multiset/total_compared*100:.2f}%")
print(f"Class IDs outside {{0,1,2,3}}: {dict(class_id_out_of_range)}")
print(f"Empty label files (valid negatives): {empty_labels}")
print(f"Absent label files (structural error): {absent_labels}")
print(f"BBox token count issues (not 5 tokens): {bbox_token_issues}")

# Also show a few mismatches for debugging
print("\n--- Sample mismatches ---")
mismatches_shown = 0
for label_path in sampled:
    if mismatches_shown >= 5:
        break
    fname = os.path.basename(label_path)
    if fname.endswith('.jpg.txt'):
        img_name = fname[:-4]
    else:
        img_name = fname[:-4] + '.jpg'
    
    repo_classes = []
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 5:
                try:
                    class_id = int(float(parts[0]))
                    repo_classes.append(class_id)
                except:
                    pass
    
    arrow_obj = arrow_map.get(img_name)
    if arrow_obj is None:
        continue
    arrow_classes = arrow_obj['categories']
    
    if repo_classes != arrow_classes:
        print(f"  {img_name}: repo={repo_classes}, arrow={arrow_classes}")
        mismatches_shown += 1