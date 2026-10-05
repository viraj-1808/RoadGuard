import os
import sys
import json
import hashlib
import traceback
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
import huggingface_hub

REPO_ID = "dronefreak/RDD2022"
REVISION = "d597e2962458f7242a72aaa1b7909118d40f5d29"
SAVE_DIR = PROJECT_ROOT / "experiments/dataset/raw_hf_rdd2022"
REPORT_PATH = PROJECT_ROOT / "experiments/analysis/overnight/dataset_b_hf_gate/candidate_identity.md"

download_timestamp = datetime.utcnow().isoformat() + "Z"
errors = []

def sha256_file(filepath, chunk_size=8192):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

print(f"=== Download: {REPO_ID} rev={REVISION} ===")
print(f"Timestamp: {download_timestamp}")

try:
    ds = load_dataset(REPO_ID, revision=REVISION, token=False)
    print(f"Dataset loaded: {ds}")
except Exception as e:
    err_msg = f"Download failed: {e}\n{traceback.format_exc()}"
    print(err_msg)
    errors.append(err_msg)
    with open(REPORT_PATH, "w") as f:
        f.write(f"# Dataset Download Failed\n\n{err_msg}\n")
    sys.exit(1)

print("Saving dataset...")
ds.save_to_disk(SAVE_DIR)

# Gather info
file_manifest = []
total_size = 0
sha256_checksums = {}

for root, dirs, files in os.walk(SAVE_DIR):
    for fname in files:
        fpath = os.path.join(root, fname)
        size = os.path.getsize(fpath)
        total_size += size
        rel = os.path.relpath(fpath, SAVE_DIR)
        file_manifest.append({"path": rel, "size": size})
        if size < 50 * 1024 * 1024:
            try:
                sha256_checksums[rel] = sha256_file(fpath)
            except Exception as e:
                sha256_checksums[rel] = f"ERROR: {e}"

print(f"Total size: {total_size} bytes ({total_size / (1024*1024):.2f} MB)")
print(f"Files: {len(file_manifest)}")

# Dataset info
dataset_info = {
    "splits": dict(ds),
    "features": dict(ds.features) if hasattr(ds, 'features') else None,
    "num_rows": {k: len(v) for k, v in ds.items()},
}
print(f"Splits: {dataset_info['splits']}")
print(f"Num rows: {dataset_info['num_rows']}")

# Fetch dataset card / repo info
try:
    repo_info = huggingface_hub.hf_hub_download(repo_id=REPO_ID, filename="README.md", revision=REVISION, repo_type="dataset")
    with open(repo_info) as f:
        dataset_card = f.read()
except Exception as e:
    dataset_card = f"Could not fetch: {e}"
    errors.append(f"Dataset card fetch error: {e}")

# Try to get repo metadata
try:
    api = huggingface_hub.HfApi()
    repo_data = api.repo_info(repo_id=REPO_ID, repo_type="dataset", revision=REVISION)
    repo_metadata = {
        "id": repo_data.id,
        "sha": repo_data.sha,
        "lastModified": str(repo_data.lastModified),
        "tags": repo_data.tags,
    }
except Exception as e:
    repo_metadata = {"error": str(e)}
    errors.append(f"Repo info error: {e}")

# Inspect first sample to find structure
sample = ds["train"][0] if "train" in ds else None
if sample:
    sample_keys = list(sample.keys())
    print(f"Sample keys: {sample_keys}")
    # Check for images/labels
    for k in sample_keys:
        v = sample[k]
        print(f"  {k}: type={type(v).__name__}, value={v}")

# Save intermediate results for report generation
results = {
    "download_timestamp": download_timestamp,
    "repo_id": REPO_ID,
    "revision": REVISION,
    "total_size": total_size,
    "total_size_mb": total_size / (1024*1024),
    "file_manifest": file_manifest,
    "sha256_checksums": sha256_checksums,
    "dataset_info": dataset_info,
    "dataset_card": dataset_card,
    "repo_metadata": repo_metadata,
    "errors": errors,
    "sample": sample,
}

with open(os.path.join(SAVE_DIR, "_inspection_results.json"), "w") as f:
    json.dump(results, f, indent=2, default=str)

print("Done. Inspection results saved.")
