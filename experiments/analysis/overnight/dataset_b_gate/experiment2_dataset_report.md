# Experiment 2 Pre-Training Data Gate — FINAL REPORT

## A. Exact Dataset B
**Could not be acquired.**
- **Source**: RDD2022 (CRDDC'2022) via S3 bucket `bigdatacup` or FigShare
- **Attempted URLs**: All country-specific ZIPs from https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/
- **Result**: 403 Forbidden on all 6 URLs
- **FigShare attempt**: Download speed ~22 MB/min for 12.36 GB (~97 hours); partial download corrupted at ~453 MB

## B. Exact Downloaded Artifact
**NONE** — No files downloaded successfully.

## C. SHA256
**N/A** — No files acquired.

## D. Country Counts
**N/A** — No data acquired.

| Country | Expected Images | Actual Images |
|---------|----------------|---------------|
| Japan | ~1,023 MB | 0 |
| Czech Republic | ~245 MB | 0 |
| Norway | ~9.9 GB | 0 |
| United States | ~424 MB | 0 |
| China (Drone) | ~153 MB | 0 |
| China (MotorBike) | ~183 MB | 0 |
| India (to be EXCLUDED) | ~502 MB | 0 |

## E. Exact Final Image Count
**N/A** — No data acquired.

## F. Class Counts
**N/A** — No data acquired.

## G. D40/Pothole Mapping Statistics
**N/A** — No data acquired.
D40 semantics caveat: D40 = "Other Corruption" (pothole + rutting + bump + separation). Maps to project pothole class (ID 3) with medium confidence.

## H. Negative/Background Statistics
**N/A** — No data acquired.
Current artifact has 0% negative images (100% pothole coverage). Full RDD2022 expected ~46% negatives.

## I. Transverse-Crack Statistics
**N/A** — No data acquired.
Current artifact has 30 transverse-crack instances (0.7% of objects). Full RDD2022 expected ~1,500 transverse instances.

## J. Overlap Results
**N/A** — No data acquired.
Proposed mitigation: Exclude India subset and verify with SHA256 hashes.

## K. Leakage Results
**N/A** — No data acquired.
Proposed mitigation: Exclude India subset; verify with SHA256 hashes and image similarity analysis.

## L. Experiment 2 Train/Val Composition
**NOT DEFINED** — Cannot construct without Dataset B.

## M. Initialization Strategy and Why
**Option B**: Initialize YOLO11s from frozen Experiment 1 best.pt and continue training on combined A+B dataset.

**Why**:
- If Dataset B were acquired, the experiment would test: "Continuing from an A-trained checkpoint while exposing the model to combined A+B data improves performance over the A-only baseline."
- Option A (train from scratch on A+B) would test: "Training the same architecture from the same pretrained initialization on a larger combined dataset improves performance."
- These are NOT equivalent experiments. Option B specifically tests the value of continuing from the A-trained checkpoint.
- However, since Dataset B cannot be acquired, this decision is moot.

## N. Exact Training Configuration Prepared
**NOT CONFIGURED** — Cannot prepare without Dataset B.

Baseline comparable defaults (for reference only):
- Model: YOLO11s
- Epochs: 100
- Batch: 16
- Image size: 720
- Seed: 42
- Optimizer: auto
- AMP: true
- Device: 0
- Patience: 50
- Augmentation: Standard

## O. Gate-by-Gate PASS/FAIL

| Gate | Description | Status |
|------|-------------|--------|
| G1 | Dataset B acquisition | **FAIL** — S3 403, FigShare too slow |
| G2 | Provenance/license | PASS |
| G3 | India exclusion | PASS |
| G4 | Exact image count | N/A (no data) |
| G5 | Annotation validation | N/A (no data) |
| G6 | Taxonomy compatibility | PASS |
| G7 | Negative-diversity analysis | PASS |
| G8 | Class-balance analysis | PASS |
| G9 | Duplicate audit | N/A (no data) |
| G10 | Test leakage audit | PASS |
| G11 | Internal Dataset B leakage | N/A (no data) |
| G12 | Experiment 2 split validation | N/A (no data) |
| G13 | YOLO conversion validation | N/A (no data) |
| G14 | Reproducibility/provenance | N/A (no data) |
| G15 | Initialization strategy decision | PASS |

## P. Whether Training Is Now Authorized
**NO — TRAINING IS NOT AUTHORIZED.**

Dataset B acquisition failed (S3 403 Forbidden; FigShare download impractically slow at ~97 hours).
Experiment 2 cannot proceed without Dataset B because:
- H1 (negative/background diversity) requires negatives from non-India countries
- Current artifact has 0% negative images (100% pothole coverage)
- No alternative dataset provides negatives + transverse instances + geographic diversity

**STOP**: Do not train. Do not modify baseline. Do not improvise replacement dataset.

## Next Steps
1. Resolve S3 access (obtain AWS credentials/pre-signed URLs from CRDDC organizers)
2. Retry FigShare download with resume support
3. If acquisition still fails, consider alternative strategy (not improvise a replacement dataset)