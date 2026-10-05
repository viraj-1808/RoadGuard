from datasets import load_from_disk

ds = load_from_disk(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022")

# Check China_Drone_000009 in train
train = ds['train']
for i in range(len(train)):
    if train[i]['file_name'] == 'China_Drone_000009.jpg':
        print(f"Found: {train[i]['file_name']}: objects={train[i]['objects']}")
        break

# Check all unique category values in the dataset
all_cats = set()
for split in ['train', 'validation', 'test']:
    for ex in ds[split]:
        for cat in ex['objects']['categories']:
            all_cats.add(cat)
print(f"All unique category values: {sorted(all_cats)}")

# Count per class
from collections import Counter
cat_counts = Counter()
for split in ['train', 'validation', 'test']:
    for ex in ds[split]:
        for cat in ex['objects']['categories']:
            cat_counts[cat] += 1
print(f"Category counts: {dict(sorted(cat_counts.items()))}")