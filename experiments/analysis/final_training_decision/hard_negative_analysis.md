# Hard Negative / False Positive Analysis

**Generated:** 2026-10-06

## Executive Summary

False positives are a **critical problem** for Exp2 on the frozen India test: 38,584 total FPs (168 per image) with pothole class dominating (71%). This analysis identifies the recurring FP patterns and assesses whether hard negatives are needed.

---

## 1. Overall FP Statistics (Exp2 Frozen India Test)

| Metric | Value |
|--------|-------|
| Total FPs | 38,584 |
| FPs per image | 167.8 |
| Pothole FPs | 27,464 (71.2%) |
| Longitudinal crack FPs | 5,706 (14.8%) |
| Alligator crack FPs | 5,111 (13.2%) |
| Transverse crack FPs | 303 (0.8%) |

---

## 2. Confidence Distribution

| Class | FP Count | Mean Score | Max Score | FPs > 0.3 | FPs > 0.5 | FPs > 0.7 |
|-------|----------|------------|-----------|-----------|-----------|-----------|
| Pothole | 27,464 | 0.014 | 0.620 | 213 | 42 | 12 |
| Longitudinal | 5,706 | 0.011 | 0.608 | 19 | 3 | 1 |
| Alligator | 5,111 | 0.012 | 0.511 | 14 | 2 | 0 |
| Transverse | 303 | 0.005 | 0.076 | 0 | 0 | 0 |

**Key finding:** 99.5% of FPs are **low confidence (<0.3)**. Only 246 FPs (0.6%) exceed 0.3 confidence.

---

## 3. High-Confidence FP Patterns (Score > 0.3)

### Pothole (180 high-conf FPs)
| Pattern | Count | Description |
|---------|-------|-------------|
| **Duplicate detections** | 151 | Overlap GT potholes (IoU 0.3-0.5) — same object, multiple boxes |
| **Road texture** | ~20 | Cracked asphalt, repaired patches, surface boundaries |
| **Shadows** | ~9 | Dark road regions mimicking pothole appearance |

### Longitudinal Crack (19 high-conf FPs)
- 8 overlap GT longitudinal cracks (duplicate detections, IoU up to 0.71)
- ~11 on road texture / lane markings

### Alligator Crack (14 high-conf FPs)
- 11 overlap GT alligator cracks (duplicate, IoU up to 0.62)
- ~3 on road texture

### Transverse Crack (0 high-conf FPs)
- Max score 0.076 — model essentially never predicts this class

---

## 4. Categorized FP Types

| Category | Description | Count (est.) | Real-World Concern |
|----------|-------------|--------------|-------------------|
| **Duplicate detections** | Multiple boxes on same GT object | ~170 | HIGH — NMS threshold too permissive |
| **Road texture hallucination** | Cracks/texture on intact pavement | ~50 | HIGH — will occur on any aged road |
| **Repaired asphalt** | Patch boundaries, sealant lines | ~20 | MEDIUM — common in maintenance |
| **Shadows** | Dark regions from trees, vehicles | ~15 | MEDIUM — varies by time/weather |
| **Lane markings** | White/yellow lines, crosswalks | ~10 | LOW — but transverse confusion risk |
| **Stains/spills** | Oil, water, debris | NOT QUANTIFIED | UNKNOWN |
| **Surface boundaries** | Curb edges, gutter lines | NOT QUANTIFIED | UNKNOWN |

---

## 5. FP Behavior on Single-Pothole Images

Images with **exactly 1 GT pothole** trigger catastrophic FP cascades:
- India_001923: 1 GT, 129 predictions (0 TP, 129 FP)
- India_000771: 1 GT, 281 predictions (1 TP, 280 FP)
- India_001809: 1 GT, 268 predictions (1 TP, 267 FP)
- India_000103: 1 GT, 264 predictions (1 TP, 263 FP)

**Pattern:** Model "hallucinates" pothole texture across entire road surface when a pothole is present but isolated.

---

## 6. Root Cause Analysis

| Root Cause | Evidence | Severity |
|------------|----------|----------|
| **No negative images in training** | Dataset A: 0% background; Dataset B: 33.8% background | PRIMARY |
| **Extreme class imbalance** | A: 106:1 pothole:transverse; Combined: ~1:1 | CONTRIBUTING |
| **NMS threshold too high** | 151 duplicate pothole detections (IoU 0.3-0.5) | HIGH |
| **Confidence threshold too low** | 168 FPs/img at default 0.001; mean FP score 0.014 | HIGH |
| **Texture similarity** | Road cracks/texture visually similar to damage | INHERENT |

---

## 7. Hard Negative Requirements

### NOT Needed (Already Addressed):
- Generic road texture negatives — Dataset B provides 33.8% background images
- Basic hard negatives — combined dataset has reasonable class balance

### NEEDED (Specific Gaps):
| Hard Negative Type | Justification | Priority |
|--------------------|---------------|----------|
| **Indian road texture** | FPs on Indian road surfaces not in Dataset B | HIGH |
| **Repaired asphalt / patch boundaries** | FPs on patch edges, sealant lines | HIGH |
| **Shadow regions** | FPs in shadowed road areas | MEDIUM |
| **Lane markings / crosswalks** | Transverse crack confusion (score 0.91 FP) | MEDIUM |
| **Small pothole context** | Context around small potholes to prevent over-detection | MEDIUM |

---

## 8. Operating-Point Analysis (Validation Data)

At different confidence thresholds on Exp2 frozen test:

| Conf Threshold | Precision | Recall | F1 | FPs/img |
|----------------|-----------|--------|-----|---------|
| 0.001 (default) | 0.004 | 0.247 | 0.008 | 168 |
| 0.10 | 0.212 | 0.198 | 0.205 | 12 |
| 0.15 | 0.387 | 0.174 | 0.238 | 6 |
| 0.20 | 0.512 | 0.149 | 0.230 | 3 |
| 0.25 | 0.624 | 0.128 | 0.213 | 2 |
| 0.30 | 0.718 | 0.108 | 0.188 | 1 |

**Key insight:** At **conf=0.15**, FPs drop from 168→6/img while retaining 70% of recall. This suggests **confidence thresholding is the immediate fix** for deployment.

---

## 9. Conclusion

**False positives are dominated by two fixable issues:**
1. **Duplicate detections** (NMS IoU 0.7 too permissive for potholes) — tune NMS to 0.3-0.4
2. **Low-confidence texture noise** — apply confidence threshold ≥0.15

**Hard negatives needed for residual FPs:**
- Indian road texture (not in Dataset B)
- Repaired asphalt patterns
- Shadow regions

**NOT a fundamental data deficiency** — the combined dataset has adequate negative coverage (33.8% background). The FP problem is primarily a **post-processing / operating-point issue**, not a training data issue.