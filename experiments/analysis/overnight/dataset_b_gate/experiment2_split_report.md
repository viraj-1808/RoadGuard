# Experiment 2 Split Report

## Status: NOT CREATED

**Dataset B not acquired — Experiment 2 split cannot be constructed.**

## Proposed Split Design (Theoretical)

If Dataset B were acquired, the split would be:

### Training Data
- **Current Dataset A (India)**: 1,071 train images / 3,049 objects
- **Dataset B (Non-India RDD2022)**: ~37,755 images / ~25,000 objects (estimated)
- **Combined Training**: ~38,826 images / ~28,000 objects (estimated)

### Validation Data
- **Current Dataset A (India)**: 229 val images / 632 objects
- **Dataset B (Non-India)**: ~5,663 images / ~3,750 objects (estimated, 15% of non-India)
- **Combined Validation**: ~5,892 images / ~4,382 objects (estimated)

### Test Data
- **Frozen Test Set**: 230 images / 679 objects (from `experiments/dataset/yolo_rdd2022_india/images/test/`)
- **Must remain unchanged and unused in training**

## Split Methodology
- Group-based splitting using country/source as grouping variable (D-006)
- Deterministic seed: 42
- No India images in Dataset B training/validation
- Test set strictly isolated

## Gate Failures Preventing Split Creation

| Gate | Status | Notes |
|------|--------|-------|
| G1 Dataset B acquisition | FAIL | S3 403, FigShare too slow |
| G4 Exact image count | N/A | No data |
| G5 Annotation validation | N/A | No data |
| G9 Duplicate audit | N/A | No data |
| G10 Test leakage audit | N/A | No data |
| G11 Internal Dataset B leakage | N/A | No data |
| G12 Experiment 2 split validation | N/A | No data |

## Conclusion

**Split cannot be created without Dataset B.**
Experiment 2 blocked until Dataset B acquisition succeeds.