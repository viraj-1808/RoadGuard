# Fine-tuned v2 Model Evaluation Report

**Experiment ID:** EXP-FINETUNE-V2-001  
**Timestamp:** 2026-10-11T14:22:34.979423Z  
**Checkpoint:** `runs/detect/experiments/training/yol11s_realworld_finetune_v2/weights/best.pt`  
**Checkpoint SHA-256:** `4d5449db73b1e9e3f57ab554b6bf3de7994829cdf275b908653da3b242403a83`

---

## Executive Summary

The fine-tuned model (`yol11s_realworld_finetune_v2/best.pt`) was evaluated on the same 7 images used in Audit v2 (4 smoke test + 5 CLEAR holdout, 7 unique) at confidence threshold 0.05, IoU threshold 0.7, imgsz 720.

**Result: Fine-tuning DEGRADED performance across all metrics compared to the original epoch72 checkpoint.**

| Metric | Epoch72 (Original) | Fine-tuned v2 | Delta | Improved? |
|--------|-------------------|---------------|-------|-----------|
| Overall TP | 3 | 1 | -2 | ❌ |
| Overall FP | 17 | 17 | 0 | ❌ |
| Overall FN | 5 | 7 | +2 | ❌ |
| Overall Precision | 0.1500 | 0.0556 | -0.0944 | ❌ |
| Overall Recall | 0.3750 | 0.1250 | -0.2500 | ❌ |
| Overall F1 | 0.2143 | 0.0769 | -0.1374 | ❌ |
| Smoke Test Matched | 3/4 | 1/4 | -2 | ❌ |
| Smoke Target (3/4) | ✅ PASSED | ❌ FAILED | | ❌ |
| Holdout Matched | 1/5 | 0/5 | -1 | ❌ |

---

## Per-Class Comparison

### Pothole (Class 3)

| Metric | Epoch72 | Fine-tuned v2 | Delta | Improved? |
|--------|---------|---------------|-------|-----------|
| TP | 3 | 1 | -2 | ❌ |
| FP | 8 | 8 | 0 | ➖ |
| FN | 3 | 5 | +2 | ❌ |
| Precision | 0.2727 | 0.1111 | -0.1616 | ❌ |
| Recall | 0.5000 | 0.1667 | -0.3333 | ❌ |
| F1 | 0.3529 | 0.1333 | -0.2196 | ❌ |

**Pothole Recall DECREASED from 50% to 16.7%** — Fine-tuning made the model WORSE at detecting potholes.

### Alligator Crack (Class 2)

| Metric | Epoch72 | Fine-tuned v2 | Delta | Improved? |
|--------|---------|---------------|-------|-----------|
| TP | 0 | 0 | 0 | ➖ |
| FP | 9 | 9 | 0 | ➖ |
| FN | 2 | 2 | 0 | ➖ |
| Precision | 0.0000 | 0.0000 | 0.0000 | ➖ |
| Recall | 0.0000 | 0.0000 | 0.0000 | ➖ |
| F1 | 0.0000 | 0.0000 | 0.0000 | ➖ |

**Alligator crack FP remains at 9** — Fine-tuning did NOT reduce false positives for alligator crack.

---

## Per-Image Breakdown (Fine-tuned v2)

### Smoke Test Images (4)

| Image | GT Classes | TP | FP | FN | Matched | Best IoU (Pothole) |
|-------|------------|----|----|----|---------|-------------------|
| road001.webp | 2× pothole | 0 | 3 | 2 | ❌ | 0.465 |
| road002.jpg | 1× pothole | 0 | 0 | 1 | ❌ | 0.000 |
| road009.jpg | 1× pothole | 0 | 3 | 1 | ❌ | 0.000 |
| road010.jpg | 1× pothole | 1 | 3 | 0 | ✅ | 0.643 |

### Holdout Images (5 CLEAR)

| Image | GT Classes | TP | FP | FN | Matched | Best IoU |
|-------|------------|----|----|----|---------|----------|
| road001.webp | 2× pothole | 0 | 3 | 2 | ❌ | 0.465 (pothole) |
| road002.jpg | 1× pothole | 0 | 0 | 1 | ❌ | 0.000 |
| road003.jpg | 1× alligator_crack | 0 | 0 | 1 | ❌ | 0.000 |
| road007.jpg | 1× pothole | 0 | 7 | 1 | ❌ | 0.000 |
| road026.jpg | 1× alligator_crack | 0 | 1 | 1 | ❌ | 0.000 |

---

## Key Findings

### 1. Pothole Recall DECREASED (50% → 16.7%)
- Original epoch72: Detected 3/6 potholes (TP=3, FN=3)
- Fine-tuned v2: Detected 1/6 potholes (TP=1, FN=5)
- **Fine-tuning made pothole detection significantly worse**

### 2. Alligator Crack FP NOT Reduced (9 → 9)
- Both models produce 9 alligator_crack false positives
- Fine-tuning did not address the class confusion issue
- Road007.jpg: 6 alligator_crack FPs (GT is pothole)
- Road009.jpg: 1 alligator_crack FP (GT is pothole)
- Road001.webp: 1 alligator_crack FP (GT is pothole)
- Road026.jpg: 1 alligator_crack FP (GT is alligator_crack, but wrong location)

### 3. Class Confusion NOT Fixed
- Fine-tuned model still predicts `alligator_crack` on pothole regions
- Road001: 1 alligator_crack FP overlapping pothole region
- Road007: 6 alligator_crack FPs on pothole region
- Road009: 1 alligator_crack FP on pothole region
- The model continues to confuse pothole texture with alligator cracking

### 4. Smoke Test Target FAILED
- Original: 3/4 matched ✅ (target: 3/4)
- Fine-tuned: 1/4 matched ❌
- Only road010.jpg matched (IoU 0.643)

### 5. Holdout Performance WORSE
- Original: 1/5 matched (road009.jpg)
- Fine-tuned: 0/5 matched

---

## Detailed Per-Image Analysis

### road001.webp (2 GT potholes)
- **Fine-tuned:** 3 FPs (2 pothole, 1 alligator_crack), 0 TP, 2 FN
- Best pothole IoU: 0.465 (below 0.5 match threshold)
- The alligator_crack FP at [389, 400, 731, 503] overlaps with second pothole GT

### road002.jpg (1 GT pothole)
- **Fine-tuned:** 0 detections, 1 FN
- Model completely misses this pothole

### road009.jpg (1 GT pothole)
- **Fine-tuned:** 3 FPs (2 pothole, 1 alligator_crack), 1 FN
- Alligator_crack FP at [134, 384, 441, 575] — large region covering bottom of image
- Original epoch72 had TP=1 here (IoU 0.599)

### road010.jpg (1 GT pothole) — ONLY MATCH
- **Fine-tuned:** 1 TP (IoU 0.643), 3 FP potholes
- Same as original: this is the only image both models detect

### road003.jpg (1 GT alligator_crack)
- **Fine-tuned:** 0 detections, 1 FN
- Large alligator crack spanning most of image — completely missed

### road007.jpg (1 GT pothole)
- **Fine-tuned:** 7 FPs (6 alligator_crack, 1 pothole), 1 FN
- Severe class confusion: predicts alligator_crack across entire pothole region
- Original also had 5 alligator_crack FPs here

### road026.jpg (1 GT alligator_crack)
- **Fine-tuned:** 1 FP alligator_crack (wrong location), 1 FN
- FP at [651, 2, 749, 176] vs GT at [99, 0, 649, 580] — no overlap

---

## Conclusion

**Fine-tuning on `yol11s_realworld_finetune_v2` FAILED to improve the model:**

1. ❌ **Pothole recall decreased** from 50% to 16.7%
2. ❌ **Alligator crack FP not reduced** (remains at 9)
3. ❌ **Class confusion not fixed** — model still predicts alligator_crack on potholes
4. ❌ **Smoke test target failed** (1/4 vs 3/4)
5. ❌ **Holdout performance worse** (0/5 vs 1/5)

**Recommendation:** The fine-tuning approach used for v2 was detrimental. Consider:
- Reviewing the fine-tuning dataset for label quality/class balance
- Checking if learning rate was too high causing catastrophic forgetting
- Evaluating whether the fine-tuning data had sufficient alligator_crack examples
- Reverting to epoch72 or trying a different fine-tuning strategy

---

## Output Files

- `FINE_TUNED_METRICS.json` — Complete evaluation metrics
- `FINE_TUNED_VS_ORIGINAL.csv` — Side-by-side comparison
- `ERROR_CASES.csv` — Per-detection error analysis
- `COMMANDS.md` — Reproduction commands
- `annotated/` — 7 annotated images (conf 0.05)
  - road001_conf0.05.jpg
  - road002_conf0.05.jpg
  - road003_conf0.05.jpg
  - road007_conf0.05.jpg
  - road009_conf0.05.jpg
  - road010_conf0.05.jpg
  - road026_conf0.05.jpg