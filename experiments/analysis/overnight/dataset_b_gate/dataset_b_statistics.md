# Dataset B Statistics

## Acquisition Status: FAILED

Could not acquire Dataset B (RDD2022 non-India subset) due to:
1. **S3 bucket access denied** (403 Forbidden) for country-specific ZIPs
2. **FigShare full dataset download impractically slow** (~97 hours at 22 MB/min)
3. **No alternative public source identified**

All statistics below are theoretical/expectational based on public documentation.

## Full Dataset RDD2022 (Expectational)

| Metric | Value |
|--------|-------|
| Total images | 47,420 |
| Labeled images | 25,727 (54%) |
| Unlabeled images | 21,693 (46%) |
| Total damage instances | 55,000+ |
| Countries | 6 (Japan, India, Czech Republic, Norway, United States, China) |
| Classes | 4 (D00 Longitudinal Crack, D10 Transverse Crack, D20 Alligator Crack, D40 Pothole) |
| Annotation format | Pascal VOC XML (train), images only (test) |

## India Subset (Expectational)

| Metric | Value |
|--------|-------|
| India images (labeled) | ~9,665 |
| Current artifact images | 1,530 |
| India transverse_crack instances | 30 |
| India pothole instances | 3,187 |
| India pothole share | 70.4% of India objects |

## Non-India Portion (RDD2022 minus India subset) (Expectational)

| Metric | Value (estimated) |
|--------|-------------------|
| Total images | ~37,755 |
| Labeled images | ~16,062 |
| Unlabeled images | ~21,693 (global) |
| Countries represented | 5 (Japan, Czech Republic, Norway, United States, China) |
| Negative/background images | ~46% of total (~17,377) |

## Current Test Set

| Metric | Value |
|--------|-------|
| Test images | 230 |
| Test GT objects | 679 |
| Origin | India subset |
| Overlap with India subset | 100% of test images |

## Class Distribution: Current Artifact vs Full RDD2022 (Expectational)

| Class | Current artifact (1,530 images) | Full RDD2022 (47,420 images) | Notes |
|-------|--------------------------------|------------------------------|-------|
| longitudinal_crack | 498 | ~18,000 (est.) | Current artifact has 11.7% of train objects |
| transverse_crack | 30 | ~1,500 (est.) | Very rare in both |
| alligator_crack | 645 | ~5,000 (est.) | |
| pothole | 3,187 | ~10,000 (est.) | D40 dominates in current artifact (73.1% of objects) |
| imbalance ratio (pothole:transverse) | 106.23x | estimated 6-8x (more balanced globally) | Current artifact severely biased |

## Negative Sample Availability

| Dataset | Negative Images (no pothole) | Notes |
|---------|-----------------------------|-------|
| Current artifact | 0 | All 1,530 images contain pothole |
| Full RDD2022 (global) | ~21,693 unlabeled | 46% of images have no damage annotations |
| Full RDD2022 (non-India) | estimated ~17,000+ | Excludes India unlabeled portion; provides negatives from other countries |

## Key Statistical Insight

The current local artifact has **100% pothole coverage** and **zero negative samples**.
The full RDD2022 dataset provides **~46% negative images** across 5+ countries, which directly addresses the H1 negative-diversity hypothesis.
However, using the full dataset requires excluding the India subset to avoid overlap with the current train/val/test splits.

## Acquisition FAILED — Statistics Remain Theoretical

These statistics are based on published analyses and official documentation.
Without the actual downloaded data, all counts are estimatory only.
Experiment 2 cannot proceed without verified actual counts.