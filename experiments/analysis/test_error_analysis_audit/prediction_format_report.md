# Prediction Format Report

## 1. predictions.json Structure

The predictions.json file contains predictions in COCO-style format with the following structure:

```json
{
  "image_id": "India_000103",
  "file_name": "India_000103.jpg", 
  "category_id": 4,        // 1=longitudinal_crack, 2=transverse_crack, 3=alligator_crack, 4=pothole
  "bbox": [133.07, 478.041, 278.281, 87.526],  // [x, y, width, height] in pixels
  "score": 0.76899
}
```

## 2. Key Characteristics

### 2.1 Class Mapping
- Predictions use **1-indexed category_ids** (1-4)
- Custom analysis converts to 0-indexed: `PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}`
- Ground truth labels use **0-indexed class_ids** (0-3)

### 2.2 Coordinate Format
- Bounding boxes are in **pixel coordinates**: [x, y, width, height]
- YOLO label files use normalized format: [class_id, x_center, y_center, width, height]
- Conversion: `x = (x_center - width/2) * img_width` (where img_width=720)

### 2.3 Confidence Values
- **Range**: 0.001 to 0.999+ (extensive range)
- **Distribution**: Very low confidence values (0.001-0.01) are prevalent
- **Mean FP confidence**: 0.027
- **Mean TP confidence**: 0.209

### 2.4 Image Coverage
- Total unique images: **230** (matches test split)
- All test images are represented in predictions.json
- Predictions are already grouped by image_id

### 2.5 Prediction Volume
- **Total predictions**: 17,198 across 230 images
- **Average predictions per image**: 74.8
- **Median predictions per image**: ~62 (estimated)
- **Range**: 2 to 130+ predictions per image (extreme outliers exist)

### 2.6 Prediction Filtering
- **Confidence Threshold**: **None applied** - ALL predictions included
- **NMS**: **Not applied** - overlapping predictions included
- **Inference Parameters**: Predictions generated with Ultralytics `model.val()` but no post-processing

## 3. Comparison with Ultralytics Validation Protocol

| Aspect | Custom Analysis | Ultralytics model.val() |
|--------|----------------|------------------------|
| Confidence Threshold | None (all predictions) | Default: 0.001 |
| NMS Applied | No | Yes (default IoU: 0.7) |
| IoU Threshold | 0.5 (matching) | 0.5 (evaluation) |
| Predictions.json | Contains ALL raw outputs | Should contain NMS-filtered predictions |

## 4. Inference Parameters Used

Based on the test_evaluation_provenance.json:
- **Model**: YOLO11s
- **Framework**: Ultralytics YOLO
- **Framework Version**: 8.4.138
- **Default Ultralytics model.val() settings**:
  - Confidence threshold: 0.001
  - NMS IoU threshold: 0.7
  - Batch size: Not specified
  - Device: GPU (CUDA)

## 5. Impact of Format on Analysis

### 5.1 Inflated False Positives
The inclusion of low-confidence noise detections (mean 0.027) and duplicate overlapping boxes results in:
- 16,602 false positives (96.5% of all predictions)
- Mean FP confidence much lower than TP confidence (0.027 vs 0.209)

### 5.2 False Sense of High Performance
The 0.8778 recall is inflated because:
- Every prediction, no matter how low confidence, counts as a potential true positive
- A prediction with confidence 0.001 that happens to overlap a GT at IoU >= 0.5 is counted as a TP
- In reality, these are likely noise detections that would be filtered out by confidence thresholding

### 5.3 Misleading Class Distribution
While the confusion matrix shows diagonal dominance (correct class predictions), the absolute counts are inflated by:
- Low-confidence false positives that happen to have the "correct" class ID
- Duplicate predictions for the same object

## 6. Recommendations for Proper Analysis

### 6.1 Apply Confidence Threshold
Use a reasonable confidence threshold (e.g., 0.25 or 0.50) to filter predictions before analysis:

```python
# Example thresholding
thresholded_predictions = [p for p in predictions if p['score'] >= 0.25]
```

### 6.2 Apply NMS
Apply Non-Maximum Suppression before computing metrics:

```python
# Example NMS
from ultralytics.utils.ops import non_max_suppression

nms_predictions = non_max_suppression(
    torch.tensor([p['bbox'] for p in predictions]),
    torch.tensor([p['score'] for p in predictions]),
    conf_thres=0.25,
    iou_thres=0.7
)
```

### 6.3 Use Ultralytics Evaluation Protocol
The official Ultralytics `model.val()` command already implements the correct protocol:

```python
from ultralytics import YOLO

model = YOLO("runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt")
results = model.val(
    data="experiments/dataset/yolo_rdd2022_india/data.yaml",
    split="test"
)
```

This command automatically handles:
1. Confidence thresholding
2. NMS application  
3. Standard COCO evaluation protocol
4. Proper precision/recall/mAP computation

## 7. Data Quality Assessment

### 7.1 Good Practices
- **Class mapping**: Clear 1-indexed to 0-indexed conversion
- **Bounding boxes**: Pixel coordinates provided (unambiguous interpretation)
- **Confidence scores**: Provided for all predictions (good for analysis)

### 7.2 Issues Identified
- **No filtering**: Predictions.json contains all raw outputs before post-processing
- **Duplicate predictions**: Overlapping boxes suggest NMS was not applied
- **Extremely low confidence values**: Predictions with confidence 0.001 indicate noise
- **High prediction volume**: 74.8 predictions per image is excessive even with conf=0.001

## 8. Conclusion

The predictions.json format is **unsuitable for direct performance evaluation** because:

1. **No confidence threshold applied** - includes noise detections
2. **No NMS applied** - includes duplicate/overlapping detections  
3. **Raw model outputs** - not the final detections used for evaluation

For proper model evaluation, either:
1. **Apply confidence threshold + NMS** to predictions.json before analysis
2. **Use Ultralytics model.val()** which already implements the correct pipeline
3. **Regenerate predictions.json** after applying proper post-processing

The current format is useful for understanding raw model behavior but not for final performance metrics.