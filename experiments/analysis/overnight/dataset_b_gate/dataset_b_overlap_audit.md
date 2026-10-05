# Dataset B Overlap Audit

## Purpose

Determine whether Dataset B (full RDD2022) overlaps with:
- Current TRAIN
- Current VAL
- Current TEST

## Critical Rule

The original 230-image test set must **never** enter Experiment 2 training.

## Overlap Analysis Status: FAILED

**No data acquired to perform overlap analysis.**

### Current Artifact

The current local artifact (`experiments/dataset/normalized_rdd2022_india/`) is derived from the **India subset** of RDD2022.

| Split | Images | Origin |
|-------|--------|--------|
| Train | 1,071 | India subset of RDD2022 |
| Val | 229 | India subset of RDD2022 |
| Test | 230 | India subset of RDD2022 |

### Dataset B Candidate

Candidate: Full RDD2022 (all 6 countries).

### Overlap Calculation Status: FAILED

**No files downloaded to analyze overlap.**

#### Case 1: Use Full RDD2022 as Dataset B (NO India exclusion)
**Cannot be evaluated due to acquisition failure.**

#### Case 2: Use Full RDD2022 minus India subset (India exclusion)
**Cannot be evaluated due to acquisition failure.**

#### Case 3: Use only non-India portions of RDD2022
**Cannot be evaluated due to acquisition failure.**

### Exact Hash Verification Status: FAILED

**No files to verify.**

### Image Similarity Analysis Status: FAILED

**No files to analyze.**

### Leakage Risk Summary: PARTIAL

Cannot assess overlap risk due to acquisition failure.

### Recommended Overlap Handling

1. **Download full RDD2022 from FigShare** (failed due to slow speed / partial corruption)
2. **Identify India subset images** (via metadata or provenance)  
3. **Exclude all India subset images** from Dataset B training set
4. **Verify with SHA256 hashes** that no India images remain in Dataset B
5. **Optionally run image similarity analysis** to detect near-duplicates
6. **Document exclusion list** for reproducibility

### Test Set Protection

The current 230-image test set must be:
- Excluded from Dataset B
- Not used in any Experiment 2 training step
- Kept frozen for final evaluation only
- Verified not to appear in any Dataset B split (hash check)

## Conclusion

**Overlap audit cannot be completed** due to acquisition failure.
Experiment 2 cannot proceed without overlap audit verification.

## Acquisition FAILED — Overlap Audit Remains Incomplete

All overlap analysis is theoretical based on provenance structure.
Actual overlap must be verified after successful data acquisition.
Experiment 2 is BLOCKED due to overlap audit failure.