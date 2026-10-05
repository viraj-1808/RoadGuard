# Country Audit

## Methodology

Country prefixes in filenames (e.g., `Japan_######.jpg`, `India_######.jpg`, `United_XXXXXX.jpg`) were used to determine country of origin. This is the standard identification method used in the RDD2022 dataset.

## Full Dataset Country Counts

| Country | Train | Val | Test | **Total** |
|---------|-------|-----|------|-----------|
| Japan | 7,432 | 1,550 | 1,524 | **10,506** |
| Norway | 5,708 | 1,256 | 1,197 | **8,161** |
| India | 5,368 | 1,172 | 1,166 | **7,706** |
| United States | 3,348 | 704 | 753 | **4,805** |
| China | 3,051 | 645 | 682 | **4,378** |
| Czech Republic | 1,962 | 431 | 436 | **2,829** |
| **Total** | **26,869** | **5,758** | **5,758** | **38,385** |

## India Subset

| Split | India Images | % of Split |
|-------|--------------|------------|
| Train | 5,368 | 20.0% |
| Validation | 1,172 | 20.4% |
| Test | 1,166 | 20.2% |
| **Total** | **7,706** | **20.1%** |

## Non-India Subset (Candidate Dataset B)

| Split | Non-India Images | % of Split |
|-------|------------------|------------|
| Train | 21,501 | 80.0% |
| Validation | 4,586 | 79.6% |
| Test | 4,592 | 79.8% |
| **Total** | **30,679** | **79.9%** |

## India Exclusion Verification

**India images BEFORE exclusion**: 7,706 (total across all splits)
**India images AFTER exclusion**: 0
**Non-India images remaining**: 30,679

**Verification**: All India images (7,706) successfully excluded from Dataset B candidate.

## India Subset vs Current Dataset A

The current Dataset A (`experiments/dataset/yolo_rdd2022_india/`) is a **subset** of the HF dataset's India portion.

| Metric | Current Dataset A | HF India Subset |
|--------|-------------------|-----------------|
| Train images | 1,071 | 5,368 |
| Val images | 229 | 1,172 |
| Test images | 230 | 1,166 |
| **Total** | **1,530** | **7,706** |

All 1,530 Dataset A images are contained within the 7,706 HF India subset images.

## Country Breakdown by Class (Train)

| Country | Long. | Trans. | Allig. | Pothole | Total |
|---------|-------|--------|--------|---------|-------|
| China | 2,843 | 1,648 | 671 | 714 | 5,876 |
| Czech | 682 | 275 | 126 | 0 | 1,083 |
| India | 1,103 | 50 | 1,428 | 969 | 3,550 |
| Japan | 2,781 | 2,847 | 4,394 | 5,871 | 15,893 |
| Norway | 6,080 | 1,226 | 334 | 0 | 7,640 |
| United States | 4,712 | 2,340 | 573 | 0 | 7,625 |

**Key observations**:
- Pothole (class 3) only appears in India, Japan, and China train data
- Czech, Norway, United States have NO pothole annotations in train
- Transverse-crack instances are distributed across all countries except Czech (which has zero in some splits)

## Conclusion

- India exclusion verified: 7,706 India images removed, 30,679 non-India images retained
- Country distribution is geographically diverse (5 countries)
- No country dominates the non-India subset (Japan leads with 10,506 total, but India had the most)
- The non-India subset provides meaningful geographic diversity for H1