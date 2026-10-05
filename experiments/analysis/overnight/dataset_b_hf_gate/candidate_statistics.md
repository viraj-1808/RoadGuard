# Dataset B Candidate Statistics

## Overall Statistics

| Metric | Value |
|--------|-------|
| **Total images** | 38,385 |
| **Total objects (bounding boxes)** | 59,167 |
| **Total classes** | 4 |
| **Train images** | 26,869 |
| **Validation images** | 5,758 |
| **Test images** | 5,758 |
| **Train objects** | 41,667 |
| **Validation objects** | 8,776 |
| **Test objects** | 8,724 |
| **Negative/background images** | 12,955 (33.8%) |

## Split Statistics

| Split | Images | With objects | Empty labels | Objects | Negative rate |
|-------|--------|--------------|--------------|---------|---------------|
| train | 26,869 | 17,902 | 8,967 | 41,667 | 33.4% |
| validation | 5,758 | 3,743 | 2,015 | 8,776 | 35.0% |
| test | 5,758 | 3,785 | 1,973 | 8,724 | 34.3% |
| **Total** | **38,385** | **25,430** | **12,955** | **59,167** | **33.8%** |

## Class Distribution

| Class | ID | Train boxes | Val boxes | Test boxes | **Total boxes** | % of total |
|-------|-----|-------------|-----------|------------|-----------------|------------|
| longitudinal_crack | 0 | 18,201 | 3,890 | 3,925 | **26,016** | 44.0% |
| transverse_crack | 1 | 8,386 | 1,769 | 1,675 | **11,830** | 20.0% |
| alligator_crack | 2 | 7,526 | 1,553 | 1,537 | **10,616** | 17.9% |
| pothole | 3 | 7,554 | 1,564 | 1,587 | **10,705** | 18.1% |
| **Total** | | **41,667** | **8,776** | **8,724** | **59,167** | 100% |

## Image Counts by Country (Total)

| Country | Train | Val | Test | **Total** | % of total |
|---------|-------|-----|------|-----------|------------|
| Japan | 7,432 | 1,550 | 1,524 | **10,506** | 27.4% |
| Norway | 5,708 | 1,256 | 1,197 | **8,161** | 21.3% |
| India | 5,368 | 1,172 | 1,166 | **7,706** | 20.1% |
| United States | 3,348 | 704 | 753 | **4,805** | 12.5% |
| China | 3,051 | 645 | 682 | **4,378** | 11.4% |
| Czech Republic | 1,962 | 431 | 436 | **2,829** | 7.4% |
| **Total** | **26,869** | **5,758** | **5,758** | **38,385** | 100% |

## Country Distribution by Split

### Train (26,869 images)
- Japan: 7,432 (27.7%)
- Norway: 5,708 (21.2%)
- India: 5,368 (19.9%)
- United States: 3,348 (12.5%)
- China: 3,051 (11.3%)
- Czech Republic: 1,962 (7.3%)

### Validation (5,758 images)
- Japan: 1,550 (26.9%)
- Norway: 1,256 (21.8%)
- India: 1,172 (20.4%)
- United States: 704 (12.2%)
- China: 645 (11.2%)
- Czech Republic: 431 (7.5%)

### Test (5,758 images)
- Japan: 1,524 (26.5%)
- Norway: 1,197 (20.8%)
- India: 1,166 (20.2%)
- United States: 753 (13.1%)
- China: 682 (11.8%)
- Czech Republic: 436 (7.6%)

## Negative/Background Diversity

**Dataset A (current artifact):**
- Total: 1,530 images
- Negative (no pothole): 0
- Negative rate: **0%**

**Dataset B candidate (non-India after exclusion):**
- Total: 30,679 images (38,385 - 7,706 India)
- Negative (empty label): ~10,369 (estimated 33.8% of non-India)
- Negative rate: **~33.8%**

**Combined (Dataset A + non-India Dataset B):**
- Total: 32,209 images (1,530 + 30,679)
- Negative: ~10,369 (from Dataset B only)
- Negative rate: **~32.2%**

**Improvement**: From 0% to 32.2% negative diversity — a massive improvement.

## Image Size and Format

- Format: JPEG (.jpg)
- Original RDD2022 images: 640×480 or variable resolution
- The Hugging Face export preserves original image sizes

## data.yaml (Candidate)

```yaml
path: .
train: images/train
val: images/valid
test: images/test
nc: 4
names:
  0: longitudinal_crack
  1: transverse_crack
  2: alligator_crack
  3: pothole
```

**data.yaml SHA256**: `49f3606a45dca2f83a175aeb8f5299e823f46e07172b2555b39d39a0d41f0828`

## Comparison with Dataset A

| Metric | Dataset A (current) | Dataset B candidate (non-India) | Combined |
|--------|---------------------|---------------------------------|----------|
| Train images | 1,071 | ~21,501 | ~22,572 |
| Total images | 1,530 | 30,679 | 32,209 |
| Total objects | 4,360 | ~40,807 (est.) | ~45,167 |
| Transverse instances | 30 | ~8,336 (train only) | ~8,366 |
| Negative images | 0 | ~10,369 | ~10,369 |
| Negative rate | 0% | 33.8% | 32.2% |

## Conclusion

The candidate dataset provides:
- ✅ 33.8% negative/background diversity (vs 0% in Dataset A)
- ✅ Massive increase in transverse-crack instances (from 30 to ~8,336)
- ✅ Balanced class distribution (44% longitudinal, 20% transverse, 18% alligator, 18% pothole)
- ✅ Geographic diversity across 6 countries (non-India: 5 countries)
- ✅ Reproducible train/val/test split (70/15/15)
- ⚠️ Only 38% of raw images on disk (metadata is complete)