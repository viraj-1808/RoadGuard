# YOLO11s Test Set Error Analysis Report

**Model**: runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt
**Dataset**: experiments/dataset/yolo_rdd2022_india/data.yaml
**Test Images**: 230
**Ground Truth Objects**: 679
**Predictions**: 230 images, 17198 detections

## Overall Performance

- **Precision**: 0.0347
- **Recall**: 0.8778
- **F1-Score**: 0.0667
- **True Positives**: 596
- **False Positives**: 16602
- **False Negatives**: 83

## Per-Class Performance

| Class | GT Count | TP | FP | FN | Precision | Recall | F1 |
|-------|----------|----|----|----|-----------|--------|----|
| longitudinal_crack | 66 | 55 | 2715 | 11 | 0.0199 | 0.8333 | 0.0388|
| transverse_crack | 5 | 2 | 531 | 3 | 0.0038 | 0.4000 | 0.0074|
| alligator_crack | 96 | 87 | 2638 | 9 | 0.0319 | 0.9062 | 0.0617|
| pothole | 512 | 452 | 10718 | 60 | 0.0405 | 0.8828 | 0.0774|

## False Negative Patterns

### longitudinal_crack (class 0): 11 missed objects
**Pattern**: POSSIBLE PATTERN: Large object size

### transverse_crack (class 1): 3 missed objects
**Pattern**: POSSIBLE PATTERN: Limited samples

### alligator_crack (class 2): 9 missed objects
**Pattern**: POSSIBLE PATTERN: Large object size

### pothole (class 3): 60 missed objects
**Pattern**: POSSIBLE PATTERN: Large object size

## False Positive Patterns

### longitudinal_crack (class 0): 2715 false detections
**Pattern**: LIKELY: Low-confidence false detections (noise/texture)

### transverse_crack (class 1): 531 false detections
**Pattern**: LIKELY: Low-confidence false detections (noise/texture)

### alligator_crack (class 2): 2638 false detections
**Pattern**: LIKELY: Low-confidence false detections (noise/texture)

### pothole (class 3): 10718 false detections
**Pattern**: LIKELY: Low-confidence false detections (noise/texture)

## Localization Quality

- **Mean IoU**: 0.709
- **IoU Std**: 0.096
- **Median IoU**: 0.718
- **Detections near IoU 0.5 boundary**: 37

## Confidence Analysis

- **TP Confidence Mean**: 0.209
- **FP Confidence Mean**: 0.027
- **Confidence Separation**: 0.181

## Most Difficult Images

| Image ID | GT | Pred | TP | FP | FN | F1 |
|----------|----|------|----|----|----|----|
| India_005569 | 2 | 78 | 0 | 78 | 2 | 0.000 |
| India_007943 | 1 | 74 | 0 | 74 | 1 | 0.000 |
| India_006532 | 1 | 130 | 1 | 129 | 0 | 0.015 |
| India_000771 | 1 | 118 | 1 | 117 | 0 | 0.017 |
| India_008127 | 1 | 115 | 1 | 114 | 0 | 0.017 |
| India_009205 | 1 | 105 | 1 | 104 | 0 | 0.019 |
| India_000545 | 1 | 103 | 1 | 102 | 0 | 0.019 |
| India_004935 | 1 | 103 | 1 | 102 | 0 | 0.019 |
| India_004553 | 1 | 84 | 1 | 83 | 0 | 0.024 |
| India_003191 | 1 | 79 | 1 | 78 | 0 | 0.025 |

## Special Notes

- **Transverse Crack Warning**: Only 5 test instances. Very small sample size makes statistical analysis unreliable.
- All analysis performed on test split only.
- Predictions use 1-indexed category_ids converted to 0-indexed for comparison.
