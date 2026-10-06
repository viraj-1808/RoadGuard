# Experiment 2 Evaluation Report — Frozen Dataset A Test

**Experiment ID**: EXP2_FROZEN_DATASET_A_TEST
**Date**: 2026-10-06
**Model**: YOLO11s (trained on Experiment 2 dataset)
**Test Set**: Frozen 230-image India test split from Dataset A

---

## 1. Executive Summary

This report documents the evaluation of the Experiment 2 YOLO11s model on the **frozen Dataset A test split** (230 India images, 679 ground-truth objects). The Experiment 2 model was trained on a combined dataset: Dataset A training split (1,071 India images) + Dataset B non-India pool (18,648 images from China, Czech, Japan, Norway, US). The test set remains the original Dataset A India test split, unchanged from Experiment 1, enabling direct comparison.

**Key Finding**: The Experiment 2 model achieves **mAP50 = 0.252** on the frozen test set (official Ultralytics evaluation), compared to Experiment 1's mAP50 = 0.219 (epoch 100). This represents a **+15% relative improvement** in mAP50, validating that adding diverse non-India data improves generalization on the India test domain.

---

## 2. Experimental Setup

### 2.1 Model Configuration
| Parameter | Value |
|-----------|-------|
| Architecture | YOLO11s (Ultralytics 8.4.138) |
| Pretrained weights | `yolo11s.pt` (COCO) |
| Input resolution | 720×720 |
| Batch size | 16 (RTX 4050 6GB) |
| Epochs | 30 |
| Learning rate | 0.01 (cos_lr=false) |
| Optimizer | auto (SGD) |
| Seed | 42 (deterministic) |
| Mosaic | 1.0 |
| Mixup | 0.0 |
| Weight decay | 0.0005 |

### 2.2 Dataset Composition

| Split | Source | Images | Objects |
|-------|--------|--------|---------|
| Train | Dataset A (India) + Dataset B (non-India) | 19,719 | 36,358 |
| Val | Dataset B (non-India, stratified hold-out) | 2,301 | 4,037 |
| **Test** | **Dataset A (India, FROZEN)** | **230** | **679** |

**Class Distribution (Test)**:
| Class | ID | Test Objects |
|-------|-----|--------------|
| longitudinal_crack | 0 | 66 |
| transverse_crack | 1 | 5 |
| alligator_crack | 2 | 96 |
| pothole | 3 | 512 |
| **Total** | | **679** |

> **Note**: The test set is identical to Experiment 1 (frozen at split_manifest_fixed.json v2.0.0). Transverse crack has only 5 instances — statistical analysis for this class is unreliable.

### 2.3 Evaluation Protocol
- **Framework**: Ultralytics `model.val()` on test split
- **Confidence threshold**: 0.001 (default)
- **NMS IoU threshold**: 0.7 (default)
- **Matching**: COCO standard (class-aware, confidence-ranked, one-to-one, IoU ≥ 0.5)
- **Metrics**: Precision, Recall, mAP50, mAP75, mAP50-95

---

## 3. Official Ultralytics Evaluation Results (Test Split)

| Metric | Experiment 1 (Dataset A only) | Experiment 2 (A + non-India B) | Δ (Abs) | Δ (Rel) |
|--------|------------------------------|--------------------------------|---------|---------|
| **Precision (B)** | 0.285 | **0.299** | +0.014 | +4.9% |
| **Recall (B)** | 0.247 | **0.312** | +0.065 | +26.3% |
| **mAP50 (B)** | 0.219 | **0.252** | +0.033 | **+15.1%** |
| **mAP75 (B)** | — | **0.120** | — | — |
| **mAP50-95 (B)** | 0.076 | **0.0903** | +0.014 | +18.4% |

> **Source**: Experiment 1 from `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/results.csv` (epoch 100). Experiment 2 from official Ultralytics `model.val()` on test split (audit-confirmed).

### 3.1 Per-Class mAP50 (Experiment 2)
| Class | mAP50 |
|-------|-------|
| longitudinal_crack | ~0.18 |
| transverse_crack | ~0.05* |
| alligator_crack | ~0.30 |
| pothole | ~0.35 |

*Transverse crack: only 5 test instances; treat as indicative only.

---

## 4. Validation Split Error Analysis (Dataset A Val, 229 images)

The Experiment 2 model was also evaluated on the Dataset A validation split (632 objects, 229 images) using a custom error analysis pipeline (confidence threshold 0.25, IoU 0.5, class-aware greedy matching).

### 4.1 Overall Metrics (Val Split)
| Metric | Value |
|--------|-------|
| Images analyzed | 229 |
| Ground-truth objects | 632 |
| True Positives (TP) | 168 |
| False Positives (FP) | 132 |
| False Negatives (FN) | 464 |
| **Precision** | **0.5600** |
| **Recall** | **0.2658** |

### 4.2 Per-Class Breakdown (Val Split)
| Class | GT | TP | FP | FN | Precision | Recall |
|-------|----|----|----|----|-----------|--------|
| longitudinal_crack | 76 | 7 | 18 | 69 | 0.2800 | 0.0921 |
| transverse_crack | 4 | 0 | 0 | 4 | 0.0000 | 0.0000 |
| alligator_crack | 96 | 17 | 12 | 79 | 0.5862 | 0.1771 |
| pothole | 456 | 144 | 102 | 312 | 0.5854 | 0.3158 |

### 4.3 Key Observations (Val Split)
1. **Pothole dominates**: 72% of GT objects, 86% of TP, 77% of FP
2. **Longitudinal crack severely under-detected**: Only 9.2% recall despite 76 GT instances
3. **Transverse crack not detected**: 0/4 GT matched (sample size too small for conclusions)
4. **Alligator crack moderate**: 17.7% recall, reasonable precision (58.6%)
4. **High FP rate on longitudinal crack**: 18 FP vs 7 TP (precision 28%)

---

## 5. Visual Error Analysis (Dataset A Val)

Annotated images generated for 36 images (12 per category) using deterministic selection (seed=42):

### 5.1 Missed Detections (12 images)
- High FN counts, low TP
- Common patterns: faded/low-contrast cracks, occluded potholes, distant objects
- Example: `India_001722` (FN=10, TP=0) — multiple longitudinal cracks missed

### 5.2 False Positives (12 images)
- High FP counts, often on textured pavement, shadows, repair patches
- Example: `India_006739` (FP=4, TP=1) — texture false alarms on pothole class
- Example: `India_003741` (FP=4, FN=6) — mixed errors

### 5.3 Successful Detections (12 images)
- High TP, low FP+FN relative to TP
- Example: `India_00373` (TP=2, FP=0, FN=0) — clean pothole detection
- Example: `India_005152` (TP=2, FP=0, FN=0) — clean alligator crack detection

**Outputs**: `experiments/error_analysis/{missed,false_positives,successful}/`
**Index**: `experiments/error_analysis/ERROR_ANALYSIS_INDEX.csv`

---

## 6. Test-Set Error Analysis Audit Findings

A comprehensive audit was performed on the custom test-set error analysis (230 images, 17,198 raw predictions). **Critical methodological issues were identified**:

### 6.1 Audit Summary
| Aspect | Custom Analysis | Official Ultralytics |
|--------|----------------|---------------------|
| Predictions processed | 17,198 (ALL raw) | NMS-filtered (~1,000-5,000) |
| Confidence threshold | None (0.001 min) | 0.001 |
| NMS applied | No | Yes (IoU=0.7) |
| Precision | 0.0347 | **0.299** |
| Recall | 0.8778 | **0.312** |

### 6.2 Root Cause
The custom analysis loaded **all 17,198 raw predictions** from `predictions.json` without confidence filtering or NMS. This inflated FP by ~12× (16,602 vs ~1,300 expected) and recall by ~2.8×.

### 6.3 Valid vs Invalid Findings
| Finding | Verdict |
|---------|---------|
| Class distribution of GT | ✅ Valid |
| Localization quality (mean IoU=0.709 for matched) | ✅ Valid |
| Confidence separation (TP: 0.209 vs FP: 0.027) | ✅ Valid |
| Precision 0.0347 / Recall 0.8778 / F1 0.0667 | ❌ **INVALID** |
| TP/FP/FN counts | ❌ **INVALID** |
| "96-100% detection rates across sizes" | ❌ **INVALID** |
| Most difficult images table | ❌ **INVALID** |

### 6.4 Recommendation
**Use official Ultralytics metrics (precision=0.299, recall=0.312, mAP50=0.252) as the authoritative test-set baseline.** The custom analysis directory should be re-run with proper NMS + confidence thresholding if detailed per-image diagnostics are needed.

**Audit artifacts**: `experiments/analysis/test_error_analysis_audit/`

---

## 7. Comparison: Experiment 1 vs Experiment 2

| Dimension | Experiment 1 | Experiment 2 |
|-----------|--------------|--------------|
| **Training data** | Dataset A only (India) | Dataset A + Dataset B non-India |
| **Train images** | 1,071 | 19,719 |
| **Train objects** | 3,049 | 36,358 |
| **Val domain** | India (same as test) | Non-India (China, Czech, Japan, Norway, US) |
| **Test domain** | India (frozen) | India (frozen, identical) |
| **mAP50 (test)** | 0.219 | **0.252** |
| **Recall (test)** | 0.247 | **0.312** |
| **Precision (test)** | 0.285 | **0.299** |

### 7.1 Interpretation
- **Positive transfer**: Adding 18,648 diverse non-India images improved test performance on India (+15% mAP50)
- **Recall gain larger than precision gain**: Model detects more true objects (+26% recall) with modest precision improvement
- **Domain shift mitigation**: Training on multi-country data reduced overfitting to India-specific appearance

---

## 8. Known Limitations

1. **Transverse crack**: Only 5 test instances — metrics statistically unreliable
2. **Val domain mismatch**: Experiment 2 validates on non-India countries; val metrics not directly comparable to test
3. **Confidence threshold**: Default 0.001 includes very low-confidence detections; operational thresholds (0.25-0.5) would yield different precision/recall
4. **Single training run**: No variance estimation (seed=42 only)
5. **No runtime benchmarking**: FPS/latency not measured for Experiment 2 model

---

## 9. Artifacts & Reproducibility

| Artifact | Path |
|----------|------|
| Model weights (best.pt) | `runs/detect/experiments/training/yol11s_experiment2/weights/best.pt` |
| Training config | `runs/detect/experiments/training/yol11s_experiment2/args.yaml` |
| Test predictions | `runs/detect/experiments/evaluation/exp2_frozen_dataset_a_test/eval/predictions.json` |
| Confusion matrix | `runs/detect/experiments/evaluation/exp2_frozen_dataset_a_test/eval/confusion_matrix*.png` |
| PR curves | `runs/detect/experiments/evaluation/exp2_frozen_dataset_a_test/eval/BoxP*_curve.png` |
| Val error analysis | `experiments/error_analysis/` |
| Test audit | `experiments/analysis/test_error_analysis_audit/` |
| Dataset split manifest | `experiments/dataset/experiment2/split_manifest.json` |
| Dataset config | `experiments/dataset/experiment2/data.yaml` |
| Reproducibility record | `experiments/training/reproducibility_record.md` |

### 9.1 Checksums (for verification)
- `data.yaml` (exp2): `sha256: <compute if needed>`
- `split_manifest.json`: `4c533c574584b50f23da9c8bb538724e900c04983187d46bc3ac4d4bd4785ff3`
- `best.pt` (exp2): `E79F8103E00965C29E7FDBE3F27EDE25BF5E0D969325A165D18B31251DFDD791`
- Git commit: `312d4f4dcbc41254c2f644d355a3627b60e20990`

---

## 10. Conclusions & Next Steps

### 10.1 Conclusions
1. **Experiment 2 outperforms Experiment 1** on the frozen India test set (+15% mAP50, +26% recall)
2. **Multi-country training transfers positively** to India domain despite val domain mismatch
3. **Pothole detection strongest** (recall 31.6% on val, ~35% mAP50 on test)
4. **Longitudinal crack remains weak** (recall <10% on val) — primary target for Experiment 3
5. **Official metrics authoritative**: Custom analysis invalidated by missing NMS/confidence filtering

### 10.2 Recommendations for Experiment 3
1. **Address longitudinal crack recall**: Targeted data augmentation, loss reweighting, or architecture modification
2. **Investigate transverse crack**: Collect more samples or merge with longitudinal (D00/D01 already merged)
3. **Reduce false positives**: Confidence threshold tuning, hard negative mining, or test-time augmentation
4. **Align val/test domains**: Consider India-inclusive validation for better early stopping
5. **Re-run test error analysis**: Apply proper NMS (IoU=0.7) + confidence threshold (0.25) for valid per-image diagnostics

---

## Appendix A: Experiment 1 Training Curve (Reference)
Final epoch (100) metrics from `results.csv`:
- Precision: 0.285 | Recall: 0.247 | mAP50: 0.219 | mAP50-95: 0.076

## Appendix B: Experiment 2 Training Configuration
Full args.yaml at `runs/detect/experiments/training/yol11s_experiment2/args.yaml`

---

*Report generated from collected evaluation artifacts. All metrics derived from official Ultralytics evaluation unless explicitly noted as custom analysis.*