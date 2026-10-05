# Data Pipeline

## Overview

The data pipeline converts raw candidate datasets into versioned, training-ready datasets that satisfy the project's requirements. The exact dataset combination, version, split proportions, and class normalization are **OPEN** and will be determined during the dataset audit and preparation phase.

**Critical Principle**: Group-based leakage prevention is **LOCKED** as a principle, but the exact grouping implementation is **OPEN** pending dataset audit.

---

## Dataset Source Registry

For each candidate dataset, record the following in `experiments/dataset/manifests/` (manifest files are not committed to Git; they are metadata only):

| Field | Example (RDD2022) | Status |
|-------|-------------------|--------|
| dataset name | `RDD2022` | |
| source | `https://github.com/sekilab/RoadDamageDetector` | |
| version | `CRDDC'2022` | |
| date checked | `YYYY-MM-DD` | |
| license | `Non-commercial (verify from source)` | |
| geographic coverage | `6 countries: Japan, India, Czech Republic, Norway, USA, China` | |
| camera perspective | `Forward-facing vehicle-mounted (smartphone)` | |
| image/video structure | `Various (India: 720x720; Japan/Czech: 600x600)` | |
| annotation format | `Pascal VOC XML` | |
| classes | `["D00", "D10", "D20", "D40"]` | |
| number of images | `47,420 total; 9,665 India subset` | |
| number of sequences/videos | `UNKNOWN - requires inspection` | |
| provenance | `GitHub sekilab/RoadDamageDetector` | |
| known limitations | `Multi-national; India subset quality unknown; license terms need verification` | |
| notes | `Verify India subset quality; convert Pascal VOC XML to project pixel format` | |

All fields remain **OPEN** until the dataset audit is performed. Do not fabricate values.

---

## File Structure

Expected dataset organization after preparation (conceptual; exact format OPEN):

```
dataset_root/
├── images/
│   ├── train/
│   │   ├── img_001.jpg
│   │   └── ...
├── labels/
│   ├── train/
│   │   ├── img_001.txt
│   │   └── ...
├── val/
│   ├── images/
│   │   ├── img_001.jpg
│   │   └── ...
│   └── labels/
│       ├── img_001.txt
│       └── ...
└── test/
    ├── images/
    │   ├── img_001.jpg
    │   └── ...
    └── labels/
        ├── img_001.txt
        └── ...
```

Coordinate conventions will be normalized during the preparation stage.

---

## Annotation Model

The project uses **axis-aligned bounding boxes** with the following conventions:

- **Coordinate system**: Pixel coordinates relative to the top-left corner of the image.
- **Format**: `[x_min, y_min, x_max, y_max]` (inclusive-inclusive pixel indices).
- **Validation**: `0 ≤ x_min < x_max ≤ image_width`, `0 ≤ y_min < y_max ≤ image_height`.
- **Class IDs**: Mapped to project-owned class enumeration (D00→0=longitudinal_crack, D10→1=transverse_crack, D20→2=alligator_crack, D40→3=pothole; see docs/CLASS_MAPPING.md for full mapping)
- **Frame relationships**: One annotation file per image (or per video frame, if video dataset).
- **Negative examples**: Hard-negative samples (non-pothole road regions) may be included if present in source datasets.
- **Class normalization**: LOCKED and IMPLEMENTED for RDD2022 India (Strategy B, CRDDC 4-class task, transformation v1.0.0). 1,530 annotations transformed; 4,360 retained, 164 excluded; all 16 invariants pass. See docs/CLASS_MAPPING.md §2 and §10.
- **Transformation tool**: `analysis/transform_rdd2022_annotations.py`
- **Validation tool**: `analysis/validate_transformation.py`
- **Transformation tests**: `tests/ml/data/inspection/test_transform_rdd2022.py` (37 tests)

---

## Normalization

During preparation, different datasets will map to the project representation:

1. **Class normalization**: Map source class labels to project class enumeration. For RDD2022 India: D00→0, D10→1, D20→2, D40→3, D01→0, D11→1 (deterministic merge), D43/D44/D50→EXCLUDED. See docs/CLASS_MAPPING.md §1 for the full mapping table.
2. **Coordinate normalization**: Convert source annotation format (e.g., Pascal VOC XML) to project `[x1, y1, x2, y2]` pixel format.
3. **Resolution handling**: Record original resolution; preprocessing will resize to model input size consistently for training and inference.
4. **Temporal alignment**: For video datasets, extract frames and associate with capture timestamps.

The normalization rules for RDD2022 India are **LOCKED** (docs/CLASS_MAPPING.md). Other datasets remain **OPEN**.

---

## Data Quality Validation

Perform and record the following checks (results stored in `experiments/dataset/validation/`):

- **Corrupt files**: Detect unreadable images/videos; log and exclude.
- **Invalid boxes**: Reject boxes with `x_min ≥ x_max`, `y_min ≥ y_max`, or out-of-bounds.
- **Missing annotations**: Flag images with zero annotations (if negatives not expected).
- **Duplicates**: Exact file hash matches (use perceptual hashing for near-duplicates).
- **Near duplicates**: Frames with significant overlap (e.g., consecutive video frames); subject to leakage analysis.
- **Suspicious samples**: Extremely small/large boxes, extreme aspect ratios, blank images.
- **Annotation consistency**: Inter-annotator agreement if multiple label sets exist.
- **Class balance**: Count instances per class; flag extreme imbalance.
- **Source diversity**: Log capture conditions (time of day, weather, road type) if metadata available.

All validation results must be recorded but **do not commit raw data or large media files**.

---

## Leakage Analysis

Grouping units to prevent information leakage (hierarchical; choose the coarsest available):

1. **Source video**: All frames from the same original video file.
2. **Source trip**: For datasets with trip/session IDs, all frames from the same logical trip.
3. **Location**: GPS-correlated blocks (if GPS metadata available).
4. **Capture session**: Temporally contiguous blocks with consistent conditions.
5. **Sequence IDs**: Dataset-provided sequence/group identifiers.

The exact grouping unit is **OPEN** pending dataset audit. The leakage prevention principle is **LOCKED**: frames from the same group must not casually be split across training, validation, and test.

### RDD2022 India: Grouping Unit Determination (2026-09-26) — State C

The sequence/group identification investigation (DATASET_AUDIT.md §18.20, full report at
`experiments/dataset/normalized_rdd2022_india/group_analysis/SYNTHESIS.md`) determined that
**no reliable grouping information exists** for this artifact.

| Check | Result |
|-------|--------|
| Sequence/video/trip/camera/timestamp/GPS metadata | **NONE** |
| XML attributes in any annotation | **NONE** |
| Grouping directory level | **NONE** |
| Filename pattern | `India_<flat index>`, no embedded grouping |
| Index sparsity | 84.52% of the 5..9,890 span absent |
| Exact duplicates (SHA-256) | 0 |
| Pixel-verified near-duplicate groups | 59 groups, 121 images, max size 3 |
| Filename-neighbor correlation (+1/+2/+5/+10) | **NULL**; +1 is 1.88% farther than random |

**State C: no reliable grouping information can be established.** The only defensible grouping is
the 59 pixel-verified near-duplicate clusters (121 images), which must be assigned as atomic units
so visually near-identical images cannot straddle split boundaries.

**Prohibited for this dataset**:
- Filename index proximity as a proxy for sequence membership (empirically falsified)
- Near-duplicate similarity as proof of video origin
- Any claim that residual leakage risk is zero — it is **unquantifiable**

A refinement to D-006 covering this case is **PROPOSED** as D-006-R1 in DECISION_LOG.md and is
**not yet applied**. D-006 itself remains LOCKED and unmodified.

Reproduction:

```powershell
python analysis/analyze_filename_structure.py    # filename + metadata evidence
python analysis/analyze_image_correlation.py     # exact dupes + neighbor correlation
python analysis/verify_near_duplicates.py        # complete linkage + pixel verification
```

None of these scripts write to the raw or normalized dataset.

---

## Split Construction

Do **not** finalize proportions yet. Document the algorithmic principle:

1. **Group**: Identify groups using the chosen leakage prevention unit.
2. **Assign split**: Assign each entire group to train, validation, or test.
3. **Verify distribution**: Check class balance, geographic/temporal spread, and instance counts per split.
4. **Iterate**: Adjust group assignments to improve distribution while preserving group integrity.

Document the exact group-to-split assignment in the dataset manifest (not in Git).

---

## Dataset Versioning

Each dataset version must record:

- **Dataset version**: Increment when sources, versions, or preparation changes.
- **Manifest**: List of sources, their versions, hashes (not the data itself).
- **Source hashes/checksums**: For integrity verification (stored externally).
- **Preprocessing version**: Hash of the preparation script/configuration.
- **Split version**: Group-to-split assignment (changes if leakage groups or assignment changes).
- **Acceptance criteria timestamp**: When the version was marked training-ready.

Example version ID: `dataset_v1.0_split_a20260917`.

---

## Acceptance Criteria

A dataset version is considered training-ready only when:

- [ ] Source provenance and licenses are verified and recorded.
- [ ] Annotation validation passes with no critical errors (e.g., corrupt files, invalid boxes).
- [ ] Leakage groups are identified and documented.
- [ ] Group-based split is constructed and verified (no group crosses train/val/test).
- [ ] Class normalization is defined and applied consistently.
- [ ] Dataset manifests and metadata are recorded (externally).
- [ ] A small sanity-check training run can proceed (does not require convergence).

Until these criteria are met, the dataset status remains **OPEN / UNDER DEEP AUDIT**.

---

---

## Audit Findings (2026-09-21) - CORRECTED

The dataset audit (docs/DATASET_AUDIT.md) provides the following verified evidence:

### Primary Dataset Candidate: RDD2022 (CORRECTED)

- **Multi-national**: 6 countries (Japan, India, Czech Republic, Norway, USA, China) - NOT India-only
- **Total images**: 47,420 (NOT 4,500) - India subset: 9,665 images, 6,831 labels
- **Annotation format**: Pascal VOC XML (NOT YOLO as previously claimed)
- **Classes**: D00, D10, D20, D40 (plus D30 in some versions)
- **Source**: GitHub sekilab/RoadDamageDetector, arXiv:2209.08538
- **License**: Non-commercial (varies by source)
- **CRITICAL ERROR PREVIOUSLY**: Previous audit stated 4,500 images, YOLO format, India-only, cited wrong Mendeley URL
- **Correct Mendeley URL**: NOT 5y9wdsg2zt/2 (that's a Turkish concrete crack dataset); correct source is GitHub sekilab/RoadDamageDetector

### Supplementary Dataset Candidate: BharatPotHole / iWatchRoad (VERIFIED)

- **Indian**: Dashcam footage across diverse Indian road conditions
- **Images**: >7,000 annotated frames
- **Annotation**: YOLO format (converted from Roboflow)
- **Single class**: Pothole
- **Source**: Kaggle / arXiv:2508.10945

### Other Candidates (VERIFIED)

- **RDD2020**: 26,336 images, India/Japan/Czech, Pascal VOC XML, CC BY 4.0 - suitable as supplementary
- **HRP4K**: 6,003 images, China (NOT India), 4K resolution, YOLO+COCO, CC BY 4.0
- **RAD**: 600 images, India, pothole classification, CC BY 4.0 - too small for training

### Combination Analysis

- Overlapping classes: Likely pothole across all candidates (D40 in RDD2022/RDD2020)
- Label semantics: UNKNOWN until annotation inspection
- Annotation conventions: Pascal VOC XML (RDD2022, RDD2020), YOLO (BharatPotHole, HRP4K)
- Domain mismatch: MEDIUM risk for non-Indian datasets (HRP4K is Chinese)
- Image-resolution mismatch: RDD2022 at various resolutions (600x600, 720x720), HRP4K at 4K
- Class imbalance: Typical for pothole datasets
- Potential duplication: RDD2020 is subset of RDD2022 (confirmed by paper)
- Negative transfer: Risk from incompatible class semantics
- Licensing compatibility: Varies by dataset; verify before combination

### Hard Negatives

Priority hard negatives for false-positive reduction:

- Cracks
- Patches
- Shadows
- Stains
- Manholes
- Water puddles

### Data Contract

The project data contract is defined in docs/DATASET_AUDIT.md:

- Image format: OPEN
- Annotation representation: Project pixel format (OPEN)
- Class representation: Single "pothole" class (LOCKED PRINCIPLE)
- Coordinate convention: Pixel coordinates, top-left origin (LOCKED PRINCIPLE)
- Metadata requirements: Defined
- Provenance requirements: Defined
- Dataset version identifier: Defined
- Source identifier: Defined
- Sequence/group identifier: Defined

### Leakage Prevention

The audit confirms the group-based leakage prevention strategy and adds:

- Grouping unit hierarchy (5 levels)
- Precedence rules for grouping
- Source dataset independent splitting
- Cross-dataset duplicate removal
- Video frame grouping

---

## RDD2022 India Transformation Specification (IMPLEMENTED, v1.0.0)

The transformation tool (transformation version 1.0.0) is implemented. See docs/CLASS_MAPPING.md
for the full specification and results.

### Commands

```powershell
# Run the transformation
python analysis/transform_rdd2022_annotations.py

# Run the independent invariant validation
python analysis/validate_transformation.py

# Run the fixture-based tests
python -m pytest tests/ml/data/inspection/test_transform_rdd2022.py -v
```

### Input

- `experiments/dataset/raw_rdd2022_india/train/annotations/xmls/*.xml` (1,530 Pascal VOC XML)
- `experiments/dataset/raw_rdd2022_india/train/images/*.jpg` (1,530 images)

### Output

```
normalized_rdd2022_india/
├── train/
│   ├── annotations/   (1,530 normalized Pascal VOC XML)
│   └── images/        (1,530 byte-identical image copies)
├── manifest.json
├── transformation_report.md
└── validation_report.json
```

**Split decision**: the normalized output mirrors the raw source's existing official `train/`
split. No `val/` or `test/` directories are created, because train/val/test splitting has not
happened and must not be simulated here.

### Transformation Invariants

All 16 automated checks pass (see `validation_report.json`):

1. Raw files remain unchanged (verified by MD5 checksums of both raw images and raw annotations)
2. Every retained object has exactly one final project class ID (0–3)
3. Excluded objects never become positive labels
4. Bounding-box coordinates are preserved (4,360 boxes verified)
5. Image dimensions are preserved
6. Image and annotation counts are conserved (1,530 / 1,530)
7. Retained + excluded + skipped == source objects (4,360 + 164 + 0 == 4,524)
8. D00 + D01 → class 0 (498 objects)
9. D10 + D11 → class 1 (30 objects)
10. D20 → class 2 (645 objects)
11. D40 → class 3 (3,187 objects)
12. D43/D44/D50 never appear in output (0 / 0 / 0)
13. Idempotent: re-running produces byte-identical output (1,530/1,530 identical)
14. Output filenames are deterministic (1:1 with source names)
15. Manifest statistics match independently recomputed values
16. Excluded-object boundaries verified (skips recorded with reasons)

### Audit Outputs

- `manifest.json` — machine-readable: per-image source/normalized paths, raw and normalized
  MD5 checksums, object counts, retained/excluded counts, raw and final class counts,
  `is_empty` flag, `skip_reason`, plus global statistics and the mapping rules table
- `transformation_report.md` — human-readable summary of the same statistics
- `validation_report.json` — independent validation results

### Observed Results

| Metric | Value |
|--------|-------|
| Source annotations / normalized | 1,530 / 1,530 |
| Source images / normalized | 1,530 / 1,530 |
| Original objects | 4,524 |
| Retained objects | 4,360 |
| Excluded objects | 164 (D43 5, D44 151, D50 8) |
| Merged (D01→D00, D11→D10) | 27, 7 |
| Skipped images | 0 |
| Empty normalized annotations | 0 |
| Invalid annotations | 0 |

Final class distribution: pothole 3,187; longitudinal_crack 498; alligator_crack 645;
transverse_crack 30.

### Known Limitations

- Selection bias inherited unchanged: 0 pothole-negative images in this artifact
- Construction-joint context (D01/D11) is lost at class level in the normalized form
- `pothole` inherits CRDDC D40's broader scope (rutting, bump, pothole, separation)
- `difficult`/`truncated` flags preserved but no filtering policy decided
- Checksums are MD5 (adequate for change detection, not tamper-resistant)

---

## Current Status

- **Dataset composition**: `OPEN / UNDER DEEP AUDIT`
- **Exact dataset combination**: `OPEN`
- **Exact dataset version**: `OPEN`
- **Exact split proportions**: `OPEN`
- **Exact class normalization**: `LOCKED` for RDD2022 India (Strategy B, CRDDC 4-class task; see docs/CLASS_MAPPING.md §1)
- **Class-mapping strategy**: `LOCKED` — Strategy B (official CRDDC 4-class task: D00, D10, D20, D40)
- **D01/D11 mapping**: `LOCKED` — D01→D00, D11→D10 (deterministic merge)
- **D43/D44/D50**: `EXCLUDED` — road markings or annotation artifact
- **D50 provenance**: `RESOLVED` — annotation artifact (8 objects, 0.5% of data, 100% D40 co-occurrence, near-identical bbox to D40 in India_007909)
- **Group-based leakage prevention**: `LOCKED` (principle); implementation `OPEN` pending audit
- **RDD2022 as primary dataset**: `RECOMMENDED, not locked` (CORRECTED: 47,420 images, Pascal VOC XML, multi-national)
- **HRP4K as supplementary dataset**: `RECOMMENDED, not locked` (CORRECTED: Chinese, not Indian)
- **BharatPotHole as supplementary dataset**: `RECOMMENDED, not locked` (VERIFIED: Indian dashcam)
- **Additional data collection**: `RECOMMENDED, not locked`

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*