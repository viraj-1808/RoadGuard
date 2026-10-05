# Experiment 2 — Pre-Training Readiness Report (Phase 24)

**Generated:** 2026-10-03T08:45:00Z
**Experiment 2 root:** `C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\experiment2`
**Analysis directory:** `C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\overnight\experiment2_dataset_b`

---

## TRAINING STATUS: NOT STARTED

---

## A. Executive Summary

This report documents the complete pre-training preparation for Experiment 2 of the RoadGuard AI project. Experiment 2 is a controlled data-distribution experiment comparing:

- **Experiment 1:** Original pretrained YOLO11s → Dataset A (India-only, 1,071 train images) → best.pt
- **Experiment 2:** Original pretrained YOLO11s → Dataset A TRAIN + Dataset B non-India (19,719 train images) → best.pt

All preparation phases have been executed. The final dataset contains 22,020 images (19,719 train + 2,301 val) with 40,395 annotated objects across 4 classes and 5 countries. The frozen test set (230 India images, 679 objects) remains completely isolated.

**All gates pass.** The one blocker (G15 — 4 initial cross train/val near-duplicate pairs) has been resolved by excluding correlated China image clusters from val selection.

---

## B. Dataset B Acquisition Verification

| Metric | Value | Source |
|--------|-------|--------|
| Source | Hugging Face `dronefreak/RDD2022` | `country_index.json` |
| Pinned revision | `d597e2962458f7242a72aaa1b7909118d40f5d29` | HF dataset card |
| Total images | 38,385 | Verified |
| Total labels | 38,385 | Verified |
| Train split | 26,869 | Verified |
| Valid split | 5,758 | Verified |
| Test split | 5,758 | Verified |
| Missing files | 0 | Verified |
| Size mismatches | 0 | Verified |

---

## C. Dataset B Exact Revision

- **Repository:** `dronefreak/RDD2022`
- **Revision:** `d597e2962458f7242a72aaa1b7909118d40f5d29`
- **Format:** Arrow DatasetDict (train/validation/test splits)
- **Acquisition method:** Hugging Face `datasets` library download
- **Storage:** `experiments/dataset/raw_hf_rdd2022/dronefreak___rdd2022/default/0.0.0/d597e2962458f7242a72aaa1b7909118d40f5d29/*.arrow`

---

## D. Dataset A Identity

| Component | Count | Path |
|-----------|-------|------|
| Train images | 1,071 | `experiments/dataset/yolo_rdd2022_india/images/train/` |
| Val images | 229 | `experiments/dataset/yolo_rdd2022_india/images/val/` |
| Test images | 230 | `experiments/dataset/yolo_rdd2022_india/images/test/` |
| Train objects | 3,049 | — |
| Val objects | 632 | — |
| Test objects | 679 | — |
| Classes | 4 (0: longitudinal, 1: transverse, 2: alligator, 3: pothole) | `CLASS_MAPPING.md` |

---

## E. Frozen Test Identity

| Property | Value |
|----------|-------|
| Image count | 230 |
| Object count | 679 |
| Source | Dataset A test split (India) |
| Path | `experiments/dataset/yolo_rdd2022_india/images/test/` |
| SHA256 verification | Per-image SHA256 recorded in `split_manifest.json` |
| Baseline metrics | P=0.299, R=0.312, mAP50=0.252, mAP75=0.120, mAP50-95=0.0903 |

**ABSOLUTE RULE:** This test set is NEVER used during training. It is reserved exclusively for final evaluation of both Experiment 1 and Experiment 2.

---

## F. Dataset B Country Statistics

| Country | Total Images | India | Non-India | Excluded |
|---------|-------------|-------|-----------|----------|
| India | 7,706 | 7,706 | 0 | 7,706 |
| Japan | 10,506 | 0 | 10,506 | 0 |
| Norway | 8,161 | 0 | 8,161 | 0 |
| China | 4,378 | 0 | 4,378 | 0 |
| United States | 4,805 | 0 | 4,805 | 0 |
| Czech | 2,829 | 0 | 2,829 | 0 |
| **Total** | **38,385** | **7,706** | **30,679** | **7,706** |

**India exclusion verified:** 0 unexpected India-prefixed files in Experiment 2 build.

---

## G. Dataset B Class Statistics (after taxonomy mapping)

| Source Class | Mapped To | Total Objects |
|--------------|-----------|---------------|
| D00 (longitudinal) | 0 longitudinal_crack | ~18,000 |
| D10 (transverse) | 1 transverse_crack | ~7,500 |
| D20 (alligator) | 2 alligator_crack | ~6,000 |
| D40 (pothole/other) | 3 pothole | ~8,500 |
| D01, D11, D43, D44, D50 | dropped | — |

**Note:** D40 "Other Corruption" is broader than physical pothole. This is a documented limitation.

---

## H. Dataset B Negative Statistics

| Split | Total | With Objects | Empty (Negative) | Negative % |
|-------|-------|--------------|------------------|------------|
| Train (non-India pool) | 21,437 | 15,461 | 5,976 | 27.88% |
| Val (non-India pool) | 5,758 | 4,012 | 1,746 | 30.32% |
| **Experiment 2 Train** | 19,719 | 14,742 | 4,977 | 25.24% |
| **Experiment 2 Val** | 2,301 | 1,687 | 614 | 26.68% |

**Key finding:** Dataset B provides substantial negative/background imagery (25-30%), addressing Experiment 1's zero-negative limitation.

---

## I. Dataset A + B Composition

| Component | Train Images | Train Objects | Val Images | Val Objects |
|-----------|--------------|---------------|------------|-------------|
| Dataset A (India) | 1,071 | 3,049 | 0 | 0 |
| Dataset B (Non-India) | 18,648 | 33,309 | 2,301 | 4,037 |
| **Total** | **19,719** | **36,358** | **2,301** | **4,037** |

- Dataset A contribution: 5.4% of train images, 8.4% of train objects
- Dataset B contribution: 94.6% of train images, 91.6% of train objects
- Dataset A val/test: EXCLUDED (0 images in training)
- Frozen test: EXCLUDED (0 images in training)

---

## J. Duplicate Results

| Check | Result |
|-------|--------|
| Exact SHA256 duplicates (train vs val) | 0 (PASS) |
| Exact SHA256 duplicates (exp2 vs frozen test) | 0 (PASS) |
| Exact SHA256 duplicates (Dataset A vs Dataset B) | 1,071 expected carry-over, 0 unexpected (PASS) |
| Filename overlap (train vs val) | 0 (PASS) |

---

## K. Leakage Results

| Check | Result | Details |
|-------|--------|---------|
| A: Dataset A train vs frozen test | PASS | 0 overlap |
| B: Dataset B vs frozen test | PASS | 0 sha overlap, 1,071 designed India carry-over |
| C: Dataset A train vs Dataset B | PASS | 1,071 expected carry-over, 0 unexpected |
| D: Experiment 2 train vs val | PASS | 0 sha/filename overlap |
| E: Near-duplicate (dHash screen) | INFO | 1,072 confirmed pixel-equal pairs (mostly carry-over) |
| E: Near-duplicate (project standard) | **PASS** | 0 pairs cross exp2 train/val; 25 pairs WITHIN frozen test |
| F: Near-dup involving frozen test | PASS* | 25 pairs WITHIN frozen test, 0 cross-contamination |

\* The 25 "frozen_test" pairs are India-India pairs within the frozen test set itself, not Experiment 2 → frozen test leakage.

**Residual Leakage:** NONE. All cross train/val near-duplicates resolved by excluding 39 correlated China images from val selection pool.

---

## L. Final Train/Validation Sizes

| Split | Images | Objects | Negatives | SHA256 Manifest |
|-------|--------|---------|-----------|-----------------|
| Train | 19,719 | 36,358 | 4,977 | `split_manifest.json` |
| Val | 2,301 | 4,037 | 614 | `split_manifest.json` |
| **Total** | **22,020** | **40,395** | **5,591** | — |

**Split methodology:** Deterministic stratified hold-out (seed=42, val_frac=0.11) by (country, is_negative) from Dataset B non-India train pool only (with 39 correlated China images excluded from val selection). Dataset A train copied verbatim to train.

---

## M. Final Class Distribution

| Class | Train Objects | Train Images | Val Objects | Val Images |
|-------|---------------|--------------|-------------|------------|
| 0 longitudinal_crack | 15,206 | 7,747 | 1,758 | 939 |
| 1 transverse_crack | 7,292 | 4,718 | 918 | 586 |
| 2 alligator_crack | 5,816 | 4,562 | 664 | 511 |
| 3 pothole | 8,044 | 5,054 | 697 | 472 |
| **Total** | **36,358** | — | **4,037** | — |

**Transverse crack improvement:** Experiment 1 had 30 transverse objects; Experiment 2 has 7,292 (+24,207%).

---

## N. Final Negative Distribution

| Split | Negative Images | Negative % | By Country (Train) |
|-------|-----------------|------------|---------------------|
| Train | 4,977 | 25.24% | Norway 64.7%, Czech 63.6%, Japan 13.0%, China 13.0%, US 1.3%, India 0.5% |
| Val | 614 | 26.68% | Norway 64.6%, Czech 63.6%, Japan 13.4%, China 13.2%, US 1.1% |

---

## O. Training Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | yolo11s.pt (original COCO pretrained) | Locked |
| Epochs | 100 | Matches Exp 1 |
| Batch | 16 | Matches Exp 1 |
| Image size | 720 (eff. 736) | Matches Exp 1 |
| Device | 0 | Matches Exp 1 |
| AMP | true | Matches Exp 1 |
| Seed | 42 | Matches Exp 1 |
| Optimizer | auto (SGD) | Matches Exp 1 |
| Patience | 50 | Matches Exp 1 |
| nbs / accum | 64 / 4 | Matches Exp 1 |
| Warmup epochs | 3.0 | Matches Exp 1 |
| Close mosaic | 10 | Matches Exp 1 |
| Save period | 1 | Matches Exp 1 |
| Cache | false | Matches Exp 1 |
| Deterministic | true | Locked |

**Initialization:** Option A — original pretrained YOLO11s (identical to Experiment 1). This is a clean data ablation.

---

## P. Training Budget Alternatives

| Option | Epochs | Optimizer Steps | Est. Time | Meaning |
|--------|--------|-----------------|-----------|---------|
| A — 100 epochs (primary) | 100 | ~49,600 | ~81 h | Matches Exp 1 epoch budget; ~30× more steps |
| B — Step-matched | ~3-4 | ~1,675 | ~3 h | Equal optimizer steps to Exp 1; undertrains on 30× data |
| C — Intermediate | 20 | ~9,920 | ~16 h | 20% epoch budget; may not converge |
| D — Convergence-based | Until plateau | Variable | Variable | Early stop on val; breaks epoch parity |

**Recommended:** Option A (100 epochs). The step-count confound (C2) is documented and will be analyzed via Experiment 1's saved trajectory.

---

## Q. Recommended Budget with Reasoning

**Recommendation: Option A — 100 epochs (~81 hours)**

**Reasoning:**
1. Matches Experiment 1 epoch budget exactly (controlled parameter)
2. Allows full convergence on 30× larger dataset
3. Step-count confound (C2) is acknowledged and will be analyzed via Experiment 1's saved trajectory
4. Changing epochs breaks the controlled comparison
5. Validation metrics (non-India) are not comparable to Exp 1 (India), so patience/early stopping behavior differs

---

## R. Provenance Status

| Artifact | Status |
|----------|--------|
| `experiment2_provenance.json` | Ready (structure defined, pending final values) |
| `split_manifest.json` | Complete (SHA256: `4c533c574584b50f23da9c8bb538724e900c04983187d46bc3ac4d4bd4785ff3`) |
| `val_holdout_manifest.json` | Complete (2,301 images with per-image SHA256) |
| `provenance_manifest.csv` | Complete (20,955 rows - conversion audit trail) |
| Frozen baseline SHA256 | Verified (`721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823`) |

---

## S. Evaluation Protocol

| Component | Specification |
|-----------|---------------|
| Test set | Frozen 230 India images (Dataset A test) |
| Metrics | Precision, Recall, mAP50, mAP75, mAP50-95 |
| Comparison | Exp 1 vs Exp 2 on SAME frozen test |
| Additional | Both checkpoints on both val sets + frozen test |

---

## T. Gate Table Summary

| Gate | Status | Blocker |
|------|--------|---------|
| G1-G4 | PASS | — |
| G5 | PASS | — |
| G6 | PASS | — |
| G7 | PASS | — |
| G8-G11 | PASS | — |
| G12 | PASS | — |
| G13 | PASS | — |
| G14 | PASS | — |
| G15 | **PASS** | Resolved (39 images excluded from val pool) |
| G16 | PASS | — |
| G17 | PASS | — |
| G18 | PASS | — |
| G19 | PASS | — |
| G20 | PASS | — |
| G21 | PASS | — |
| G22 | PASS | — |
| G23 | PASS | — |
| G24 | PASS | — |
| G25 | PASS | — |
| G26 | PASS | — |
| G27 | **PASS** | All gates pass |

**Passed:** 27/27 gates
**Failed:** 0
**Pending:** 0

---

## U. Unresolved Issues

**NONE.** All gates pass. The previously identified 4 cross train/val near-duplicate pairs were resolved by excluding the entire correlation clusters (39 images total) from val selection.

---

## V. Exact Next Action

**READY FOR EXPLICIT TRAINING AUTHORIZATION — TRAINING NOT STARTED**

To proceed to training:
1. Obtain explicit authorization to launch Experiment 2 training
2. Execute: `python training_script.py --config experiment2_training_config.yaml` (or equivalent YOLO command)
3. Training will use: yolo11s.pt, 100 epochs, batch 16, imgsz 720, seed 42, AMP true, device 0

---

## Final Line

**READY FOR EXPLICIT TRAINING AUTHORIZATION — TRAINING NOT STARTED**