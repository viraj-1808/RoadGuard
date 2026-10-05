# Dataset B Hypothesis Fit Assessment

## Acquisition Status: FAILED

Could not acquire Dataset B (RDD2022 non-India subset) due to:
1. **S3 bucket access denied** (403 Forbidden) for country-specific ZIPs
2. **FigShare full dataset download impractically slow** (~97 hours at 22 MB/min)
3. **No alternative public source identified**

All hypothesis fit assessments below are theoretical/expectational based on public documentation.

## Hypothesis H1: Negative/Background Diversity Deficiency

### Problem Statement
Current training data has **100% pothole coverage**: every image contains D40 annotations. Zero negative/background images exist. The model has no concept of "non-pothole" road regions.

### Dataset B Negative Availability Status: THEORETICAL

| Dataset | Negative Images (no pothole) | Negative Coverage | H1 Fit Assessment |
|---------|-----------------------------|--------------------|-------------------|
| Current artifact | 0 | 0% | Baseline fails H1 |
| Full RDD2022 (global, theo) | ~21,693 unlabeled (46%) | 46% | **Theoretical positive impact** |
| Full RDD2022 (non-India, theo) | ~17,000+ (estimated 45-50%) | 45-50% | **Theoretical positive impact** |
| Current artifact + non-India negatives (theo) | ~17,000+ | 45-50% | **Addresses H1 (if acquired)** |

### Assessment: H1 Fit = PASS (methodologically, but not verified)

**Reasoning**:
- Full RDD2022 provides 46% negative images across 5+ countries (Japan, Czech, Norway, US, China)
- These negatives include normal road surfaces, shadows, textures without damage
- Using only non-India portions ensures zero overlap with current train/val/test
- The 46% negative rate is a meaningful increase from 0%
- Combined with current artifact's 0%, the effective negative pool becomes 17,000+ images

**Caveat**: If the India subset is inadvertently included, H1 fit reverts to failure because India images are 100% pothole-positive.
**Critical gap**: Data cannot be acquired to verify.

### Confidence: LOW (no actual data)

## Hypothesis H2: Class Imbalance — Rare Class Under-representation

### Problem Statement
transverse_crack has only 30 instances. Other classes likely similarly imbalanced. Standard training ignores rare classes.

### Dataset B Class-Balance Availability Status: THEORETICAL

| Dataset | Transverse Instances | As Share | H2 Fit Assessment |
|---------|---------------------|----|-------------------|
| Current artifact | 30 | 0.7% | Baseline fails H2 |
| Full RDD2022 (theo) | ~1,500 (est.) | ~3% | Theoretical improvement |
| Full RDD2022 non-India (theo) | ~1,500 (est.) | ~8-10% | Theoretical improvement |
| Current artifact + non-India (theo) | ~1,530 | ~8-10% | Addresses H2 (if acquired) |

### Assessment: H2 Fit = PASS (methodologically, but not verified)

**Reasoning**:
- Non-India RDD2022 transverse instances (~1,500) dramatically improve representation
- Imbalance ratio drops from 106:1 to ~51:1, a 52% reduction
- Transverse class still rare but now has meaningful training examples
- Risk: transverse semantics in non-India images may differ (road surface, lighting, crack patterns)
- Mitigation: verify transverse class compatibility (see taxonomy section)

**Critical gap**: Data cannot be acquired to verify class distribution.

### Confidence: LOW (no actual data)

## Hypothesis H4: Localization Quality

### Problem Statement
mAP50-95 = 0.0903 << mAP50 = 0.252. Boxes are loose/imprecise.

### Dataset B Localization Impact Status: THEORETICAL

| Aspect | Current artifact | Full RDD2022 (non-India, theo) | Expected Impact |
|--------|----------------|--------------------------|-----------------|
| Box annotation quality | Pascal VOC XML (standard) | Pascal VOC XML (standard) | Neutral |
| Object size distribution | 54% of potholes <1% area | Similar distribution expected | Neutral |
| Geographic variety | India-only | 5 countries (different camera angles, road surfaces, lighting) | **Theoretical improvement** |

### Assessment: H4 Fit = UNKNOWN (no actual data)

**Reasoning**:
- Localization quality is primarily a model/loss-function issue, not purely data quantity
- Adding more diverse geographies may help model generalize box positioning
- Dataset B alone unlikely to disproportionately raise mAP50-95

### Confidence: LOW (no actual data)

## Summary Table

| Hypothesis | H1 Negative Diversity | H2 Class Imbalance | H4 Localization |
|------------|----------------------|--------------------|-----------------|
| Current artifact status | FAIL (0% negatives) | FAIL (30 instances, 106x imbalance) | UNKNOWN |
| Full RDD2022 non-India (theoretical) | PASS (46% negatives) | PASS (1,500 transverse) | UNKNOWN |
| Confidence | LOW (no data) | LOW (no data) | LOW (no data) |

## Overall Hypothesis Fit Rating

- **H1**: Using non-India RDD2022 as Dataset B **would theoretically address** the primary hypothesis. Confidence: **LOW** (data not acquired).
- **H2**: Using non-India RDD2022 as Dataset B **would theoretically improve** transverse-crack imbalance. Confidence: **LOW** (data not acquired).
- **H4**: Dataset B alone **would theoretically** not meaningfully improve mAP50-95. Confidence: **LOW** (no data).

## Acquisition FAILED

**All hypothesis fit assessments are theoretical and unverified.**
Dataset B could not be acquired due to S3 403 errors and FigShare download slowness.

**Experiment 2 CANNOT PROCEED** — no actual data to verify hypothesis fit.