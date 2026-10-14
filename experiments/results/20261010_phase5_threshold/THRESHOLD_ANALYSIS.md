# Threshold Analysis for Pothole Detection (Class 3)

Models: exp1_epoch86, exp2_epoch72
IoU threshold for matching: 0.5
NMS IoU: 0.6
Confidence thresholds tested: [0.05, 0.1, 0.15, 0.2, 0.25]

## exp1_epoch86

| Threshold | Precision | Recall | F1 | FP | TP | FN |
|-----------|-----------|--------|-----|----|----|----|
| 0.05 | 0.0119 | 0.0044 | 0.0064 | 166 | 2 | 454 |
| 0.10 | 0.0090 | 0.0022 | 0.0035 | 110 | 1 | 455 |
| 0.15 | 0.0118 | 0.0022 | 0.0037 | 84 | 1 | 455 |
| 0.20 | 0.0156 | 0.0022 | 0.0038 | 63 | 1 | 455 |
| 0.25 | 0.0200 | 0.0022 | 0.0040 | 49 | 1 | 455 |

**Best threshold for pothole F1: 0.05 (F1 = 0.0064)**

## exp2_epoch72

| Threshold | Precision | Recall | F1 | FP | TP | FN |
|-----------|-----------|--------|-----|----|----|----|
| 0.05 | 0.0410 | 0.0110 | 0.0173 | 117 | 5 | 451 |
| 0.10 | 0.0357 | 0.0044 | 0.0078 | 54 | 2 | 454 |
| 0.15 | 0.0588 | 0.0044 | 0.0082 | 32 | 2 | 454 |
| 0.20 | 0.0476 | 0.0022 | 0.0042 | 20 | 1 | 455 |
| 0.25 | 0.0500 | 0.0022 | 0.0042 | 19 | 1 | 455 |

**Best threshold for pothole F1: 0.05 (F1 = 0.0173)**

## Summary: Best Pothole F1 by Model

| Model | Best Threshold | Best F1 | Precision | Recall |
|-------|----------------|---------|-----------|--------|
| exp1_epoch86 | 0.05 | 0.0064 | 0.0119 | 0.0044 |
| exp2_epoch72 | 0.05 | 0.0173 | 0.0410 | 0.0110 |
