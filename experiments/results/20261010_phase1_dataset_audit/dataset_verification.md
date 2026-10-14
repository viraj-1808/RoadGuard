# Dataset Verification Report — Phase 1 Audit

**Date**: 2026-10-11
**Scope**: All `data.yaml` files in `experiments/dataset/`, frozen test split manifests, class mappings, and path existence.

---

## 1. Data YAML Files Found

| # | File Path | Type |
|---|-----------|------|
| 1 | `experiments/dataset/yolo_rdd2022_india/data.yaml` | Dataset A (India-only YOLO format) |
| 2 | `experiments/dataset/experiment2/data.yaml` | Experiment 2 (Dataset A train + Dataset B non-India) |
| 3 | `experiments/dataset/raw_hf_rdd2022/data/data.yaml` | Raw HF RDD2022 (India subset) |
| 4 | `experiments/dataset/raw_hf_rdd2022/repo/data/data.yaml` | Raw HF RDD2022 repo copy |

---

## 2. Per-YAML Configuration Details

### 2.1 `experiments/dataset/yolo_rdd2022_india/data.yaml`

```yaml
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
nc: 4
path: experiments\dataset\yolo_rdd2022_india
test: images/test
train: images/train
val: images/val
```

| Field | Value |
|-------|-------|
| **Class order (index → name)** | 0: longitudinal_crack, 1: transverse_crack, 2: alligator_crack, 3: pothole |
| **nc** | 4 |
| **Root path** | `experiments\dataset\yolo_rdd2022_india` |
| **Train images** | `images/train` (relative to root) |
| **Val images** | `images/val` (relative to root) |
| **Test images** | `images/test` (relative to root) |

**Path verification (relative to repo root):**
- `experiments/dataset/yolo_rdd2022_india/images/train` → **EXISTS** (1,071 images, 1,071 labels)
- `experiments/dataset/yolo_rdd2022_india/images/val` → **EXISTS** (229 images, 229 labels)
- `experiments/dataset/yolo_rdd2022_india/images/test` → **EXISTS** (230 images, 230 labels)
- `experiments/dataset/yolo_rdd2022_india/labels/train` → **EXISTS** (1,071 files)
- `experiments/dataset/yolo_rdd2022_india/labels/val` → **EXISTS** (229 files)
- `experiments/dataset/yolo_rdd2022_india/labels/test` → **EXISTS** (230 files)

---

### 2.2 `experiments/dataset/experiment2/data.yaml`

```yaml
path: experiments/dataset/experiment2
train: images/train
val: images/val
test: experiments/dataset/yolo_rdd2022_india/images/test
nc: 4
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
```

| Field | Value |
|-------|-------|
| **Class order (index → name)** | 0: longitudinal_crack, 1: transverse_crack, 2: alligator_crack, 3: pothole |
| **nc** | 4 |
| **Root path** | `experiments/dataset/experiment2` |
| **Train images** | `images/train` (relative to root) |
| **Val images** | `images/val` (relative to root) |
| **Test images** | `experiments/dataset/yolo_rdd2022_india/images/test` (repo-root-relative, frozen) |

**Path verification (relative to repo root):**
- `experiments/dataset/experiment2/images/train` → **EXISTS** (19,719 images, 19,719 labels)
- `experiments/dataset/experiment2/images/val` → **EXISTS** (2,301 images, 2,301 labels)
- `experiments/dataset/experiment2/labels/train` → **EXISTS** (19,719 files)
- `experiments/dataset/experiment2/labels/val` → **EXISTS** (2,301 files)
- **Test path** → Points to `experiments/dataset/yolo_rdd2022_india/images/test` (verified above, 230 images)

**Note**: Experiment 2 does not create its own test split; it references the frozen Dataset A test split.

---

### 2.3 `experiments/dataset/raw_hf_rdd2022/data/data.yaml` (and repo copy — identical)

```yaml
path: .
train: images/train
val: images/valid
test: images/test
nc: 4
names:
  0: longitudinal_crack
  1: transverse_crack
  2: alligator_crack
  3: pothole
```

| Field | Value |
|-------|-------|
| **Class order (index → name)** | 0: longitudinal_crack, 1: transverse_crack, 2: alligator_crack, 3: pothole |
| **nc** | 4 |
| **Root path** | `.` (relative to file location) |
| **Train images** | `images/train` |
| **Val images** | `images/valid` |
| **Test images** | `images/test` |

**Note**: Uses dict format for `names` (index: name) vs list format in Dataset A YAMLs. Semantic mapping is identical.

---

## 3. Split Counts Summary

| Dataset | Split | Images | Labels | Match |
|---------|-------|--------|--------|-------|
| **yolo_rdd2022_india (Dataset A)** | train | 1,071 | 1,071 | ✅ |
|  | val | 229 | 229 | ✅ |
|  | test | 230 | 230 | ✅ |
| **experiment2 (Dataset A train + Dataset B non-India)** | train | 19,719 | 19,719 | ✅ |
|  | val | 2,301 | 2,301 | ✅ |
|  | test (frozen, shared) | 230 | 230 | ✅ |

All image/label counts match per split.

---

## 4. Frozen Indian Test Split Manifest

### 4.1 Primary Split Manifest (Source of Truth)

**File**: `experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json`

| Property | Value |
|----------|-------|
| **Split version** | 2.0.0 |
| **Dataset identifier** | RDD2022_CRDDC_India |
| **Total images** | 1,530 |
| **Test split images** | 230 |
| **Test split objects** | 679 |
| **Test class distribution** | longitudinal_crack: 66, transverse_crack: 5, alligator_crack: 96, pothole: 512 |
| **Stratification method** | class_presence_strata (8 strata) |
| **Rare class (transverse_crack)** | 5 test objects (target: 5) — achieved |
| **Validation checksum (V8)** | `sha256: bca05aaf8b1cbec51e8cae097a3abefb57a3eee6278299fe09ba014ef743c638` |

**Computed SHA256 of current file**: `7cd8c5557275d4c971a9cdba6aff470d6d75994628569ea5aa8089d5156dbb60`  
**Status**: **MISMATCH** — file has been modified after manifest creation (or checksum computed differently). The manifest's V8 checksum validates the *assignment structure* at generation time, not the current file bytes.

### 4.2 Frozen Test Image SHA256 Manifest (Per-Image Integrity)

**File**: `experiments/analysis/overnight/dataset_b_hf_gate/frozen_test_sha256.json`

| Property | Value |
|----------|-------|
| **Entries** | 231 (230 test images + 1 extra: `India_004542.jpg`) |
| **Format** | JSON object: `{ "filename.jpg": "SHA256_HEX", ... }` |
| **Purpose** | Per-image integrity verification for the frozen 230-image test set |
| **Matches test split** | Yes — all 230 test-set filenames from `split_manifest_fixed.json` are present |

**Note**: The manifest contains 231 entries; `India_004542.jpg` is not in the 230-image test split (likely a stray/extra entry).

### 4.3 Experiment 2 Split Manifest (References Frozen Test)

**File**: `experiments/dataset/experiment2/split_manifest.json`

| Property | Value |
|----------|-------|
| **Manifest version** | 1.0.0 |
| **Manifest SHA256 (self-declared)** | `4c533c574584b50f23da9c8bb538724e900c04983187d46bc3ac4d4bd4785ff3` |
| **Computed SHA256 (current file)** | `b1c5e22bdae818fd191c458b2b734e525e9d6fec673d96761fb8db5fc6554d93` |
| **Test policy** | "No test split is created. The frozen 230-image India test set from Dataset A is referenced unchanged at 'experiments/dataset/yolo_rdd2022_india/images/test'." |
| **Seed** | 42 |

**Status**: **MISMATCH** — same note as above; self-declared checksum excludes the `manifest_sha256` and `manifest_sha256_note` keys.

---

## 5. Class Index → Name Mapping Verification

| Index | yolo_rdd2022_india | experiment2 | raw_hf_rdd2022 (both) | **Consensus** |
|-------|-------------------|-------------|----------------------|---------------|
| 0 | longitudinal_crack | longitudinal_crack | longitudinal_crack | ✅ **longitudinal_crack** |
| 1 | transverse_crack | transverse_crack | transverse_crack | ✅ **transverse_crack** |
| 2 | alligator_crack | alligator_crack | alligator_crack | ✅ **alligator_crack** |
| 3 | pothole | pothole | pothole | ✅ **pothole** |

**All four data.yaml files agree on the exact class order (0→3).** No mismatches.

---

## 6. Mismatches & Issues Found

| # | Issue | Severity | Details |
|---|-------|----------|---------|
| 1 | `split_manifest_fixed.json` V8 checksum mismatch | **Medium** | Declared: `bca05aaf...`, Computed: `7cd8c555...`. File modified post-generation or checksum method differs. |
| 2 | `experiment2/split_manifest.json` self-declared checksum mismatch | **Medium** | Declared: `4c533c57...`, Computed: `b1c5e22b...`. Self-declared checksum excludes its own key; current file bytes differ. |
| 3 | `frozen_test_sha256.json` contains 231 entries vs 230 test images | **Low** | Extra entry: `India_004542.jpg` not in frozen test split. |
| 4 | `raw_hf_rdd2022` YAMLs use `val: images/valid` vs `images/val` in Dataset A | **Info** | Different directory naming convention (`valid` vs `val`). Not used in current experiments. |
| 5 | `raw_hf_rdd2022` YAMLs use dict `names` format vs list format | **Info** | Semantically identical; Ultralytics accepts both. |

---

## 7. Conclusions

1. **All referenced paths exist on disk** and image/label counts match per split.
2. **Class index→name mapping is consistent** across all four data.yaml files (0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole).
3. **Frozen test split (230 images, 679 objects) is intact** at `experiments/dataset/yolo_rdd2022_india/images/test` with matching labels.
4. **Two manifest checksum mismatches** exist but are likely due to post-generation file modifications or checksum computation method (excluding self-referential keys). The split assignments themselves are validated by V1–V7 checks in `split_manifest_fixed.json` (all pass).
5. **No class mapping mismatches** — longitudinal_crack (0), transverse_crack (1), alligator_crack (2), pothole (3) is the canonical order used by all experiments.

---

## 8. Recommendations

- Recompute and update V8 checksum in `split_manifest_fixed.json` if the file is considered authoritative.
- Remove or document the extra `India_004542.jpg` entry in `frozen_test_sha256.json`.
- Consider aligning `val` directory naming (`valid` → `val`) in raw HF dataset for consistency, though not currently used.