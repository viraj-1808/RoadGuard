# Experiment 1 Validation Report

**Checkpoint:** `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt`  
**Dataset:** `experiments/dataset/yolo_rdd2022_india/data.yaml` (val split = 229 images)  
**Validation Date:** 2026-10-11

---

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| **Command** | `python run_validation.py` (see script below) |
| **Model Path** | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt` |
| **Model SHA-256** | `885db673fe10ed7d18c552e16320850efb5d5902c42f63acaaa25ecb2666663e` |
| **Ultralytics Version** | 8.4.138 |
| **PyTorch Version** | 2.14.0+cu126 |
| **CUDA Available** | True |
| **CUDA Device** | NVIDIA GeForce RTX 4050 Laptop GPU (6140 MiB) |
| **Image Size** | 736 (requested 720, adjusted to multiple of 32) |
| **Batch Size** | 16 |
| **Device** | 0 (GPU) |
| **Confidence Threshold** | 0.001 |
| **IoU Threshold (NMS)** | 0.6 |
| **Class Order** | `['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole']` |
| **Split Validated** | `val` (229 images, 632 instances) |

### Validation Script

```python
from ultralytics import YOLO
from multiprocessing import freeze_support

def main():
    model = YOLO("runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt")
    metrics = model.val(
        data="experiments/dataset/yolo_rdd2022_india/data.yaml",
        imgsz=720,
        batch=16,
        device=0,
        save_json=True,
        project="experiments/results/20261010_phase2_validation",
        name="exp1_epoch86_val",
        exist_ok=False,
        verbose=True
    )
    return metrics

if __name__ == '__main__':
    freeze_support()
    main()
```

---

## Overall Metrics

| Metric | Value |
|--------|-------|
| **Precision (P)** | 0.281 |
| **Recall (R)** | 0.253 |
| **mAP@0.5 (mAP50)** | 0.216 |
| **mAP@0.5:0.95 (mAP50-95)** | 0.0794 |

---

## Per-Class Metrics

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|-------|--------|-----------|-----------|--------|-------|----------|
| **longitudinal_crack** | 55 | 76 | 0.229 | 0.273 | 0.145 | 0.0602 |
| **transverse_crack** | 4 | 4 | 0.000 | 0.000 | 0.000 | 0.000 |
| **alligator_crack** | 79 | 96 | 0.402 | 0.260 | 0.274 | 0.0997 |
| **pothole** | 229 | 456 | 0.493 | 0.480 | 0.444 | 0.158 |
| **ALL (weighted)** | 229 | 632 | **0.281** | **0.253** | **0.216** | **0.0794** |

---

## COCO Evaluation Metrics

### Average Precision (AP)

| Metric | Value |
|--------|-------|
| AP @ IoU=0.50:0.95 (all areas) | 0.082 |
| AP @ IoU=0.50 (all areas) | 0.217 |
| AP @ IoU=0.75 (all areas) | 0.045 |
| AP @ IoU=0.50:0.95 (small) | 0.073 |
| AP @ IoU=0.50:0.95 (medium) | 0.067 |
| AP @ IoU=0.50:0.95 (large) | 0.109 |

### Average Recall (AR)

| Metric | Value |
|--------|-------|
| AR @ IoU=0.50:0.95 (maxDets=1) | 0.105 |
| AR @ IoU=0.50:0.95 (maxDets=10) | 0.234 |
| AR @ IoU=0.50:0.95 (maxDets=100) | 0.271 |
| AR @ IoU=0.50:0.95 (small) | 0.145 |
| AR @ IoU=0.50:0.95 (medium) | 0.220 |
| AR @ IoU=0.50:0.95 (large) | 0.314 |
| AR @ IoU=0.50 (maxDets=100) | 0.576 |
| AR @ IoU=0.75 (maxDets=100) | 0.220 |

---

## Confusion Matrix

The confusion matrix was generated and saved as:
- `confusion_matrix.png` (raw counts)
- `confusion_matrix_normalized.png` (normalized)

**Note:** The raw confusion matrix data is available in the validation output directory. Due to the format of the ultralytics output, the exact matrix values should be read from the saved PNG or extracted from the validator object programmatically.

---

## PR Curves

Saved as `BoxPR_curve.png` - Precision-Recall curves for each class and overall.

---

## F1 Curves

Saved as `BoxF1_curve.png` - F1-score vs confidence threshold for each class and overall.

---

## P/R Curves

- `BoxP_curve.png` - Precision vs confidence threshold
- `BoxR_curve.png` - Recall vs confidence threshold

---

## Inference Speed

| Stage | Time per Image |
|-------|----------------|
| Preprocess | 4.3 ms |
| Inference | 11.1 ms |
| Loss | 0.0 ms |
| Postprocess | 1.0 ms |
| **Total** | **~16.4 ms** |

---

## FP/FN Examples

Visual examples saved in validation output directory:
- `val_batch0_labels.jpg` / `val_batch0_pred.jpg` - Ground truth vs predictions (batch 0)
- `val_batch1_labels.jpg` / `val_batch1_pred.jpg` - Ground truth vs predictions (batch 1)
- `val_batch2_labels.jpg` / `val_batch2_pred.jpg` - Ground truth vs predictions (batch 2)

---

## Key Observations

1. **Pothole detection** performs best (mAP50=0.444), likely due to highest instance count (456) and distinct visual features.

2. **Transverse crack** completely fails (all metrics = 0.000) with only 4 instances in validation set - severe data scarcity.

3. **Longitudinal crack** struggles (mAP50=0.145) despite 76 instances - may need more diverse training samples or augmentation.

4. **Alligator crack** shows moderate performance (mAP50=0.274) with 96 instances.

5. **Overall mAP50-95 (0.079)** is significantly lower than mAP50 (0.216), indicating poor localization precision at higher IoU thresholds.

6. **COCO AP@0.5:0.95 (0.082)** aligns with ultralytics mAP50-95 (0.0794), confirming consistency.

---

## Output Files

All validation artifacts saved to:
```
runs/detect/experiments/results/20261010_phase2_validation/exp1_epoch86_val-3/
├── BoxF1_curve.png
├── BoxPR_curve.png
├── BoxP_curve.png
├── BoxR_curve.png
├── confusion_matrix.png
├── confusion_matrix_normalized.png
├── predictions.json (COCO format)
├── val_batch0_labels.jpg
├── val_batch0_pred.jpg
├── val_batch1_labels.jpg
├── val_batch1_pred.jpg
├── val_batch2_labels.jpg
└── val_batch2_pred.jpg
```