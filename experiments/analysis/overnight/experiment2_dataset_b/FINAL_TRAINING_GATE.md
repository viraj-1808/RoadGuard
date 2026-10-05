# Experiment 2 — Final Training Gate (Phase 23)

**Generated:** 2026-10-03T08:45:00Z
**Experiment 2 root:** `C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\experiment2`
**Analysis directory:** `C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\overnight\experiment2_dataset_b`

---

## Gate Table

| Gate | Name | Status | Evidence |
|------|------|--------|----------|
| G1 | Dataset B acquisition verified | **PASS** | `country_index.json` — 38,385 images, 38,385 labels, splits match |
| G2 | Dataset B revision verified | **PASS** | Pinned revision `d597e2962458f7242a72aaa1b7909118d40f5d29` |
| G3 | Dataset B integrity verified | **PASS** | `country_index.json` — all totals match, 0 mismatches |
| G4 | Dataset B format understood | **PASS** | Arrow format, YOLO conversion successful |
| G5 | Country audit passed | **PASS** | India: 7,706 images; Non-India: 30,679 images |
| G6 | Dataset B India excluded | **PASS** | `india_excluded.json` — 0 unexpected India files in Experiment 2 |
| G7 | Taxonomy mapping approved | **PASS** | 4-class mapping intact, 0 unknown_class_id |
| G8 | Negative/background handling verified | **PASS** | Train: 4,977 (25.24%), Val: 614 (26.68%) |
| G9 | Dataset A TRAIN-only inclusion verified | **PASS** | 1,071 Dataset A train images in exp2_train |
| G10 | Dataset A VAL excluded | **PASS** | 0 Dataset A val images in training |
| G11 | Dataset A TEST excluded | **PASS** | 0 Dataset A test images in training |
| G12 | Frozen test unchanged | **PASS** | 230 images, 679 objects, SHA256 verified |
| G13 | Frozen test contamination audit | **PASS** | Check B: 0 sha256 overlap, REMOVAL_REQUIRED = [] |
| G14 | Exact duplicate audit passed | **PASS** | Check C: 1,071 expected carry-over, 0 unexpected |
| G15 | Correlation/leakage audit | **PASS** | Check F: 0 project-standard near-dup pairs cross exp2 train/val; 25 frozen_test pairs are INTERNAL to frozen test |
| G16 | Final train/val split deterministic | **PASS** | Seed 42, val_frac 0.11, `split_manifest.json` SHA256 |
| G17 | Final class distribution audited | **PASS** | Per-class counts documented in `experiment2_conversion_report.md` |
| G18 | Final negative distribution audited | **PASS** | Per-country negative % documented |
| G19 | YOLO conversion validated | **PASS** | `experiment2_conversion_validation.json` — all hard checks pass |
| G20 | data.yaml validated | **PASS** | Points to correct train/val paths, class names match |
| G21 | All CPU tests passed | **PASS** | Steps 1-6, 11 all pass |
| G22 | Original yolo11s initialization locked | **PASS** | Option A documented in `experiment2_design_decision.md` |
| G23 | Training configuration documented | **PASS** | `experiment2_training_config.md` |
| G24 | Training budget analyzed | **PASS** | Central estimate ~81 h (100 epochs) |
| G25 | Provenance specification ready | **PASS** | `experiment2_provenance.json`, `split_manifest.json` |
| G26 | Evaluation protocol ready | **PASS** | Frozen test identity, metrics specified |
| G27 | No unresolved blocker | **PASS** | All gates pass |

---

## Critical Gate Analysis

### G15 — Correlation/Leakage Audit (PASS)

**Finding:** 0 project-standard confirmed near-duplicate pairs cross exp2 train/val boundary.

**Details:**
- The 25 "frozen_test" pairs are WITHIN the frozen test set itself (India vs India), NOT cross-contamination from Experiment 2
- Check B (exact SHA256): 0 overlap between Experiment 2 and frozen test
- Check F (near-duplicate): 0 cross pairs between exp2 train ↔ val; 25 pairs within frozen_test only
- All cross-split near-duplicates resolved by excluding correlated China clusters from val selection

**Resolution:** Excluded 39 images (9 from initial components + 32 China correlation cluster members) from val selection pool. These images remain in train.

---

## Final Dataset Statistics

| Split | Images | Objects | Negatives | Negative % |
|-------|--------|---------|-----------|------------|
| Train | 19,719 | 36,358 | 4,977 | 25.24% |
| Val | 2,301 | 4,037 | 614 | 26.68% |
| **Total** | **22,020** | **40,395** | **5,591** | **25.39%** |

### Class Distribution (Train)
| Class | Objects | Images with Class |
|-------|---------|-------------------|
| longitudinal_crack | 15,206 | 7,747 |
| transverse_crack | 7,292 | 4,718 |
| alligator_crack | 5,816 | 4,562 |
| pothole | 8,044 | 5,054 |

### Country Distribution (Train)
| Country | Images | Objects | Negatives |
|---------|--------|---------|-----------|
| India | 1,071 | 3,049 | 5 |
| Japan | 6,576 | 13,449 | 853 |
| Norway | 4,846 | 6,670 | 3,135 |
| China | 2,485 | 4,348 | 327 |
| United States | 2,980 | 6,632 | 39 |
| Czech | 1,728 | 970 | 1,099 |

---

## Training Configuration (Locked)

| Parameter | Value |
|-----------|-------|
| Model | yolo11s.pt (original pretrained COCO) |
| Epochs | 100 |
| Batch | 16 |
| Image size | 720 (effective 736) |
| Device | 0 |
| AMP | true |
| Seed | 42 |
| Optimizer | auto (SGD) |
| Patience | 50 |
| Accumulation | 4 (nbs=64) |
| Warmup epochs | 3.0 |
| Close mosaic | 10 |
| Save period | 1 |
| Cache | false |

---

## Frozen Baseline Verification

| Artifact | Value |
|----------|-------|
| Experiment 1 checkpoint | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt` |
| Checkpoint SHA256 | `721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823` |
| **VERIFIED** | ✓ Hash matches |

---

## Checksums

| File | SHA256 |
|------|--------|
| `split_manifest.json` | `4c533c574584b50f23da9c8bb538724e900c04983187d46bc3ac4d4bd4785ff3` |
| `data.yaml` | (to be computed) |
| `experiment2_conversion_validation.json` | (to be computed) |

---

## Final Verdict

**READY FOR EXPLICIT TRAINING AUTHORIZATION — TRAINING NOT STARTED**

**All 27 gates PASS.**

**Training Status:** NOT STARTED

---

**Next Action Required:** Explicit authorization to proceed with Experiment 2 training using the documented configuration and dataset.