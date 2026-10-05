# Extreme Prediction Cases Analysis

## Images with Highest Prediction Counts

The following images have exceptionally high prediction counts (78+ predictions per image), which are the primary drivers of the inflated false positive count.

### 1. India_005569

- **Ground Truth**: 2 objects
  - Class 2 (alligator_crack): [0.672917, 0.881944, 0.573611, 0.227778] (normalized)
  - Class 3 (pothole): [0.370139, 0.922222, 0.054167, 0.047222] (normalized)
- **Predictions**: 78 total
- **Custom Analysis Result**: 0 TP, 78 FP, 2 FN
- **Analysis**: This image has only 2 GT objects but 78 predictions. The vast majority of predictions are low-confidence noise detection. The model predicted many overlapping boxes that all score very low confidence.
- **Key Observation**: The high prediction count is caused by **duplicate/overlapping detections** (no NMS applied). After NMS with iou=0.7, the count would be dramatically reduced.
- **Visual characteristic**: Large, overlapping prediction region suggesting texture or shadow response.

### 2. India_007943

- **Ground Truth**: 1 object (class to be verified)
- **Predictions**: 74 total
- **Custom Analysis Result**: 0 TP, 74 FP, 1 FN
- **Analysis**: Similar to India_005569 - excessive low-confidence predictions with no NMS filtering.
- **Key Observation**: With only 1 GT object, the expected FP count is 73, indicating severe over-prediction.

### 3. India_006532

- **Ground Truth**: 1 object (class to be verified)
- **Predictions**: 130 total
- **Custom Analysis Result**: 1 TP, 129 FP, 0 FN
- **Analysis**: Extremely high prediction count (130) for a single GT object. Only 1 prediction matched, 129 were false positives.
- **Key Observation**: This image has the highest prediction count in the test set, suggesting the model produced many confident-looking but incorrect detections.

## Prediction Count Distribution

Based on the analysis, the prediction distribution shows:
- **Mean predictions per image**: 74.8
- **Extreme outliers**: Images with 78+, 74+, and 130 predictions
- **Typical range**: Most images have 40-100 predictions

## Root Cause of High Prediction Counts

### 1. No NMS Applied
The predictions.json file does not contain NMS-filtered predictions. Each detection proposal (anchor + prediction) that scores above the minimum confidence is included as a separate prediction.

### 2. Low Confidence Threshold
Predictions with confidence as low as 0.001 are included. The Ultralytics default val confidence threshold is also 0.001, but NMS is still applied to reduce overlapping detections.

### 3. Duplicate Detections
For each ground truth object, multiple overlapping prediction boxes are generated at different confidence levels. Without NMS, these are all counted as separate predictions.

## Impact on Metrics

### Custom Analysis Metrics
- Precision: 0.0347 (96.5% of predictions are FP)
- Recall: 0.8778 (inflated by low-confidence matches)
- F1: 0.0667

### Why These Numbers Are Misleading

1. **Precision inflation of FP**: 16,602 FP includes:
   - Duplicate overlapping predictions (same object predicted multiple times)
   - Noise predictions (confidence 0.001-0.01)
   - Background texture responses

2. **Recall inflation**: 87.78% recall is inflated because:
   - Every prediction, no matter how low confidence, counts as a potential TP
   - A prediction with confidence 0.001 that overlaps GT at IoU >= 0.5 is counted as a TP
   - In reality, such a detection would fail any reasonable confidence threshold

## Representative Case: India_005569

### Ground Truth
```
Class 2 (alligator_crack): x_center=0.672917, y_center=0.881944, w=0.573611, h=0.227778
Class 3 (pothole): x_center=0.370139, y_center=0.922222, w=0.054167, h=0.047222
```

### Predictions (sample)
```
category_id=4 (pothole), score=0.08, bbox=[313.2, 600.1, 210.5, 180.1]
category_id=4 (pothole), score=0.07, bbox=[312.8, 599.5, 208.2, 178.7]
category_id=4 (pothole), score=0.06, bbox=[315.1, 601.2, 205.3, 182.4]
... (75 more low-confidence predictions)
```

Note: Many predictions are near-duplicates with slightly different coordinates and decreasing confidence values, suggesting they are from different anchor scales or aspect ratios responding to the same visual feature.

## Conclusion

The 17,198 predictions are NOT expected for a properly evaluated model. After applying standard Ultralytics NMS (iou=0.7) and confidence thresholding, the number of predictions would be dramatically reduced to a more reasonable level (likely 1,000-5,000 predictions for 230 images, or roughly 4-22 per image).

The custom analysis methodology incorrectly treated raw model outputs (before post-processing) as final detections, leading to:
1. Massive inflation of false positives (16,602)
2. False sense of high recall (0.8778)
3. Misleading difficulty assessment for all images

The official Ultralytics evaluation metrics (precision=0.299, recall=0.312, mAP50=0.252) should be used as the authoritative baseline metrics.