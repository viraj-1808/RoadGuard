# Corrected Error Analysis Methodology

## Overview

This analysis implements a corrected diagnostic pipeline for YOLO11s test set evaluation.

## Key Corrections Applied

1. **Confidence Filtering**: Predictions with confidence < 0.25 are excluded
2. **Non-Maximum Suppression (NMS)**: IoU threshold = 0.7 per image per class
3. **Class-Aware Matching**: IoU >= 0.5, 1:1 ground truth:prediction mapping
4. **Confidence-Ranked Matching**: Higher IoU + higher confidence prioritized
5. **Correct Metric Computation**: Only valid detections contribute to TP/FP/FN

## Pipeline Steps

1. Load predictions.json (17,198 raw predictions)
2. Filter predictions: conf >= 0.25 (682 predictions remain)
3. Apply NMS per image per class (iou=0.7)
4. For each image: class-aware one-to-one matching (IoU >= 0.5)
5. Count valid TP/FP/FN
6. Generate error metrics

## Comparison with Official Ultralytics Metrics

Official Ultralytics metrics (provided for reference, not to be replaced):
- Precision: 0.299
- Recall: 0.312
- mAP50: 0.252
- mAP50-95: 0.0903

## Methodological Gaps Acknowledged

1. Single IoU threshold (0.5) only captures mAP50 performance
2. No area scaling or size binning for scale-aware analysis
3. Limited to detection accuracy, no orientation or severity metrics
4. Small sample sizes for rare classes (e.g., transverse cracks)
5. No analysis of detection timing or training dynamics
