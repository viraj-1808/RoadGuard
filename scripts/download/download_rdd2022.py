#!/usr/bin/env python
"""Download dronefreak/RDD2022 dataset from Hugging Face."""
import os
import sys
import time
from huggingface_hub import snapshot_download

TARGET_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022"

def main():
    start = time.time()
    print(f"Starting download to: {TARGET_DIR}", flush=True)

    result = snapshot_download(
        repo_id="dronefreak/RDD2022",
        repo_type="dataset",
        local_dir=TARGET_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,
        max_workers=8,
        tolerate_scan_warning=True,
    )

    elapsed = time.time() - start
    print(f"Download completed in {elapsed:.1f}s", flush=True)
    print(f"Result path: {result}", flush=True)

    # Count final files
    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(result):
        for f in files:
            total_files += 1
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
            except OSError:
                pass

    print(f"Total files: {total_files}", flush=True)
    print(f"Total size: {total_size / (1024*1024*1024):.2f} GB", flush=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())