# Transverse Crack Analysis (Class 1)

**Generated:** 2026-10-06

## Executive Summary

Transverse crack is the **most critically deficient class** in the current training data and model performance. Dataset A contains only 21 training examples, while Dataset B provides 7,292. The model achieves **zero recall on the frozen India test set** (0/5 detected).

---

## 1. Data Distribution

| Split | Dataset A | Dataset B | Total |
|-------|-----------|-----------|-------|
| Train | 21 | 7,292 | 7,313 |
| Val | 4 | 918 | 922 |
| Test | 5 | N/A (frozen) | 5 |
| **Total** | **30** | **8,210** | **8,240** |

**Imbalance ratio in Dataset A:** Pothole:Transverse = 106:1
**Ratio in combined (A+B) training:** ~1:1 (balanced)

---

## 2. Size Distribution Comparison

### Dataset A (21 train examples)
| Size Category | Count | Percentage |
|---------------|-------|------------|
| Very Small (<0.1%) | 0 | 0.0% |
| Small (0.1-1%) | 5 | 23.8% |
| Medium (1-10%) | 16 | 76.2% |
| Large (>10%) | 0 | 0.0% |

### Dataset B (7,292 train examples)
| Size Category | Count | Percentage |
|---------------|-------|------------|
| Very Small (<0.1%) | 245 | 3.4% |
| Small (0.1-1%) | 3,234 | 44.4% |
| Medium (1-10%) | 3,589 | 49.2% |
| Large (>10%) | 224 | 3.1% |

**Key finding:** Dataset B provides the **full size spectrum** including 245 very small and 224 large transverse cracks completely absent from Dataset A.

---

## 3. Aspect Ratio Characteristics

Transverse cracks are long and thin (perpendicular to travel direction):
- **Normalized width mean:** ~0.21-0.22 (spans significant image width)
- **Normalized height mean:** ~0.12-0.17 (thin in travel direction)
- **Aspect ratio (w/h):** ~1.5-2.0 typical

Dataset A has only 21 examples to learn this distinctive shape.

---

## 4. Model Performance Evidence

### Frozen India Test (Exp2)
| Metric | Value |
|--------|-------|
| Recall | **0.000** (0/5 detected) |
| Precision | 1.000 (artifact: no predictions = no FP) |
| mAP50 | 0.0113 |
| mAP50-95 | 0.0092 |

### Dataset B Validation (Exp2)
| Metric | Value |
|--------|-------|
| Recall | 0.493 |
| Precision | 0.579 |
| mAP50 | 0.516 |
| mAP50-95 | 0.245 |

**Domain gap (B val → India test):**
- Recall drop: **0.493** (100% relative)
- mAP50-95 drop: **0.236** (96% relative)

---

## 5. Visual Failure Evidence

From `experiments/analysis/overnight/visual_cases/contact_transverse_all_missed.jpg`:
- All 5 frozen test transverse cracks missed: India_000115, India_001133, India_007153, India_007329, India_008017
- One high-confidence FALSE POSITIVE: India_001585 (score 0.91) — **road marking confusion**

From `contact_fp_high_confidence.jpg`:
- Transverse FP on road markings suggests class confusion with lane markings/crosswalks

---

## 6. Failure Cause Analysis

| Hypothesis | Evidence | Verdict |
|------------|----------|---------|
| **Data scarcity (Dataset A)** | Only 21 train examples; 106:1 imbalance | **PRIMARY** — Cannot learn class from 21 examples |
| Appearance mismatch (A vs B) | B has diverse sizes; A only medium | **CONTRIBUTING** — B's very small/large absent in A |
| Class confusion | High-conf FP on road markings (score 0.91) | **CONTRIBUTING** — Model confuses transverse with lane markings |
| Localization failure | Not applicable (no detections) | Not primary |
| Confidence failure | No predictions at any threshold | **PRIMARY** — Model never predicts this class |

---

## 7. Visual Compatibility (Dataset A vs B)

**NOT ESTABLISHED** — No visual inspection of Dataset B transverse examples was performed. However:
- Both from RDD2022 (same annotation protocol)
- Same camera type (smartphone dashcam)
- Same forward-facing viewpoint
- **Likely compatible** but not proven

---

## 8. Conclusion

**Transverse crack failure is caused primarily by catastrophic data scarcity in Dataset A (21 examples).**

Dataset B resolves this with 7,292 training examples (347× increase) covering the full size spectrum. The model's zero recall on India test is expected given 21 training samples.

**Remaining risk:** Even with Dataset B, the India test recall is 0.000 vs Dataset B val 0.493 — a 100% domain gap. This suggests:
1. Dataset B transverse cracks may not visually match India transverse cracks
2. OR the frozen test 5 examples are visually distinct
3. OR model needs more training to generalize

**Recommendation:** Dataset B is necessary but may not be sufficient. India-specific transverse crack data would be the most targeted improvement.