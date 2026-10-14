# Verified Dataset Status & Fine-Tuning Justification Report

**Dataset:** RoadGuard Real-World v1.0  
**Date:** 2026-10-11  
**Checkpoint Baseline:** `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt` (SHA-256: e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5) — **PRESERVED, NOT MODIFIED**

---

## 1. Verified Dataset Status

| Metric | Value | Status |
|--------|-------|--------|
| **Total source images** | 39 | ✅ Complete |
| **Confirmed annotations** | 20 images, 25 instances | ✅ Complete |
| **NEEDS_HUMAN_REVIEW** | 15 images | ⏳ **BLOCKED** |
| **LIKELY_NEGATIVE** | 3 images | ⏳ **BLOCKED** |
| **Uncertain total** | 18 images | ⏳ **BLOCKED** |
| **Verification rate** | 20/39 = 51% | ⚠️ **Insufficient** |

### Confirmed Class Distribution
| Class | Instances | Images |
|-------|-----------|--------|
| longitudinal_crack (0) | 2 | 2 |
| transverse_crack (1) | 0 | 0 |
| alligator_crack (2) | 11 | 9 |
| pothole (3) | 12 | 11 |

### Leakage-Safe Split (Confirmed Only)
| Split | Images | Instances | Classes Covered |
|-------|--------|-----------|-----------------|
| train | 10 | 13 | pothole, alligator_crack, longitudinal_crack |
| val | 5 | 6 | pothole, alligator_crack |
| holdout | 5 | 6 | pothole, alligator_crack |

---

## 2. Annotation Quality Verification

| Check | Result | Details |
|-------|--------|---------|
| Class mapping | ✅ PASS | 0=longitudinal, 1=transverse, 2=alligator, 3=pothole |
| Bbox format | ✅ PASS | YOLO normalized (x_center, y_center, width, height) |
| Bbox bounds | ✅ PASS | All values in [0,1] range |
| Class IDs valid | ✅ PASS | Only 0,2,3 used (no class 1 instances) |
| No duplicates | ✅ PASS | Each instance unique per image |
| Provenance tracked | ✅ PASS | model_derived / model_derived_epoch72 / human_reviewed |
| Split leakage | ✅ PASS | Near-duplicates grouped, no train/val/holdout overlap |
| Provenance balance | ⚠️ WARNING | 15 model_derived, 2 model_derived_epoch72, 3 human_reviewed |

---

## 3. Fine-Tuning Justification Assessment

### Requirements for Safe Fine-Tuning (per instructions)
| Requirement | Met? | Evidence |
|-------------|------|----------|
| Valid starting checkpoint | ✅ | epoch72.pt has optimizer state, beats baseline |
| Correct data configuration | ✅ | Dataset YAML verified, class mapping consistent |
| Plausible improvement path | ⚠️ PARTIAL | Class confusion identified but insufficient verified data |
| Sufficient verified training data | ❌ **NO** | Only 20/39 images verified (51%) |
| Conservative DataLoader possible | ✅ | workers=2, prefetch=2, cache=False tested |
| RAM/VRAM monitoring | ✅ | Implemented in fine-tune v2 |
| Best validation checkpoint preserved | ✅ | Would be separate from epoch72 |

### Critical Blocker: **Insufficient Verified Data**
- **20 verified images** is far below the 100+ needed for reliable 75/100 evaluation
- **Only 51% verification rate** — 18 images still need human decisions
- **Class imbalance persists:** 0 transverse_crack instances, only 2 longitudinal_crack
- **Provenance imbalance:** 75% model-derived, only 15% human-reviewed

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Catastrophic forgetting (as in v2) | HIGH | Model degradation | Need more verified data before retry |
| Class confusion persists | HIGH | alligator_crack FP remains | Need hard negatives + balanced labels |
| Overfitting to 20 images | HIGH | Poor generalization | Need ≥100 verified images |
| Memory pressure crash | MEDIUM | Training loss | Conservative config tested |

---

## 4. Recommendation: **DO NOT FINE-TUNE YET**

### Verdict: **Insufficient evidence to justify fine-tuning**

**Reasoning:**
1. **Only 51% of images verified** — fine-tuning on mostly model-derived labels risks reinforcing errors
2. **Previous fine-tune (v2) degraded performance** — pothole recall dropped 50%→16.7%
3. **Class confusion root cause unaddressed** — need human-verified hard negatives for alligator_crack
4. **Transverse crack has 0 instances** — cannot train meaningful detector
5. **75/100 target unachievable** — need ≥100 verified images

---

## 5. Required Actions Before Next Fine-Tuning Attempt

### Priority 1: Complete Human Review (Blocks Everything)
- [ ] Annotate 15 NEEDS_HUMAN_REVIEW images
- [ ] Confirm 3 LIKELY_NEGATIVE images
- **Target:** ≥35 verified images (90% verification rate)

### Priority 2: Collect Additional Data
- [ ] Source ≥65 additional real-world road images with verified annotations
- [ ] Prioritize: transverse_crack examples, high-res potholes, portrait orientation
- [ ] Target: ≥100 total verified images for 75/100 evaluation

### Priority 3: Address Class Confusion
- [ ] Collect 50+ hard negative patches (clean road misclassified as alligator_crack)
- [ ] Create balanced training set with equal class representation
- [ ] Implement contrastive loss between pothole/alligator_crack embeddings

### Priority 4: Architecture/Inference Fixes
- [ ] Implement SAHI with verified 4K GT (current SAHI finds FP)
- [ ] Multi-scale training (640/720/800/1280)
- [ ] Portrait/landscape augmentation pipeline

---

## 6. Experiment 2 epoch72 Checkpoint Status

| Property | Value |
|----------|-------|
| **Path** | `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt` |
| **SHA-256** | `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5` |
| **Status** | **PRESERVED** — not modified, not overwritten |
| **Optimizer State** | ✅ Intact (can resume) |
| **Best Metrics** | mAP@50=0.300, mAP@50-95=0.118 on frozen test (beats baseline) |
| **Smoke Test** | 3/4 potholes at IoU≥0.5 (conf=0.05) |

---

## 7. Summary Statement

**Fine-tuning is NOT justified at this time.**

The verified dataset contains only **20/39 images (51%)** with confirmed ground truth. The remaining **18 images require human annotation decisions** before the dataset can support reliable training or evaluation. The previous fine-tuning attempt (v2) degraded model performance, likely due to insufficient verified data and class imbalance.

**Next actionable step:** Complete human review of the 18 uncertain images using the provided `human_review_package/`, then re-assess with a target of ≥35 verified images before considering another fine-tuning run.

**All existing checkpoints, data, and outputs preserved.** The baseline epoch72.pt remains intact and available for inference or future training resumption.