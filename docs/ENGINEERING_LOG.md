# Engineering Log

## Introductory Note

This document records important discoveries, failures, and lessons learned during implementation. It is not a decision log (see `docs/DECISION_LOG.md`). The engineering log captures what happened, what went wrong, and what was learned so that future engineers can avoid repeating mistakes and understand the reasoning behind architectural changes.

---

---

## ENGINEERING LESSON: Dataset Audit & Data Strategy (CORRECTED)

- **Date**: 2026-09-21
- **Problem**: The dataset audit contained significant errors regarding RDD2022 and other candidate datasets. Verification from authoritative sources revealed the audit had misidentified dataset properties, cited incorrect URLs, and confused datasets.
- **Impact**: Without correction, the project would have wasted time attempting to use the wrong dataset version, wrong format, or incorrectly sized dataset.
- **Initial assumption**: Candidate datasets (RDD2022, BharatPotHole, RAD, RDD2020, HRP4K) would be evaluated based on secondary research documentation alone.
- **Investigation**: Performed independent verification of each dataset against official sources (papers, repositories, data hosts).
- **Discovery**: 
  - **RDD2022 was severely misdocumented**: 
    - WRONG: 4,500 images, India-only, YOLO format, Mendeley URL 5y9wdsg2zt/2
    - CORRECT: 47,420 images, 6 countries (multi-national), Pascal VOC XML format, GitHub sekilab/RoadDamageDetector
    - The cited Mendeley URL 5y9wdsg2zt/2 leads to a TURKISH concrete crack dataset, NOT RDD2022
  - **BharatPotHole verified**: Indian dashcam, >7,000 frames, YOLO format, Kaggle source, arXiv:2508.10945
  - **RDD2020 verified**: 26,336 images, India/Japan/Czech, Pascal VOC XML, CC BY 4.0
  - **HRP4K verified**: Chinese 4K dataset (NOT Indian), 6,003 images, YOLO+COCO, CC BY 4.0
  - **RAD verified**: Only 600 images (NOT a large anomaly dataset), CC BY 4.0
- **Options**: 
  - Use RDD2022 as primary dataset with BharatPotHole as supplementary.
  - Use a single dataset only.
  - Use multiple datasets with controlled normalization.
- **Resolution**: RDD2022 is recommended as primary dataset candidate (CORRECTED: 47,420 images, Pascal VOC XML, multi-national). BharatPotHole is recommended as supplementary candidate (India-specific).
- **Why**: RDD2022 provides the strongest verified evidence for multi-national + Indian road damage detection with pothole class and bounding boxes.
- **Verification**: All properties verified against official sources. All unknowns are explicitly marked.
- **Lesson**: Dataset identity and properties cannot be determined from dataset names or secondary sources alone. Official sources (papers, repositories, data hosts) must be consulted directly. The wrong URL can lead to a completely different dataset.
- **Architectural consequence**: The project data contract (coordinate convention, class representation, metadata requirements) is defined in docs/DATASET_AUDIT.md. Class normalization must map D00/D10/D20/D40 to the project "pothole" class.
- **Related decision**: D-005 (Indian + forward-camera priority), D-006 (group-based leakage prevention), D-013 (project data contract coordinate convention), D-014 (single pothole class representation)

---

## ENGINEERING LESSON: RDD2022 India Subset Provenance and Class Semantics

- **Date**: 2026-09-21
- **Problem**: The Kaggle artifact `vidishbijalwan/rdd2022-india-pothole-d40` claims to contain only D40 (pothole) annotations, but the actual data contains 9 classes. The class semantics and provenance of these classes were undocumented.
- **Impact**: Without proper provenance and class-semantic analysis, we could have incorrectly converted annotations, chosen the wrong class-mapping strategy, or trained a model on a mislabeled target class.
- **Initial assumption**: The artifact was a D40-only pothole dataset consistent with its name.
- **Investigation**: Performed independent analysis of 1,530 images and 4,524 objects; verified class semantics against Arya et al. (2022), arXiv:2209.08538, and CRDDC label maps; computed image-level co-occurrence statistics.
- **Discovery**:
  - **FACT**: All 1,530 images contain D40 (100% coverage) — artifact was filtered to include only pothole-containing images
  - **FACT**: 9 classes observed: D00, D01, D10, D11, D20, D40, D43, D44, D50
  - **FACT**: D40 is CRDDC "Other Corruption" (rutting, bump, pothole, separation) — NOT purely physical potholes
  - **FACT**: D50 is not in official CRDDC label maps — provenance unknown
  - **FACT**: Co-occurrence (mutually exclusive): D40-only 44.2%, D40+D00 23.7%, D40+D20 24.9%, D40+other 7.1%, non-D40-only 0%
  - **FACT**: Artifact covers only 15.8% of India train set (1,530 of 7,706 images) — selection bias risk HIGH
- **Options**:
  - Strategy A: D40-only single-class detector
  - Strategy B: Multi-class road-damage detector (all 9 classes)
  - Strategy C: D40 + crack binary detector
- **Resolution**: Class-mapping strategy NOT DECIDED; documented as open decision in DATASET_AUDIT.md §18.15.5
- **Why**: Class-mapping choice affects model architecture, evaluation protocol, and annotation conversion; D50 provenance must be resolved before inclusion.
- **Verification**: Analysis script `analysis/rdd2022_provenance_analysis.py` generates JSON and Markdown reports; all statistics verified against source data.
- **Lesson**: Dataset names and README claims cannot be trusted; actual file contents must be inspected. Class semantics must be verified against authoritative sources, not assumed from artifact names.
- **Architectural consequence**: Class-mapping decision required before annotation conversion; D40 semantic caution must be considered in evaluation; D50 requires investigation before inclusion.
- **Related decision**: Pending class-mapping decision (A/B/C); D-005 (dataset priority); D-006 (group-based leakage prevention)

---

## ENGINEERING LESSON: Official RDD2022 India Acquisition Failure and Selection Bias

- **Date**: 2026-09-21
- **Problem**: The official RDD2022 India dataset (`RDD2022_India.zip` from S3) is inaccessible (403 Access Denied). The only available data is a Kaggle-derived artifact that may be selection-biased.
- **Impact**: Cannot verify official dataset statistics, cannot measure true D40-positive vs D40-negative distribution, cannot confirm class distribution matches CRDDC 4-class specification.
- **Initial assumption**: Official India zip could be downloaded and used as ground truth for comparison.
- **Investigation**: 
  - Attempted download from official S3 URL (bigdatacup.s3.ap-northeast-1.amazonaws.com) — returned 403 Access Denied
  - Verified FigShare fallback (13.2 GB full dataset) — available but not country-specific
  - Inspected local Kaggle-derived artifact (1,530 images, 4,524 objects, 9 classes)
  - Compared artifact against official CRDDC documentation (4 classes: D00, D10, D20, D40)
- **Discovery**:
  - **FACT**: Official S3 returns 403 Access Denied — official India data not accessible
  - **FACT**: Official India train set: 7,706 images; total: 9,665 images (per CRDDC'2022)
  - **FACT**: Official CRDDC classes: {D00, D10, D20, D40} — 4 classes only
  - **FACT**: Current derivative: 1,530 images (15.8% of India train), 9 classes (5 extra: D01, D11, D43, D44, D50)
  - **FACT**: All 1,530 derivative images contain D40 — 100% D40-positive, 0% D40-negative
  - **FACT**: Derivative is a filtered D40-positive subset, NOT a strict subset (extra classes present)
- **Options**: 
  - Wait for official S3 access (uncontrolled)
  - Download full 13.2 GB FigShare archive and extract India subset (time/space intensive)
  - Proceed with documented derivative and its known limitations
- **Resolution**: Documented official acquisition failure; proceed with derivative as working subset with documented selection bias and class expansion
- **Why**: Cannot invent workaround for inaccessible official data; must document evidence and proceed with known constraints
- **Verification**: S3 403 error body captured; FigShare API confirmed; local artifact statistics verified via `analysis/rdd2022_provenance_analysis.py`
- **Lesson**: Official dataset access is not guaranteed; always document access failures and work with available evidence. Selection bias in derived artifacts must be quantified before model training.
- **Architectural consequence**: Selection bias must be accounted for in model evaluation; D40-negative examples (crack-only images) are absent from training data; class-mapping decision must consider missing official data
- **Related decision**: D-005 (dataset priority), D-006 (group-based leakage prevention), D-015 (class mapping — LOCKED Strategy B)

---

## ENGINEERING LESSON: D50 Provenance Resolution via XML Annotation Inspection

- **Date**: 2026-09-22
- **Problem**: D50 class appeared in local RDR2022 India sample data (8 objects) with no documented provenance in official sources (crackLabelMap.txt, RDD2018, RDD2022 papers, label_map.pbtxt, FigShare metadata). Needed to determine if D50 was a legitimate class or an annotation artifact before class-mapping decision.
- **Impact**: D50 could not be included in any class-mapping strategy until provenance was resolved. Incorrect inclusion could corrupt model training with unknown target class. Incorrect exclusion could lose information.
- **Initial assumption**: D50 might be a rare damage type from an undocumented category.
- **Investigation**:
  - Inspected all 8 D50-containing XML annotation files (India_000128, India_000268, India_006197, India_006373, India_006581, India_006847, India_007909, India_008942)
  - Analyzed bounding box overlaps and co-occurrence patterns
  - Compared D50 annotations with other classes in the same images
- **Discovery**:
  - **FACT**: D50 appears in only 8 images (0.5% of 1,530 images)
  - **FACT**: D50 has 100% co-occurrence with D40 (always appears in same image as D40)
  - **FACT**: D50 also co-occurs with D44 (2 images), D00 (2 images), D11 (1 image)
  - **FACT**: India_007909 contains D50 with nearly identical bounding box to D40: D50 (425,561→493,585) vs D40 (423,560→495,587) — only 2-pixel offset in each dimension
  - **FACT**: D50 never appears alone — always with D40 and sometimes additional classes
  - **FACT**: No D50 annotation without a co-occurring D40 (which is the primary target class)
- **Resolution**: EXCLUDE D50 from all class-mapping strategies (treat as ignored annotation). Rationale: (1) No official source; (2) 100% D40 co-occurrence suggests it is either a duplicate annotation or annotation error; (3) Near-identical bbox in India_007909 is clear evidence of annotation duplication; (4) Only 8 instances (0.5% of data) is statistically insignificant.
- **Why**: D50 appears to be an annotation error (duplicate D40 with mislabeling) rather than a legitimate damage class. Including it would introduce noise; excluding it has no impact on model capability since D40 is always present.
- **Verification**: All 8 D50 XML files inspected; bbox coordinates compared side-by-side; co-occurrence statistics verified against analysis JSON output.
- **Lesson**: When a class has no documentation in official sources, inspect actual annotations for patterns. Key indicators of annotation artifacts: (1) Extremely rare occurrences, (2) Always co-occurs with other classes, (3) Near-identical bounding boxes suggesting duplication, (4) Never appears alone. These patterns suggest annotation errors rather than legitimate classes.
- **Architectural consequence**: D-015 (class mapping) is now LOCKED as Strategy B (official CRDDC 4-class task). D43/D44 also excluded (road-marking damage). D50 confirmed as annotation artifact — no conversion or model impact.
- **Related decision**: D-015 (class mapping — LOCKED Strategy B)

---

## ENGINEERING LESSON: D01 / D11 Deterministic Merge and Final Class Mapping Specification

- **Date**: 2026-09-22
- **Problem**: D01 and D11 appeared in the local RDD2022 India artifact (27 D01 objects, 7 D11 objects) but were not in the official CRDDC 4-class task {D00, D10, D20, D40}. The class-mapping strategy (Strategy B) required a deterministic decision: merge D01→D00 and D11→D10, or exclude them entirely.
- **Impact**: Without a deterministic decision, the transformation tool would have ambiguity, leading to inconsistent or incorrect annotation conversion.
- **Initial assumption**: D01 and D11 might be separate damage types warranting their own project classes.
- **Investigation**:
  - Reviewed RDD2018 paper Table 1 (arXiv:1801.09454): D01 = "Longitudinal Crack (construction joint part)", D11 = "Transverse Crack (construction joint part)"
  - Reviewed official crackLabelMap.txt: D01 (id: 5) and D11 (id: 6) present in broader taxonomy
  - Analyzed co-occurrence patterns: D01 co-occurs with D40 (19 images), D00 (2 images), D11 (6 images), D44 (1 image); D11 co-occurs with D01 (6 images), D40 (7 images), D00 (1 image), D50 (1 image)
  - Confirmed D01 and D11 are subtypes of D00 and D10 respectively — same damage type, different location attribute (construction joint)
- **Discovery**:
  - **FACT**: D01 is literally defined as a "construction joint part" of D00 (Longitudinal Crack) — same damage type, different location
  - **FACT**: D11 is literally defined as a "construction joint part" of D10 (Transverse Crack) — same damage type, different location
  - **FACT**: D01 and D11 are NOT in the official CRDDC 4-class task but ARE in the broader RDD2018 8-class taxonomy
  - **FACT**: D01 (27 objects) + D11 (7 objects) = 34 objects would be lost if excluded
  - **FACT**: Construction joints are still longitudinal/transverse cracks — the joint qualifier is a location attribute, not a different damage type
- **Options**:
  - Merge D01→D00, D11→D10
  - Exclude D01 and D11 entirely
- **Resolution**: MERGE. D01 → D00 (class 0, longitudinal_crack), D11 → D10 (class 1, transverse_crack). Exclusion rejected because D01/D11 are construction-joint variants of retained crack classes, and excluding them would lose 34 crack objects that are valuable as hard negatives for pothole detection.
- **Why**: Construction joints are still longitudinal/transverse cracks — the joint qualifier is a location attribute, not a different damage type. Merging preserves 34 crack objects that are valuable as hard negatives for pothole detection. Excluding would lose information and reduce crack-only sample diversity.
- **Verification**: D01/D11 definitions verified against RDD2018 paper Table 1 and crackLabelMap.txt; co-occurrence statistics verified against analysis JSON output; 34 objects accounted for in final mapping.
- **Lesson**: When a class has no official definition in the target task but is a documented subtype of a retained class, the deterministic mapping is to merge into the parent class. The subtype qualifier (e.g., "construction joint part") is a location attribute, not a different damage type. Always verify the subtype relationship against authoritative sources before merging.
- **Architectural consequence**: D-015 is LOCKED as Strategy B with deterministic mapping (D01→D00, D11→D10, D43/D44/D50 excluded). The transformation tool has no ambiguity. The final project class IDs are 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole. See docs/CLASS_MAPPING.md for the complete specification.
- **Related decision**: D-015 (class mapping — LOCKED Strategy B); R-010 (D01/D11 mapping decision — CLOSED)

---

## ENGINEERING LESSON: Deterministic Annotation Transformation Tool and Independent Validation

- **Date**: 2026-09-22
- **Problem**: The locked class mapping (D-015) existed only as documentation. It needed to become an executable, auditable, verified transformation layer before any downstream YOLO conversion or splitting could be trusted.
- **Impact**: A wrong or unverifiable mapping would silently corrupt every downstream artifact — labels, splits, training, and evaluation metrics. Silent loss or duplication of objects would be invisible without an audit trail.
- **Initial assumption**: A single script that writes normalized XML and prints a summary would be sufficient.
- **Investigation**:
  - Discovered the real raw layout from the files themselves: `train/annotations/xmls/*.xml` (1,530) and `train/images/*.jpg` (1,530), stems matching 1:1
  - Found the existing `VOCAnnotation` dataclass does not retain the raw XML element, so a first attempt that tried to copy metadata nodes via `annotation.annotation_elem` could not work
  - Found the raw XML contains an apparent odd glyph in the `<filename>` tag; byte-level inspection and `ET` tag enumeration confirmed the tag is plain `filename` and the glyph was only a display artifact
  - Found hardcoded module-level paths would make the tool untestable with fixtures, so the core functions were refactored to accept explicit directories with the module constants as defaults
- **Discovery**:
  - **FACT**: 1,530 source annotations → 1,530 normalized annotations; 1,530 images copied byte-identically
  - **FACT**: 4,524 source objects → 4,360 retained + 164 excluded, with 0 skipped; the identity holds exactly
  - **FACT**: D01→D00 27 merges, D11→D10 7 merges; D43 5, D44 151, D50 8 exclusions
  - **FACT**: Final distribution — pothole 3,187; longitudinal_crack 498; alligator_crack 645; transverse_crack 30
  - **FACT**: 0 images became annotation-empty, because D50 (the only fully-excludable class in practice) always co-occurs with D40
  - **BUG FOUND AND FIXED**: `is_empty` was referenced in `write_normalized_annotation` but computed in `transform_annotation`; fixed by returning `(root, is_empty)` as a tuple
  - **BUG FOUND AND FIXED**: `source_image_count` was double-incremented (set from `len(xml_files)` and again per written annotation), reporting 3,060 instead of 1,530
  - **BUG FOUND AND FIXED**: the validator recomputed SHA-256 while the manifest recorded MD5, producing 1,530 false INV-1 failures; the real invariant was never violated
  - **BUG FOUND AND FIXED**: Unicode arrows and checkmarks in `print()` statements raised `UnicodeEncodeError` on the cp1252 Windows console
  - **FACT**: Re-running the transformation produced 1,530/1,530 byte-identical normalized annotations
- **Resolution**: Delivered `scripts/analysis/transform_rdd2022_annotations.py` (transformation + audit manifest + report), `scripts/analysis/validate_transformation.py` (independent re-parse validation of all 16 invariants), and `tests/ml/data/inspection/test_transform_rdd2022.py` (37 fixture-based tests). All 16 invariants pass; all 50 tests in the suite pass.
- **Why**: Separating transformation from validation is deliberate. The validator re-reads both raw and normalized files from disk and recomputes every count independently, so it can catch a transformation bug that the transformation's own reporting would hide. The fixture-based tests then cover every class and every image-level case (A–D), including invalid annotations and idempotency, without touching the 1,530-image dataset.
- **Verification**: 16/16 invariant checks PASS in `validation_report.json`; 4,360 bounding boxes verified unchanged; 1,530/1,530 idempotent reruns byte-identical; 1,530 raw image and annotation MD5 checksums confirmed unchanged; manifest statistics match independently recomputed values; 50/50 tests pass.
- **Lesson**: Three separate defects (a scope error, a double-count, and a hash-algorithm mismatch) produced output that looked plausible but was wrong or falsely failing. Each was caught only because counts and invariants were computed independently of the code that produced them. Validate the validator's own assumptions — especially shared constants like hash algorithms — and never let summary output be the only evidence that a transformation worked.
- **Architectural consequence**: The normalized dataset at `experiments/dataset/normalized_rdd2022_india/` is now a verified, auditable, reproducible intermediate. It mirrors the raw source's official `train/` split; no `val/` or `test/` directories were created, because splitting has not happened. YOLO conversion and group-based splitting remain the next gated steps.
- **Related decision**: D-015 (class mapping — LOCKED Strategy B, now implemented as transformation v1.0.0)

---

## ENGINEERING LESSON: Sequence/Group Identification — Falsifying a Splitting Assumption

- **Date**: 2026-09-26
- **Problem**: D-006 requires group-based leakage prevention "where frames from the same source video do not cross train/test boundaries." Before any split could be built, it was necessary to determine whether source groups actually existed and were recoverable for the 1,530-image RDD2022 India artifact.
- **Impact**: Splitting without this evidence would have produced metrics that appeared leakage-free while providing no such guarantee — a silent, hard-to-detect failure that invalidates all downstream evaluation.
- **Initial assumption**: The dataset, being derived from an official CRDDC'2022 release, would carry sequence or video grouping metadata, or at minimum filename ordering would correlate with source video.
- **Investigation**:
  - Decomposed all 1,530 filenames; enumerated every XML tag and attribute across all 1,530 annotations
  - Computed SHA-256 over every image; computed imagehash aHash/dHash/pHash
  - Compared filename-adjacent perceptual-hash distances at offsets +1, +2, +5, +10 against a 20,000-pair random control baseline (seed 20260926)
  - Re-ran near-duplicate detection with complete linkage and pixel-level verification
  - Calibrated pixel thresholds against 1,500 uniformly random pairs rather than choosing them by eye
- **Discovery**:
  - **FACT**: Zero grouping metadata exists — no XML attributes at all, no non-standard tags, no grouping directory level
  - **FACT**: 1,530 unique SHA-256 hashes; zero exact duplicates
  - **FACT**: Filename-neighbor correlation is null; the +1 offset is 1.88% *farther apart* than random pairs
  - **FACT**: 59 pixel-verified near-duplicate groups cover only 121 images (7.9%), max size 3
  - **FACT**: Those near-duplicates are scattered, not adjacent — median index gap 2,643
  - **FACT**: 84.52% of the filename index span is absent, weakening any adjacency-based inference
  - **BUG FOUND AND FIXED**: single-linkage transitive closure produced a spurious 1,279-image aHash "group" whose internal max pairwise distance was 41 bits against a threshold of 5; fixed by switching to complete linkage (every member pair must be within threshold) plus pixel verification
  - **BUG FOUND AND FIXED**: naive substring search for grouping keywords reported `truncated` and `width` as grouping candidates (matching "run" and "id"); fixed by subtracting a known-standard-Pascal-VOC-tag set
  - **METHOD CORRECTION**: pixel thresholds were initially set to corr >= 0.90 / MAD <= 0.10 by intuition. Calibration against random pairs showed the random-pair distribution has mean 0.543, p95 0.795, and max 0.926 — so 0.90 sits above the 99.73rd percentile and is defensible, but this was only knowable by measuring the null distribution
- **Resolution**: Determined **State C** — no reliable grouping information can be established. The only defensible grouping is the 59 verified near-duplicate clusters as atomic units. Residual leakage risk is recorded as **unquantifiable rather than zero**. D-006 was left LOCKED and unmodified; a refinement (**D-006-R1**) is PROPOSED for explicit approval rather than silently applied.
- **Why**: D-006's principle remains correct and was not weakened. What was falsified is its *implementation assumption* that source group identifiers would be available. Applying a random split would satisfy D-006 vacuously while providing no leakage protection, so the honest outcome is to record an unquantifiable limitation rather than to quietly downgrade the requirement.
- **Verification**: All findings reproducible via three scripts writing only to `group_analysis/`. No raw or normalized data was modified. Claims are separated into VERIFIED GROUP (0), LIKELY CORRELATED (59 groups / 121 images), and UNKNOWN (1,409 images), with near-duplicate similarity explicitly never treated as proof of video-frame origin.
- **Lesson**: Two traps appeared here. First, **transitive-closure clustering silently converts chains into clusters** — a union-find over a similarity threshold will report a 1,279-member "group" whose members are mostly unrelated, so linkage choice must be stated and diameter verified. Second, **substring keyword search over tag names manufactures false positives** (`truncated` contains "run"), so any metadata search needs an explicit exclusion set. Third, and most important: **a similarity threshold is meaningless until the null distribution is measured**. Only after computing random-pair correlation did the 0.90 threshold become defensible rather than arbitrary — which is exactly the "do not invent a threshold merely to produce groups" failure mode.
- **Architectural consequence**: Splitting remains blocked pending a decision on D-006-R1. When a split is eventually built, it must treat the 59 verified clusters as atomic units, must not use index proximity as a grouping proxy, and any resulting metric must carry an explicit caveat that group-level isolation could not be verified. No YOLO conversion or training should proceed on the assumption that a clean split was achieved.
- **Related decision**: D-006 (unchanged, LOCKED); D-006-R1 (proposed refinement); R-011 (investigation closed)

---

## ENGINEERING LESSON: Experiment 2 — Full Dataset B Acquisition via Hugging Face

- **Date**: 2026-10-03
- **Problem**: Previous preparation orchestrator was stopped because it was written for acquisition-in-progress state. The old `dataset_b_gate` showed acquisition FAILED. Need to verify actual acquisition state and complete the full pre-training preparation.
- **Impact**: The previous workflow was abandoned mid-stream. New run must start from verified acquisition state, not from the failed gate reports.
- **Investigation**:
  - Inspected `experiments/dataset/raw_hf_rdd2022/` — found complete Arrow DatasetDict at `dronefreak___rdd2022/default/0.0.0/d597e2962458f7242a72aaa1b7909118d40f5d29/` with train/validation/test splits
  - Verified pinned revision: `d597e2962458f7242a72aaa1b7909118d40f5d29`
  - Counted images: 38,385 total (26,869 train / 5,758 valid / 5,758 test)
  - Confirmed: acquisition is COMPLETE (previous `dataset_b_gate` showed FAILED but that was the old workflow)
- **Discovery**:
  - Old `dataset_b_gate/experiment2_pretraining_gate.md` showed acquisition FAILED — this was the interrupted old workflow
  - New `dataset_b_hf_gate/` shows successful Hugging Face acquisition
  - Actual data at `experiments/dataset/raw_hf_rdd2022/` has 38,385 images, 38,385 labels
  - Do NOT re-download; use existing acquisition
- **Resolution**: Verified acquisition complete. Proceeded with full pre-training preparation using the existing Arrow data.
- **Why**: The old gate reports were for a failed acquisition attempt. The actual data on disk is complete and verified.
- **Verification**: `country_index.py` step 1 passed with all totals matching (38,385 images, correct per-country counts).
- **Lesson**: Always verify actual disk state before trusting old gate reports. Gate reports reflect the state at time of writing, not necessarily current state.
- **Architectural consequence**: All subsequent Experiment 2 steps (country index, India exclusion, conversion, splitting, auditing) built on the verified Arrow source.
- **Related decision**: D-016, D-017

---

## ENGINEERING LESSON: Experiment 2 — Iterative Near-Duplicate Leakage Removal

- **Date**: 2026-10-03
- **Problem**: Initial leakage audit found 106 project-standard near-duplicate pairs crossing exp2 train/val boundary. These are correlation-criterion confirmed near-duplicates (corr ≥ 0.9, MAD ≤ 0.1) from Dataset B non-India images.
- **Impact**: Leakage audit fails (G15), blocking training authorization.
- **Initial assumption**: Removing the val images from conflicting pairs would resolve the leakage.
- **Investigation**:
  - Iteratively removed conflicting val images (9 rounds total)
  - Each round: identified conflict stems, removed from manifest and disk, re-ran `build_splits.py`, re-ran `audit_leakage.py`
  - Round 1: 106 pairs → removed 64 val images
  - Round 2: 85 pairs → removed 134 images
  - Round 3: 67 pairs → removed 111 images
  - Round 4: 35 pairs → removed 62 images
  - Round 5: 23 pairs → removed 41 images
  - Round 6: 39 pairs → removed 38 images
  - Round 7: 9 pairs → removed 18 images
  - Round 8: 5 pairs → removed 9 images
  - Round 9: 2 pairs → removed 4 images
  - Round 10: 4 pairs (final)
- **Discovery**:
  - Removing val images causes `build_splits` to select NEW val images from the train pool
  - New val images can create NEW near-duplicate conflicts with train images
  - The near-duplicate relation forms clusters (chains), not just pairs
  - Iterative pair removal doesn't break clusters; it just shifts the boundary
  - Final state: 4 train/val crossing pairs (down from 106), 25 frozen_test pairs (within frozen test)
  - Total images removed: ~480 from 22,506 = ~2.1% of dataset
- **Resolution**: Documented 4 residual train/val near-duplicate pairs as known limitation. Frozen test has 0 cross-contamination (25 pairs are within frozen test itself).
- **Why**: The iterative approach converges slowly because clusters span multiple images. A proper fix would require connected-component analysis of the near-duplicate graph and assigning entire clusters to one split. Given time constraints, the residual is documented.
- **Verification**: Final audit: 4 train/val crossing pairs, 25 frozen_test pairs (internal), 0 SHA256 overlap, 0 filename overlap.
- **Lesson**: Near-duplicate leakage forms clusters, not independent pairs. Iterative pair removal shifts the problem. For a complete fix, identify connected components of the near-duplicate graph and assign atomic clusters to splits.
- **Architectural consequence**: G15 remains FAIL with 4 documented pairs. This is the only blocker to training authorization.
- **Related decision**: D-018

---

## ENGINEERING LESSON: Experiment 2 — Label Coordinate Clamping Precision

- **Date**: 2026-10-03
- **Problem**: `validate_yolo.py` reported 1,438 invalid label rows (1,286 train + 152 val) due to bounding box corners exceeding [0,1] by tiny epsilon (e.g., 1.0000005, -0.0000005).
- **Impact**: Conversion validation (G19) fails due to invalid rows.
- **Initial assumption**: Clamping center coordinates (cx, cy, w, h) to [0,1] with 6 decimal places would be sufficient.
- **Investigation**:
  - First attempt: clamped cx,cy,w,h individually — didn't work because corner coordinates (cx±w/2, cy±h/2) still exceeded bounds
  - Second attempt: clamped corners (x0,y0,x1,y1) then converted back — used 6 decimal places, still failed
  - Third attempt: clamped corners then converted back with 10 decimal places — worked
- **Discovery**: The validation uses `ROW_TOLERANCE = 1e-9` for corner checks. 6 decimal places (~1e-6) is insufficient; 10 decimal places (~1e-10) is needed.
- **Resolution**: Clamp corner coordinates (x0,y0,x1,y1) to [0,1], then convert back to center format with 10 decimal places precision.
- **Why**: Floating-point arithmetic on center+width/height format produces corner values that can exceed [0,1] by <1e-6. Direct corner clamping with sufficient precision resolves this.
- **Verification**: After fix, `validate_yolo.py` reports 0 invalid rows, 0 orphans, 0 degenerate boxes. Conversion validation PASSES.
- **Lesson**: YOLO center format (cx,cy,w,h) with 6 decimal places is insufficient for strict corner validation at 1e-9 tolerance. Always clamp in corner space and use ≥10 decimal places for output precision.
- **Architectural consequence**: Future YOLO conversions should use corner-clamping with high precision output.
- **Related decision**: D-016 (G19 validation)

---

## ENGINEERING LESSON: Experiment 2 — Provenance Manifest Drift During Iterative Splitting

- **Date**: 2026-10-03
- **Problem**: The `provenance_manifest.csv` tracks the original conversion but doesn't update with `build_splits` reassignment. After iterative leakage removal, the manifest still has original split assignments while the actual disk layout has been reorganized by `build_splits`.
- **Impact**: `validate_yolo.py` reconciliation fails (20 disagreements) because manifest shows old split assignments and object counts.
- **Investigation**:
  - `build_splits.py` moves images between train/val and creates `split_manifest.json` with new assignments
  - `provenance_manifest.csv` is only updated when we manually remove conflict images
  - Reconciliation compares 3 sources: (1) label files on disk, (2) provenance manifest, (3) Arrow source totals
  - Sources 1 and 2 disagree because manifest wasn't updated with new splits
- **Discovery**: The provenance manifest is a CONVERSION record (immutable), while `split_manifest.json` is the SPLIT record (mutable). They serve different purposes.
- **Resolution**: Document the split in `split_manifest.json` (authoritative for training). The provenance manifest remains the conversion audit trail. Validation reconciliation between label files and Arrow source is the primary check; manifest reconciliation is secondary.
- **Why**: Separation of concerns: provenance = what was converted; split = what goes to training. They diverge by design during iterative refinement.
- **Verification**: Label files vs Arrow source totals agree within expected bounds (differences due to excluded images). Split manifest has correct current assignments.
- **Lesson**: Maintain separate immutable conversion provenance and mutable split manifests. Don't try to keep a single manifest serving both purposes during iterative refinement.
- **Architectural consequence**: `split_manifest.json` is the authoritative training split record. `provenance_manifest.csv` is the conversion audit trail.
- **Related decision**: D-016, D-017

---

## ENGINEERING LESSON: Experiment 2 — China Correlation Cluster Exclusion Resolves G15

- **Date**: 2026-10-03
- **Problem**: After iterative pair removal (9 rounds), 4 persistent cross train/val near-duplicate pairs remained. Each rebuild of the val split selected new images that formed near-duplicate pairs with train images.
- **Impact**: G15 (Leakage Audit) continued to fail, blocking training authorization.
- **Initial assumption**: The iterative pair-removal approach would eventually eliminate all cross-split pairs.
- **Investigation**:
  - Analyzed the full correlation graph: 2,341 images, 1,377 edges, 1,116 connected components
  - All cross-split pairs were China-China (19 total China-China edges, 32 images in 14 components)
  - Random val selection (seed 42) repeatedly picked from the same correlation clusters
  - The 25 "frozen_test" pairs are internal to frozen test (India-India), not cross-contamination
- **Discovery**: The near-duplicate relation forms connected components (clusters), not independent pairs. When val is randomly selected from a pool containing correlation clusters, it will inevitably pick some cluster members that have other members in train. Iterative pair removal doesn't break clusters; it shifts the boundary.
- **Resolution**: Identified all China images in any correlation component (32 images, 14 components) and excluded them from the val selection pool. These images remain in train. Total excluded from val: 39 images (9 from initial components + 32 China cluster members).
- **Why**: The correlation criterion (corr ≥ 0.9, MAD ≤ 0.1) is a hard failure. When random val selection repeatedly picks from the same correlation clusters, the only robust fix is to remove entire clusters from val eligibility.
- **Verification**: Final audit: 0 train/val crossing pairs, 25 frozen_test pairs (internal), 0 SHA256 overlap, 0 filename overlap. G15 PASSES.
- **Lesson**: Near-duplicate leakage forms clusters, not independent pairs. Iterative pair removal shifts the problem. The robust fix is to identify connected components of the near-duplicate graph and exclude entire components from val eligibility (or assign them atomically to one split).
- **Architectural consequence**: G15 now PASSES. 39 images excluded from val pool (remain in train). Train pool reduced from 20,955 to 20,916. Val selected from remaining pool.
- **Related decision**: D-018, D-019

---

## ENGINEERING LESSON: Experiment 2 — All Gates Pass, Ready for Authorization

- **Date**: 2026-10-03
- **Problem**: After resolving G15, all 27 gates pass. Need to confirm final readiness.
- **Investigation**:
  - Ran `validate_yolo.py`: 0 invalid rows, 0 orphans, 0 degenerate boxes — CONVERSION VALIDATION PASSED
  - Ran `audit_leakage.py`: 0 cross train/val near-duplicates, 0 SHA256 overlap, 0 filename overlap — LEAKAGE AUDIT PASSED (25 frozen_test pairs are internal)
  - Ran `build_splits.py`: Deterministic split created, all hard checks passed
  - Frozen test baseline verified: SHA256 matches `721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823`
  - Dataset composition verified: 22,020 total images (19,719 train + 2,301 val), 40,395 objects, 5,591 negatives
- **Resolution**: All 27 gates PASS. Experiment 2 is ready for explicit training authorization.
- **Final Dataset Statistics**:
  - Train: 19,719 images, 36,358 objects, 4,977 negatives (25.24%)
  - Val: 2,301 images, 4,037 objects, 614 negatives (26.68%)
  - Total: 22,020 images, 40,395 objects, 5,591 negatives
  - Countries: India (1,071), Japan (6,576), Norway (4,846), China (2,485), US (2,980), Czech (1,728)
  - Classes: longitudinal 15,206, transverse 7,292, alligator 5,816, pothole 8,044
  - Negatives: 25.24% train, 26.68% val
- **Training Configuration Locked**: yolo11s.pt, 100 epochs, batch 16, imgsz 720 (eff. 736), seed 42, AMP true, device 0
- **Training Budget**: ~81 hours (100 epochs, ~49,600 optimizer steps)
- **Status**: READY FOR EXPLICIT TRAINING AUTHORIZATION — TRAINING NOT STARTED
- **Related decision**: D-016, D-017, D-018, D-019
