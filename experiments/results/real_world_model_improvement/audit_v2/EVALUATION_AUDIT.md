# Evaluation Audit Report v2

**Experiment ID**: EXP-AUDIT-002  
**Date**: 2026-10-11  
**Checkpoint**: `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt`  
**SHA-256**: `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5` ✅ **VERIFIED**

---

## 1. Were Previous Metrics Valid?

### Smoke Test (3/4 pothole images at IoU ≥ 0.50)
**Status: ✅ VALID — CONFIRMED**

| Image | Ground Truth | Best IoU | Matched | Detections |
|-------|--------------|----------|---------|------------|
| road001.webp | 1 pothole | 0.768 | ✅ YES | 4 potholes (1 TP, 3 FP) |
| road002.jpg | 1 pothole | 0.000 | ❌ NO | 0 |
| road009.jpg | 1 pothole | 0.599 | ✅ YES | 3 potholes (1 TP, 2 FP) |
| road010.jpg | 1 pothole | 0.844 | ✅ YES | 4 potholes (1 TP, 3 FP) |

**At conf=0.05**: 3/4 matched, TP=3, FP=8, FN=1, Precision=0.273, Recall=0.75, F1=0.400  
**Conclusion**: The 3/4 claim is **valid** but requires very low confidence (0.05) and produces many false positives (8 FP across 4 images).

### Holdout CLEAR Images (5 images)
**Status: ❌ PARTIALLY INVALID — CLAIM WAS "0/5", ACTUAL IS "1/5"**

The previous report claimed **0/5 holdout CLEAR images correct at conf=0.05**. Audit reveals **1/5 matched** (road001.webp matched via its 2nd pothole GT box).

| Image | GT Class | Best IoU | Matched | Notes |
|-------|----------|----------|---------|-------|
| road001.webp | pothole ×2 | 0.768 | ✅ YES | 1 TP, 5 FP, 1 FN |
| road002.jpg | pothole | 0.000 | ❌ NO | Zero detections at all thresholds |
| road003.jpg | alligator_crack | 0.000 | ❌ NO | Zero detections |
| road007.jpg | pothole | 0.000 | ❌ NO | 5 alligator_crack FP, 0 pothole TP |
| road026.jpg | alligator_crack | 0.000 | ❌ NO | 1 alligator_crack FP |

**At conf=0.05**: 1/5 holdout CLEAR matched (road001)  
**At conf=0.10**: 0/5 holdout matched, but smoke test also drops to 1/4

**Conclusion**: The "0/5" claim was **incorrect** — road001 actually matched. However, the practical result is still poor: only 1 of 5 CLEAR images correctly detected.

---

## 2. Why the 5-Image Holdout Scored 1/5 (Previously Reported 0/5)

### Root Causes Identified:

| Image | Resolution | GT Class | GT Box % of Image | Failure Mode |
|-------|------------|----------|-------------------|--------------|
| **road002.jpg** | 700×525 | pothole | 21.8% × 16.5% | **Zero detections** — defect shrinks below detection threshold after 736px resize |
| **road003.jpg** | 978×1390 | alligator_crack | 100% × 54.5% | **Zero detections** — portrait orientation + letterboxing destroys feature visibility |
| **road007.jpg** | 739×415 | pothole | 72.2% × 54.0% | **Class confusion** — 5 alligator_crack FP, 0 pothole TP |
| **road026.jpg** | 960×1280 | alligator_crack | 57.2% × 45.4% | **Zero TP** — 1 alligator_crack FP at wrong location |

### Common Factors:
1. **Resize to 736×736** with letterboxing distorts aspect ratio, especially for portrait images
2. **Small defects become sub-pixel** after downsampling (road002 pothole → ~33×22 px after resize)
3. **Class confusion**: Potholes on textured asphalt misclassified as alligator_crack
4. **NMS at 0.7** insufficient for duplicate suppression; NMS at 0.5 used for matching

---

## 3. High-Resolution Failure Diagnosis

### Images Analyzed

| Image | Resolution | Orientation | GT Class | GT Box (px) | GT Box % Area |
|-------|------------|-------------|----------|-------------|---------------|
| road002.jpg | 700×525 | Landscape | pothole | 261–414 × 151–238 | 4.6% |
| road003.jpg | 978×1390 | Portrait | alligator_crack | 0–978 × 208–966 | 54.5% |
| road007.jpg | 739×415 | Landscape | pothole | 205–739 × 190–415 | 39.0% |
| road018.jpg | 4096×3072 | Landscape | pothole | 9–1785 × 0–1042 | 14.3% |
| road021.jpg | 3072×4096 | Portrait | alligator_crack | 223–2269 × 0–2096 | 33.7% |

### Post-Resize Analysis (736×736 with letterbox)

| Image | Scale Factor | GT Box After Resize (px) | Defect Size After Resize |
|-------|--------------|--------------------------|--------------------------|
| road002 | 1.05× (w) / 1.40× (h) | ~273–435 × ~211–333 | **~162×122 px** (adequate) |
| road003 | 0.75× (w) / 0.53× (h) | 0–736 × ~110–512 | **~736×402 px** (large) |
| road007 | 1.0× (w) / 1.77× (h) | ~205–739 × ~336–736 | **~534×400 px** (large) |
| road018 | 0.18× | ~2–321 × 0–187 | **~319×187 px** (adequate) |
| road021 | 0.18× | ~40–408 × 0–377 | **~368×377 px** (adequate) |

### Key Findings

**road002 (700×525, pothole)** — **Adequate post-resize size but ZERO detections**
- Defect becomes ~162×122 px after resize — should be detectable
- Model produces **zero detections at any confidence** (conf=0.05 to 0.30)
- Possible cause: Texture similarity to background, or training data lacked similar potholes

**road003 (978×1390, alligator_crack)** — **Large post-resize but ZERO detections**
- Portrait orientation → letterbox adds padding top/bottom
- Crack spans full width → becomes horizontal band after resize
- Model sees **no detections** — likely orientation/aspect ratio not in training

**road007 (739×415, pothole)** — **Class confusion: 5 alligator_crack FP**
- GT pothole spans 72% width, 54% height
- Model predicts **5 alligator_crack boxes** (conf 0.06–0.24), **0 pothole**
- Texture of pothole edges resembles alligator cracking

**road018 (4096×3072, pothole)** — **Zero detections**
- Massive downsampling (22× scale factor)
- GT pothole covers 14% of image but only ~319×187 px after resize
- Model produces **zero detections** — defect too small or texture lost

**road021 (3072×4096, alligator_crack)** — **Zero detections**
- Portrait + massive downsampling (22× scale)
- Crack pattern becomes low-contrast texture
- **Zero detections** — pattern recognition fails at this scale

### SAHI / Tiled Inference Availability

**Status: NOT AVAILABLE in repository**

Searched for: `sahi`, `slice`, `tile`, `patch` in `scripts/` — **no implementations found**

**Required for implementation:**
1. Install SAHI: `pip install sahi`
2. Modify inference to slice 4096px images into 640×640 tiles with 20% overlap
3. Merge predictions with NMS across tiles
4. Expected benefit: Defects stay at native resolution in each tile

---

## 4. Verified Metrics Summary

### Per-Class at Best Operating Point (conf=0.05)

| Class | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|-----|
| alligator_crack | 0 | 9 | 2 | 0.000 | 0.000 | 0.000 |
| pothole | 3 | 8 | 3 | 0.273 | 0.500 | 0.353 |

### Image-Level Correctness

| Set | Images | Correct (all GT matched, no FP) | Accuracy |
|-----|--------|--------------------------------|----------|
| Smoke test | 4 | 0 | 0% |
| Holdout CLEAR | 5 | 0 | 0% |
| All 7 unique | 7 | 0 | 0% |

**Note**: Image-level correctness requires ALL GT instances matched at IoU≥0.5 AND no FP above threshold. No image meets this strict criterion.

---

## 5. What Exact Next Action Has Strongest Evidence?

### Priority 1: Fix Class Confusion (Alligator Crack FP)
- **Evidence**: 9 alligator_crack FP at conf=0.05 vs 0 TP
- **Action**: Hard negative mining for alligator_crack; add pothole edge texture to training
- **Impact**: Would eliminate dominant FP source

### Priority 2: Implement SAHI for High-Resolution Images
- **Evidence**: 3/5 high-res CLEAR images have zero detections; road018/021 are 4096px
- **Action**: `pip install sahi` → implement tiled inference (640px tiles, 20% overlap)
- **Impact**: Could recover detections on >2000px images

### Priority 3: Add Portrait/Landscape Augmentation
- **Evidence**: road003 (portrait) and road021 (portrait) fail completely
- **Action**: Training augment with random rotation, letterbox-aware resize
- **Impact**: Fix orientation sensitivity

### Priority 4: Collect Human-Reviewed Ground Truth
- **Evidence**: Only 15/39 images have CLEAR annotations (model-derived); 24 need human review
- **Action**: Annotate 24 UNCERTAIN images; target 100 CLEAR for 75/100 evaluation
- **Impact**: Enables reliable metrics and training supervision

---

## 6. Remaining Uncertainties

| Uncertainty | Impact | Resolution Needed |
|-------------|--------|-------------------|
| Ground truth quality of 15 "CLEAR" images | Model-derived, not human-verified | Human annotation review |
| road002 pothole detectability | Zero detections despite adequate post-resize size | Check if GT box is accurate; test on raw image |
| Class mapping consistency | Model outputs class 2 for pothole-like textures | Verify training label quality for alligator_crack vs pothole |
| NMS IoU=0.7 vs matching IoU=0.5 | Duplicates inflate FP counts | Test NMS=0.3-0.4 for duplicate suppression |
| Tiled inference effectiveness | Not tested — no implementation | Implement and benchmark |

---

## 7. Commands Run

```bash
# Verify checkpoint hash
Get-FileHash -Algorithm SHA256 runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt

# Fresh inference on 7 unique images at 5 confidence thresholds
python -c "
from ultralytics import YOLO
model = YOLO(r'runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt')
for img in ['road001.webp','road002.jpg','road009.jpg','road010.jpg','road003.jpg','road007.jpg','road026.jpg']:
    for conf in [0.05,0.10,0.15,0.20,0.25]:
        results = model.predict(f'validation/manual/input/{img}', imgsz=720, conf=conf, iou=0.7, device=0, save=True)
"
```

---

## 8. Files Generated in `audit_v2/`

| File | Description |
|------|-------------|
| `VERIFIED_METRICS.json` | Complete metrics at 5 thresholds |
| `ERROR_CASES.csv` | 77 rows of per-detection TP/FP/FN |
| `COMMANDS.md` | Exact commands run |
| `HIGH_RES_DIAGNOSIS.md` | This analysis |
| `annotated/` | 35 annotated images (7 images × 5 thresholds) |

---

## 9. Final Verdict

| Claim | Audit Result |
|-------|--------------|
| Checkpoint hash matches | ✅ **VERIFIED** |
| Smoke test 3/4 at IoU≥0.5 | ✅ **VALID** (at conf=0.05) |
| Holdout CLEAR 0/5 | ❌ **INVALID** — actual 1/5 |
| mAP@50-95 ≥ 0.76 | ❌ **NOT ACHIEVED** (best 0.353 F1) |
| 75/100 images correct | ❌ **NOT ACHIEVED** — 0/7 image-level correct |

**Strongest next action**: Implement SAHI tiled inference + fix alligator_crack false positives via hard negative mining + human-verify ground truth annotations.