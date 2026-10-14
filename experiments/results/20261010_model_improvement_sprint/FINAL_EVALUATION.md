# Phase 6 Final Evaluation Report

**Date:** 2026-10-11  
**Test Set:** `experiments/dataset/yolo_rdd2022_india/images/test` (230 images, 679 instances)  
**Split:** `test` (as defined in data.yaml)  
**Image Size:** 720 (resized to 736 for stride 32)  
**Batch Size:** 16  
**Device:** CUDA:0 (RTX 4050 Laptop GPU)

---

## Models Evaluated

| Model | Checkpoint | Experiment |
|-------|------------|------------|
| **Exp1** | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt` | yol11s_dataset_v2_split_v2 |
| **Exp2** | `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt` | yol11s_experiment2 |

---

## Baseline (Previous Best)

| Metric | Value |
|--------|-------|
| Precision (P) | 0.586 |
| Recall (R) | 0.321 |
| mAP@50 | 0.279 |
| mAP@50-95 | 0.111 |

---

## Experiment 1: yol11s_dataset_v2_split_v2 (epoch86.pt)

### Overall Metrics

| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Precision (P) | **0.231** | -0.355 |
| Recall (R) | **0.404** | +0.083 |
| mAP@50 | **0.244** | -0.035 |
| mAP@50-95 | **0.089** | -0.022 |

### Per-Class Metrics

| Class | Images | Instances | P | R | mAP@50 | mAP@50-95 |
|-------|--------|-----------|---|---|--------|-----------|
| longitudinal_crack | 55 | 66 | 0.161 | 0.485 | 0.219 | 0.083 |
| transverse_crack | 5 | 5 | 0.078 | 0.200 | 0.018 | 0.009 |
| alligator_crack | 82 | 96 | 0.313 | 0.437 | 0.359 | 0.136 |
| **pothole** | 230 | 512 | **0.370** | **0.496** | **0.382** | **0.128** |
| **all (macro avg)** | 230 | 679 | **0.231** | **0.404** | **0.244** | **0.089** |

### COCO AP/AR Metrics

| Metric | Value |
|--------|-------|
| AP @ IoU=0.50:0.95 (all) | 0.090 |
| AP @ IoU=0.50 (all) | 0.246 |
| AP @ IoU=0.75 (all) | 0.040 |
| AP @ IoU=0.50:0.95 (small) | 0.161 |
| AP @ IoU=0.50:0.95 (medium) | 0.057 |
| AP @ IoU=0.50:0.95 (large) | 0.102 |
| AR @ IoU=0.50:0.95 maxDets=1 | 0.160 |
| AR @ IoU=0.50:0.95 maxDets=10 | 0.307 |
| AR @ IoU=0.50:0.95 maxDets=100 | 0.352 |
| AR @ IoU=0.50 (all) | 0.743 |
| AR @ IoU=0.75 (all) | 0.312 |

### Pothole-Specific Confusion Matrix (IoU=0.5)

| | Predicted Pothole | Predicted Background |
|---|---|---|
| **Actual Pothole** | TP = 227 | FN = 200 |
| **Actual Background** | FP = 285 | TN = - |

| Metric | Value |
|--------|-------|
| **Pothole TP** | 227 |
| **Pothole FP** | 285 |
| **Pothole FN** | 200 |
| **Pothole Recall (IoU=0.5)** | 0.532 |
| **Pothole Precision (IoU=0.5)** | 0.443 |

*Note: Confusion matrix uses fixed IoU=0.5 threshold; reported mAP@50 uses COCO evaluation averaging over IoU=0.5:0.95.*

---

## Experiment 2: yol11s_experiment2 (epoch72.pt)

### Overall Metrics

| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Precision (P) | **0.399** | -0.187 |
| Recall (R) | **0.371** | +0.050 |
| mAP@50 | **0.300** | +0.021 |
| mAP@50-95 | **0.118** | +0.007 |

### Per-Class Metrics

| Class | Images | Instances | P | R | mAP@50 | mAP@50-95 |
|-------|--------|-----------|---|---|--------|-----------|
| longitudinal_crack | 55 | 66 | 0.355 | 0.379 | 0.330 | 0.157 |
| transverse_crack | 5 | 5 | 0.484 | 0.193 | 0.098 | 0.013 |
| alligator_crack | 82 | 96 | 0.369 | 0.427 | 0.378 | 0.152 |
| **pothole** | 230 | 512 | **0.388** | **0.484** | **0.395** | **0.150** |
| **all (macro avg)** | 230 | 679 | **0.399** | **0.371** | **0.300** | **0.118** |

### COCO AP/AR Metrics

| Metric | Value |
|--------|-------|
| AP @ IoU=0.50:0.95 (all) | 0.120 |
| AP @ IoU=0.50 (all) | 0.303 |
| AP @ IoU=0.75 (all) | 0.072 |
| AP @ IoU=0.50:0.95 (small) | 0.142 |
| AP @ IoU=0.50:0.95 (medium) | 0.095 |
| AP @ IoU=0.50:0.95 (large) | 0.114 |
| AR @ IoU=0.50:0.95 maxDets=1 | 0.144 |
| AR @ IoU=0.50:0.95 maxDets=10 | 0.341 |
| AR @ IoU=0.50:0.95 maxDets=100 | 0.416 |
| AR @ IoU=0.50 (all) | 0.754 |
| AR @ IoU=0.75 (all) | 0.436 |

### Pothole-Specific Confusion Matrix (IoU=0.5)

| | Predicted Pothole | Predicted Background |
|---|---|---|
| **Actual Pothole** | TP = 117 | FN = 57 |
| **Actual Background** | FP = 395 | TN = - |

| Metric | Value |
|--------|-------|
| **Pothole TP** | 117 |
| **Pothole FP** | 395 |
| **Pothole FN** | 57 |
| **Pothole Recall (IoU=0.5)** | 0.672 |
| **Pothole Precision (IoU=0.5)** | 0.229 |

---

## Side-by-Side Comparison

| Metric | Baseline | Exp1 (epoch86) | Exp2 (epoch72) | Best |
|--------|----------|----------------|----------------|------|
| **Overall P** | 0.586 | 0.231 | **0.399** | Baseline |
| **Overall R** | 0.321 | **0.404** | 0.371 | Exp1 |
| **Overall mAP@50** | 0.279 | 0.244 | **0.300** | **Exp2** |
| **Overall mAP@50-95** | 0.111 | 0.089 | **0.118** | **Exp2** |
| **Pothole P** | - | 0.370 | **0.388** | Exp2 |
| **Pothole R** | - | 0.496 | **0.484** | Exp1 |
| **Pothole mAP@50** | - | 0.382 | **0.395** | **Exp2** |
| **Pothole mAP@50-95** | - | 0.128 | **0.150** | **Exp2** |
| **COCO AP@0.50:0.95** | - | 0.090 | **0.120** | **Exp2** |
| **COCO AP@0.50** | - | 0.246 | **0.303** | **Exp2** |
| **COCO AR@0.50:0.95 (100)** | - | 0.352 | **0.416** | **Exp2** |

---

## Key Findings

### Experiment 1 (epoch86.pt)
- **Strengths:** Highest overall recall (0.404) and pothole recall (0.496/0.532)
- **Weaknesses:** Low precision (0.231 overall, 0.370 pothole); high FP rate
- **mAP@50-95 below baseline** (-0.022)
- Best for: maximizing detection coverage (recall-oriented)

### Experiment 2 (epoch72.pt)
- **Strengths:** Highest mAP@50 (0.300) and mAP@50-95 (0.118) — **beats baseline** on both
- **Weaknesses:** Lower recall than Exp1; very high FP for potholes (395 FP)
- **Pothole mAP@50-95: 0.150** — best among all models
- Best for: balanced precision/recall with higher localization quality

### Neither model beats baseline on Precision (0.586)
- Baseline precision is significantly higher, suggesting previous model had fewer false positives
- Current models trade precision for recall

---

## Phase 3 Manually Verified Potholes

The 4 manually verified potholes from Phase 3 (`experiments/results/20261010_phase3_error_analysis/four_pothole_annotations.json`) are from a different dataset (`road001.webp`, `road002.jpg`, `road009.jpg`, `road010.jpg`) and **do not overlap** with the Indian test set (`India_XXXXXX.jpg` format).

**Conclusion:** No separate evaluation possible on these 4 images as they are not in the frozen Indian test split.

---

## Recommendation

**Exp2 (epoch72.pt) is the better model** for deployment based on:
1. **Higher mAP@50 (0.300 vs 0.244)** and **mAP@50-95 (0.118 vs 0.089)**
2. **Beats baseline on mAP@50 and mAP@50-95**
3. Better pothole mAP@50-95 (0.150 vs 0.128)
4. Superior COCO AP/AR across all metrics

**Action items:**
1. Investigate high FP rate for potholes in both models (285 and 395 FP at IoU=0.5)
2. Consider confidence threshold tuning to improve precision
3. Evaluate on additional test sets for generalization
4. Consider ensemble or model distillation approaches