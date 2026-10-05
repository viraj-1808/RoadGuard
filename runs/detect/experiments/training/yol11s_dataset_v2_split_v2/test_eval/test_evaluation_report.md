# Test Evaluation Report

## Overview
This report summarizes the held-out test evaluation of the YOLO11s baseline model.

## Provenance

### Model Checkpoint
- **Path**: runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt
- **SHA256**: 721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823
- **Match Expected**: True

### Dataset Configuration
- **Data YAML**: experiments/dataset/yolo_rdd2022_india/data.yaml
- **Train**: images/train
- **Val**: images/val  
- **Test**: images/test

### Test Split Statistics
- **Images**: 230
- **Ground Truth Objects**: 679
- **Class Distribution**:
  - longitudinal_crack: 66 instances
  - transverse_crack: 5 instances
  - alligator_crack: 96 instances
  - pothole: 512 instances

### Evaluation Configuration
- **Split**: test (explicitly specified, not using Ultralytics default)
- **Model**: YOLO11s
- **Task**: Object Detection
- **Metrics**: Standard COCO metrics (mAP@0.5:0.95, mAP@0.5, etc.)

## Results

### Overall Metrics
- **mAP@0.5:0.95**: 0.0903
- **mAP@0.5**: 0.252
- **mAP@0.75**: 0.120
- **Precision**: 0.299
- **Recall**: 0.312

### Per-Class Metrics
- **longitudinal_crack**: mAP=0.0871, P=0.340, R=0.288
- **transverse_crack**: mAP=0.00923, P=0.000, R=0.000
- **alligator_crack**: mAP=0.135, P=0.426, R=0.490
- **pothole**: mAP=0.130, P=0.429, R=0.469

### Speed Performance
- **Preprocess**: 4.6 ms/image
- **Inference**: 11.8 ms/image
- **Loss**: 0.0 ms/image
- **Postprocess**: 2.4 ms/image

## Artifacts Generated
- predictions.json: Test-only predictions (230 unique images)
- confusion_matrix.png: Test confusion matrix
- confusion_matrix_normalized.png: Normalized test confusion matrix
- BoxP_curve.png: Precision-Recall curve for precision
- BoxR_curve.png: Precision-Recall curve for recall
- BoxF1_curve.png: Precision-Recall curve for F1-score
- BoxPR_curve.png: Precision-Recall curve
- test_metrics.json: Overall and per-class metrics
- test_evaluation_report.md: This file
- test_evaluation_provenance.json: Reproducibility information

## Verification
- Best.pt SHA256 matches expected value: True
- data.yaml confirms train/val/test split structure: True
- split_manifest_fixed.json confirms test=230 images, 679 objects: True
- 230 unique test images evaluated: True
- 679 test ground-truth objects represented: True
- No training or validation images evaluated: True
- Model checkpoint unchanged during evaluation: True
