# High-Resolution Image Failure Diagnosis

## Executive Summary

The model (epoch72.pt) fails on 5 CLEAR high-resolution images despite clear visible defects. **No SAHI/tiling implementation exists in the repository.** The root cause is **extreme downsampling during letterbox resize** to the model's input size (736×736), which shrinks large-image defects below the model's effective receptive field.

---

## 1. SAHI/Tiling Implementation Status

**Result: NO SAHI or tiling implementation exists in the repository.**

- Searched for: `sahi`, `SlicingAided`, `slice`, `tile`, `patch` in all `.py` files
- Only unrelated matches found (mock patching, percentile functions, dataloader patches)
- The inference pipeline (`inference/adapters/yolo_adapter.py`) uses standard single-image inference only
- No sliding window, tiling, or multi-scale inference logic present

**What would be needed for SAHI:**
1. Install `sahi` package: `pip install sahi`
2. Implement slicing inference wrapper:
   - Slice height/width: 640×640 (matching model stride)
   - Overlap ratio: 0.2 (standard)
   - Post-process: merge overlapping predictions with NMS
3. Modify `YOLOAdapter.predict_image()` to support tiled mode
4. Handle coordinate mapping from slices back to original image

---

## 2. Per-Image Analysis

### Common Settings
- Model input size: **736×736** (imgsz=720 rounded to stride 32)
- Letterbox resize: maintains aspect ratio, pads to 736×736
- Confidence thresholds tested: 0.05, 0.10, 0.15, 0.20, 0.25
- Inference at conf=0.001 reveals all low-confidence predictions

### road002.jpg (700×525) — CLEAR Pothole
| Metric | Value |
|--------|-------|
| Original GT bbox | [260.8, 150.7, 413.6, 237.6] |
| GT area (original) | 13,271 px² (3.6% of image) |
| Letterbox scale | 1.0514 (upscaled) |
| Letterboxed size | 736×552 (pad: 0, 92) |
| **GT size in letterboxed** | **160.7×91.3 = 14,671 px²** |
| GT max dimension | **160.7 px** |
| Detections at conf≥0.05 | **0** |
| Low-conf detections near GT | 1× class 3 (pothole) at **conf=0.0014**, dist=87.8px |

**Diagnosis:** Defect is large enough (160px) but model produces only extremely low-confidence pothole detection (0.0014). The defect covers ~3.7% of letterboxed image — should be detectable. Failure likely due to **domain shift** (real-world vs training distribution) or **insufficient training on similar pothole appearance**.

---

### road003.jpg (978×1390) — CLEAR Alligator Crack
| Metric | Value |
|--------|-------|
| Original GT bbox | [0, 208.0, 978, 965.9] (full width!) |
| GT area (original) | 741,207 px² (**54.5% of image**) |
| Letterbox scale | 0.5295 |
| Letterboxed size | 517×736 (pad: 109, 0) |
| **GT size in letterboxed** | **517.8×401.3 = 207,809 px²** |
| GT max dimension | **517.8 px** |
| Detections at conf≥0.05 | **0** |
| Detections at conf=0.001 | **NONE AT ALL** |

**Diagnosis:** **CRITICAL FAILURE** — Defect covers >50% of original image and 517px in letterboxed space (70% of width). Model produces **zero detections** even at conf=0.001. This suggests:
- The alligator crack pattern is **not recognized** by the model
- Possible **class confusion**: model may not have learned this crack type well
- The defect spans nearly full width — may exceed receptive field context

---

### road007.jpg (739×415) — CLEAR Pothole
| Metric | Value |
|--------|-------|
| Original GT bbox | [205.1, 190.4, 739, 415] (touches right/bottom edge) |
| GT area (original) | 119,901 px² (**39.1% of image**) |
| Letterbox scale | 0.9959 |
| Letterboxed size | 736×413 (pad: 0, 161) |
| **GT size in letterboxed** | **531.7×223.7 = 118,930 px²** |
| GT max dimension | **531.7 px** |
| Detections at conf≥0.05 | 5× alligator_crack (FP), 0× pothole (TP) |
| Low-conf pothole near GT | 3× class 3 at conf **0.0011–0.0333** |
| Dominant false class | **alligator_crack (class 2)** — 60+ detections at conf 0.001–0.24 |

**Diagnosis:** **Severe class confusion** — Model strongly predicts alligator_crack (high confidence up to 0.24) instead of pothole. The pothole touches image edges which may confuse the model. GT is very large (531px) — should be easily detectable. The model has learned to associate this visual pattern with alligator_crack.

---

### road018.jpg (4096×3072) — CLEAR Pothole
| Metric | Value |
|--------|-------|
| Original GT bbox | [9.0, 0, 1785.3, 1042.6] |
| GT area (original) | 1,851,847 px² (**14.7% of image**) |
| Letterbox scale | **0.1797** (extreme downsampling) |
| Letterboxed size | 736×552 (pad: 0, 92) |
| **GT size in letterboxed** | **319.2×187.3 = 59,792 px²** |
| GT max dimension | **319.2 px** |
| Detections at conf≥0.05 | **0** |
| Detections near GT (100px) | **NONE** |
| All detections location | Far from GT (different image region) |

**Diagnosis:** **Extreme downsampling (5.6×)** shrinks a large defect to 319px. While 319px should be detectable, the pothole occupies only ~11% of letterboxed image. More critically, **all detections appear in wrong location** — model attends to different image regions. The 4096px width loses massive detail at 0.18× scale.

---

### road021.jpg (3072×4096) — CLEAR Alligator Crack
| Metric | Value |
|--------|-------|
| Original GT bbox | [222.9, 0, 2268.6, 2095.6] |
| GT area (original) | 4,287,010 px² (**34.1% of image**) |
| Letterbox scale | **0.1797** (extreme downsampling) |
| Letterboxed size | 552×736 (pad: 92, 0) |
| **GT size in letterboxed** | **367.6×376.6 = 138,417 px²** |
| GT max dimension | **376.6 px** |
| Detections at conf≥0.05 | **0** |
| Detections near GT (100px) | **NONE** |
| All detections location | Bottom of image (class 0, 1) — wrong region |

**Diagnosis:** Similar to road018 — **extreme downsampling (5.6×)**. Defect is large (376px) but model produces zero detections near GT. All predictions cluster at bottom of image (likely artifacts from letterbox padding or sky/horizon). The alligator crack pattern at this scale becomes unrecognizable.

---

## 3. Root Cause Analysis

### Effective Receptive Field Comparison

| Image | GT Max Dim (letterboxed) | YOLO11s Receptive Field* | Ratio |
|-------|-------------------------|-------------------------|-------|
| road002 | 160.7 px | ~150-200 px | ~0.8-1.1x |
| road003 | 517.8 px | ~150-200 px | **2.6-3.5x** |
| road007 | 531.7 px | ~150-200 px | **2.7-3.5x** |
| road018 | 319.2 px | ~150-200 px | **1.6-2.1x** |
| road021 | 376.6 px | ~150-200 px | **1.9-2.5x** |

*YOLO11s effective receptive field estimated at 150-200px at stride 32.

**Key Finding:** For road003, road007, road018, road021 — the defect **exceeds the receptive field**. The model cannot "see" the full defect pattern at once, leading to:
- Fragmented predictions (road007: many small alligator_crack boxes)
- Complete miss (road003, road018, road021: no detection near GT)
- Class confusion (road007: pothole → alligator_crack)

### Downsampling Impact

| Image | Original Max Dim | Scale Factor | Information Loss |
|-------|-----------------|--------------|------------------|
| road002 | 413 px | 1.05× (upscale) | None |
| road003 | 978 px | 0.53× | Moderate |
| road007 | 739 px | 1.00× | Minimal |
| road018 | 1785 px | **0.18×** | **Severe (5.6× reduction)** |
| road021 | 2268 px | **0.18×** | **Severe (5.6× reduction)** |

The 4K images (road018, road021) suffer **>5× downsampling**, destroying fine crack/pothole texture details the model relies on.

---

## 4. Low-Confidence Detection Analysis

At conf=0.001 (near noise floor):

| Image | Target Class | Detections Near GT | Best Conf | Notes |
|-------|-------------|-------------------|-----------|-------|
| road002 | pothole (3) | 1 | 0.0014 | Very weak signal |
| road003 | alligator (2) | 0 | N/A | **Complete miss** |
| road007 | pothole (3) | 3 | 0.0333 | Strong class confusion |
| road018 | pothole (3) | 0 | N/A | Wrong region attended |
| road021 | alligator (2) | 0 | N/A | Wrong region attended |

**Conclusion:** The model has **no meaningful signal** for these defects at native resolution. Even at near-zero threshold, detections are absent or misclassified.

---

## 5. Recommendations

### Immediate (No Retraining)
1. **Implement SAHI/tiled inference** — Process 4K images in 640×640 tiles with 20% overlap
2. **Increase inference resolution** — Test imgsz=1280 or 1536 (if GPU memory allows)
3. **Multi-scale inference** — Run at multiple scales and merge predictions

### Model Improvement (Requires Retraining)
1. **Add high-resolution training data** — Include 4K images in training with proper augmentation
2. **Resize-aware training** — Train with random scales up to 1280/1536
3. **Class balancing** — Address alligator_crack vs pothole confusion (road007)
4. **Hard negative mining** — Add road018/road021 as hard negatives

### Architecture Considerations
- YOLO11s stride=32 limits small object detection
- Consider YOLO11m/l with larger receptive field
- Feature pyramid enhancements for multi-scale defects

---

## 6. Files Generated

- `HIGH_RES_DIAGNOSIS.md` — This report
- `TILED_COMPARISON.json` — Not generated (no SAHI implementation)
- Per-image diagnostic details included above

---

## 7. Reproduction Commands

```bash
# Standard inference (already run)
python scripts/audit_v2_evaluation.py

# Low-confidence diagnostic (this analysis)
python debug_high_res.py

# Letterbox size computation
python -c "
# ... (see script above)
"
```