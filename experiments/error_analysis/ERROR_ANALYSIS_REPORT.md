# Dataset A Validation Error Analysis Report

## Purpose
This report documents the visual error analysis of the Experiment 2 model's
predictions on the Dataset A validation split. It generates annotated images
that illustrate **missed detections**, **false positives**, and **successful detections**
to build a visual evidence base for root-cause analysis before designing Experiment 3.

## Source Artifacts
- **Prediction file**: `runs\detect\val-5\prediction_boxes.json`
- **Image dir**: `experiments\dataset\yolo_rdd2022_india\images\val/`
- **Label dir**: `experiments\dataset\yolo_rdd2022_india\labels\val/`
- **Experiment 2 model**: `runs/detect/experiments/training/yol11s_experiment2/weights/best.pt`

## Analysis Settings
- **Confidence threshold**: 0.25
- **IoU matching threshold**: 0.5
- **Matching**: class-aware greedy (highest-confidence prediction matched to best-IoU ground truth of same class)
- **Image size**: 720x720 (Dataset A)

## Class Mapping
| ID | Class Name |
|----|------------|
| 0 | longitudinal_crack |
| 1 | transverse_crack |
| 2 | alligator_crack |
| 3 | pothole |

## Scope
- **Images analyzed**: 229
- **Total ground-truth objects**: 632
- **Total TP**: 168
- **Total FP**: 132
- **Total FN**: 464
- **Overall precision**: 0.5600
- **Overall recall**: 0.2658

## Per-Class Breakdown
| Class | GT | TP | FP | FN | Precision | Recall |
|-------|----|----|----|----|-----------|--------|
| longitudinal_crack | 76 | 7 | 18 | 69 | 0.2800 | 0.0921 |
| transverse_crack | 4 | 0 | 0 | 4 | 0.0000 | 0.0000 |
| alligator_crack | 96 | 17 | 12 | 79 | 0.5862 | 0.1771 |
| pothole | 456 | 144 | 102 | 312 | 0.5854 | 0.3158 |

## Selected Examples
### missed (12 images)
- `India_002020`: TP=0 FP=1 FN=8 | GT=8 Preds=1
- `India_001722`: TP=0 FP=1 FN=10 | GT=10 Preds=1
- `India_006847`: TP=1 FP=0 FN=1 | GT=2 Preds=1
- `India_002509`: TP=1 FP=0 FN=4 | GT=5 Preds=1
- `India_000223`: TP=1 FP=1 FN=6 | GT=7 Preds=2
- `India_003177`: TP=1 FP=0 FN=3 | GT=4 Preds=1
- `India_003576`: TP=0 FP=1 FN=4 | GT=4 Preds=1
- `India_000994`: TP=3 FP=0 FN=6 | GT=9 Preds=3
- `India_000352`: TP=0 FP=0 FN=4 | GT=4 Preds=0
- `India_000685`: TP=1 FP=1 FN=3 | GT=4 Preds=2
- `India_000576`: TP=0 FP=0 FN=3 | GT=3 Preds=0
- `India_001443`: TP=0 FP=1 FN=4 | GT=4 Preds=1
### false_positives (12 images)
- `India_000710`: TP=3 FP=4 FN=0 | GT=3 Preds=7
- `India_003686`: TP=1 FP=2 FN=1 | GT=2 Preds=3
- `India_000586`: TP=0 FP=1 FN=4 | GT=4 Preds=1
- `India_003741`: TP=1 FP=4 FN=6 | GT=7 Preds=5
- `India_000654`: TP=1 FP=1 FN=0 | GT=1 Preds=2
- `India_001037`: TP=0 FP=2 FN=3 | GT=3 Preds=2
- `India_000759`: TP=1 FP=1 FN=1 | GT=2 Preds=2
- `India_002775`: TP=1 FP=1 FN=3 | GT=4 Preds=2
- `India_006739`: TP=1 FP=4 FN=1 | GT=2 Preds=5
- `India_002340`: TP=0 FP=1 FN=1 | GT=1 Preds=1
- `India_002877`: TP=3 FP=2 FN=2 | GT=5 Preds=5
- `India_003048`: TP=0 FP=1 FN=1 | GT=1 Preds=1
### successful (12 images)
- `India_000808`: TP=3 FP=2 FN=2 | GT=5 Preds=5
- `India_000054`: TP=1 FP=1 FN=1 | GT=2 Preds=2
- `India_001314`: TP=2 FP=1 FN=3 | GT=5 Preds=3
- `India_000373`: TP=2 FP=0 FN=0 | GT=2 Preds=2
- `India_001419`: TP=2 FP=0 FN=1 | GT=3 Preds=2
- `India_002069`: TP=2 FP=1 FN=1 | GT=3 Preds=3
- `India_008188`: TP=2 FP=1 FN=1 | GT=3 Preds=3
- `India_003556`: TP=2 FP=0 FN=0 | GT=2 Preds=2
- `India_004612`: TP=1 FP=0 FN=2 | GT=3 Preds=1
- `India_005152`: TP=2 FP=0 FN=0 | GT=2 Preds=2
- `India_006087`: TP=1 FP=0 FN=2 | GT=3 Preds=1
- `India_006749`: TP=2 FP=1 FN=0 | GT=2 Preds=3

## Selection Methodology
Selection is deterministic (seed=42).

- **Missed**: filtered to images with FN > 0, sorted by total severity, then scored to prioritize class diversity.
- **False positives**: filtered to images with FP > 0, excluding images already selected for missed, scored for class diversity.
- **Successful**: filtered to images with TP >= 3 and (FP + FN) <= 0.6 * TP, excluding images already selected for the first two categories.
- Each category targets 12 images with representation across the 4 classes where possible.

## Limitations
Selection tries to represent all four classes but is constrained by the available error distribution.
If a class has too few representative examples, it may be under-represented or absent in a category.
Image selection is best-effort diversity, not exhaustive ranking.

## Outputs
- Annotated images: `experiments/error_analysis/missed/`, `false_positives/`, `successful/`
- Index CSV: `experiments/error_analysis/ERROR_ANALYSIS_INDEX.csv`
- This report: `experiments/error_analysis/ERROR_ANALYSIS_REPORT.md`

## Visual Legend
- **Green**: Ground-truth box that was matched (TP)
- **Orange**: Ground-truth box that was missed (FN)
- **Blue**: Prediction that correctly matched a GT (TP)
- **Red**: Prediction with no matching GT (FP)
