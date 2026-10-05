# YOLO11s Test-Set Error Analysis Audit Report

## 1. EXECUTIVE SUMMARY

The custom error analysis produced results that **do not match** the official Ultralytics evaluation. The root cause is a **fundamental methodological mismatch**:

- The custom analysis treated **all 17,198 raw predictions** from predictions.json as final detections, including extremely low-confidence noise predictions (many at confidence 0.001).
- The official Ultralytics evaluation uses a **confidence threshold** (default 0.001) and **NMS** to filter predictions before computing metrics.
- The custom analysis did **not apply NMS**, meaning duplicate/overlapping detections were counted as separate false positives.

## 2. THE CORE DISCREPANCY

| Metric | Custom Analysis | Official Ultralytics |
|--------|----------------|---------------------|
| Precision | 0.0347 | 0.299 |
| Recall | 0.8778 | 0.312 |
| TP | 596 | NOT DIRECTLY REPORTED |
| FP | 16,602 | NOT DIRECTLY REPORTED |
| FN | 83 | NOT DIRECTLY REPORTED |

## 3. ROOT CAUSE ANALYSIS

### 3.1 predictions.json Contains Raw, Unfiltered Detections

The predictions.json file contains **17,198 raw detections** across 230 test images. This is an average of **74.8 predictions per image**. These predictions include:

- Confidence values as low as **0.001**
- Many **duplicate/overlapping boxes** for the same visual region
- **No NMS filtering** applied

### 3.2 The Custom Analysis Did Not Apply Confidence Filtering

The custom analysis script (`analyze_test_errors.py`, lines 112-137) loads ALL predictions from predictions.json without any confidence threshold:

```python
def load_predictions(pred_file):
    """Load predictions from COCO-style JSON."""
    with open(pred_file, 'r') as f:
        pred_data = json.load(f)
    # NO confidence filtering
    # NO NMS
    # Loads ALL 17,198 predictions
```

### 3.3 The Custom Analysis Did Not Apply NMS

The `compute_matches` function (lines 139-170) uses greedy IoU-based matching but does NOT apply NMS first. This means:

- Multiple overlapping predictions for the same object are each counted as separate false positives
- Images with 78+ predictions (like India_005569) have many duplicate boxes

### 3.4 How Ultralytics Computes Metrics

The official Ultralytics `model.val()` method:
1. Runs inference with confidence threshold (default 0.001)
2. Applies NMS with IoU threshold (default 0.7)
3. Computes precision/recall/mAP using the standard COCO evaluation protocol
4. The reported precision (0.299) and recall (0.312) reflect the NMS-filtered, thresholded detections

### 3.5 Why Recall Differs

The custom analysis reports recall = 0.8778 because it counts **every prediction** as a potential match, including extremely low-confidence ones. A prediction with confidence 0.001 that happens to overlap a GT object at IoU >= 0.5 is counted as a true positive. This inflates recall.

The official Ultralytics recall (0.312) reflects the actual detection quality after proper filtering.

### 3.6 Why Precision Differs

The custom analysis reports precision = 0.0347 because it counts **all 16,602 unmatched predictions** as false positives. Most of these are low-confidence noise (mean FP confidence = 0.027) that would be filtered out by a reasonable confidence threshold or NMS.

## 4. WHAT THE CUSTOM ANALYSIS ACTUALLY MEASURED

The custom analysis measured: "If we take ALL raw model outputs (including noise) and match them to ground truth, what would the metrics be?"

This is **not** a valid evaluation of model performance. It measures the raw output quality before any post-processing.

## 5. WHAT REMAINS VALID

Despite the methodological issues, some observations from the custom analysis remain valid:

1. **Class distribution of ground truth** - correct
2. **Per-image GT counts** - correct
3. **Confusion matrix structure** - the diagonal dominance (correct class predictions) is still meaningful, though the counts are inflated
4. **Localization quality of matched detections** - the mean IoU of 0.709 for the 596 matched detections is a valid measure of localization quality for those specific matches
5. **Confidence separation** - TP detections (mean 0.209) vs FP detections (mean 0.027) shows the model does have some confidence calibration

## 6. WHAT MUST BE DISCARDED

1. **Precision (0.0347)** - INVALID, does not reflect actual model precision
2. **Recall (0.8778)** - INVALID, inflated by counting all raw predictions
3. **F1-Score (0.0667)** - INVALID, based on invalid precision/recall
4. **TP/FP/FN counts** - MISLEADING, do not reflect standard evaluation protocol
5. **"Detection rates consistent across object sizes (96-100%)"** - INVALID, based on inflated recall
6. **Most difficult images analysis** - MISLEADING, based on invalid per-image metrics

## 7. VERDICT

| Claim | Verdict |
|-------|---------|
| TP/FP/FN counts | **INVALID** - do not use standard evaluation protocol |
| Precision/Recall | **INVALID** - no confidence threshold or NMS applied |
| False-positive conclusion | **PARTIALLY VALID** - the observation that there are many low-confidence noise detections is correct, but the count is inflated |
| False-negative conclusion | **PARTIALLY VALID** - the identification of missed objects is correct, but the FN count may be inflated by matching issues |
| Localization conclusion | **PARTIALLY VALID** - mean IoU of 0.709 for matched detections is a valid observation, but the matching procedure is non-standard |
| Confidence conclusion | **VALID** - the observation that TP detections have higher confidence than FP detections is correct |
| Class-confusion conclusion | **PARTIALLY VALID** - the observation of diagonal dominance is correct, but the counts are inflated |
| Size-analysis conclusion | **INVALID** - based on inflated recall values |

## 8. RECOMMENDATION

The custom error analysis should be **re-run** using the standard Ultralytics evaluation protocol:
1. Apply confidence threshold (default 0.001 or a reasonable value like 0.25)
2. Apply NMS with IoU threshold 0.7
3. Use the standard COCO matching protocol
4. Report metrics consistent with Ultralytics

Alternatively, the existing official Ultralytics evaluation results (precision=0.299, recall=0.312, mAP50=0.252) should be used as the authoritative metrics.