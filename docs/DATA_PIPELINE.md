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
| source | `https://data.mendeley.com/datasets/5y9wdsg2zt/2` | |
| version | `2.0` | |
| date checked | `YYYY-MM-DD` | |
| license | `CC BY-NC-SA 4.0` | |
| geographic coverage | `India (multiple cities)` | |
| camera perspective | `Forward-facing vehicle-mounted` | |
| image/video structure | `Images: 640x480, JPEG` | |
| annotation format | `YOLO txt files (class x_center y_center width height)` | |
| classes | `["pothole"]` | |
| number of images | `4,500` | |
| number of sequences/videos | `N/A (image dataset)` | |
| provenance | `Downloaded from Mendeley Data` | |
| known limitations | `Some night images; moderate resolution` | |
| notes | `Check alignment with forward-camera relevance` | |

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
- **Class IDs**: Mapped to a project-owned class enumeration (currently single class: `"pothole"`).
- **Frame relationships**: One annotation file per image (or per video frame, if video dataset).
- **Negative examples**: Hard-negative samples (non-pothole road regions) may be included if present in source datasets.

Exact class mapping is **OPEN** pending dataset audit.

---

## Normalization

During preparation, different datasets will map to the project representation:

1. **Class normalization**: Map source class labels to the project's pothole class (e.g., `"pothole"`, `"pothole_damage"` → `"pothole"`).
2. **Coordinate normalization**: Convert source annotation format (e.g., YOLO center format) to project `[x1, y1, x2, y2]` pixel format.
3. **Resolution handling**: Record original resolution; preprocessing will resize to model input size consistently for training and inference.
4. **Temporal alignment**: For video datasets, extract frames and associate with capture timestamps.

The normalization rules are **OPEN** pending dataset inspection.

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

## Current Status

- **Dataset composition**: `OPEN / UNDER DEEP AUDIT`
- **Exact dataset combination**: `OPEN`
- **Exact dataset version**: `OPEN`
- **Exact split proportions**: `OPEN`
- **Exact class normalization**: `OPEN`
- **Group-based leakage prevention**: `LOCKED` (principle); implementation `OPEN` pending audit

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*