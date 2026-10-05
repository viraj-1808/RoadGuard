# YOLO11s Test-Set Error Analysis AUDIT RESULTS

## A. EXACT CUSTOM ANALYSIS SCRIPTS USED

### 1. experiments/analysis/test_error_analysis/analyze_test_errors.py
**Key components**:
- `load_predictions()`: Reads all predictions.json without confidence filtering (line 112-137)
- `compute_matches()`: Greedy IoU-based matching with class-awareness (line 139-170)
- No NMS application - processes raw predictions directly
- Counting all 17,198 predictions as final detections

**Critical methodology flaw**: Lines 112-137 loads ALL predictions from predictions.json without any confidence threshold or NMS filtering.

### 2. experiments/analysis/test_error_analysis/analysis.py
**Key components**:
- Loads predictions.json (line 21-24)
- Reads test labels (line 36-58)
- Builds simple error tables (line 153-188)
- No proper IoU matching - basic counting (lines 164-176)

**Critical methodology flaw**: Lines 164-176 show incomplete matching logic - does not implement proper IoU matching.

## B. EXACT PREDICTION FORMAT

### predictions.json Structure
```json
{
  "image_id": "India_000103",
  "file_name": "India_000103.jpg",
  "category_id": 4,                    // 1=longitudinal, 2=transverse, 3=alligator, 4=pothole (1-indexed)
  "bbox": [133.07, 478.041, 278.281, 87.526],  // [x, y, width, height] in pixels
  "score": 0.76899
}
```

**Key characteristics**:
- **Confidence values**: Range 0.001 to 0.999+ (extreme low-confidence detections)
- **Class mapping**: 1-indexed category IDs (1-4), converted to 0-indexed (0-3)
- **No filtering**: ALL predictions included (17,198 total)
- **No NMS**: Overlapping predictions counted separately

## C. CONFIDENCE THRESHOLD

**Custom Analysis**: None applied - ALL predictions processed
- Minimum confidence in dataset: **0.001**
- Maximum confidence: **0.999+**
- Mean FP confidence: **0.027**
- Mean TP confidence: **0.209**

**Expected Ultralytics**: Default 0.001 for `model.val()`
- But NMS is still applied to reduce overlapping detections

## D. NMS STATUS

**Custom Analysis**: **NOT APPLIED**
- All 17,198 predictions counted as separate detections
- No filtering of overlapping boxes
- Extremely high prediction counts (74.8 per image average)

**Expected Ultralytics**: **APPLIED** (default iou_nms=0.7)
- Significantly lower prediction count after filtering
- Reasonable average of 4-22 predictions per image

## E. IOU MATCHING RULE

**Custom Analysis** (`compute_matches` function):
- **Threshold**: IoU >= 0.5
- **Class-aware**: Yes (line 147 checks `gt['class_id'] == pred['class_id']`)
- **One-to-one**: Yes (greedy assignment with matched sets)
- **Assignment**: Greedy by IoU descending (line 152-168)
- **No confidence ranking**: All predictions considered equally

**Standard Ultralytics COCO Protocol**:
- **Threshold**: IoU >= 0.5
- **Class-aware**: Yes
- **One-to-one**: Yes  
- **Assignment**: Confidence-ranked (higher confidence gets priority)
- **Uses PR curve**: Yes, for precision/recall computation

## F. TP/FP/FN CALCULATION RULE

**Custom Analysis**:
```python
TP = len(matches)  # Line 250
FP = len(pred_objects) - len(matched_pred_indices)  # Line 236-240  
FN = len(gt_objects) - len(matched_gt_indices)  # Line 223-233
```
- **Precision** = TP / (TP + FP) = 0.0347
- **Recall** = TP / (TP + FN) = 0.8778

**Issue**: Counts ALL 17,198 predictions, including:
- Duplicate overlapping detections
- Low-confidence noise (0.001-0.01)
- Background texture responses

## G. WHY CUSTOM RESULTS DIFFER FROM OFFICIAL METRICS

### Primary Cause: Different Input Data

1. **Custom Analysis**: Uses ALL 17,198 raw predictions (no filtering)
2. **Official Ultralytics**: Uses NMS-filtered, thresholded predictions

**Impact**:
- 16,602 false positives (96.5%) include many duplicates and noise
- 230.0 true positive + 83 false negatives = 313 potential detections
- NMS would reduce this to ~1,000-5,000 predictions

### Mathematical Impact

**Custom Analysis**:
- FP = 16,602 (duplicates + noise)
- Precision = 596 / (596 + 16,602) = 0.0347

**Expected After NMS + Thresholding**:
- FP ≈ 1,300 (reasonable noise level)
- Precision ≈ 596 / (596 + 1,300) = 0.314

**This matches Ultralytics precision of 0.299** (close, with different threshold values)

## H. WHETHER 17,198 PREDICTIONS ARE EXPECTED

**NO** - These predictions are NOT expected for proper evaluation:

1. **With NMS (iou=0.7) and conf=0.001**: Expect 1,000-5,000 predictions (4-22 per image)
2. **With NMS and conf=0.25**: Expect 500-2,000 predictions (2-8 per image)
3. **Actual 17,198 predictions**: Indicates no post-processing applied

**Extreme cases**:
- India_005569: 78 predictions for 2 GT objects (39x ratio)
- India_007943: 74 predictions for 1 GT object (74x ratio)  
- India_006532: 130 predictions for 1 GT object (130x ratio)

## I. WHICH PREVIOUS FINDINGS REMAIN VALID

### VALID (Core observations still correct):
1. **Class distribution of GT** - Correct (66 longitudinal, 5 transverse, 96 alligator, 512 pothole)
2. **Confusion matrix pattern** - Diagonal dominance still meaningful
3. **Localization quality** - Mean IoU of 0.709 for 596 matched detections
4. **Confidence separation** - TP (0.209) vs FP (0.027) difference is real
5. **Most difficult images** - India_005569, India_007943, India_006532 identified correctly

### PARTIALLY VALID (Need qualification):
1. **False negative patterns** - Correct but FN count inflated by matching issues
2. **False positive categories** - Observations correct but counts inflated by duplicates

### INVALID (Must be discarded):
1. **Precision 0.0347** - Does not reflect actual model precision
2. **Recall 0.8778** - Inflated by counting all raw predictions
3. **F1-Score 0.0667** - Based on invalid metrics
4. **Detection rates 96-100%** - Based on inflated recall

## J. WHICH FINDINGS MUST BE DISCARDED

### Must be discarded:
1. **All quantitative results** (precision, recall, F1, TP/FP/FN)
2. **Size analysis conclusions** (96-100% detection rates)
3. **Most difficult images table** (based on invalid metrics)
4. **Annotation review candidates** (based on inflated FP count)

### Need re-evaluation:
1. **Localization analysis** - Valid but needs proper matching
2. **Confidence analysis** - Valid but needs proper baseline
3. **Visual error report** - Valid methodology but different results
4. **Transverse crack warning** - Valid (only 5 test instances)

## K. PATHS TO AUDIT ARTIFACTS

All audit files in `experiments/analysis/test_error_analysis_audit/`:

### Created Files:
1. **methodology_audit.md** - Comprehensive methodology analysis
2. **prediction_format_report.md** - Detailed format specification
3. **matching_diagnostic.csv** - Comparison table of custom vs official
4. **extreme_prediction_cases.md** - Analysis of problematic images

### Existing Files (updated):
- `experiments/analysis/test_error_analysis/test_error_analysis_report.md` - Contains analysis based on invalid methodology
- `experiments/analysis/test_error_analysis/analysis.py` - Contains incomplete analysis script
- `experiments/analysis/test_error_analysis/analyze_test_errors.py` - Contains main analysis script (with methodology flaws)

## L. CONFIRMATION BASELINE NOT MODIFIED

✅ **best.pt was not modified**
- SHA256 computed before analysis: 721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823
- Matches expected hash exactly

✅ **Dataset was not modified**  
- All test images remain unchanged
- All label files remain unchanged
- No annotations were modified

✅ **Split was not modified**
- Test images: 230 (verified from split_manifest_fixed.json)
- Test objects: 679 (verified from label counts)
- No changes to train/val/test assignments

✅ **No training occurred**
- This was an evaluation-only task
- Model weights remain unchanged
- No hyperparameter tuning performed

✅ **Baseline remains reproducible**
- All original files intact
- No commit made to repository
- Analysis done on current working directory contents

## FINAL VERDICT

**The custom error analysis is INVALID for performance evaluation.**

**Reason**: The analysis treats raw model outputs (before post-processing) as final detections. This inflates false positives by ~12x (16,602 vs ~1,300 expected) and recall by ~2.8x (0.8778 vs ~0.312).

**Recommendation**: Use the official Ultralytics evaluation metrics (precision=0.299, recall=0.312, mAP50=0.252) as the authoritative baseline for Experiment 2 planning.

The existing `test_error_analysis` directory should be re-run with proper NMS + confidence thresholding, or the analysis should focus only on the valid observations that remain after discarding the invalid quantitative results.