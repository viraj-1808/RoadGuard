import os
import time
import traceback
from pathlib import Path
from huggingface_hub import snapshot_download, hf_hub_download

REPO_ID = "dronefreak/RDD2022"
REVISION = "d597e2962458f7242a72aaa1b7909118d40f5d29"
OUTPUT_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022"

base = Path(OUTPUT_DIR)

# Count current images
train_images = list((base / "data" / "images" / "train").rglob("*.jpg"))
test_images = list((base / "data" / "images" / "test").rglob("*.jpg"))
print(f"Current images: train={len(train_images)}, test={len(test_images)}")
print(f"Missing train: {26869 - len(train_images)}, Missing valid: 5758, Missing test: 0")

# Method 1: snapshot_download with repo_type=dataset and use_xet=False
print("\n=== METHOD 1: snapshot_download with repo_type=dataset ===")
try:
    snapshot_download(
        repo_id=REPO_ID,
        revision=REVISION,
        repo_type="dataset",
        local_dir=OUTPUT_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print("Method 1 succeeded!")

    # Recount
    train_images = list((base / "data" / "images" / "train").rglob("*.jpg"))
    test_images = list((base / "data" / "images" / "test").rglob("*.jpg"))
    valid_dir = base / "data" / "images" / "valid"
    valid_images = list(valid_dir.rglob("*.jpg")) if valid_dir.exists() else []
    print(f"After Method 1: train={len(train_images)}, valid={len(valid_images)}, test={len(test_images)}")
except Exception as e:
    print(f"Method 1 failed: {e}")

# Method 2: Download individual files
print("\n=== METHOD 2: Download individual files ===")
try:
    # Try downloading a single file as test
    test_file = hf_hub_download(
        repo_id=REPO_ID,
        revision=REVISION,
        filename="data/images/train/shard_000/United_000001.jpg",
        repo_type="dataset",
        local_dir=OUTPUT_DIR,
    )
    print(f"Method 2 test download succeeded: {test_file}")
except Exception as e:
    print(f"Method 2 failed: {e}")
    traceback.print_exc()

# Method 3: Try without revision
print("\n=== METHOD 3: snapshot_download without revision ===")
try:
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=OUTPUT_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print("Method 3 succeeded!")
except Exception as e:
    print(f"Method 3 failed: {e}")
    traceback.print_exc()

# Final state
print("\n=== FINAL STATE ===")
train_dir = base / "data" / "images" / "train"
valid_dir = base / "data" / "images" / "valid"
test_dir = base / "data" / "images" / "test"

if train_dir.exists():
    print(f"train: {len(list(train_dir.rglob('*.jpg')))} images")
if valid_dir.exists():
    print(f"valid: {len(list(valid_dir.rglob('*.jpg')))} images")
else:
    print("valid: directory not found")
if test_dir.exists():
    print(f"test: {len(list(test_dir.rglob('*.jpg')))} images")

# Check labels
labels_dir = base / "data" / "labels"
if labels_dir.exists():
    for split in ['train', 'valid', 'test']:
        split_dir = labels_dir / split
        if split_dir.exists():
            count = len(list(split_dir.rglob("*.txt")))
            print(f"labels/{split}: {count} txt files")
        else:
            print(f"labels/{split}: not found")
else:
    print("labels: directory not found")