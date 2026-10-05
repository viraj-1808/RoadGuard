import os
import json
from datasets import load_dataset
from huggingface_hub import snapshot_download
import hashlib
from datetime import datetime

# Configuration
REPO_ID = "dronefreak/RDD2022"
REVISION = "d597e2962458f7242a72aaa1b7909118d40f5d29"
OUTPUT_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022"
REPORT_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\overnight\dataset_b_hf_gate"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

print(f"Starting download of {REPO_ID}@{REVISION}")
print(f"Output directory: {OUTPUT_DIR}")

try:
    # Method 1: Use snapshot_download for full repo
    print("Downloading dataset using snapshot_download...")
    downloaded_path = snapshot_download(
        repo_id=REPO_ID,
        revision=REVISION,
        local_dir=OUTPUT_DIR,
        local_dir_use_symlinks=False
    )
    print(f"Download completed to: {downloaded_path}")
    
    # Also try loading with datasets library to verify
    print("Verifying with datasets library...")
    ds = load_dataset(REPO_ID, revision=REVISION)
    print(f"Dataset loaded: {ds}")
    print(f"Splits: {list(ds.keys())}")
    for split in ds.keys():
        print(f"  {split}: {len(ds[split])} examples")
        
except Exception as e:
    print(f"Error during download: {e}")
    import traceback
    traceback.print_exc()

print("Download attempt finished.")