# Dataset Audit Summary (CORRECTED)

**Reference**: docs/DATASET_AUDIT.md (full audit)
**Date**: 2026-09-21
**Status**: CORRECTED - Audit performed with verified information; strategy recommended but not locked

**CRITICAL CORRECTION**: The previous audit contained significant errors regarding RDD2022. The corrected audit has verified actual dataset properties from official sources.

---

## Key Findings (CORRECTED)

### Primary Candidate: RDD2022

- **Multi-national**: 6 countries (Japan, India, Czech Republic, Norway, USA, China) - NOT India-only
- **Total images**: 47,420 (NOT 4,500)
- **India subset**: 9,665 images, 6,831 labels
- **Annotation format**: Pascal VOC XML (NOT YOLO)
- **Classes**: D00, D10, D20, D40 (plus D30 in some versions)
- **Source**: GitHub sekilab/RoadDamageDetector, arXiv:2209.08538
- **License**: Non-commercial (CC BY 4.0)
- **Status**: RECOMMENDED as primary candidate; not locked pending annotation quality inspection
- **CRITICAL ERROR PREVIOUSLY**: Previous audit stated 4,500 images, YOLO format, India-only, cited wrong Mendeley URL

### RDD2022 India Subset: Provenance and Class Semantics (2026-09-21 to 2026-09-22)

- **Artifact**: Kaggle `vidishbijalwan/rdd2022-india-pothole-d40` — 1,530 images (15.8% of India train set)
- **Artifact claims**: "D40 only" but actually contains 9 classes (D00, D01, D10, D11, D20, D40, D43, D44, D50)
- **D40 coverage**: 100% of images contain D40 — selection bias confirmed (no crack-only or non-D40 images)
- **D40 object count**: 3,187 of 4,524 total objects (70.4%)
- **D40 semantic scope**: CRDDC "Other Corruption" category (rutting, bump, pothole, separation) — NOT purely physical potholes
- **Co-occurrence (mutually exclusive)**: D40-only: 677 (44.2%), D40+D00: 363 (23.7%), D40+D20: 381 (24.9%), D40+other: 109 (7.1%)
- **D43 definition**: VERIFIED — "White line blur" (RDD2018, arXiv:1801.09454); road marking damage, not structural
- **D44 definition**: VERIFIED — "Cross walk blur" (RDD2018, arXiv:1801.09454); road marking damage, not structural
- **D50 definition**: RESOLVED — annotation artifact (8 objects, 0.5% of data); 100% D40 co-occurrence; near-identical bbox to D40 in India_007909 (2-pixel offset); no official source; EXCLUDED from all strategies
- **D01 definition**: VERIFIED — "Longitudinal Crack (construction joint part)" (RDD2018 Table 1); construction joint variant of D00
- **D11 definition**: VERIFIED — "Transverse Crack (construction joint part)" (RDD2018 Table 1); construction joint variant of D10
- **9-class vs 4-class reconciliation**: Official CRDDC uses 4 classes {D00, D10, D20, D40}; artifact contains 5 extra (D01, D11, D43, D44, D50)
- **Negative-example problem**: 0 negative samples (images without D40) in artifact; 0 pure-negative samples (images without damage); selection bias makes evaluation unreliable
- **Coverage gap**: 8,135 India train images missing from artifact; selection bias risk HIGH
- **Class-mapping strategy**: DECIDED — Strategy B (official CRDDC 4-class task)
- **D01 → D00**: VERIFIED — construction joint variant; deterministic merge
- **D11 → D10**: VERIFIED — construction joint variant; deterministic merge
- **D43/D44/D50**: EXCLUDED — road markings or annotation artifact
- **Source**: `analysis/rdd2022_provenance_analysis.py`, `analysis/output/rdd2022_provenance_report.md`, local XML inspection (8 D50 files)

### Official RDD2022 India Acquisition Status (2026-09-21)

- **Official India ZIP (S3)**: `RDD2022_India.zip` (502.3 MB) — **403 Access Denied**
- **Official India train images**: 7,706 (per CRDDC'2022 documentation)
- **Official India total (train+test)**: 9,665 images
- **Official CRDDC classes**: {D00, D10, D20, D40} — 4 classes only
- **FigShare fallback**: 13.2 GB full RDD2022 dataset (not country-specific)
- **Conclusion**: Official India data not accessible; current artifact is a filtered D40-positive subset (15.8% of India train set)
- **Derivative vs Official**: Artifact is a filtered, class-expanded derivative — filtered to D40-positive images, containing 5 extra classes beyond official 4

### Supplementary Candidate: BharatPotHole / iWatchRoad

- **Indian**: Dashcam footage across diverse Indian road conditions
- **Images**: >7,000 annotated frames
- **Annotation**: YOLO format (converted from Roboflow)
- **Single class**: Pothole
- **Source**: Kaggle / arXiv:2508.10945
- **Status**: RECOMMENDED as supplementary candidate; not locked

### Other Candidates

- **RDD2020**: 26,336 images, India/Japan/Czech, Pascal VOC XML, CC BY 4.0 - suitable as supplementary
- **HRP4K**: 6,003 images, China (NOT India), 4K resolution, YOLO+COCO, CC BY 4.0
- **RAD**: 600 images, India, pothole classification, CC BY 4.0 - too small for training

## Locked Principles

| Principle | Rationale |
|-----------|-----------|
| Group-based leakage prevention | Prevents data leakage across splits |
| Single "pothole" class representation | Model-independent, canonical naming |
| Pixel coordinate convention `[x1, y1, x2, y2]` | Simple, convertible, framework-independent |
| Project data contract requirements | Provenance, metadata, versioning, grouping |

## Important Corrections from Previous Audit

| Claim | Previous Audit (WRONG) | Corrected Audit (VERIFIED) |
|-------|----------------------|---------------------------|
| RDD2022 image count | 4,500 | 47,420 (total), 9,665 (India) |
| RDD2022 annotation format | YOLO txt | Pascal VOC XML |
| RDD2022 geographic scope | India-only | 6 countries |
| RDD2022 Mendeley URL | data.mendeley.com/datasets/5y9wdsg2zt/2 (WRONG - leads to Turkish concrete crack dataset) | GitHub sekilab/RoadDamageDetector |
| RDD2022 license | CC BY-NC-SA 4.0 | Non-commercial (verify from source) |
| BharatPotHole | UNKNOWN | >7,000 dashcam frames, YOLO format |
| RAD | Unknown "Road Anomaly Dataset" | 600-image Indian pothole classification dataset |
| HRP4K | "Pothole detection dataset" | 6,003 images from China, 4K resolution |

## Sequence/Group Identification for Leakage-Safe Splitting (2026-09-26)

Full report: `experiments/dataset/normalized_rdd2022_india/group_analysis/SYNTHESIS.md`

- **Grouping metadata**: **NONE** — zero XML attributes in all 1,530 files; no sequence/video/trip/camera/timestamp/GPS field; no grouping directory level; 18 standard Pascal VOC tags only
- **Filename structure**: `India_<6-digit flat index>`, range 5..9,890, span 9,886, 8,356 indices (84.52%) absent; no embedded grouping
- **Exact duplicates (SHA-256)**: **0** — all 1,530 images have unique content
- **Near duplicates**: 59 pixel-verified groups covering 121 images (7.9%), max group size 3; 583 genuine match pairs vs ~10 expected by chance (~58× enrichment)
- **Near-duplicates are NOT filename neighbors**: median index gap 2,643; only 1 of 583 pairs within an index gap of 10
- **Neighbor correlation**: **NULL** — dHash mean +1 = 26.211, +2 = 25.757, +5 = 25.885, +10 = 25.110, random = 25.727. The +1 offset is 1.88% *farther* than random
- **Thresholds calibrated** against 1,500 random pairs (corr mean 0.543, p95 0.795, max 0.926), not chosen arbitrarily
- **Verdict**: **State C** — no reliable grouping information can be established
- **Confidence classes**: VERIFIED GROUP 0; LIKELY CORRELATED 59 groups / 121 images; UNKNOWN 1,409 images
- **D-006**: principle stands unchanged; implementation assumption falsified. Refinement **D-006-R1 PROPOSED, not applied**
- **Residual risk**: unquantifiable, not zero. Must be recorded, not assumed away
- **Critical limitation**: this is a filtered, D40-positive-derived subset (1,530 of ~9,890 index positions, 100% D40-positive). Findings are NOT representative of the full official India release

## Open Decisions

| Decision | Reason |
|----------|--------|
| Exact split proportions | Evidence insufficient for locking |
| Dataset combination (RDD2022 + BharatPotHole) | Annotation compatibility unknown |
| Final dataset composition | Requires inspection of all candidates |
| Annotation quality | Requires actual file inspection |
| Grouping/splitting strategy | **State C** — no reliable group info exists; D-006-R1 refinement proposed, awaiting approval |

## Hard Negatives (Recommended)

Cracks, patches, shadows, stains, manholes, water puddles

## Data Pipeline Next Steps

1. Inspect RDD2022 annotations (Pascal VOC XML, format, quality, difficulty, class names)
2. Inspect BharatPotHole annotations for compatibility
3. Verify RDD2020 India subset quality
4. Normalize annotations to project data contract
5. Perform group-based splitting
6. Create hard-negative dataset
7. Verify leakage prevention in practice

## Evidence Discipline

All claims are classified as: FACT, RESEARCH FINDING, ENGINEERING INFERENCE, ASSUMPTION, or OPEN QUESTION. Unknowns are explicitly marked, not assumed. Previous incorrect claims have been corrected with verified evidence.