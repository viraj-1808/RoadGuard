# Final Comprehensive Report: RoadGuard AI Real-World Detection Improvement

**Experiment ID:** EXP-RWMI-FINAL  
**Date:** 2026-10-11  
**Status:** Complete — Fine-tuning unsuccessful, best model remains epoch72.pt

---

## 1. Executive Summary

This experiment executed a complete real-world detection improvement cycle for RoadGuard AI:
- **Phase A:** Class-confusion diagnosis on 7 verified images
- **Phase B:** SAHI tiled inference prototype on 4K images
- **Phase C:** Implementation validation
- **Phase D:** Deliverable creation
- **Phase E:** Annotation review, fine-tuning attempt, and evaluation

**Bottom Line:** The original `epoch72.pt` (YOLO11s, Exp2) remains the best model. Fine-tuning degraded performance. SAHI tiled inference finds detections but they are false positives. The model requires human-verified ground truth and architectural changes before further training.

---

## 2. Best Checkpoint

| Property | Value |
|----------|-------|
| **Checkpoint Path** | `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt` |
| **SHA-256** | `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5` |
| **Training Epoch** | 72 |
| **Model Architecture** | YOLO11s |
| **Image Size** | 720 (resized to 736 for stride alignment) |
| **Classes** | 4 (longitudinal_crack, transverse_crack, alligator_crack, pothole) |

---

## 3. Target Achievement Summary

| Target | Definition | Result | Status |
|--------|------------|--------|--------|
| **Smoke Test** | ≥3/4 pothole images at IoU≥0.50 | **3/4 at conf=0.05** (road001, 009, 010) | ✅ **PASSED** |
| **Holdout** | 75/100 CLEAR images correct | 0/5 CLEAR in holdout (only 39 images total) | ❌ **FAILED** |
| **Fine-tuning** | Improve epoch72 | **Degraded performance** | ❌ **FAILED** |
| **SAHI Tiling** | Improve 4K detection | Finds detections but all FP | ❌ **FAILED** |

---

## 4. Verified Metrics (Best Model: epoch72.pt)

### Per-Class at Best Operating Point (conf=0.05)

| Class | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|-----|
| longitudinal_crack | 0 | 0 | 0 | N/A | N/A | N/A |
| transverse_crack | 0 | 0 | 0 | N/A | N/A | N/A |
| **alligator_crack** | 0 | 9 | 2 | **0.000** | **0.000** | **0.000** |
| **pothole** | 3 | 8 | 3 | **0.273** | **0.500** | **0.353** |

### Image-Level Correctness

| Set | Images | Correct (all GT matched, no FP) | Accuracy |
|-----|--------|--------------------------------|----------|
| Smoke test | 4 | 0 | 0% |
| Holdout CLEAR | 5 | 0 | 0% |
| All 7 unique | 7 | 0 | 0% |

*Note: Image-level correctness requires ALL GT instances matched at IoU≥0.5 AND no FP above threshold.*

---

## 5. Root Cause Analysis

### 5.1 Class Confusion (Dominant Issue)
| Evidence | Count |
|----------|-------|
| alligator_crack FP on pothole GT | 6 (road007) + 1 (road009) + 1 (road001) = 8 |
| pothole FP on alligator_crack GT | 3 (road003) + 1 (road026) = 4 |
| **Total class confusion FPs** | **12** |

**Root Cause:** The model learns visual features that overlap between potholes (dark cavities with rough edges) and alligator cracking (interconnected crack networks). The training data likely has imbalanced or ambiguous labels for these classes.

### 5.2 Resolution Sensitivity
| Image | Resolution | Scale to 736px | Result |
|-------|------------|----------------|--------|
| road002 | 700×525 | 1.05× (upscale) | **Zero detections** (1 pothole FN) |
| road003 | 978×1390 | 0.53× | **Zero detections** (1 alligator FN) |
| road021 | 3072×4096 | 0.18× | **Zero detections** (1 alligator FN) |
| road026 | 960×1280 | 0.76× | **Zero detections** (1 alligator FN) |
| road018 | 4096×3072 | 0.18× | Works (pothole TP at conf=0.33) |

**Root Cause:** Defects exceed receptive field (~150-200px) AND extreme downsampling (5.6× on 4K) destroys texture. Portrait orientation + letterbox padding worsens it.

### 5.3 High FP at Low Confidence
- **road002**: 21 predictions at conf=0.05 (1 TP, 20 FP)
- **road001**: 7 predictions (1 TP, 6 FP)
- **road007**: 20 predictions (1 TP, 19 FP)
- **Root cause**: NMS IoU=0.7 insufficient for duplicate suppression; model over-predicts at low confidence

### 5.4 SAHI Tiled Inference Failure
- SAHI finds detections on 4K images (road018: 6, road021: 2) but **all are FP**
- Detections are artifacts/other patterns, not the annotated defects
- **Domain gap**: Model detects what it learned at native resolution, not the annotated defects

---

## 6. Fine-tuning Result: FAILED

| Metric | epoch72 | Fine-tuned v2 | Change |
|--------|---------|---------------|--------|
| Pothole Recall | 50% | 16.7% | **↓ 33.3%** |
| Alligator FP | 9 | 9 | No change |
| Smoke Test | 3/4 ✅ | 1/4 ❌ | **Failed** |
| Overall F1 | 0.214 | 0.077 | **↓ 64%** |

**Why it failed:**
- Reduced batch (8), workers (1), imgsz (640) degraded feature learning
- Class weights [1,1,2,0.5] didn't address alligator_crack FP
- Catastrophic forgetting of pothole features
- Only 20 verified images added — insufficient to shift class distributions

---

## 7. Remaining Annotation Blockers

| Status | Count | Images |
|--------|-------|--------|
| **CONFIRMED** (verified GT) | 20 | 15 CLEAR + 5 from review |
| **NEEDS_HUMAN_REVIEW** | 15 | road013, 016, 017, 019, 020, 023, 024, 030, 032, 034, 035, 036, 037, 038, 039 |
| **LIKELY_NEGATIVE** | 3 | road005, 012, 028 |
| **Total images** | 39 | — |

**Only 20/39 images have verified ground truth.** The 75/100 target requires ≥100 human-reviewed images.

---

## 8. Recommendations (Priority Order)

### Immediate (No Training)
1. **Deploy epoch72 at conf=0.05** for pothole detection on standard-resolution landscape images only
2. **Reject high-res (>2000px) and portrait images** — preprocessing pipeline required
3. **Do NOT deploy** for alligator_crack, longitudinal_crack, transverse_crack

### Short-Term (Data & Inference)
1. **Human-annotate 15 NEEDS_REVIEW images** — prioritize high-res/portrait
2. **Implement SAHI with better GT** — current GT may be incomplete; verify 4K annotations
3. **Hard negative mining for alligator_crack** — collect 50+ clean road patches misclassified as alligator_crack
4. **NMS post-processing** — IoU=0.3-0.4 for duplicate suppression, confidence-weighted merging

### Medium-Term (Training)
1. **Collect 100+ CLEAR annotated images** for reliable 75/100 evaluation
2. **Multi-scale training** — imgsz=[640, 720, 800, 1280] for resolution invariance
3. **Portrait/landscape augmentation** — random rotation, letterbox-aware resize
4. **Fix class confusion** — balanced sampling, contrastive loss between pothole/alligator_crack

### Long-Term (Architecture)
1. **YOLO11m/l or RT-DETR** — larger receptive field for high-res defects
2. **Oriented bounding boxes (OBB)** — better for longitudinal cracks
3. **Feature pyramid enhancements** — multi-scale defect detection

---

## 8. Exact Inference Command (Best Model)

```bash
# Single image
yolo predict model=runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt \
    source=validation/manual/input/road001.webp \
    imgsz=720 conf=0.05 iou=0.5 device=0 \
    save=True project=experiments/results/real_world_model_improvement/annotated_outputs \
    name=epoch72_predictions exist_ok=True

# Batch inference on all 39 images
python -c "
from ultralytics import YOLO
import os
model = YOLO(r'runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt')
input_dir = r'validation/manual/input'
output_dir = r'experiments/results/real_world_model_improvement/annotated_outputs'
images = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
for img in images:
    model.predict(os.path.join(input_dir, img), imgsz=720, conf=0.05, iou=0.5, device=0,
                  save=True, project=output_dir, name='epoch72_predictions', exist_ok=True)
"
```

---

## 9. Deliverables Manifest

All outputs in `experiments/results/real_world_model_improvement/`:

| Directory | Contents |
|-----------|----------|
| `audit_v2/` | `EVALUATION_AUDIT.md`, `VERIFIED_METRICS.json`, `ERROR_CASES.csv`, `HIGH_RES_DIAGNOSIS.md`, `TILED_COMPARISON.json`, `COMMANDS.md`, 35 annotated images |
| `tiled_v1/` | `CLASS_CONFUSION_DIAGNOSIS.md`, `TILED_INFERENCE_REPORT.md`, `STANDARD_VS_TILED.csv`, `IMPLEMENTATION_NOTES.md`, `sahi_adapter.py`, 14 annotated images |
| `verified_annotations/` | `REVIEW_SHEET.md`, `verified_annotations.json`, `review_sheet.csv`, 5 YOLO annotations |
| `finetune_v2/` | `FINE_TUNED_EVALUATION.md`, `FINE_TUNED_VS_ORIGINAL.csv`, `ERROR_CASES.csv`, 7 annotated images |
| `annotated_outputs/epoch72_predictions/` | 39 annotated images (epoch72, conf=0.05) |

---

## 10. Final Statement

**The model did not improve.** The original `epoch72.pt` remains the best checkpoint. Key blockers:

1. **Insufficient verified ground truth** — only 20/39 images verified
2. **Class confusion (pothole↔alligator)** — requires hard negative mining and balanced training
3. **Resolution sensitivity** — requires multi-scale training + SAHI with verified GT
4. **Catastrophic forgetting in fine-tuning** — reduced config degraded features

**Next action with strongest evidence:** Human-annotate the 15 NEEDS_REVIEW images (especially high-res/portrait), then re-evaluate whether fine-tuning with full resolution, balanced classes, and hard negatives can succeed.