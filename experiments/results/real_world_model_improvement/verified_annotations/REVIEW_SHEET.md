# Comprehensive Review Sheet for 23 UNCERTAIN Images

**Experiment**: Phase E Step 1 - Human Review of UNCERTAIN Images
**Model**: epoch72.pt (YOLO11s) at conf=0.05, iou=0.7, imgsz=736
**Source Data**: Original predictions (EXP-INF-003, best.pt, conf=0.25) + Error Analysis (20261010_phase3) + epoch72 inference

---

## road004.jpg

- **Resolution**: 640x480
- **Data Split**: train
- **Review Flags**: needs_human_review, likely_false_positive
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections; image may contain subtle defects below confidence threshold or no visible damage

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.705, bbox=[4.577371120452881, 164.34092712402344, 638.752685546875, 478.333984375])

### Proposed Ground Truth
alligator_crack (conf=0.705, bbox=[4.577371120452881, 164.34092712402344, 638.752685546875, 478.333984375])

### Status: **CONFIRMED** (source: model_derived)

---

## road005.jpg

- **Resolution**: 452x678
- **Data Split**: holdout
- **Review Flags**: needs_human_review, likely_false_positive
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections; image may contain subtle defects below confidence threshold or no visible damage

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **LIKELY_NEGATIVE** (source: human_reviewed)

---

## road012.jpg

- **Resolution**: 612x406
- **Data Split**: holdout
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**:  bbox at image corner 0-216

### Original Model Predictions (best.pt, conf=0.25)
pothole (conf=0.315, bbox=[0.0, 0.0, 216.05039978027344, 79.12346649169922])

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **LIKELY_NEGATIVE** (source: human_reviewed)

---

## road013.jpg

- **Resolution**: 1200x900
- **Data Split**: train
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 1200x900 image; may be clean road or defects below threshold

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road016.jpg

- **Resolution**: 4096x3072
- **Data Split**: holdout
- **Review Flags**: needs_human_review, high_res_may_miss_defects, possible_missed_detections
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 4096x3072 image; very high resolution may cause small defects to be missed at 720 imgsz

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road017.jpg

- **Resolution**: 3072x4096
- **Data Split**: val
- **Review Flags**: needs_human_review, portrait_orientation, possible_missed_detections
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image; portrait orientation + high res may cause missed defects

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road019.jpg

- **Resolution**: 3072x4096
- **Data Split**: holdout
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image; high res portrait orientation

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road020.jpg

- **Resolution**: 960x1280
- **Data Split**: val
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 960x1280 portrait image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road022.jpg

- **Resolution**: 1280x960
- **Data Split**: val
- **Review Flags**: model_missed_visible_damage
- **Error Analysis - Visible Damage**: yes
- **Error Analysis - Class**: pothole
- **Error Analysis Notes**: 349-566) spans 62% of width; possibly oversized"

### Original Model Predictions (best.pt, conf=0.25)
pothole (conf=0.311, bbox=[120.78581237792969, 349.0760803222656, 907.45849609375, 566.1356811523438])

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.127, bbox=[130.0, 365.90118408203125, 617.6322631835938, 515.8994750976562])

### Proposed Ground Truth
pothole (conf=0.311, bbox=[120.78581237792969, 349.0760803222656, 907.45849609375, 566.1356811523438])

### Status: **CONFIRMED** (source: human_reviewed)

---

## road023.jpg

- **Resolution**: 3072x4096
- **Data Split**: holdout
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.328, bbox=[0.0, 658.130615234375, 3072.0, 1956.4248046875]); longitudinal_crack (conf=0.210, bbox=[14.69570541381836, 2959.922607421875, 282.0379333496094, 3477.347900390625]); alligator_crack (conf=0.137, bbox=[1354.9630126953125, 854.9038696289062, 3063.253173828125, 1979.5103759765625]); alligator_crack (conf=0.064, bbox=[0.0, 676.6028442382812, 3072.0, 3246.86328125]); transverse_crack (conf=0.051, bbox=[2077.385498046875, 933.4005126953125, 3033.288330078125, 1051.1162109375])

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road024.jpg

- **Resolution**: 960x1280
- **Data Split**: train
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 960x1280 portrait image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road028.jpg

- **Resolution**: 3072x4096
- **Data Split**: train
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.051, bbox=[2023.6070556640625, 919.3014526367188, 3059.22216796875, 1739.37939453125])

### Proposed Ground Truth
None

### Status: **LIKELY_NEGATIVE** (source: human_reviewed)

---

## road029.jpg

- **Resolution**: 960x1280
- **Data Split**: holdout
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 960x1280 portrait image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.337, bbox=[2.40574049949646, 207.8732147216797, 960.0, 757.4553833007812])

### Proposed Ground Truth
alligator_crack (conf=0.337, bbox=[2.40574049949646, 207.8732147216797, 960.0, 757.4553833007812])

### Status: **CONFIRMED** (source: model_derived)

---

## road030.jpg

- **Resolution**: 3072x4096
- **Data Split**: train
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.110, bbox=[384.8262634277344, 3207.680419921875, 2531.3525390625, 4096.0]); alligator_crack (conf=0.085, bbox=[1209.3995361328125, 6.775390625, 2179.326904296875, 870.0772705078125])

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road031.jpg

- **Resolution**: 960x1280
- **Data Split**: train
- **Review Flags**: model_missed_visible_damage
- **Error Analysis - Visible Damage**: yes
- **Error Analysis - Class**: alligator_crack
- **Error Analysis Notes**: Single alligator_crack detection at moderate confidence (136-553

### Original Model Predictions (best.pt, conf=0.25)
alligator_crack (conf=0.312, bbox=[136.26458740234375, 353.9178161621094, 552.5153198242188, 932.2827758789062])

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
alligator_crack (conf=0.312, bbox=[136.26458740234375, 353.9178161621094, 552.5153198242188, 932.2827758789062])

### Status: **CONFIRMED** (source: human_reviewed)

---

## road032.jpg

- **Resolution**: 4096x3072
- **Data Split**: val
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 4096x3072 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road033.jpg

- **Resolution**: 960x1280
- **Data Split**: val
- **Review Flags**: model_missed_visible_damage
- **Error Analysis - Visible Damage**: yes
- **Error Analysis - Class**: alligator_crack
- **Error Analysis Notes**: 0-333) may be corner artifact"

### Original Model Predictions (best.pt, conf=0.25)
alligator_crack (conf=0.316, bbox=[0.0, 0.0, 311.8957824707031, 332.987548828125])

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
alligator_crack (conf=0.316, bbox=[0.0, 0.0, 311.8957824707031, 332.987548828125])

### Status: **CONFIRMED** (source: human_reviewed)

---

## road034.jpg

- **Resolution**: 960x1280
- **Data Split**: train
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 960x1280 portrait image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
alligator_crack (conf=0.166, bbox=[642.0169067382812, 323.14520263671875, 955.4000244140625, 545.5084228515625]); alligator_crack (conf=0.077, bbox=[506.9397277832031, 327.2607421875, 957.1891479492188, 542.1329345703125]); pothole (conf=0.072, bbox=[0.0, 442.9920654296875, 960.0, 1276.2476806640625])

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road035.jpg

- **Resolution**: 4096x3072
- **Data Split**: train
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 4096x3072 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road036.jpg

- **Resolution**: 960x1280
- **Data Split**: train
- **Review Flags**: needs_human_review, portrait_orientation
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 960x1280 portrait image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road037.jpg

- **Resolution**: 4096x3072
- **Data Split**: holdout
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 4096x3072 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road038.jpg

- **Resolution**: 1280x960
- **Data Split**: holdout
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 1280x960 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## road039.jpg

- **Resolution**: 3072x4096
- **Data Split**: holdout
- **Review Flags**: needs_human_review
- **Error Analysis - Visible Damage**: uncertain
- **Error Analysis - Class**: uncertain
- **Error Analysis Notes**: No detections on 3072x4096 image

### Original Model Predictions (best.pt, conf=0.25)
None

### Epoch72 Predictions (epoch72.pt, conf=0.05)
None

### Proposed Ground Truth
None

### Status: **NEEDS_HUMAN_REVIEW** (source: human_reviewed)

---

## Summary Table

| Image | Resolution | Split | Orig Preds | Epoch72 Preds | EA Visible | EA Class | Proposed GT | Status |
|-------|------------|-------|------------|---------------|------------|----------|-------------|--------|
| road004.jpg | 640x480 | train | None... | alligator_crack (conf=0.705, bbox=[4.5773711204528... | uncertain | uncertain | alligator_crack (conf=0.705, bbox=[4.5773711204528... | **CONFIRMED** |
| road005.jpg | 452x678 | holdout | None... | None... | uncertain | uncertain | None... | **LIKELY_NEGATIVE** |
| road012.jpg | 612x406 | holdout | pothole (conf=0.315, bbox=[0.0, 0.0, 216.050399780... | None... | uncertain | uncertain | None... | **LIKELY_NEGATIVE** |
| road013.jpg | 1200x900 | train | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road016.jpg | 4096x3072 | holdout | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road017.jpg | 3072x4096 | val | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road019.jpg | 3072x4096 | holdout | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road020.jpg | 960x1280 | val | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road022.jpg | 1280x960 | val | pothole (conf=0.311, bbox=[120.78581237792969, 349... | alligator_crack (conf=0.127, bbox=[130.0, 365.9011... | yes | pothole | pothole (conf=0.311, bbox=[120.78581237792969, 349... | **CONFIRMED** |
| road023.jpg | 3072x4096 | holdout | None... | alligator_crack (conf=0.328, bbox=[0.0, 658.130615... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road024.jpg | 960x1280 | train | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road028.jpg | 3072x4096 | train | None... | alligator_crack (conf=0.051, bbox=[2023.6070556640... | uncertain | uncertain | None... | **LIKELY_NEGATIVE** |
| road029.jpg | 960x1280 | holdout | None... | alligator_crack (conf=0.337, bbox=[2.4057404994964... | uncertain | uncertain | alligator_crack (conf=0.337, bbox=[2.4057404994964... | **CONFIRMED** |
| road030.jpg | 3072x4096 | train | None... | alligator_crack (conf=0.110, bbox=[384.82626342773... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road031.jpg | 960x1280 | train | alligator_crack (conf=0.312, bbox=[136.26458740234... | None... | yes | alligator_crack | alligator_crack (conf=0.312, bbox=[136.26458740234... | **CONFIRMED** |
| road032.jpg | 4096x3072 | val | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road033.jpg | 960x1280 | val | alligator_crack (conf=0.316, bbox=[0.0, 0.0, 311.8... | None... | yes | alligator_crack | alligator_crack (conf=0.316, bbox=[0.0, 0.0, 311.8... | **CONFIRMED** |
| road034.jpg | 960x1280 | train | None... | alligator_crack (conf=0.166, bbox=[642.01690673828... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road035.jpg | 4096x3072 | train | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road036.jpg | 960x1280 | train | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road037.jpg | 4096x3072 | holdout | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road038.jpg | 1280x960 | holdout | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
| road039.jpg | 3072x4096 | holdout | None... | None... | uncertain | uncertain | None... | **NEEDS_HUMAN_REVIEW** |
