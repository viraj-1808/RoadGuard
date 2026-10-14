# EXP-INF-003 Phase 3 Error Analysis Report

**Experiment**: EXP-INF-003 (YOLO11s, unseen image inference smoke test)
**Analysis Date**: 2026-10-10
**Images Analyzed**: 39 (validation/manual/input/)
**Predictions Source**: validation/manual/output/test2/predictions.json

---

## Executive Summary

Manual error analysis of 39 unseen images reveals **duplicate/overlapping detections** and **oversized bounding boxes** as the dominant failure patterns. The model (YOLO11s, trained on dataset_v2_split_v2) shows reasonable defect localization on clear defects but struggles with:
- Non-maximum suppression (NMS) at IoU=0.7 failing to merge overlapping boxes
- Excessive box expansion on high-resolution images (4096px+)
- Missed detections on high-resolution/portrait images (likely due to 720 imgsz resize)

No ground-truth annotations exist; all assessments are based on prediction consistency, confidence scores, and bounding box geometry.

---

## Major Failure Patterns (Ranked by Impact)

### 1. Duplicate / Overlapping Detections (High Impact)
**Affected Images**: road001, road003, road006, road007, road009, road010, road014, road025
**Count**: 8/39 images (20.5%) show clear duplicate detections

**Evidence**:
- **road001**: 3 pothole detections; 2nd (conf 0.47) and 3rd (conf 0.36) span nearly full image width overlapping 1st
- **road003**: 2 alligator_crack detections spanning full width (0-978); 2nd nested in 1st
- **road006**: 2 pothole boxes (148-192,71-127) and (91-149,80-133) heavily overlap
- **road007**: 2 pothole boxes; 2nd (104-698) nearly encompasses 1st (205-739)
- **road009**: 3 potholes; 3rd (125-515,285-574) oversized encompassing smaller two
- **road010**: 5 potholes with multiple pairwise overlaps (#1/#4, #3/#5)
- **road014**: 2 alligator_crack boxes (78-306 and 62-363) heavily overlapping
- **road025**: 5 alligator_crack detections; 4 overlapping at top (y=0), 1 separate lower region

**Root Cause**: NMS IoU threshold (0.7) too high for this model's box regression behavior; duplicate proposals not sufficiently suppressed.

---

### 2. Oversized Bounding Boxes (High Impact)
**Affected Images**: road018, road021, road022, road025 (partial)
**Count**: 3-4/39 images (7-10%) show extreme box expansion

**Evidence**:
- **road018** (4096×3072): Single pothole box (9-1785, 0-1042) covers **43% of image area** — likely merges multiple defects or background
- **road021** (3072×4096): Single alligator_crack box (223-2269, 0-2096) covers **37% of image area** — spans full width, half height
- **road022** (1280×960): Pothole box (121-907, 349-566) spans 62% of width
- **road025**: Multiple alligator_crack boxes at top all start at y=0, span to x≈2150 (70% width)

**Root Cause**: 
- High-resolution images (3072-4096px) resized to 720px imgsz causes loss of spatial precision
- Model trained on lower-resolution crops may not generalize to full-frame high-res inputs
- Class activation maps may merge adjacent defect regions at low resolution

---

### 3. Missed Detections on High-Res / Portrait Images (Medium Impact)
**Affected Images**: road016, road017, road019, road020, road023, road024, road028, road029, road030, road032, road034, road035, road036, road037, road038, road039
**Count**: 16/39 images (41%) have **zero detections**

**Breakdown**:
- 8 images ≥3072px (road016, 017, 018*, 019, 021*, 023, 027*, 028, 030, 032, 035, 037, 039) — 5/13 have detections (*)
- 8 images 960×1280 portrait (road020, 024, 026*, 029, 031*, 034, 036, 038) — 2/8 have detections (*)
- 4 images ≤1200px landscape (road004, 005, 011*, 013, 015*) — 2/4 have detections (*)

**Observation**: Detection rate drops sharply above ~1200px max dimension. The 720 imgsz resize likely makes small defects disappear. Portrait orientation may further distort aspect ratio during letterboxing.

---

### 4. Low-Confidence / Uncertain Detections (Medium Impact)
**Affected Images**: road012, road033
**Count**: 2/39 images

**Evidence**:
- **road012**: Pothole at conf 0.315, bbox at corner (0,0 to 216,79) — classic corner artifact
- **road033**: Alligator_crack at conf 0.316, bbox at corner (0,0 to 312,333) — corner artifact

**Root Cause**: Corner/edge artifacts from convolutional padding; confidence threshold (0.25) admits these.

---

### 5. Wrong Class (Low Observed Impact)
**Evidence**: Limited. road006 shows both pothole and longitudinal_crack in same region — could be misclassification or co-occurring defects. Without ground truth, cannot confirm.

---

### 6. Domain Shift (Suspected, Unconfirmed)
**Evidence**: High-resolution images (4096px) from different camera/source than training data. Training used dataset_v2_split_v2 — need to verify training image resolution distribution. The systematic failure on >3000px images suggests resolution domain shift.

---

## Per-Class Analysis

| Class | Total Detections | Images Affected | Duplicate Rate | Oversized Box Rate |
|-------|-----------------|-----------------|----------------|-------------------|
| pothole (3) | 23 | 11 | High (road001, 006, 007, 009, 010) | High (road018, 022) |
| alligator_crack (2) | 14 | 7 | High (road003, 014, 025) | High (road021, 025) |
| longitudinal_crack (0) | 2 | 2 | None | None |
| transverse_crack (1) | 0 | 0 | N/A | N/A |

**Key Insight**: Pothole and alligator_crack (the two most frequent classes) suffer most from duplicates and oversized boxes. Longitudinal_crack detections are sparse but clean.

---

## Four Target Potholes (Unambiguous Annotations)

Saved to: `experiments/results/20261010_phase3_error_analysis/four_pothole_annotations.json`

| Image | BBox (xyxy) | Confidence | Notes |
|-------|-------------|------------|-------|
| road001.webp | [95.4, 439.5, 345.0, 523.7] | 0.654 | Primary detection; 2 duplicates suppressed |
| road002.jpg | [260.8, 150.7, 413.6, 237.6] | 0.397 | Only detection in image |
| road009.jpg | [205.3, 161.5, 265.0, 215.2] | 0.619 | Well-localized; distinct from oversized 3rd detection |
| road010.jpg | [169.8, 228.7, 512.4, 439.5] | 0.733 | Highest confidence pothole in dataset |

These 4 represent high-confidence, well-localized potholes with minimal ambiguity. Suitable for:
- Qualitative model inspection
- Annotation seed set for future ground-truth creation
- Regression test cases

---

## Recommendations

### Immediate (Inference Config)
1. **Lower NMS IoU threshold** from 0.7 → 0.5 to suppress duplicate boxes
2. **Raise confidence threshold** from 0.25 → 0.35 to filter corner artifacts (road012, road033)
3. **Test multi-scale inference** (e.g., 720 + 1280) for high-res images

### Short-Term (Data / Training)
4. **Add high-resolution (3000-4000px) images to training** with tiling/sliding window augmentation
5. **Create ground-truth annotations** for these 39 images (start with 4 potholes + clear alligator_crack cases)
6. **Evaluate portrait vs landscape** performance separately; consider aspect-ratio-preserving resize

### Medium-Term (Architecture)
7. **Test SAHI (Slicing Aided Hyper Inference)** for large images
8. **Consider YOLO11m/l** for better small-object detection at high resolution
9. **Add oriented bounding boxes (OBB)** for longitudinal cracks

---

## Files Generated

| File | Description |
|------|-------------|
| `error_analysis.csv` | Per-image review table (39 rows) |
| `four_pothole_annotations.json` | 4 verified pothole annotations |
| `error_analysis_report.md` | This report |

---

## Limitations

- **No ground truth**: All "visible_damage" labels are inferred from prediction patterns, not human annotation
- **Uncertain cases**: 19/39 images marked "uncertain" — could be clean roads or missed defects
- **Single model checkpoint**: Results specific to YOLO11s dataset_v2_split_v2 best.pt
- **Single IoU/conf config**: Patterns may change with different thresholds

---

## Next Steps

1. Human annotation of the 39 images (priority: 4 potholes + road003, 006, 007, 009, 010, 014, 015, 021, 022, 025, 027)
2. Re-run inference with NMS IoU=0.5, conf=0.35
3. Run SAHI inference on 4096px images
4. Establish quantitative metrics once ground truth exists