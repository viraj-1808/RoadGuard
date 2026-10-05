import random
from datasets import load_from_disk
from collections import Counter
import os
import glob

# Load dataset
ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")
train_ds = ds['train']
print(f"Train split: {len(train_ds)} examples")

# Build filename -> Arrow record map for train
arrow_map = {}
for ex in train_ds:
    arrow_map[ex['file_name']] = ex['objects']

# Find repo label files for train using glob (faster)
labels_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022\data\labels\train"
label_files = glob.glob(os.path.join(labels_root, "shard_*", "*.txt"))
print(f"Train repo label files found: {len(label_files)}")

# Simple random sample of 500
random.seed(42)
sampled = random.sample(label_files, 500)
print(f"Random sampled {len(sampled)} train images")

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
    
    arrow_obj = arrow_map.get(img_name)
    if arrow_obj is None:
        absent_labels += 1
        continue
    
    arrow_classes = arrow_obj['categories']
    
    if repo_classes == arrow_classes:
        agreement_seq += 1
    
    if Counter(repo_classes) == Counter(arrow_classes):
        agreement_multiset += 1
    
    total_compared += 1

print(f"\n=== STEP 2 RESULTS (Train split, n={total_compared}) ===")
print(f"Sequence agreement: {agreement_seq}/{total_compared} = {agreement_seq/total_compared*100:.2f}%")
print(f"Multiset agreement: {agreement_multiset}/{total_compared} = {agreement_multiset/total_compared*100:.2f}%")
print(f"Class IDs outside {{0,1,2,3}}: {dict(class_id_out_of_range)}")
print(f"Empty label files (valid negatives): {empty_labels}")
print(f"Absent label files (structural error): {absent_labels}")
print(f"BBox token count issues (not 5 tokens): {bbox_token_issues}")

# Show mismatches
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