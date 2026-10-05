# Class Mapping Specification

## 1. Final Deterministic Class Mapping

| Raw class | Final project class | Action | Reason |
|-----------|---------------------|--------|--------|
| D00 | longitudinal_crack | KEEP | Official CRDDC class; longitudinal road crack |
| D01 | longitudinal_crack | MERGE → D00 | Construction joint variant of D00 (Arya et al. 2022); same damage type, different location |
| D10 | transverse_crack | KEEP | Official CRDDC class; transverse road crack |
| D11 | transverse_crack | MERGE → D10 | Construction joint variant of D10 (Arya et al. 2022); same damage type, different location |
| D20 | alligator_crack | KEEP | Official CRDDC class; alligator/connected crack pattern |
| D40 | pothole | KEEP | Official CRDDC class; pothole/rutting/bump/separation |
| D43 | — | EXCLUDE | Road marking damage (white line blur); not structural road damage |
| D44 | — | EXCLUDE | Road marking damage (crosswalk blur); not structural road damage |
| D50 | — | EXCLUDE | Annotation artifact; no official source; 100% D40 co-occurrence; near-identical bbox to D40 in India_007909 |

## 2. Canonical Project Class IDs

| Project ID | Class Name | Description | Source |
|------------|------------|-------------|--------|
| 0 | longitudinal_crack | Linear cracks aligned with direction of travel | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 1 | transverse_crack | Cracks perpendicular to direction of travel | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 2 | alligator_crack | Interconnected cracks forming alligator-skin pattern | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 3 | pothole | Pothole, rutting, bump, separation (CRDDC "Other Corruption") | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |

**Note**: Project class IDs 0–3 are the canonical ordering for all future datasets, models, and evaluation. The raw class IDs (D00/D01/D10/D11/D20/D40) must NOT be used as project class IDs in any downstream system.

## 3. Annotation-Level Rules

- Every retained object receives exactly one final project class ID (0–3)
- D01 annotations are relabeled as class 0 (longitudinal_crack)
- D11 annotations are relabeled as class 1 (transverse_crack)
- D43/D44/D50 annotations are excluded and never become positive labels
- Excluded annotations are logged but NOT deleted from raw files
- Bounding-box coordinates are preserved exactly as-is for all retained objects
- No object is silently duplicated
- No object is silently lost except through the explicit exclusion rule for D43/D44/D50
- Raw annotation files remain unchanged (conversion is read-only; normalized output is written to a separate directory)

## 4. Image-Level Rules

### Case A: Image contains D40 + excluded annotations (D43/D44/D50)
- Image is retained
- D40 object is retained as class 3 (pothole)
- D43/D44/D50 objects are excluded (logged, not deleted from raw)
- Image has at least one positive label (D40) → positive sample

### Case B: Image contains D40 + other retained classes (D00/D01/D10/D11/D20)
- Image is retained
- All retained objects are included with their final project class IDs
- D01 → class 0, D11 → class 1, D00 → class 0, D10 → class 1, D20 → class 2, D40 → class 3
- Multi-class image: contains multiple project classes → used for multi-class evaluation

### Case C: Image contains only excluded annotations (D43/D44/D50 only, no D40/D00/D10/D20)
- Image becomes annotation-empty after mapping
- Image is NOT deleted from the dataset directory
- Image is logged in the audit report as "annotation-empty after mapping"
- Image is excluded from training/evaluation (no labels to learn from)
- Image may serve as background/negative sample for hard-negative mining if image-level labels are added later

### Case D: Image contains only retained non-D40 classes (D00/D01/D10/D11/D20 only, no D40)
- Image is retained
- All retained objects are included with their final project class IDs
- Image has no pothole (D40) label → negative sample for pothole detection
- These are crack-only images; valuable for training the model to distinguish cracks from potholes
- Currently 0 such images exist in the artifact (selection bias), but the rule is documented for future data

### General rule
- No image is automatically deleted
- Annotation-empty images are retained but excluded from training/evaluation
- All exclusion decisions are logged with the reason

## 5. Transformation Invariants

The future conversion tool MUST guarantee:

1. Raw files remain unchanged (read-only conversion)
2. Every retained object has exactly one final project class ID (0–3)
3. Excluded objects never become positive labels
4. Bounding-box coordinates are preserved (no coordinate transformation at this stage)
5. Image pixels are unchanged
6. Image/annotation relationships remain valid (every image in the output has a corresponding annotation file, even if empty)
7. No object is silently duplicated
8. No object is silently lost except through the explicitly documented exclusion rule for D43/D44/D50
9. D01 → class 0, D11 → class 1 (deterministic merge, no ambiguity)
10. All mapping decisions are logged per-object and per-image

## 6. Future Audit Requirements

The transformation tool MUST report:

- Source image count (total images in input)
- Source object count (total annotations in input)
- Count by raw class (D00, D01, D10, D11, D20, D40, D43, D44, D50)
- Count by final project class (0, 1, 2, 3)
- Excluded annotation count (D43 + D44 + D50)
- Images becoming annotation-empty after mapping
- Invalid annotations encountered (malformed XML, missing fields, out-of-bounds coordinates)
- Images skipped (with reason for each skip)
- Reasons for each exclusion/skip (must be explicit, not silent)

## 7. Output Data Contract

**STATUS: IMPLEMENTED** (transformation version 1.0.0). The actual on-disk structure mirrors the
raw source's official `train/` split, because the raw source already provides an official split
that must be preserved. No `val/` or `test/` directories are created, since splitting has not
happened yet and inventing one here would be a false claim.

```
normalized_rdd2022_india/
├── train/
│   ├── annotations/
│   │   └── India_XXXXXX.xml      (1,530 files; Pascal VOC, project class names)
│   └── images/
│       └── India_XXXXXX.jpg      (1,530 files; byte-identical copies)
├── manifest.json                  (audit manifest, machine-readable)
├── transformation_report.md       (human-readable global report)
└── validation_report.json         (independent invariant validation results)
```

- **Representation choice**: Pascal VOC XML retained (not YOLO). The normalized form is a
  lossless project-owned intermediate: coordinates, dimensions, `pose`, `truncated`, `difficult`,
  and `filename` are all preserved; only `<name>` is rewritten to the project class name.
- **Image location**: `normalized_rdd2022_india/train/images/<image_id>.jpg`
- **Label location**: `normalized_rdd2022_india/train/annotations/<image_id>.xml`
- **Class IDs**: 0 = longitudinal_crack, 1 = transverse_crack, 2 = alligator_crack, 3 = pothole
  (IDs are defined here; the normalized XML uses the class *names*, and the ID mapping is
  recorded in `manifest.json` under `transformation_rules.class_mapping`)
- **Label coordinate convention**: Project pixel format [x1, y1, x2, y2] with top-left origin
  (per D-013); unchanged from source
- **Metadata/manifests**:
  - `manifest.json`: per-image audit records (source/normalized paths, raw and normalized
    checksums, object counts, retained/excluded counts, class counts, `is_empty` flag,
    `skip_reason`), plus global `statistics` and the full `transformation_rules` mapping table
  - `transformation_report.md`: human-readable summary of the same statistics
  - `validation_report.json`: independent re-parse validation results (see §11)
- **Provenance/version fields**: `transformation_version`, `source_dataset_identifier`
  (`RDD2022_CRDDC_India`), `source_dataset_version` (`CRDDC'2022`), per-file MD5 checksums

## 8. Documentation Changes

- **docs/DECISION_LOG.md**: D-015 expanded with exact deterministic mapping (D01→D00, D11→D10, D43/D44/D50 excluded)
- **docs/DATASET_AUDIT.md**: §18.15.5 updated with final deterministic mapping; §18.15.7 updated with all decisions resolved except train/val/test split and artifact expansion
- **docs/DATASET_AUDIT_SUMMARY.md**: Updated with final class mapping table and D50 resolution
- **docs/DATA_PIPELINE.md**: Updated with transformation spec, invariants, and audit requirements
- **docs/RESEARCH_REGISTER.md**: R-009 updated with D50 resolution and class-mapping decision
- **docs/ENGINEERING_LOG.md**: Added D50 resolution lesson and D01/D11 merge decision

## 9. Validation

- All 13 VOC parser tests pass
- Provenance analysis script produces correct JSON/MD reports
- D01 count (27) + D11 count (7) = 34 objects to be merged into D00/D10
- D43 count (5) + D44 count (151) + D50 count (8) = 164 objects to be excluded
- Total retained objects: D00 (471) + D10 (23) + D20 (645) + D40 (3187) + D01→D00 (27) + D11→D10 (7) = 4,360 objects across 4 project classes
- No D01/D11/D43/D44/D50 objects in final project class distribution
- D50 excluded: 8 objects (0.5% of total) — annotation artifact, no information loss

## 10. Implementation Record (transformation v1.0.0)

### Tooling

| Component | Path | Purpose |
|-----------|------|---------|
| Transformation tool | `analysis/transform_rdd2022_annotations.py` | Applies the mapping, writes normalized VOC XML, copies images, emits manifest + report |
| Independent validator | `analysis/validate_transformation.py` | Re-parses raw and normalized files from disk and checks all invariants without reusing transformation state |
| Tests | `tests/ml/data/inspection/test_transform_rdd2022.py` | 37 fixture-based tests; the real dataset is never used as a fixture |

### Commands

```powershell
# Run the transformation
python analysis/transform_rdd2022_annotations.py

# Run the independent invariant validation
python analysis/validate_transformation.py

# Run the tests
python -m pytest tests/ml/data/inspection/test_transform_rdd2022.py -v
```

### Input

- `experiments/dataset/raw_rdd2022_india/train/annotations/xmls/*.xml` (1,530 Pascal VOC XML)
- `experiments/dataset/raw_rdd2022_india/train/images/*.jpg` (1,530 images)

The structure was discovered from the actual files, not assumed: annotations live under
`train/annotations/xmls/`, images under `train/images/`, and stem names match 1:1
(`India_000005.xml` ↔ `India_000005.jpg`).

### Observed results (independently computed, not hardcoded)

| Metric | Value |
|--------|-------|
| Source annotations | 1,530 |
| Normalized annotations | 1,530 |
| Source images / normalized images | 1,530 / 1,530 |
| Original objects | 4,524 |
| Retained objects | 4,360 |
| Excluded objects | 164 |
| Skipped images | 0 |
| Empty normalized annotations | 0 |
| Invalid annotations | 0 |

Raw class counts: D00 471, D01 27, D10 23, D11 7, D20 645, D40 3,187, D43 5, D44 151, D50 8.

Final class counts: longitudinal_crack 498, transverse_crack 30, alligator_crack 645, pothole 3,187.

Exclusion detail: D43 5, D44 151, D50 8. Merge detail: D01→D00 27, D11→D10 7.

The expected totals (4,524 / 4,360 / 164) stated in the task are reproduced by the tool's own
computation and are asserted only as a post-run cross-check, never as input.

### Validation results

All 16 checks pass (`validation_report.json`, `overall_status: PASS`):

| Invariant | Result |
|-----------|--------|
| Raw files unchanged (raw image + raw annotation MD5) | PASS |
| Every retained object maps to exactly one final class | PASS |
| No excluded object appears in normalized annotations | PASS |
| Bounding-box coordinates unchanged | PASS (4,360 boxes verified) |
| Image dimensions unchanged | PASS |
| Image/annotation count conserved | PASS |
| Retained + excluded + skipped == source objects | PASS (4,360 + 164 + 0 = 4,524) |
| D00 + D01 → class 0 | PASS (498) |
| D10 + D11 → class 1 | PASS (30) |
| D20 → class 2 | PASS (645) |
| D40 → class 3 | PASS (3,187) |
| D43/D44/D50 never in output | PASS (0/0/0) |
| Idempotent rerun | PASS (1,530/1,530 byte-identical) |
| Deterministic output filenames | PASS (1:1 with source names) |
| Manifest statistics match recomputed values | PASS |

### Known limitations

- **Selection bias is unchanged.** 100% of source images are D40-positive, so the normalized set
  contains zero pothole-negative images. Case D (crack-only) is implemented and tested but has no
  instances in this artifact.
- **Construction-joint context is lost at class level.** D01/D11 merge into D00/D10 as decided.
  The raw files retain the distinction, but the normalized form cannot express it.
- **D40 semantic breadth is inherited.** CRDDC D40 covers rutting, bump, pothole, and separation;
  the project class name `pothole` is therefore broader than a strict physical pothole.
- **`difficult` / `truncated` flags are preserved but not yet acted upon.** No filtering policy
  for them has been decided.
- **No `val/` or `test/` directories exist yet**, by design. Group identification for
  leakage-safe splitting has not been performed.
- **Checksums are MD5**, matching the manifest. MD5 is adequate for change detection here but is
  not a tamper-resistant digest.
- **The validator re-derives expected values from the same `CLASS_MAPPING` constant** that the
  transformation uses. It independently re-reads and re-compares all files, but it cannot detect a
  wrong constant; that error would require human review of `docs/CLASS_MAPPING.md` §1.
