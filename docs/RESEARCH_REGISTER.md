# Research Register

This document records research evidence independently from architectural decisions. It provides a transparent record of what research was performed, what was found, and what engineering implications were drawn.

## Purpose

To ensure that engineering decisions are traceable to research evidence and to enable future researchers to understand the reasoning behind architectural choices.

## Template

```text
Research ID:
Question:
Topic:
Source:
Source date:
Technology / Dataset:
Version:
Finding:
Evidence:
Engineering implication:
Confidence:
Affected decision:
Date checked:
Revisit condition:
Status:
```

---

## Research Entries

### R-001: Dataset Candidate Survey

- **Question**: Which dataset sources are viable for pothole detection in India?
- **Topic**: Dataset survey
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: RDD2022, BharatPotHole, RAD, RDD2020, HRP4K
- **Version**: As listed in candidate survey
- **Finding**: Each candidate has strengths; exact suitability requires annotation audit and leakage analysis.
- **Evidence**: `docs/DATA_PIPELINE.md` lists candidate sources with required properties.
- **Engineering implication**: Dataset audit phase is required before dataset version can be locked.
- **Confidence**: MEDIUM
- **Affected decision**: D-005 (Indian + forward-camera priority), D-006 (group-based leakage prevention)
- **Date checked**: 2026-09-17
- **Revisit condition**: After dataset audit is performed.
- **Status**: UNDER AUDIT

---

### R-002: Model Candidate Survey

- **Question**: Which detector architectures are reasonable candidates for pothole detection?
- **Topic**: Model survey
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: YOLO11s, YOLO26s, RF-DETR-S
- **Version**: As listed in candidate survey
- **Finding**: Each candidate has trade-offs in architecture, latency, and performance. Empirical comparison is required.
- **Evidence**: `docs/MODEL_TRAINING.md` lists candidate models; `docs/MODEL_EVALUATION.md` defines evaluation protocol.
- **Engineering implication**: Experiments must follow the same dataset, split, and evaluation protocol for fair comparison.
- **Confidence**: MEDIUM
- **Affected decision**: D-004 (candidate-model comparison)
- **Date checked**: 2026-09-17
- **Revisit condition**: After experiments are completed.
- **Status**: PENDING

---

### R-003: Pretraining / Fine-Tuning Effectiveness

- **Question**: Does pretrained initialization + fine-tuning outperform training from scratch on pothole detection?
- **Topic**: Transfer learning evaluation
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: Not yet evaluated
- **Version**: N/A
- **Finding**: Transfer learning is the primary training strategy; a controlled comparison with training from scratch may be evaluated as a secondary experiment.
- **Evidence**: `docs/MODEL_TRAINING.md` documents the primary training philosophy.
- **Engineering implication**: All experiments must begin with pretrained initialization; training from scratch is secondary.
- **Confidence**: HIGH (architectural decision; not empirically verified on our dataset)
- **Affected decision**: D-003 (transfer learning as primary training strategy)
- **Date checked**: 2026-09-17
- **Revisit conditions**: After the controlled comparison experiment (if performed).
- **Status**: LOCKED (strategy direction)

---

---

### R-004: RDD2022 Dataset Audit (CORRECTED)

- **Question**: What are the verified properties of RDD2022?
- **Topic**: Dataset audit
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022
- **Version**: CRDDC'2022 challenge release
- **Finding**: 
  - **FACT**: Multi-national (6 countries: Japan, India, Czech Republic, Norway, USA, China), smartphone dashcam, pothole class (D40), bounding boxes, 47,420 images, India subset 9,665 images, CC BY 4.0 license.
  - **CRITICAL CORRECTION**: Previous research finding was incorrect - it stated 4,500 images, YOLO format, India-only, and cited wrong Mendeley URL.
  - **VERIFIED**: Actual dataset is GitHub sekilab/RoadDamageDetector, 47,420 images, Pascal VOC XML, multi-national.
  - **OPEN**: Exact annotation quality, leakage grouping, size distribution, object-count distribution.
- **Evidence**: docs/DATASET_AUDIT.md#3
- **Engineering implication**: Strong multi-national candidate for general detection, requires annotation audit and leakage analysis before use. India-specific suitability requires verification of India subset quality.
- **Confidence**: MEDIUM (verified facts are FACT; previous incorrect facts have been corrected)
- **Affected decision**: D-005 (Indian + forward-camera priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: After annotation quality inspection.
- **Status**: LOCKED (properties verified after correction)

---

### R-007: RDD2022 India Subset Provenance and Class Semantics

- **Question**: What is the provenance chain, class semantics, and co-occurrence structure of the real RDD2022 India artifact?
- **Topic**: Dataset provenance, class semantics, co-occurrence analysis
- **Source**: Independent analysis of Kaggle `vidishbijalwan/rdd2022-india-pothole-d40`; official RDD2022 (arXiv:2209.08538, CRDDC label maps)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022 India subset (1,530-image artifact)
- **Version**: CRDDC'2022 challenge release
- **Finding**:
  - **FACT**: Artifact is a filtered subset of India train set (15.8%); Pascal VOC XML; 720x720 resolution; India locations (Delhi, Gurugram, Haryana)
  - **FACT**: All 1,530 images contain D40 — artifact was filtered to include only pothole-containing images
  - **FACT**: 9 classes observed (D00, D01, D10, D11, D20, D40, D43, D44, D50), not just D40 as Kaggle README claims
  - **FACT**: D40 semantic scope is "Other Corruption" (rutting, bump, pothole, separation) per CRDDC — NOT purely physical potholes
  - **FACT**: D50 is not in official CRDDC label maps — provenance unknown
  - **FACT**: Co-occurrence (mutually exclusive): D40-only 44.2%, D40+D00 23.7%, D40+D20 24.9%, D40+other 7.1%, non-D40-only 0%
  - **OPEN**: Class-mapping strategy (A/B/C) not decided; D50/D43/D44 provenance; geographic/seasonal coverage
- **Evidence**: `analysis/rdd2022_provenance_analysis.py`, `analysis/output/rdd2022_provenance_analysis.json`, `analysis/output/rdd2022_provenance_report.md`, `docs/DATASET_AUDIT.md` §18.15
- **Engineering implication**: Class-mapping decision (A/B/C) required before annotation conversion; D50 requires investigation; D40 semantic caution must be considered in evaluation; selection bias risk HIGH; artifact covers only 15.8% of India train set
- **Confidence**: HIGH (verified from data); MEDIUM (class-mapping undecided)
- **Affected decision**: D-005 (dataset priority), D-006 (group-based leakage prevention), D-0XX (class mapping — pending)
- **Date checked**: 2026-09-21
- **Revisit condition**: After class-mapping decision is made; after D50 provenance is resolved.
- **Status**: OPEN (class-mapping and D50 provenance)

---

### R-008: Official RDD2022 India Acquisition and Selection Bias

- **Question**: Is the official RDD2022 India dataset accessible, and what is the selection bias of the current derivative?
- **Topic**: Dataset acquisition, selection bias, derivative comparison
- **Source**: S3 URL check (bigdatacup.s3.ap-northeast-1.amazonaws.com); FigShare API; local artifact inspection
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022 India (official vs. Kaggle derivative)
- **Version**: CRDDC'2022 challenge release
- **Finding**:
  - **FACT**: Official `RDD2022_India.zip` (502.3 MB) returns 403 Access Denied from S3 bucket
  - **FACT**: Official India train set: 7,706 images; total India subset: 9,665 images (per CRDDC'2022 documentation)
  - **FACT**: Official CRDDC classes: {D00, D10, D20, D40} — 4 classes per label_map.pbtxt and crackLabelMap.txt
  - **FACT**: FigShare full RDD2022 archive is 13.2 GB (not country-specific) — available as fallback
  - **FACT**: Current derivative (1,530 images) is 15.8% of India train set and contains 9 classes (5 extra beyond official 4)
  - **FACT**: All 1,530 derivative images are D40-positive (100% selection bias); 0% are D40-negative
  - **INFERENCE**: Derivative is a filtered D40-positive subset — NOT a strict subset (extra classes) and NOT a converted copy (VOC XML preserved)
  - **OPEN**: Official India D40-positive vs D40-negative distribution (unmeasurable without official data)
  - **OPEN**: ML impact of D40-only training on real-world deployment (crack-only images absent)
- **Evidence**: `docs/DATASET_AUDIT.md` §18.16, §18.17, §18.18; `analysis/output/rdd2022_provenance_analysis.json`
- **Engineering implication**: Cannot verify official vs derivative comparison without official data; selection bias is confirmed and must be documented; class-mapping decision (A/B/C) must account for absent D40-negative examples
- **Confidence**: HIGH (verified from S3/FigShare API responses and local data analysis)
- **Affected decision**: D-005 (dataset priority), D-006 (group-based leakage prevention), D-0XX (class mapping — pending)
- **Date checked**: 2026-09-21
- **Revisit condition**: After official India data acquisition attempt; after class-mapping decision.
- **Status**: OPEN (acquisition failure documented; selection bias confirmed)

---

### R-009: D43 / D44 / D50 Provenance Resolution

- **Question**: What are the semantic meanings and provenance of D43, D44, and D50, and how do they relate to the official CRDDC four-class task?
- **Topic**: Class semantics, provenance, taxonomy reconciliation
- **Source**: Official RDD2018 paper (arXiv:1801.09454), RDD2022 paper (arXiv:2209.08538), official crackLabelMap.txt, local XML annotation inspection
- **Source date**: 2026-09-22
- **Technology / Dataset**: RDD2018/RDD2022 taxonomy, local Kaggle-derived artifact
- **Version**: CRDDC'2022 challenge release
- **Finding**:
  - **VERIFIED (D43)**: "White line blur" — road marking damage, not structural road damage. Source: RDD2018 Table 1; crackLabelMap.txt
  - **VERIFIED (D44)**: "Cross walk blur" — road marking damage, not structural road damage. Source: RDD2018 Table 1; crackLabelMap.txt; not in official CRDDC four-class task
  - **RESOLVED (D50)**: Annotation artifact — 8 objects across 8 images (0.5% of data); 100% co-occurrence with D40; near-identical bbox to D40 in India_007909 (2-pixel offset in each dimension); no authoritative source in crackLabelMap.txt, RDD2018, RDD2022, label_map.pbtxt, or FigShare; RECOMMENDATION: EXCLUDE from all class-mapping strategies as ignored annotation
  - **FACT**: Official CRDDC task uses exactly {D00, D10, D20, D40}
  - **FACT**: RDD2018 used 8 classes {D00, D01, D10, D11, D20, D40, D43, D44}
  - **INFERENCE**: D43/D44 are inherited from RDD2018 taxonomy, retained in label map but excluded from CRDDC task
  - **INFERENCE**: D50 is an annotation artifact (duplicate D40 or mislabeling error) with no official source
- **Evidence**: `docs/DATASET_AUDIT.md` §18.15.2a, §18.19; `analysis/rdd2022_provenance_analysis.py`; `crackLabelMap.txt`; RDD2018 paper Table 1; local XML inspection (India_000128, India_000268, India_006197, India_006373, India_006581, India_006847, India_007909, India_008942)
- **Engineering implication**: D43/D44/D50 require explicit mapping decisions before annotation conversion; D50 must be EXCLUDED from all strategies; D43/D44 are road marking damage, not structural damage; D-015 (class mapping) is LOCKED as Strategy B
- **Confidence**: HIGH (D43/D44 verified from two authoritative sources); HIGH (D50 resolved as annotation artifact from 8 XML files)
- **Affected decision**: D-015 (class mapping — LOCKED as Strategy B)
- **Date checked**: 2026-09-22
- **Revisit condition**: After official India data acquisition attempt; if project scope changes to include road markings.
- **Status**: CLOSED (D50 provenance resolved; class-mapping decision made)

---

### R-010: D01 / D11 Mapping Decision

- **Question**: Should D01 and D11 be merged into D00 and D10 respectively, or excluded from the project class mapping?
- **Topic**: Class semantics, taxonomy reconciliation, deterministic mapping
- **Source**: Official RDD2018 paper (arXiv:1801.09454), RDD2022 paper (arXiv:2209.08538), official crackLabelMap.txt, local artifact inspection
- **Source date**: 2026-09-22
- **Technology / Dataset**: RDD2018/RDD2022 taxonomy, local Kaggle-derived artifact
- **Version**: CRDDC'2022 challenge release
- **Finding**:
  - **VERIFIED (D01)**: "Longitudinal Crack (construction joint part)" — construction joint variant of D00 (Longitudinal Crack). Source: RDD2018 Table 1; crackLabelMap.txt (id: 5)
  - **VERIFIED (D11)**: "Transverse Crack (construction joint part)" — construction joint variant of D10 (Transverse Crack). Source: RDD2018 Table 1; crackLabelMap.txt (id: 6)
  - **FACT**: D01 and D11 are subtypes of D00 and D10 respectively — same damage type, different location attribute (construction joint)
  - **FACT**: D01 appears in 19 images (27 objects); D11 appears in 7 images (7 objects) — total 34 objects
  - **FACT**: D01 and D11 are NOT in the official CRDDC 4-class task {D00, D10, D20, D40}
  - **FACT**: D01 and D11 ARE in the official crackLabelMap.txt (broader RDD2018 taxonomy)
  - **DECISION**: D01 → D00, D11 → D10 (deterministic merge)
  - **Rationale**: Construction joints are still longitudinal/transverse cracks — the joint qualifier is a location attribute, not a different damage type. Merging preserves 34 crack objects that are valuable as hard negatives for pothole detection. Excluding would lose information and reduce crack-only sample diversity.
- **Evidence**: `docs/DATASET_AUDIT.md` §18.15.2, §18.15.5a; `docs/CLASS_MAPPING.md` §1; `crackLabelMap.txt`; RDD2018 paper Table 1
- **Engineering implication**: D01 and D11 annotations are relabeled as class 0 (longitudinal_crack) and class 1 (transverse_crack) respectively during transformation; construction joint context is preserved in raw annotations but lost at class level; D-015 is LOCKED as Strategy B with deterministic mapping
- **Confidence**: HIGH (D01/D11 verified from two authoritative sources; mapping rationale is deterministic)
- **Affected decision**: D-015 (class mapping — LOCKED as Strategy B)
- **Date checked**: 2026-09-22
- **Revisit condition**: If construction joint crack patterns become a distinct project class; if D01/D11 object counts grow significantly in future data
- **Status**: CLOSED (deterministic mapping decided)

---

### R-011: Sequence/Group Identification for Leakage-Safe Splitting

- **Question**: Do the 1,530 RDD2022 India artifact images contain correlated sequences/groups that must be respected during dataset splitting, and is reliable grouping information obtainable?
- **Topic**: Sequence/group identification, duplicate detection, leakage risk
- **Source**: Local artifact inspection; SHA-256; imagehash dHash/aHash/pHash; pixel-level verification; random-pair calibration
- **Source date**: 2026-09-26
- **Technology / Dataset**: RDD2022 India Kaggle-derived artifact (1,530 images)
- **Version**: CRDDC'2022 derivative
- **Finding**:
  - **FACT**: No grouping metadata of any kind. Zero XML attributes across all 1,530 files; no non-standard tags; no sequence/video/trip/camera/timestamp/GPS field; no grouping directory level
  - **FACT**: Filenames are `India_<6-digit flat index>`, range 5..9,890, span 9,886, with 8,356 indices (84.52%) absent. Zero-padding uniform; lexical order equals numeric order
  - **FACT**: 1,530 unique SHA-256 hashes — **zero exact duplicates**
  - **FACT**: Pixel-verified near-duplicate analysis (complete linkage) yields 59 groups covering 121 images (7.9%), max group size 3; 583 genuine match pairs vs ~10 expected by chance (~58x enrichment)
  - **FACT**: Verified near-duplicate pairs are NOT filename neighbors — median index gap 2,643; only 1 of 583 pairs within an index gap of 10
  - **FACT**: Filename-neighbor correlation is null. dHash mean: +1 = 26.211, +2 = 25.757, +5 = 25.885, +10 = 25.110, random baseline = 25.727. The +1 offset is 1.88% *farther* than random
  - **FACT**: Thresholds were calibrated against 1,500 random pairs (corr mean 0.543, p95 0.795, max 0.926; 0.27% reach 0.90; 0% reach 0.95), so corr >= 0.90 sits above the 99.73rd percentile
  - **INFERENCE**: Filename index adjacency carries no usable correlation signal in this artifact
  - **INFERENCE**: The near-duplicate signal is real but sparse (121 images, clusters <= 3) and does not constitute recoverable sequence structure
  - **INFERENCE**: State C — no reliable grouping information can be established; residual leakage risk is unquantifiable rather than zero
  - **OPEN**: Whether the full official India release provides sequence metadata (unanswerable while S3 returns 403)
  - **OPEN**: Whether the 121 clustered images share common video origin or are separate visits to the same locations
  - **OPEN**: Whether the flat index is a release ordering or a capture ordering
- **Evidence**: `docs/DATASET_AUDIT.md` §18.20; `experiments/dataset/normalized_rdd2022_india/group_analysis/SYNTHESIS.md`, `filename_report.{json,md}`, `image_correlation.{json,md}`, `near_duplicate_verification.{json,md}`; `scripts/analysis/analyze_filename_structure.py`, `scripts/analysis/analyze_image_correlation.py`, `scripts/analysis/verify_near_duplicates.py`
- **Engineering implication**: D-006's principle stands but its implementation assumption (available source group IDs) is falsified for this artifact. A refinement (D-006-R1) is PROPOSED, not applied. Any future split must treat the 59 verified clusters as atomic units, must not use index proximity as a grouping proxy, and must record residual leakage risk as unquantifiable.
- **Confidence**: HIGH for the absence of metadata, exact-duplicate absence, and null neighbor correlation (directly measured). MEDIUM-HIGH for the near-duplicate cluster structure (pixel-verified with calibrated thresholds, but visual identity does not establish capture origin).
- **Affected decision**: D-006 (unchanged); D-006-R1 (proposed refinement)
- **Date checked**: 2026-09-26
- **Revisit condition**: Official India release becomes accessible; a candidate dataset supplies verifiable group IDs; embedding-based semantic correlation analysis is performed.
- **Status**: CLOSED (investigation complete; grouping determined to be State C)

---

### R-005: Dataset Combination Analysis

- **Question**: Can multiple candidate datasets be combined effectively?
- **Topic**: Dataset combination analysis
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022 + HRP4K (potential primary + supplementary)
- **Version**: N/A (analysis)
- **Finding**: 
  - FACT: Class semantics may differ between datasets
  - FACT: RDD2022 uses Pascal VOC XML format; others UNKNOWN
  - FACT: Potential duplication between RDD2022 and RDD2020
  - INFERENCE: Label semantics mismatch can cause negative transfer
  - INFERENCE: Licensing (non-commercial, verify from source) may restrict combination
- **Evidence**: docs/DATASET_AUDIT.md#8
- **Engineering implication**: Dataset compatibility requires annotation inspection and licensing verification before combination.
- **Confidence**: MEDIUM
- **Affected decision**: D-005 (dataset priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: After annotation inspection and licensing verification.
- **Status**: PENDING

---

### R-006: Hard Negative Taxonomy for Pothole Detection

- **Question**: What non-pothole examples should be included as hard negatives?
- **Topic**: Hard negative strategy
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: N/A (taxonomy)
- **Version**: N/A
- **Finding**: 
  - FACT: Cracks, patches, shadows, and stains are visually similar to potholes
  - INFERENCE: These should be included in negative samples
  - INFERENCE: Manholes and water puddles may also be helpful
- **Evidence**: docs/DATASET_AUDIT.md#9
- **Engineering implication**: Add hard negatives from deployment domain during dataset preparation.
- **Confidence**: HIGH (visual similarity is well-established)
- **Affected decision**: None (future task)
- **Date checked**: 2026-09-21
- **Revisit condition**: After model training with hard negatives.
- **Status**: RECOMMENDED

---

---

*This register supplements the original entries. Entries will be added as research is performed.*

*See DATASET_AUDIT.md for the full dataset audit findings.*
*See PROJECT.md and DECISION_LOG.md for related source-of-truth documents.*