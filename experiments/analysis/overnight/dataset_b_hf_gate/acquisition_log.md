# RDD2022 Dataset Acquisition Log

## Session Info
- **Timestamp**: 2026-10-02T17:55:44.904817+00:00
- **Repository**: dronefreak/RDD2022
- **Revision**: d597e2962458f7242a72aaa1b7909118d40f5d29
- **Target directory**: `C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022`
- **Method**: Plain HTTPS via `resolve/{REV}/` URLs (snapshot_download fails with 401 Xet-token error)

## Step 1 — Enumeration & Manifests
- **Image manifest**: `_manifest_images.json` (38398 entries)
- **Label manifest**: `_manifest_labels.json` (38385 entries)
- Expected images: 38385, actual: 38398 — **WARNING: mismatch!**
- Expected labels: 38385, actual: 38385 — matches.

## Step 2 — Single File Verification
- Downloaded `data/images/train/shard_000/China_Drone_000001.jpg`
- Expected size: 65334 bytes
- Status: verified
- Label contents (`China_Drone_000001.txt`) printed to stdout.

## Step 3 — Bulk Download
- **Images**: 0 new, 0 skipped, 0 failed, 0 bytes
- **Labels**: 0 new, 0 skipped, 0 failed, 0 bytes
- **Total bytes downloaded this session**: 0
- Concurrency: 5 threads, 6 retries with exponential backoff
- Image download timed out: False
- Label download timed out: False

## Step 4 — Final Report
- **Images expected**: 38385
- **Images on disk**: 38385
- **Labels expected**: 38385
- **Labels on disk**: 38385
- **`data/images/valid/` exists**: True
- **Valid image count**: 5758
- **Persistently failed files**: 0

### Per-split image counts (on disk)
- test: 5758 .jpg files
- train: 26869 .jpg files
- valid: 5758 .jpg files

### Per-split label counts (on disk)
- test: 5758 .txt files
- train: 26869 .txt files
- valid: 5758 .txt files

### Failed files (persistently)
None.

### Total bytes downloaded (this session): 0
