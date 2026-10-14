# Human Decision Required - Concise List

**Dataset:** RoadGuard Real-World v1.0  
**Date:** 2026-10-11  
**Total Images Requiring Human Decision:** 18 (15 NEEDS_HUMAN_REVIEW + 3 LIKELY_NEGATIVE)

---

## NEEDS_HUMAN_REVIEW (15) — Must annotate or confirm negative

| # | Image | Resolution | Orientation | Key Issue |
|---|-------|------------|-------------|-----------|
| 1 | road013.jpg | 1200×900 | Landscape | High-res, no detections |
| 2 | road016.jpg | 4096×3072 | Landscape | 4K, extreme downsampling (5.6×) |
| 3 | road017.jpg | 3072×4096 | Portrait | 4K, letterbox + downsampling |
| 4 | road019.jpg | 3072×4096 | Portrait | 4K, letterbox + downsampling |
| 5 | road020.jpg | 960×1280 | Portrait | No detections |
| 6 | road023.jpg | 3072×4096 | Portrait | 5 low-conf multi-class detections |
| 7 | road024.jpg | 960×1280 | Portrait | No detections |
| 8 | road030.jpg | 3072×4096 | Portrait | 2 low-conf alligator_crack |
| 9 | road032.jpg | 4096×3072 | Landscape | 4K, no detections |
| 10 | road034.jpg | 960×1280 | Portrait | 3 low-conf (2 alligator, 1 pothole) |
| 11 | road035.jpg | 4096×3072 | Landscape | 4K, no detections |
| 12 | road036.jpg | 960×1280 | Portrait | No detections |
| 13 | road037.jpg | 4096×3072 | Landscape | 4K, no detections |
| 14 | road038.jpg | 1280×960 | Landscape | Standard res, no detections |
| 15 | road039.jpg | 3072×4096 | Portrait | 4K, no detections |

**Priority Order for Review:**
1. **High-res pothole candidates:** road016, road018 (but 018 confirmed), road022 (confirmed), road023
2. **High-res alligator candidates:** road021 (confirmed), road023, road025, road027, road030
3. **Portrait images:** road017, road019, road020, road024, road026, road029, road031, road033, road034, road036, road039
3. **Standard resolution ambiguous:** road013, road038

---

## LIKELY_NEGATIVE (3) — Confirm clean or annotate

| # | Image | Resolution | Reason |
|---|-------|------------|--------|
| 1 | road005.jpg | 452×678 | No detections, small image |
| 2 | road012.jpg | 612×406 | Corner artifact pothole (original model only) |
| 3 | road028.jpg | 3072×4096 | 4K portrait, 1 very low-conf alligator (0.051) |

---

## Action Required per Image

For each NEEDS_HUMAN_REVIEW image:
1. Open `human_review_package/review_images/<image>` at native resolution
2. Inspect for visible: pothole, alligator_crack, longitudinal_crack, transverse_crack
3. If damage found: draw bounding box(es) with correct class in `review_template.html`
4. Export JSON and save to `annotations_v1/confirmed/<image>.txt` (YOLO format)
5. If no damage: mark as NEGATIVE in review tool

For each LIKELY_NEGATIVE image:
1. Confirm no target damage visible
2. If confirmed clean: no annotation needed (implicit negative)
3. If damage found: annotate as above

---

## Output Locations

- Review images: `experiments/results/real_world_model_improvement/human_review_package/review_images/`
- Review interface: `experiments/results/real_world_model_improvement/human_review_package/review_template.html`
- Confirmed annotations: `experiments/results/real_world_model_improvement/annotations_v1/confirmed/`
- Uncertain metadata: `experiments/results/real_world_model_improvement/annotations_v1/uncertain/metadata.json`
- Review instructions: `experiments/results/real_world_model_improvement/human_review_package/review_instructions.md`

---

## Decision Deadline

These 18 images block the creation of a fully verified dataset. Without human decisions:
- Only 20/39 images have verified GT (51%)
- Fine-tuning cannot be justified (insufficient verified data)
- 75/100 target unmeasurable (need ≥100 verified images)

**Next step:** Complete human review of these 18 images, then re-evaluate fine-tuning viability.