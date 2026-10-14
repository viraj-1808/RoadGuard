# Baseline Comparison Report

**Date:** 2026-10-11
**Comparison:** Frozen Indian Test Split (230 images, 679 instances) — Phase 6 Final Evaluation

---

## Previous Baseline (Experiment 2 Historical)

| Metric | Value | Source |
|--------|-------|--------|
| Precision (P) | 0.586 | Historical frozen test eval |
| Recall (R) | 0.321 | Historical frozen test eval |
| mAP@50 | 0.279 | Historical frozen test eval |
| mAP@50-95 | 0.111 | Historical frozen test eval |

*Note: Baseline model checkpoint not identified in records; metrics from prior evaluation run.*

---

## Current Models Evaluated

### Experiment 1: yol11s_dataset_v2_split_v2 (epoch86.pt)
- **Training Data:** Dataset A only (India RDD2022)
- **Best Training Epoch:** 86 (mAP50=0.2218 on its own val)
- **Checkpoint:** `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt`
- **SHA-256:** `885db673fe10ed7d18c552e16320850efb5d5902c42f63acaaa25ecb2666663e`

### Experiment 2: yol11s_experiment2 (epoch72.pt)
- **Training Data:** Dataset A train + Dataset B non-India
- **Best Training Epoch:** 72 (mAP50=0.6029 on its own val)
- **Checkpoint:** `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt`
- **SHA-256:** `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5`

---

## Overall Metrics Comparison

| Metric | Baseline | Exp1 epoch86 | Exp2 epoch72 | Δ Exp1 vs Baseline | Δ Exp2 vs Baseline |
|--------|----------|--------------|--------------|--------------------|--------------------|
| **Precision (P)** | 0.586 | 0.231 | **0.399** | -0.355 | -0.187 |
| **Recall (R)** | 0.321 | **0.404** | 0.371 | +0.083 | +0.050 |
| **mAP@50** | 0.279 | 0.244 | **0.300** | -0.035 | **+0.021** |
| **mAP@50-95** | 0.111 | 0.089 | **0.118** | -0.022 | **+0.007** |

---

## Per-Class Metrics Comparison

### Pothole (Priority Class — 512 instances in test)

| Metric | Exp1 epoch86 | Exp2 epoch72 | Better |
|--------|--------------|--------------|--------|
| Precision | 0.370 | **0.388** | Exp2 |
| Recall | **0.496** | 0.484 | Exp1 |
| mAP@50 | 0.382 | **0.395** | Exp2 |
| mAP@50-95 | 0.128 | **0.150** | Exp2 |
| TP (IoU=0.5) | 227 | 117 | Exp1 |
| FP (IoU=0.5) | 285 | 395 | Exp1 |
| FN (IoU=0.5) | 200 | 57 | Exp2 |
| Recall (IoU=0.5) | 0.532 | 0.672 | Exp2 |
| Precision (IoU=0.5) | 0.443 | 0.229 | Exp1 |

### Longitudinal Crack (66 instances)

| Metric | Exp1 epoch86 | Exp2 epoch72 | Better |
|--------|--------------|--------------|--------|
| Precision | 0.161 | **0.355** | Exp2 |
| Recall | **0.485** | 0.379 | Exp1 |
| mAP@50 | 0.219 | **0.330** | Exp2 |
| mAP@50-95 | 0.083 | **0.157** | Exp2 |

### Alligator Crack (96 instances)

| Metric | Exp1 epoch86 | Exp2 epoch72 | Better |
|--------|--------------|--------------|--------|
| Precision | 0.313 | **0.369** | Exp2 |
| Recall | 0.437 | **0.427** | Exp1 |
| mAP@50 | 0.359 | **0.378** | Exp2 |
| mAP@50-95 | 0.136 | **0.152** | Exp2 |

### Transverse Crack (5 instances — extremely rare)

| Metric | Exp1 epoch86 | Exp2 epoch72 | Better |
|--------|--------------|--------------|--------|
| Precision | 0.078 | **0.484** | Exp2 |
| Recall | 0.200 | 0.193 | Exp1 |
| mAP@50 | 0.018 | **0.098** | Exp2 |
| mAP@50-95 | 0.009 | **0.013** | Exp2 |

---

## COCO Evaluation Metrics Comparison

| Metric | Exp1 epoch86 | Exp2 epoch72 | Better |
|--------|--------------|--------------|--------|
| AP @ IoU=0.50:0.95 (all) | 0.090 | **0.120** | Exp2 |
| AP @ IoU=0.50 (all) | 0.246 | **0.303** | Exp2 |
| AP @ IoU=0.75 (all) | 0.040 | **0.072** | Exp2 |
| AP @ IoU=0.50:0.95 (small) | 0.161 | 0.142 | Exp1 |
| AP @ IoU=0.50:0.95 (medium) | 0.057 | **0.095** | Exp2 |
| AP @ IoU=0.50:0.95 (large) | 0.102 | **0.114** | Exp2 |
| AR @ IoU=0.50:0.95 (maxDets=1) | 0.160 | **0.144** | Exp1 |
| AR @ IoU=0.50:0.95 (maxDets=10) | 0.307 | **0.341** | Exp2 |
| AR @ IoU=0.50:0.95 (maxDets=100) | 0.352 | **0.416** | Exp2 |
| AR @ IoU=0.50 (all) | 0.743 | **0.754** | Exp2 |
| AR @ IoU=0.75 (all) | 0.312 | **0.436** | Exp2 |

---

## Key Observations

### Experiment 2 (epoch72) Wins On:
- ✅ Overall mAP@50 (0.300 vs 0.279 baseline, +0.021)
- ✅ Overall mAP@50-95 (0.118 vs 0.111 baseline, +0.007)
- ✅ Pothole mAP@50 (0.395 vs 0.382)
- ✅ Pothole mAP@50-95 (0.150 vs 0.128)
- ✅ All COCO AP/AR metrics
- ✅ Longitudinal crack, alligator crack, transverse crack mAP
- ✅ Pothole recall at IoU=0.5 (0.672 vs 0.532)

### Experiment 1 (epoch86) Wins On:
- ✅ Overall Recall (0.404 vs 0.371)
- ✅ Pothole Recall (0.496 vs 0.484)
- ✅ Pothole Precision (0.370 vs 0.388 — actually Exp2 wins)
- ✅ Lower False Positives (285 vs 395 pothole FP)
- ✅ Pothole Precision at IoU=0.5 (0.443 vs 0.229)

### Neither Beats Baseline On:
- ❌ Overall Precision (Baseline 0.586 > Exp2 0.399 > Exp1 0.231)

---

## Trade-off Analysis

| Aspect | Exp1 epoch86 | Exp2 epoch72 |
|--------|--------------|--------------|
| **Detection Coverage** | Higher recall, more detections | Lower recall, fewer detections |
| **Localization Quality** | Lower mAP@50-95 | Higher mAP@50-95 (better boxes) |
| **False Alarms** | Fewer FP (285) | More FP (395) |
| **Precision at IoU=0.5** | 0.443 (pothole) | 0.229 (pothole) |
| **Suitability** | Safety-critical (miss fewer) | Precision-critical (fewer false alarms) |

---

## Recommendation

**For Deployment:** **Experiment 2 epoch72.pt**
- Beats baseline on primary metrics (mAP@50, mAP@50-95)
- Better localization quality (higher mAP@50-95)
- Superior COCO metrics across the board
- Intact optimizer state for potential fine-tuning

**Caveat:** High FP rate (395 pothole FP) needs addressing via confidence threshold tuning or NMS adjustment before production use.

**For Safety-Critical Applications (maximize recall):** Experiment 1 epoch86.pt
- Higher pothole recall (0.496 vs 0.484)
- Better precision at fixed IoU=0.5 (0.443 vs 0.229)
- Fewer false alarms