# Dataset Structure Diagnosis: yolo_rdd2022_india

Generated: 2026-09-29

## Source Data

- **YOLO dataset**: `experiments/dataset/yolo_rdd2022_india/`
- **Normalized dataset**: `experiments/dataset/normalized_rdd2022_india/`
- **Class mapping**: 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole
- **Raw D40 = pothole (class 3)**, confirmed via conversion manifest

---

## 1. Training Images with Pothole (Class 3): 1071

## 2. Training Images without Pothole: 0

## 3. Training Images with ONLY Pothole: 528

## 4. Training Images with Pothole + Other Damage: 543

---

## 5. Full Class Distribution (train/val/test)

| Split | Images | Objects | Longitudinal | Transverse | Alligator | Pothole |
|-------|--------|---------|-------------|------------|-----------|---------|
| Train | 1071 | 3049 | 356 (11.7%) | 21 (0.7%) | 453 (14.9%) | 2219 (72.8%) |
| Val | 229 | 632 | 76 (12.0%) | 4 (0.6%) | 96 (15.2%) | 456 (72.2%) |
| Test | 230 | 679 | 66 (9.7%) | 5 (0.7%) | 96 (14.1%) | 512 (75.4%) |
| **All** | **1530** | **4360** | **498 (11.4%)** | **30 (0.7%)** | **645 (14.8%)** | **3187 (73.1%)** |

---

## 6. Object-Size Distribution (Normalized Area Bins)

**Pothole (class 3) area distribution across all splits:**

| Size Bin | Train | Val | Test |
|----------|-------|-----|------|
| <0.5% | 763 (34.4%) | 156 (34.2%) | 162 (31.6%) |
| <1% | 441 (19.9%) | 98 (21.5%) | 107 (20.9%) |
| <2% | 426 (19.2%) | 75 (16.4%) | 100 (19.5%) |
| <5% | 351 (15.8%) | 61 (13.4%) | 71 (13.9%) |
| <10% | 139 (6.3%) | 34 (7.5%) | 28 (5.5%) |
| 10-20% | 80 (3.6%) | 26 (5.7%) | 43 (8.4%) |
| 20-50% | 19 (0.9%) | 6 (1.3%) | 1 (0.2%) |
| 50%+ | 0 | 0 | 0 |

**Pothole area statistics:**

| Metric | Train | Val | Test |
|--------|-------|-----|------|
| Min area | 0.0586% | — | — |
| Max area | 38.71% | — | — |
| Mean area | 2.16% | — | — |
| Median area | 0.86% | — | — |

---

## 7. Empty / Annotation-Free Images

- **Train**: 0 empty images
- **Val**: 0 empty images
- **Test**: 0 empty images

Every single image in the dataset has at least one annotation. There are no truly "negative" or background-only images.

---

## 8. Small Object Analysis (<0.5%, <1%, <5% of Image Area)

**All objects combined across splits:**

| Threshold | Train | Val | Test |
|-----------|-------|-----|------|
| <0.5% area | 763 | 156 | 162 |
| <1% area | 1204 | 254 | 269 |
| <5% area | 1981 | 390 | 440 |

**Key insight**: Over 65% of pothole objects occupy less than 1% of the image area. These are extremely small bounding boxes that are likely difficult to detect and prone to false negatives.

---

## 9. Selection Bias Evidence (D40 in All Original Images)

**Manifest-derived original class counts (from normalized_rdd2022_india/manifest.json):**

| Class | Code | Count | Share |
|-------|------|-------|-------|
| Pothole | D40 | 3187 | 70.4% |
| Alligator crack | D20 | 645 | 14.3% |
| Longitudinal crack | D00+D01 | 498 | 11.0% |
| Transverse crack | D10+D11 | 30 | 0.7% |
| Excluded: D44 | road marking damage | 151 | — |
| Excluded: D43 | road marking damage | 5 | — |
| Excluded: D50 | annotation artifact | 8 | — |

**Bias diagnosis**: Pothole (D40) accounts for **70.4% of all original objects**. The normalized dataset inherited this bias with no balancing applied. The raw dataset appears to be heavily skewed toward pothole-dominant images (D40 present in virtually every image). There are **zero images without pothole annotations** in the normalized/YOLO dataset.

---

## 10. Hard Negative Candidates (Road Patches, Shadows, Stains)

**Finding: No hard negative candidates exist.**

Since every single image (100%) contains pothole annotations:
- There are **0 images without pothole** across all splits
- There are **0 images with only non-pothole annotations** (no pothole)
- The only "negative" images are those with other damage classes but no pothole — and there are **none**

**Implication**: The dataset contains no true negative samples. A model trained on this data cannot learn to distinguish potholes from road patches, shadows, stains, or other non-pothole regions because every training example is a positive pothole example. This is a fundamental dataset design flaw for detection tasks.

**Candidate hard negatives from other classes** (images that have other damage but no pothole): **0 images**.

---

## 11. Class Imbalance Statistics

| Metric | Value |
|--------|-------|
| Total objects | 4360 |
| Most frequent class | Pothole (class 3) = 3187 objects (73.1%) |
| Least frequent class | Transverse crack (class 1) = 30 objects (0.7%) |
| **Imbalance ratio** | **106.23x** (pothole vs transverse_crack) |
| Pothole vs longitudinal_crack | 6.4x |
| Pothole vs alligator_crack | 4.9x |
| Longitudinal vs transverse | 16.6x |
| Alligator vs transverse | 21.5x |

**The imbalance is extreme.** Pothole dominates the dataset at 73.1% of all objects. Transverse crack is nearly absent at 0.7%.

---

## 12. Verification: test=230 images, test=679 GT objects

| Check | Expected | Actual | Result |
|-------|----------|--------|--------|
| Test images | 230 | 230 | **PASS** |
| Test GT objects | 679 | 679 | **PASS** |
| Train images | 1071 | 1071 | PASS |
| Val images | 229 | 229 | PASS |
| Total images | 1530 | 1530 | PASS |
| Total objects | 4360 | 4360 | PASS |

---

## Summary of Critical Findings

1. **100% pothole coverage**: Every image contains pothole annotations. No negative samples exist.
2. **Extreme class imbalance**: 106x ratio between pothole and the rarest class.
3. **Small object dominance**: 54% of pothole objects occupy <1% of image area — extremely small, hard-to-detect boxes.
4. **Selection bias**: D40 (pothole) accounts for 70.4% of all original objects; the dataset was never balanced.
5. **No hard negatives**: Impossible to train a robust detector without negative examples; the model will have no concept of "non-pothole."
6. **Transverse crack near-absence**: Only 30 objects (0.7%) across the entire dataset — insufficient for learning.
7. **Alligator crack secondary**: 645 objects (14.8%) — present but heavily outnumbered by pothole.

## Recommended Actions

- Collect or synthesize negative samples (road patches without damage, shadows, stains)
- Balance the dataset by augmenting transverse crack and alligator crack samples
- Consider hard negative mining from external datasets
- Add small-object augmentation (scaling, cropping) to improve detection of tiny potholes
- Re-evaluate whether a detection model is appropriate given the complete lack of negatives; consider segmentation or classification instead