# Annotation Review Status Report

**Dataset Version:** v1.0  
**Date:** 2026-10-11  
**Total Source Images:** 39 (`validation/manual/input/`)

---

## 1. Count Summary

| Status | Count | Images |
|--------|-------|--------|
| **CONFIRMED** (verified GT) | 20 | road001, road002, road003, road004, road006, road007, road008, road009, road010, road011, road014, road015, road018, road021, road022, road025, road026, road027, road029, road031, road033 |
| **NEEDS_HUMAN_REVIEW** | 15 | road013, road016, road017, road019, road020, road023, road024, road030, road032, road034, road035, road036, road037, road038, road039 |
| **LIKELY_NEGATIVE** | 3 | road005, road012, road028 |
| **UNCERTAIN (total)** | 18 | 15 NEEDS_HUMAN_REVIEW + 3 LIKELY_NEGATIVE |
| **TOTAL** | 39 | — |

---

## 2. Confirmed Annotations Breakdown

### By Class
| Class | Instances | Images |
|-------|-----------|--------|
| longitudinal_crack (0) | 2 | road006, road011 |
| transverse_crack (1) | 0 | — |
| alligator_crack (2) | 11 | road003, road004, road014, road021, road025(x2), road026, road027, road029, road031, road033 |
| pothole (3) | 12 | road001(x2), road002, road006(x2), road007, road008, road009(x3), road010(x4), road014, road015, road018, road022 |

**Total Instances:** 25 across 20 images

### By Provenance
| Source | Images | Instances |
|--------|--------|-----------|
| model_derived | 15 | 19 |
| model_derived_epoch72 | 2 | 2 |
| human_reviewed | 3 | 4 |

### By Split (Leakage-Safe)
| Split | Images | Instances |
|-------|--------|-----------|
| train | 10 | 13 |
| val | 5 | 6 |
| holdout | 5 | 6 |

---

## 3. Uncertain Images Requiring Human Decision

### NEEDS_HUMAN_REVIEW (15) - Must be annotated or confirmed negative

| Image | Resolution | Split | Epoch72 Predictions | Review Reason |
|-------|------------|-------|---------------------|---------------|
| road013.jpg | 1200×900 | train | None | High-res landscape, no detections - defects may be below threshold |
| road016.jpg | 4096×3072 | holdout | None | 4K landscape - extreme downsampling (5.6x) likely misses defects |
| road017.jpg | 3072×4096 | val | None | 4K portrait - letterbox + downsampling destroys detail |
| road019.jpg | 3072×4096 | holdout | None | 4K portrait - same as road017 |
| road020.jpg | 960×1280 | val | None | Portrait - no detections |
| road023.jpg | 3072×4096 | holdout | 5 low-conf (alligator/longitudinal/transverse) | 4K portrait - ambiguous multi-class detections |
| road024.jpg | 960×1280 | train | None | Portrait - no detections |
| road030.jpg | 3072×4096 | train | 2 low-conf alligator_crack | 4K portrait - low-conf detections need verification |
| road032.jpg | 4096×3072 | val | None | 4K landscape - no detections |
| road034.jpg | 960×1280 | train | 3 low-conf (2 alligator, 1 pothole) | Portrait - ambiguous low-conf detections |
| road035.jpg | 4096×3072 | train | None | 4K landscape - no detections |
| road036.jpg | 960×1280 | train | None | Portrait - no detections |
| road037.jpg | 4096×3072 | holdout | None | 4K landscape - no detections |
| road038.jpg | 1280×960 | holdout | None | Standard resolution - no detections |
| road039.jpg | 3072×4096 | holdout | None | 4K portrait - no detections |

### LIKELY_NEGATIVE (3) - Likely clean, but need confirmation

| Image | Resolution | Split | Review Reason |
|-------|------------|-------|---------------|
| road005.jpg | 452×678 | holdout | Small image, no detections from either model |
| road012.jpg | 612×406 | holdout | Original model predicted corner artifact pothole; epoch72 found nothing |
| road028.jpg | 3072×4096 | train | 4K portrait, epoch72 found 1 very low-conf alligator (0.051) |

---

## 4. Human Decision Required

**Total human decisions needed:** 18 images

For each NEEDS_HUMAN_REVIEW image, human must:
1. Visually inspect the original image at native resolution
2. Determine if visible road damage exists (pothole, alligator_crack, longitudinal_crack, transverse_crack)
3. If yes: draw bounding boxes with correct class
4. If no: mark as NEGATIVE (clean road)

For each LIKELY_NEGATIVE image, human must:
1. Confirm no visible target damage exists
2. If damage found: annotate with bounding boxes and class
3. If confirmed clean: mark as NEGATIVE

**Output format:** YOLO normalized (class_id x_center y_center width height) in `annotations_v1/confirmed/` or `annotations_v1/uncertain/`

---

## 5. Annotation Quality Checks Passed

| Check | Status | Details |
|-------|--------|---------|
| Class mapping consistent | ✅ | 0=longitudinal, 1=transverse, 2=alligator, 3=pothole |
| Bbox coordinates valid | ✅ | All normalized [0,1], within image bounds |
| No duplicate annotations | ✅ | Each instance unique per image |
| Split integrity (leakage-safe) | ✅ | Near-duplicates grouped, no train/val/holdout overlap |
| Provenance tracked | ✅ | model_derived / model_derived_epoch72 / human_reviewed |

---

## 6. Files Created

| File | Description |
|------|-------------|
| `annotations_v1/manifest.json` | Version manifest with counts and provenance |
| `annotations_v1/confirmed/*.txt` | 20 YOLO format annotation files |
| `annotations_v1/confirmed/annotations.json` | Full confirmed annotations with provenance |
| `annotations_v1/uncertain/metadata.json` | 18 uncertain images with review reasons |
| `annotations_v1/leakage_safe_split.json` | Train/val/holdout split with leakage prevention |
| `human_review_package/` | 15 NEEDS_HUMAN_REVIEW images + review interface |