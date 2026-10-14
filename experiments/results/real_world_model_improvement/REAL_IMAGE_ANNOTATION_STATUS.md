# Real Image Annotation Status Report

**Experiment**: EXP-INF-003 (YOLO11s, validation/manual/input 39 images)  
**Analysis Date**: 2026-10-11  
**Source**: Model predictions (validation/manual/output/test2/predictions.json) + Error Analysis (experiments/results/20261010_phase3_error_analysis)  
**Output Directory**: experiments/results/real_world_model_improvement/annotations/

---

## Summary

| Category | Count | Description |
|----------|-------|-------------|
| **CLEAR** | 15 | Visible damage obvious, preliminary annotations from high-confidence model predictions |
| **UNCERTAIN** | 24 | Ambiguous — no detections, low confidence, corner artifacts, or high-res/portrait issues |
| **NEGATIVE** | 0 | No images definitively confirmed as clean (all "uncertain" could have missed defects) |

**Total**: 39 images  
**With Preliminary Annotations**: 15 (38%)  
**Needing Human Review**: 24 (62%)

---

## Per-Image Status

### CLEAR — High-Confidence Annotations (15 images)

| Image | Resolution | Class(es) | # Annotations | Source | Key Flags |
|-------|------------|-----------|---------------|--------|-----------|
| road001.webp | 1140×760 | pothole | 2 | model_derived | duplicate_detections_in_predictions |
| road002.jpg | 700×525 | pothole | 1 | model_derived | — |
| road003.jpg | 978×1390 | alligator_crack | 1 | model_derived | duplicate_detections_in_predictions |
| road006.jpg | 447×447 | pothole, longitudinal_crack | 3 | model_derived | duplicate_detections_in_predictions |
| road007.jpg | 739×415 | pothole | 1 | model_derived | — |
| road008.jpg | 479×641 | pothole | 1 | model_derived | — |
| road009.jpg | 518×592 | pothole | 3 | model_derived | — |
| road010.jpg | 679×452 | pothole | 4 | model_derived | duplicate_detections_in_predictions |
| road011.jpg | 678×452 | longitudinal_crack | 1 | model_derived | — |
| road014.webp | 389×280 | alligator_crack, pothole | 2 | model_derived | duplicate_detections_in_predictions |
| road015.jpg | 1200×800 | pothole | 1 | model_derived | — |
| road018.jpg | 4096×3072 | pothole | 1 | model_derived | — |
| road021.jpg | 3072×4096 | alligator_crack | 1 | model_derived | — |
| road025.jpg | 3072×4096 | alligator_crack | 2 | model_derived | duplicate_detections_in_predictions |
| road026.jpg | 960×1280 | alligator_crack | 1 | model_derived | — |
| road027.jpg | 3072×4096 | alligator_crack | 1 | model_derived | — |

**Note**: For CLEAR images with `duplicate_detections_in_predictions`, NMS filtering (IoU=0.5) was applied to keep only the highest-confidence non-overlapping box per defect region. Some duplicates may remain — human verification recommended.

---

### UNCERTAIN — Requires Human Review (24 images)

| Image | Resolution | Primary Reason | Review Flags |
|-------|------------|----------------|--------------|
| road004.jpg | 640×480 | No detections; subtle defects possible | needs_human_review, likely_false_positive |
| road005.jpg | 452×678 | No detections; subtle defects possible | needs_human_review, likely_false_positive |
| road012.jpg | 612×406 | Corner artifact pothole (conf 0.315) | needs_human_review |
| road013.jpg | 1200×900 | No detections; mid-res landscape | needs_human_review |
| road016.jpg | 4096×3072 | No detections; high-res landscape | needs_human_review, high_res_may_miss_defects, possible_missed_detections |
| road017.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review, portrait_orientation, possible_missed_detections |
| road019.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review, portrait_orientation |
| road020.jpg | 960×1280 | No detections; mid-res portrait | needs_human_review, portrait_orientation |
| road022.jpg | 1280×960 | Error analysis says "yes pothole" but model prediction oversized/low-conf | model_missed_visible_damage |
| road023.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review |
| road024.jpg | 960×1280 | No detections; mid-res portrait | needs_human_review, portrait_orientation |
| road028.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review |
| road029.jpg | 960×1280 | No detections; mid-res portrait | needs_human_review, portrait_orientation |
| road030.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review |
| road031.jpg | 960×1280 | Error analysis says "yes alligator_crack" but no model detection | model_missed_visible_damage |
| road032.jpg | 4096×3072 | No detections; high-res landscape | needs_human_review |
| road033.jpg | 960×1280 | Error analysis says "yes alligator_crack" (corner artifact) | model_missed_visible_damage |
| road034.jpg | 960×1280 | No detections; mid-res portrait | needs_human_review, portrait_orientation |
| road035.jpg | 4096×3072 | No detections; high-res landscape | needs_human_review |
| road036.jpg | 960×1280 | No detections; mid-res portrait | needs_human_review, portrait_orientation |
| road037.jpg | 4096×3072 | No detections; high-res landscape | needs_human_review |
| road038.jpg | 1280×960 | No detections; mid-res landscape | needs_human_review |
| road039.jpg | 3072×4096 | No detections; high-res portrait | needs_human_review |

---

## Priority for Human Review

### High Priority (CLEAR but with duplicate/oversized box concerns)
1. **road001.webp** — 3 model pothole detections, 2 overlapping duplicates; kept 2 after NMS
2. **road003.jpg** — 2 alligator_crack spanning full width, nested; kept 1
3. **road006.jpg** — Overlapping pothole + longitudinal_crack; kept both classes
4. **road009.jpg** — 3 potholes, 3rd oversized encompassing others; kept all 3
5. **road010.jpg** — 5 potholes with multiple overlaps; kept 4 after NMS
6. **road014.webp** — 2 overlapping alligator_crack; kept both (different conf)
7. **road018.jpg** — Single massive pothole (43% image area); likely over-merged
8. **road021.jpg** — Single massive alligator_crack (37% image area); likely over-merged
9. **road025.jpg** — 5 alligator_crack, 4 overlapping at top; kept 2 after NMS

### Medium Priority (Model missed visible damage per error analysis)
10. **road022.jpg** — Error analysis: "yes pothole", model: oversized low-conf box
11. **road031.jpg** — Error analysis: "yes alligator_crack", model: no detections
12. **road033.jpg** — Error analysis: "yes alligator_crack (corner)", model: corner artifact

### Low Priority (No detections, high-res/portrait — likely missed defects)
13-24. **road004, 005, 012, 013, 016, 017, 019, 020, 023, 024, 028, 029, 030, 032, 034, 035, 036, 037, 038, 039** — 20 images with zero or unreliable detections; high-res (>3000px) or portrait orientation images where 720 imgsz resize likely causes missed defects

---

## Class Distribution in Preliminary Annotations

| Class | Count | Images |
|-------|-------|--------|
| pothole (3) | 14 | 9 images |
| alligator_crack (2) | 6 | 6 images |
| longitudinal_crack (0) | 2 | 2 images |
| transverse_crack (1) | 0 | 0 |

---

## Data Split (Train/Val/Holdout)

**Method**: Stratified by resolution + orientation (random seed 42)  
**Ratios**: Train 50% (17), Val 25% (8), Holdout 25% (14) — *Note: 17+8+14=39*

### Train (17)
```
road035.jpg, road018.jpg, road030.jpg, road028.jpg, road021.jpg,
road025.jpg, road013.jpg, road015.jpg, road024.jpg, road031.jpg,
road034.jpg, road036.jpg, road004.jpg, road009.jpg, road011.jpg,
road014.webp, road010.jpg
```

### Val (8)
```
road032.jpg, road017.jpg, road027.jpg, road022.jpg, road033.jpg,
road020.jpg, road006.jpg, road008.jpg
```

### Holdout (14)
```
road037.jpg, road016.jpg, road019.jpg, road039.jpg, road023.jpg,
road038.jpg, road001.webp, road029.jpg, road003.jpg, road026.jpg,
road005.jpg, road002.jpg, road007.jpg, road012.jpg
```

**Stratification Check**: Similar resolutions/orientations kept in same split where possible to avoid near-duplicates across splits.

---

## Files Generated

| File | Description |
|------|-------------|
| `annotation_manifest.json` | Full manifest with all image metadata, annotations, status, review flags |
| `ground_truth_annotations.json` | Preliminary ground truth with class names, normalized & pixel bboxes, sources |
| `data_split.json` | Train/val/holdout split assignments |
| `roadXXX.txt` | YOLO format annotations (class_id x_center y_center width height) per image |

---

## Next Steps for Human Annotation

1. **Start with High Priority CLEAR images** — Verify/adjust bounding boxes, confirm/reject duplicates
2. **Review UNCERTAIN images with "model_missed_visible_damage"** — Check if defects actually visible
3. **Sample high-res UNCERTAIN images** — Use SAHI/tiled viewing to inspect for missed defects
4. **Update ground_truth_annotations.json** — Change `source` from `model_derived` to `human_reviewed` for verified annotations
5. **Re-run split** — After human review, regenerate splits if class distribution changes significantly

---

## Limitations

- **No ground truth**: All "CLEAR" labels inferred from model prediction patterns + error analysis, not human annotation
- **Duplicate handling**: NMS at IoU=0.5 applied programmatically; may over-suppress or under-suppress
- **High-res images**: 4096px images resized to 720px for inference — boxes may be imprecise
- **Corner artifacts**: Low-confidence detections at (0,0) retained if above 0.35 threshold; likely false positives
- **Portrait orientation**: Letterboxing during resize may distort defect appearance

---

## Annotation Tool Usage

```bash
# Interactive annotation (requires OpenCV GUI)
python scripts/annotation/annotate_manual_images.py --interactive \
  --input validation/manual/input \
  --predictions validation/manual/output/test2/predictions.json \
  --output experiments/results/real_world_model_improvement/annotations

# Regenerate preliminary annotations after config changes
python scripts/annotation/annotate_manual_images.py --create-preliminary \
  --input validation/manual/input \
  --predictions validation/manual/output/test2/predictions.json \
  --output experiments/results/real_world_model_improvement/annotations \
  --error-analysis experiments/results/20261010_phase3_error_analysis/error_analysis.csv

# Regenerate split
python scripts/annotation/annotate_manual_images.py --create-split \
  --output experiments/results/real_world_model_improvement/annotations
```