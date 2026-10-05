import os
import glob
from collections import Counter
from datasets import load_from_disk

# Load validation split Arrow counts
ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")
val_ds = ds['validation']

arrow_counts = Counter()
for ex in val_ds:
    for cat in ex['objects']['categories']:
        arrow_counts[cat] += 1
print(f"Arrow validation category counts: {dict(sorted(arrow_counts.items()))}")

# Recount from ALL repo .txt files in validation split
labels_root = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022\data\labels\valid"
label_files = glob.glob(os.path.join(labels_root, "shard_*", "*.txt"))
print(f"Validation repo label files: {len(label_files)}")

repo_counts = Counter()
class_id_out_of_range = Counter()
empty_labels = 0
bbox_token_issues = 0
total_boxes = 0

for i, label_path in enumerate(label_files):
    with open(label_path, 'r') as f:
        has_content = False
        for line in f:
            line = line.strip()
            if not line:
                continue
            has_content = True
            parts = line.split()
            if len(parts) != 5:
                bbox_token_issues += 1
                continue
            try:
                class_id = int(float(parts[0]))
                repo_counts[class_id] += 1
                total_boxes += 1
                if class_id not in {0, 1, 2, 3}:
                    class_id_out_of_range[class_id] += 1
            except ValueError:
                bbox_token_issues += 1
        if not has_content:
            empty_labels += 1

print(f"\n=== Validation split, ALL {len(label_files)} files ===")
print(f"Repo label class counts: {dict(sorted(repo_counts.items()))}")
print(f"Arrow category counts:   {dict(sorted(arrow_counts.items()))}")
print(f"Match: {dict(repo_counts) == dict(arrow_counts)}")
print(f"Total boxes in repo labels: {total_boxes}")
print(f"Total boxes in Arrow: {sum(arrow_counts.values())}")
print(f"Class IDs outside {{0,1,2,3}}: {dict(class_id_out_of_range)}")
print(f"Empty label files (valid negatives): {empty_labels}")
print(f"BBox token count issues (not 5 tokens): {bbox_token_issues}")