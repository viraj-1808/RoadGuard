# Experiment 2 Epoch 72 Validation Report

**Generated:** 2026-10-11T09:47:00.960046

## Experiment Configuration

- **Checkpoint:** `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt`
- **Model SHA-256:** `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5`
- **Data YAML:** `experiments/dataset/yolo_rdd2022_india/data.yaml`
- **Validation Split:** 229 images (Dataset A val)
- **Command:** `model.val(data='experiments/dataset/yolo_rdd2022_india/data.yaml', imgsz=720, batch=16, device=0, save_json=True, project='experiments/results/20261010_phase2_validation', name='exp2_epoch72_val', exist_ok=False, verbose=True)`

## Package Versions

- **ultralytics:** 8.4.138
- **torch:** 2.14.0+cu126
- **opencv:** 4.14.0
- **numpy:** 2.5.2

## Inference Settings

- **Image Size:** 720 (effective: 736 - multiple of stride 32)
- **Batch Size:** 16
- **Device:** cuda:0
- **Confidence Threshold:** 0.001
- **IoU Threshold (NMS):** 0.6
- **Class Order:** ['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole']

## Overall Metrics

| Metric | Value |
|--------|-------|
| mp | 0.5388 |
| mr | 0.1973 |
| map50 | 0.2195 |
| map50_95 | 0.0893 |
| map75 | 0.0491 |
| fitness | 0.0893 |

## Per-Class Metrics

| Class | Precision | Recall | mAP@50 | mAP@50-95 | F1 |
|-------|-----------|--------|--------|-----------|-----|
| longitudinal_crack | 0.2431 | 0.1711 | 0.1954 | 0.0890 | 0.2008 |
| transverse_crack | 1.0000 | 0.0000 | 0.0357 | 0.0079 | 0.0000 |
| alligator_crack | 0.4658 | 0.2083 | 0.2609 | 0.1042 | 0.2879 |
| pothole | 0.4461 | 0.4098 | 0.3858 | 0.1562 | 0.4272 |

## Confusion Matrix (Raw Counts)

Rows = Ground Truth, Cols = Predicted (last row/col = background)

| | longitudinal_crack | transverse_crack | alligator_crack | pothole | background |
|---|---|---|---|---|
| longitudinal_crack | 7 | 0 | 0 | 0 | 7 |
| transverse_crack | 0 | 0 | 0 | 0 | 0 |
| alligator_crack | 0 | 0 | 15 | 1 | 5 |
| pothole | 0 | 0 | 1 | 110 | 51 |
| background | 69 | 4 | 80 | 345 | 0 |

## Confusion Matrix (Normalized %)

Rows = Ground Truth, Cols = Predicted (last row/col = background)

| | longitudinal_crack | transverse_crack | alligator_crack | pothole | background |
|---|---|---|---|---|
| longitudinal_crack | 50.00% | 0.00% | 0.00% | 0.00% | 50.00% |
| transverse_crack | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| alligator_crack | 0.00% | 0.00% | 71.43% | 4.76% | 23.81% |
| pothole | 0.00% | 0.00% | 0.62% | 67.90% | 31.48% |
| background | 13.86% | 0.80% | 16.06% | 69.28% | 0.00% |

## COCO Evaluation Metrics

| Metric | Value |
|--------|-------|
| AP_IoU_50_95 | 0.091 |
| AP_IoU_50 | 0.221 |
| AP_IoU_75 | 0.051 |
| AP_small | 0.105 |
| AP_medium | 0.093 |
| AP_large | 0.106 |
| AR_max1 | 0.112 |
| AR_max10 | 0.319 |
| AR_max100 | 0.398 |
| AR_small | 0.315 |
| AR_medium | 0.288 |
| AR_large | 0.438 |
| AR_IoU_50 | 0.806 |
| AR_IoU_75 | 0.313 |

## Speed Metrics (per image)

| Stage | Time (ms) |
|-------|-----------|
| preprocess | 3.2 |
| inference | 12.0 |
| loss | 0.0 |
| postprocess | 0.8 |

## Generated Artifacts

The following files were generated in the validation output directory:

- `predictions.json` - COCO format predictions
- `confusion_matrix.png` - Confusion matrix visualization
- `confusion_matrix_normalized.png` - Normalized confusion matrix
- `BoxPR_curve.png` - Precision-Recall curves per class
- `BoxF1_curve.png` - F1 curves per class
- `BoxP_curve.png` - Precision curves per class
- `BoxR_curve.png` - Recall curves per class
- `val_batch*_labels.jpg` - Ground truth visualization
- `val_batch*_pred.jpg` - Prediction visualization

## Notes

- Validation performed on **Dataset A validation split (229 images)** for fair comparison
- **NOT using frozen test split**
- Image size 720 adjusted to 736 (multiple of max stride 32)
- Best mAP50 during training was 0.6029 at epoch 72; validation mAP50 = 0.2195
