# Pothole Analysis (Class 3)

**Generated:** 2026-10-06

## Executive Summary

Pothole is the primary real-world use case and the dominant class in Dataset A (72-75% of objects). Dataset B provides substantial additional pothole data (8,044 train) with better size diversity. However, a **68% domain gap** exists between Dataset B validation (mAP50-95=0.488) and frozen India test (mAP50-95=0.152).

---

## 1. Data Distribution

| Split | Dataset A | Dataset B | Total |
|-------|-----------|-----------|-------|
| Train | 2,219 | 8,044 | 10,263 |
| Val | 456 | 697 | 1,153 |
| Test | 512 | N/A | 512 |
| **Total** | **3,187** | **8,741** | **11,928** |

**Proportion in training:**
- Dataset A: 72.8% of objects
- Dataset B: 22.1% of objects (more balanced)

---

## 2. Size Distribution Comparison

### Dataset A (2,219 train)
| Size Category | Count | Percentage |
|---------------|-------|------------|
| Very Small (<0.1%) | 25 | 1.1% |
| Small (0.1-1%) | 1,179 | 53.1% |
| Medium (1-10%) | 916 | 41.3% |
| Large (>10%) | 99 | 4.5% |

### Dataset B (8,044 train)
| Size Category | Count | Percentage |
|---------------|-------|------------|
| Very Small (<0.1%) | 257 | 3.2% |
| Small (0.1-1%) | 3,089 | 38.4% |
| Medium (1-10%) | 3,107 | 38.6% |
| Large (>10%) | 1,591 | 19.8% |

**Key differences:**
- Dataset B has **2.9× more very small** potholes
- Dataset B has **4.4× more large** potholes
- Dataset A is concentrated in small/medium (94% combined)

---

## 3. Model Performance

### Frozen India Test (Exp2)
| Metric | Value |
|--------|-------|
| Precision | 0.452 |
| Recall | 0.475 |
| mAP50 | 0.420 |
| mAP50-95 | 0.152 |

### Dataset B Validation (Exp2)
| Metric | Value |
|--------|-------|
| Precision | 0.681 |
| Recall | 0.776 |
| mAP50 | 0.774 |
| mAP50-95 | 0.488 |

### Experiment 1 (Dataset A only, frozen test)
| Metric | Value |
|--------|-------|
| mAP50-95 | 0.0903 |

**Improvement from Exp1 → Exp2 on India test:** +68% mAP50-95 (0.090 → 0.152)

**Domain gap (B val → India test):**
- mAP50-95 drop: **0.336** (69% relative)
- Recall drop: **0.301** (39% relative)
- Precision drop: **0.229** (34% relative)

---

## 4. Visual Failure Evidence

From `experiments/analysis/overnight/visual_cases/`:
- **contact_fp_high_confidence.jpg**: High-confidence pothole FPs on road texture, repaired patches, shadows
- **contact_fn_small.jpg**: Small pothole misses (areas 575-11,092 px², avg 2,713 px²)
- **contact_fn_large.jpg**: Some large potholes missed due to unusual appearance
- **Frozen test FPs**: 27,464 pothole FPs (71% of all FPs), 167.8/img average
- **High-conf FPs**: 180 pothole FPs >0.3 score, 151 overlap GT potholes (duplicate detections)

---

## 5. Failure Mode Breakdown

| Failure Mode | Evidence | Severity |
|--------------|----------|----------|
| **Small pothole misses** | 89/270 FNs (33%) are small objects; mean FN area 2,713 px² | HIGH |
| **Massive FP explosion** | 27,464 FPs (168/img); many on road texture | CRITICAL |
| **Duplicate detections** | 151 high-conf FPs overlap GT (IoU 0.3-0.5) | HIGH |
| **Pothole↔Alligator confusion** | 6 cross-class high-conf overlaps | MEDIUM |
| **Localization quality** | Mean IoU 0.738; 55% of TPs in 0.5-0.7 band | MEDIUM |

---

## 6. What KIND of Pothole Data Would Be Useful

### Supported by Evidence:
| Missing Category | Evidence |
|------------------|----------|
| **Small/distant forward-facing potholes** | 33% of FNs are small; Dataset A only 1.1% very small |
| **Indian road potholes** | 69% domain gap from B val → India test |
| **Irregular-shaped potholes** | Visual FNs show non-circular shapes missed |
| **Difficult-background potholes** | FPs on repaired asphalt, shadows, texture |
| **Wet/monsoon potholes** | NOT ESTABLISHED — no weather metadata |

### NOT Supported (Speculative):
| Category | Why Not Supported |
|----------|-------------------|
| Night/low-light potholes | No lighting metadata |
| Different camera viewpoints | Both datasets forward-facing |

---

## 7. Domain Gap Analysis

The 69% mAP50-95 drop from Dataset B validation to India test is the **largest single domain gap** for any class.

Possible causes:
1. **Road surface appearance** — India roads may have different texture/color
2. **Pothole morphology** — Indian potholes may differ in shape/depth/edges
3. **Scale distribution** — Test has different size distribution than B val
4. **Background clutter** — Different road markings, repairs, shadows
5. **Camera characteristics** — Different resolution/aspect in test (720x720 square)

**Critical finding:** Dataset B validation is **not predictive** of India deployment performance for potholes.

---

## 8. Conclusion

**Pothole detection has improved (+68% mAP50-95 vs Exp1) but remains insufficient for real-world deployment.**

- **Recall 0.475** = misses 52.5% of potholes
- **Precision 0.452** = many false alarms
- **Domain gap 69%** = Dataset B validation doesn't transfer to India

**Most impactful missing data:**
1. **Small/distant potholes** on Indian roads (forward-facing viewpoint)
2. **Indian road surface textures** as hard negatives
3. **Irregular pothole shapes** (not just circular)

Dataset B helps (better size diversity, more examples) but the domain gap suggests **India-specific pothole data** would be the highest-value addition.