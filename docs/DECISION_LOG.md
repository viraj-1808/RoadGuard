# Decision Log

This document records major architectural decisions for the project.

Use a structured format for each decision.

---

## D-001: Object Detection as Core Task

- **Date**: 2026-09-17
- **Problem**: What is the core technical problem the system must solve?
- **Context**: Potholes need to be identified in road imagery automatically.
- **Options considered**: Classification, segmentation, object detection.
- **Evidence**: Object detection provides both classification and localization, which is necessary for bounding-box output and event generation.
- **Decision**: Use object detection as the core ML task.
- **Why**: Detection outputs bounding boxes and class labels, which are needed for downstream tracking and event generation.
- **Rejected alternatives**: Pure classification (no localization), segmentation (too expensive for real-time inference).
- **Consequences**: The entire system is built around bounding-box detections.
- **Risks**: Detection quality depends heavily on dataset and training.
- **Revisit conditions**: If 3D measurement becomes a goal, segmentation may be revisited.
- **Status**: LOCKED

---

## D-002: Training/Fine-Tuning is Central ML Contribution

- **Date**: 2026-09-17
- **Problem**: What is the ML project's core technical contribution?
- **Context**: The system needs a pothole detector.
- **Options considered**: Train from scratch, fine-tune pretrained, use off-the-shelf detector.
- **Evidence**: Fine-tuning pretrained weights on a pothole dataset provides the best balance of performance and development speed.
- **Decision**: Training/fine-tuning is the central ML contribution.
- **Why**: The project must own the model and its training process to ensure it works on the target domain.
- **Rejected alternatives**: Using an off-the-shelf detector without customization.
- **Consequences**: Significant effort is invested in dataset preparation and training.
- **Risks**: Dataset quality and size may limit fine-tuning effectiveness.
- **Revisit conditions**: If dataset is too small, training from scratch may be evaluated as a secondary experiment.
- **Status**: LOCKED

---

## D-003: Transfer Learning as Primary Training Strategy

- **Date**: 2026-09-17
- **Problem**: What is the primary training approach?
- **Context**: Training a model from scratch requires large amounts of data and compute.
- **Options considered**: Training from scratch, transfer learning/fine-tuning, ensemble of pretrained models.
- **Evidence**: Pretrained weights on large-scale datasets provide strong feature extractors that adapt well to pothole detection with fine-tuning.
- **Decision**: Pretrained initialization followed by fine-tuning is the primary training strategy.
- **Why**: Transfer learning reduces data requirements and training time.
- **Rejected alternatives**: Training from scratch as the primary approach (may be evaluated as a controlled comparison).
- **Consequences**: Model selection is constrained to architectures with available pretrained weights.
- **Risks**: Pretrained weights may not generalize well to pothole-specific features.
- **Revisit conditions**: If fine-tuning underperforms significantly, training from scratch may be evaluated.
- **Status**: LOCKED

---

## D-004: Candidate-Model Comparison

- **Date**: 2026-09-17
- **Problem**: Which model architectures should be evaluated?
- **Context**: Multiple detector architectures exist with different trade-offs.
- **Options considered**: YOLO11s, YOLO26s, RF-DETR-S, other architectures.
- **Evidence**: YOLO26 is a recent candidate, YOLO11 provides a baseline, RF-DETR offers a transformer-based challenger.
- **Decision**: Evaluate YOLO11s, YOLO26s, and RF-DETR-S as candidate models.
- **Why**: These represent different architectural paradigms (CNN-based YOLO, newer YOLO, transformer-based DETR).
- **Rejected alternatives**: Locking a single model prematurely.
- **Consequences**: The final model is not yet selected; evaluation will determine the best candidate.
- **Risks**: Evaluation must be fair and rigorous to avoid bias toward one architecture.
- **Revisit conditions**: After evaluation, the final model is selected based on the full criteria.
- **Status**: LOCKED (candidates selected; final model OPEN)

---

## D-005: Indian + Forward-Camera Dataset Priority (CORRECTED)

- **Date**: 2026-09-17
- **Problem**: What dataset characteristics are required?
- **Context**: The system must work on Indian roads with forward-facing cameras.
- **Options considered**: Any dataset, Indian-specific datasets, forward-camera datasets, both.
- **Evidence**: The deployment target is Indian roads with forward-facing vehicle cameras. **CRITICAL CORRECTION**: Previous audit incorrectly assumed RDD2022 was India-only with YOLO format and 4,500 images. Verification established RDD2022 is multi-national (6 countries) with Pascal VOC XML, 47,420 total images, and a 9,665-image India subset.
- **Decision**: Prioritize datasets with Indian relevance and forward-camera relevance.
- **Why**: The system must generalize to the target deployment environment.
- **Rejected alternatives**: Using datasets from unrelated domains without validation.
- **Consequences**: Dataset candidates must be audited for Indian road conditions and forward-camera imagery.
- **Risks**: Available Indian datasets may be limited in size or quality.
- **Revisit conditions**: After dataset audit, the exact dataset combination may be adjusted.
- **Status**: LOCKED (priority direction; exact dataset OPEN). **CORRECTED**: RDD2022 is multi-national, not India-only.

---

## D-006: Group-Based Leakage Prevention

- **Date**: 2026-09-17
- **Problem**: How should data be split to prevent information leakage?
- **Context**: Frames from the same source video are strongly correlated.
- **Options considered**: Random split, group-based split, time-based split.
- **Evidence**: Random splits can leak correlated frames into both training and test sets, inflating metrics.
- **Decision**: Use group-based splitting where frames from the same source video do not cross train/test boundaries.
- **Why**: Prevent overoptimistic evaluation metrics from correlated data.
- **Rejected alternatives**: Random splitting (leads to leakage).
- **Consequences**: Train/test splits must be constructed at the video/source level.
- **Risks**: May reduce effective training data if sources are few.
- **Revisit conditions**: After source identification and grouping are complete.
- **Status**: LOCKED

---

## D-007: Model/Application Adapter Boundary

- **Date**: 2026-09-17
- **Problem**: How to protect the application from framework-specific model details?
- **Context**: The model could be YOLO, RF-DETR, or a future architecture.
- **Options considered**: Expose model objects directly, use an adapter/boundary, use a framework-agnostic inference server.
- **Evidence**: Exposing framework-specific objects throughout the repository creates tight coupling and prevents model swapping.
- **Decision**: Place a project-owned model adapter between the model and the rest of the system.
- **Why**: The detector can later be replaced without rewriting the rest of the application.
- **Rejected alternatives**: Direct dependency on framework-specific model objects.
- **Consequences**: The inference module owns the adapter; other modules depend on the project's detection contract.
- **Risks**: The adapter must be well-designed to avoid becoming a bottleneck.
- **Revisit conditions**: When the final model is selected and the adapter is implemented.
- **Status**: LOCKED

---

## D-008: Detection vs Tracking Separation

- **Date**: 2026-09-17
- **Problem**: How to separate detection and tracking responsibilities?
- **Context**: Detection and tracking are distinct technical problems with different requirements.
- **Options considered**: Combine detection and tracking, separate them into distinct modules.
- **Evidence**: Detection is a per-frame problem; tracking is a temporal association problem. They have different interfaces and can evolve independently.
- **Decision**: Keep detection and tracking as separate responsibilities.
- **Why**: Each component can be developed, tested, and replaced independently.
- **Rejected alternatives**: Combining detection and tracking into a single module.
- **Consequences**: The detector outputs detections; the tracker consumes detections and produces tracks.
- **Risks**: Interface between detection and tracking must be well-defined.
- **Revisit conditions**: When the tracker is designed.
- **Status**: LOCKED

---

## D-009: Detection vs Event Separation

- **Date**: 2026-09-17
- **Problem**: Is every detection a reportable pothole event?
- **Context**: A frame-level detection is not automatically a reportable event.
- **Options considered**: Treat every detection as an event, add an event engine to filter/aggregate detections.
- **Evidence**: Detections are noisy and temporary; events represent logical occurrences that warrant reporting.
- **Decision**: A frame-level detection is NOT automatically a reportable pothole event. An event engine handles the conversion.
- **Why**: Prevents flooding the system with transient detections that are not real pothole occurrences.
- **Rejected alternatives**: Directly promoting every detection to an event.
- **Consequences**: The event engine is a separate downstream component that must be designed.
- **Risks**: Event confirmation rules are not yet defined.
- **Revisit conditions**: When the event engine is designed.
- **Status**: LOCKED

---

## D-010: Live-Camera Freshness Principle

- **Date**: 2026-09-17
- **Problem**: How to handle live-camera inference?
- **Context**: For live inference, freshness is more important than preserving an unlimited backlog of stale frames.
- **Options considered**: Unbounded queues, bounded buffering, drop-frame strategies.
- **Evidence**: Unbounded queues can lead to memory exhaustion and processing stale data.
- **Decision**: Use bounded buffering and prioritize freshness over an unlimited backlog.
- **Why**: Live inference must respond to current conditions, not old frames.
- **Rejected alternatives**: Unbounded queues (risk of resource exhaustion).
- **Consequences**: The inference runtime must implement bounded buffers.
- **Risks**: May drop frames under high load.
- **Revisit conditions**: When the runtime is designed.
- **Status**: LOCKED

---

## D-011: Explicit Failure States

- **Date**: 2026-09-17
- **Problem**: How should the system handle failures?
- **Context**: The system must handle errors gracefully and explicitly.
- **Options considered**: Silent failures, generic error handling, explicit failure states.
- **Evidence**: Explicit failure states make debugging and monitoring easier.
- **Decision**: Include explicit failure states in the system design.
- **Why**: Reliability requires that failures are visible and handled.
- **Rejected alternatives**: Silent failures or unhandled exceptions.
- **Consequences**: All components must define and handle their failure states.
- **Risks**: May add complexity to component interfaces.
- **Revisit conditions**: When reliability engineering begins.
- **Status**: LOCKED

---

## D-012: Initial Scalability Strategy

- **Date**: 2026-09-17
- **Problem**: What is the initial deployment architecture?
- **Context**: The system must start somewhere and scale later.
- **Options considered**: Distributed from day one, single-machine first, cloud-native from the start.
- **Evidence**: A single-camera, single-machine deployment is the simplest starting point.
- **Decision**: Start with single-camera, single-machine deployment. Future paths include centralized inference, multiple cameras, and partitioned inference workers.
- **Why**: Simplicity at the start reduces risk and allows the core ML pipeline to be validated.
- **Rejected alternatives**: Distributed or Kubernetes-based deployment from the start.
- **Consequences**: The initial deployment is simple; scalability is a future concern.
- **Risks**: May need to refactor for distributed deployment later.
- **Revisit conditions**: When operational requirements demand scaling.
- **Status**: LOCKED

---

---

## D-013: Project Data Contract Coordinate Convention

- **Date**: 2026-09-21
- **Problem**: What coordinate convention should the project use for bounding boxes across datasets?
- **Context**: Candidate datasets may use different annotation formats (YOLO center format, COCO, etc.).
- **Options considered**: YOLO center format, COCO format, project pixel format.
- **Evidence**: Dataset audit (docs/DATASET_AUDIT.md) shows RDD2022 uses Pascal VOC XML format, and other datasets may use different formats.
- **Decision**: Use a project-owned pixel coordinate convention: `[x1, y1, x2, y2]` in pixel coordinates with top-left origin.
- **Why**: This is model-independent, simple to validate, and can be converted from any source format.
- **Rejected alternatives**: Using a framework-specific format (e.g., YOLO center format) as the project contract.
- **Consequences**: All datasets must be converted to the project pixel format during preparation.
- **Risks**: Conversion errors may introduce annotation issues; validation is required.
- **Revisit conditions**: If a specific training framework requires a different format, the conversion layer must handle it.
- **Status**: LOCKED PRINCIPLE

---

## D-014: Single Pothole Class Representation

- **Date**: 2026-09-21
- **Problem**: How should the project represent the pothole class across datasets?
- **Context**: Candidate datasets may have different class names for potholes.
- **Options considered**: Multiple class names, single canonical "pothole" class, per-dataset class mapping.
- **Evidence**: Dataset audit (docs/DATASET_AUDIT.md) shows RDD2022 directly represents pothole as a class, and other datasets may have different class semantics.
- **Decision**: Use a single canonical "pothole" class in the project data contract.
- **Why**: This keeps the project model-independent and avoids framework-specific class naming.
- **Rejected alternatives**: Using per-dataset class names in the project contract.
- **Consequences**: Class normalization is required during dataset preparation.
- **Risks**: Some datasets may have ambiguous or different pothole definitions; annotation inspection is required.
- **Revisit conditions**: If annotation inspection reveals that datasets represent fundamentally different defect types, the class mapping must be revisited.
- **Status**: LOCKED PRINCIPLE

---

## D-015: Class-Mapping Strategy

- **Date**: 2026-09-22
- **Problem**: How should the 9-class Kaggle-derived RDD2022 India artifact be mapped to the project's pothole-detection goal, given that the official CRDDC task uses only 4 classes?
- **Context**: The local artifact contains 9 classes (D00, D01, D10, D11, D20, D40, D43, D44, D50), but the official CRDDC'2022 task uses exactly {D00, D10, D20, D40}. D43/D44 are road-marking damage (white line blur, crosswalk blur) from RDD2018, and D50 has unknown provenance (annotation artifact — duplicate D40 in India_007909).
- **Options considered**:
  - **Strategy A**: D40-only single-class pothole detector
  - **Strategy B**: Four-class road-damage detector (official CRDDC task) — SELECTED
  - **Strategy C**: D40 + crack binary detector
  - **Strategy D**: Full 8-class RDD taxonomy detector (excludes D50)
- **Evidence**: docs/DATASET_AUDIT.md §18.15.2a, §18.15.5, §18.19; R-009; docs/CLASS_MAPPING.md
- **Decision**: Strategy B (official CRDDC 4-class task). D43/D44 excluded (road-marking damage, not structural). D50 excluded (annotation artifact, no official provenance, 100% D40 co-occurrence). D01 → D00 (construction joint variant of longitudinal crack). D11 → D10 (construction joint variant of transverse crack).
- **Why**: Aligns with official benchmark; excludes non-structural classes; standardizes evaluation; D50 confirmed as annotation artifact (duplicate D40 bbox in India_007909); D01/D11 are explicitly defined as subtypes of D00/D10 in RDD2018 paper (Arya et al. 2022, Table 1); merging preserves 34 crack objects rather than losing them; construction joints are still longitudinal/transverse cracks (location attribute, not different damage type)
- **Rejected alternatives**: Strategy A (too narrow for road-damage context); Strategy C (collapses crack subtypes, still no negatives); Strategy D (D43/D44 are rare road markings, not structural damage); D01/D11 exclusion (would lose 34 crack objects and hard-negative information)
- **Consequences**: Class mapping is resolved before annotation conversion, YOLO label generation, or model training; D50 must be excluded from all annotations; D43/D44 must be excluded; D01 and D11 are deterministic merges to D00 and D10 respectively; raw XML files remain unchanged; normalized output written to separate directory
- **Risks**: Selection bias still HIGH (100% D40-positive images); no D40-negative examples in artifact; D01/D11 merge merges construction joint context into parent class (location info lost at class level but preserved in raw annotations until normalization)
- **Revisit conditions**: If official India data becomes accessible (re-run selection-bias analysis); if project scope changes to include road markings; if D50 is confirmed as a legitimate class; if D01/D11 object counts grow significantly and construction joint patterns warrant separate treatment
- **Status**: LOCKED

### D-015.1 Final Class Mapping

| Raw class | Final project class | Action | Reason |
|-----------|---------------------|--------|--------|
| D00 | 0 / longitudinal_crack | KEEP | Official CRDDC class; longitudinal road crack |
| D01 | 0 / longitudinal_crack | MERGE → D00 | Construction joint variant of D00 (Arya et al. 2022); same damage type, different location |
| D10 | 1 / transverse_crack | KEEP | Official CRDDC class; transverse road crack |
| D11 | 1 / transverse_crack | MERGE → D10 | Construction joint variant of D10 (Arya et al. 2022); same damage type, different location |
| D20 | 2 / alligator_crack | KEEP | Official CRDDC class; alligator/connected crack pattern |
| D40 | 3 / pothole | KEEP | Official CRDDC class; pothole/rutting/bump/separation |
| D43 | — | EXCLUDE | Road marking damage (white line blur); not structural road damage |
| D44 | — | EXCLUDE | Road marking damage (crosswalk blur); not structural road damage |
| D50 | — | EXCLUDE | Annotation artifact; no official source; 100% D40 co-occurrence; near-identical bbox to D40 in India_007909 |

### D-015.2 Annotation-Level Rules

- Every retained object receives exactly one final project class ID (0–3)
- D01 annotations → class 0 (longitudinal_crack)
- D11 annotations → class 1 (transverse_crack)
- D43/D44/D50 annotations are excluded; never become positive labels
- Excluded annotations are logged but NOT deleted from raw files
- Bounding-box coordinates preserved exactly for retained objects
- No object is silently duplicated or silently lost (except D43/D44/D50 via explicit rule)
- Raw annotation files remain unchanged

### D-015.3 Image-Level Rules

- **Case A** (D40 + excluded annotations): Image retained; D40 object kept; excluded objects logged; image is positive sample
- **Case B** (D40 + other retained classes): Image retained; all retained objects kept with final project class IDs; multi-class image for evaluation
- **Case C** (only excluded annotations): Image retained but becomes annotation-empty; logged; excluded from training/evaluation; may serve as background for future hard-negative mining
- **Case D** (only retained non-D40 classes): Image retained; all objects kept; no D40 → negative sample for pothole detection; crack-only image for crack/pothole distinction
- **General**: No image automatically deleted; annotation-empty images retained but excluded from training/evaluation; all exclusion decisions logged with reason

### D-015.4 Canonical Project Classes

| Project ID | Class Name | Description | Source |
|------------|------------|-------------|--------|
| 0 | longitudinal_crack | Linear cracks aligned with direction of travel | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 1 | transverse_crack | Cracks perpendicular to direction of travel | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 2 | alligator_crack | Interconnected cracks forming alligator-skin pattern | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |
| 3 | pothole | Pothole, rutting, bump, separation (CRDDC "Other Corruption") | RDD2018/RDD2022 taxonomy; Arya et al. 2022 |

### D-015.5 Transformation Invariants

1. Raw files remain unchanged (read-only conversion)
2. Every retained object has exactly one final project class ID (0–3)
3. Excluded objects never become positive labels
4. Bounding-box coordinates preserved (no coordinate transformation at this stage)
5. Image pixels unchanged
6. Image/annotation relationships remain valid (every image has corresponding annotation, even if empty)
7. No object silently duplicated
8. No object silently lost except through explicit exclusion rule for D43/D44/D50
9. D01 → class 0, D11 → class 1 (deterministic merge, no ambiguity)
10. All mapping decisions logged per-object and per-image

### D-015.6 Audit Requirements

Transformation tool MUST report: source image count, source object count, count by raw class, count by final project class, excluded annotation count, images becoming annotation-empty, invalid annotations encountered, images skipped, reason for each skip.

### D-015.7 Output Data Contract

- Image location: `normalized_rdd2022_india/images/{train,val}/<image_id>.jpg`
- Label location: `normalized_rdd2022_india/labels/{train,val}/<image_id>.txt` (or .xml, format TBD)
- Class IDs: 0 = longitudinal_crack, 1 = transverse_crack, 2 = alligator_crack, 3 = pothole
- Coordinate convention: Project pixel format [x1, y1, x2, y2] with top-left origin (per D-013)
- Metadata: class_mapping.json, provenance.json, manifest.json
- Provenance fields: source_id, dataset_version, split_version, provenance, license, checksum

---

## D-006-R1: Group Identification When Source Metadata Is Absent (PROPOSED)

- **Date**: 2026-09-26
- **Parent decision**: D-006 (Group-Based Leakage Prevention)
- **Status**: **PROPOSED — NOT APPLIED.** Requires explicit approval. D-006 remains LOCKED and unmodified.
- **Trigger**: Sequence/group identification investigation (DATASET_AUDIT.md §18.20) found that the RDD2022 India artifact contains **no** sequence, video, trip, camera, or timestamp metadata of any kind, falsifying D-006's implicit implementation assumption that such identifiers would be available.

### Evidence

| Finding | Value |
|---------|-------|
| XML attributes in any of 1,530 annotations | NONE |
| Non-standard XML tags | NONE (18 standard Pascal VOC tags only) |
| Grouping directory level | NONE |
| Filename pattern | `India_<flat index>`, no embedded grouping |
| Index sparsity | 84.52% of the 5..9,890 span is absent |
| Exact duplicates (SHA-256) | 0 |
| Pixel-verified near-duplicate groups | 59 groups, 121 images, max size 3 |
| Neighbor correlation (+1/+2/+5/+10) | Null; +1 is 1.88% *farther* than random |
| Near-duplicate index gap | Median 2,643; only 1 of 583 pairs within 10 |

### Problem with D-006 as written

D-006 requires that "frames from the same source video do not cross train/test boundaries." For
this artifact, the grouping unit that D-006 presupposes **does not exist and cannot be
reconstructed** from the available data. Applying a random split would satisfy the letter of
D-006 vacuously while providing no leakage protection, and would risk reporting leakage-free
metrics that are not leakage-free.

### Proposed refinement (exact text to add to D-006)

> **Implementation fallback when source group identifiers are unavailable.**
>
> Where a dataset provides no sequence, video, trip, camera, or timestamp metadata, the
> group-based splitting principle is satisfied only to the extent that evidence allows, and the
> following rules apply:
>
> 1. Group units are derived from **verified content identity** — exact duplicates (SHA-256)
>    and pixel-verified near-duplicate clusters — and these clusters are assigned as **atomic
>    units** that may not straddle train/validation/test boundaries.
> 2. **Filename index proximity must never be used as a proxy for sequence membership.** This
>    was empirically falsified for the RDD2022 India artifact (§18.20.5).
> 3. Where no grouping information can be established at all, the resulting **residual leakage
>    risk must be recorded as unquantifiable rather than assumed to be zero**, and the split
>    must be documented as a known limitation of any resulting metric.
> 4. Metrics produced under such a split must carry an explicit caveat that group-level
>    isolation could not be verified.

### What this refinement does NOT do

- It does not weaken or replace D-006's principle
- It does not authorize random splitting as "good enough"
- It does not assert that the near-duplicate clusters are source sequences
- It does not claim the residual risk is bounded

### Alternatives considered and rejected

| Alternative | Why rejected |
|-------------|--------------|
| Silently switch to random splitting | Would produce falsely reassuring metrics; hides an unquantifiable risk |
| Group by filename index blocks (e.g. blocks of 100) | §18.20.5 shows index adjacency carries no correlation signal; would create false groups and reduce effective sample size for no benefit |
| Treat all 59 near-duplicate clusters as sequences | Over-claims: visual identity does not establish common capture |
| Drop the 121 clustered images | Destroys 7.9% of an already small, selection-biased dataset to solve an unquantifiable problem |
| Block splitting by index to guarantee isolation | Assumes a capture ordering that §18.20.5 provides no evidence for |

### Revisit conditions

- The official RDD2022 India release becomes accessible and provides sequence metadata
- A different candidate dataset supplies verifiable group identifiers
- CLIP/DINOv2 embedding analysis establishes semantic correlation that perceptual hashes miss

### Evidence

`docs/DATASET_AUDIT.md` §18.20; `experiments/dataset/normalized_rdd2022_india/group_analysis/SYNTHESIS.md`;
R-011.

---

---

## D-019: Experiment 2 — China Correlation Cluster Exclusion from Val Pool

- **Date**: 2026-10-03
- **Problem**: Random stratified val selection repeatedly selected China images that formed near-duplicate pairs with train images, causing persistent G15 failures.
- **Context**: The correlation graph contained 32 China images in 14 components. Random val selection (seed 42) kept picking images from these components that had other members in train.
- **Evidence**: 4 cross train/val pairs persisted across multiple rebuilds. All were China-China pairs. The 25 "frozen_test" pairs are internal to frozen test, not cross-contamination.
- **Decision**: Identify all China images participating in any correlation cluster (32 images, 14 components) and exclude them from the val selection pool. These images remain in train.
- **Why**: The correlation criterion (corr ≥ 0.9, MAD ≤ 0.1) is a hard failure. When random val selection repeatedly picks from the same correlation clusters, the only robust fix is to remove the entire clusters from val eligibility.
- **Consequences**: 32 China images excluded from val pool. Total excluded from val: 39 images (9 initial + 32 China). Train pool reduced from 20,955 to 20,916. Val selected from remaining pool.
- **Status**: LOCKED

---

## D-016: Experiment 2 — Controlled Data-Distribution Experiment Design

- **Date**: 2026-10-03
- **Problem**: How to isolate the effect of expanding training distribution from India-only to multi-national?
- **Context**: Experiment 1 trained on 1,071 India-only images (3,049 objects). Experiment 2 adds Dataset B non-India images (18,650 images, 33,289 objects from 5 countries).
- **Options considered**:
  - Option A: Initialize from original pretrained YOLO11s (identical to Exp 1)
  - Option B: Initialize from Experiment 1's best.pt
- **Evidence**: Option A provides a clean data ablation (only training data changes). Option B varies both data and initialization, making attribution impossible. Experiment 1's best.pt encodes zero-negative prior (anti-aligned with Exp 2's 25% negatives) and degenerate transverse_crack head.
- **Decision**: **Option A — original pretrained YOLO11s initialization** (identical to Experiment 1).
- **Why**: Only the training distribution changes. All other factors (architecture, initialization, hyperparameters, evaluation set) are held fixed.
- **Rejected alternatives**: Option B (continuing from Exp 1 best.pt) — varies two factors simultaneously, inherits degenerate priors, efficiency gain (~3%) doesn't justify interpretive cost.
- **Consequences**: Experiment 2 runs ~30× more optimizer steps (49,600 vs 1,675) at same epoch budget. This step-count confound (C2) must be reported alongside results.
- **Risks**: Longer training time (~82 h vs ~2.9 h for Exp 1). Step-count confound cannot be separated from data effect in a single run.
- **Revisit conditions**: If training budget proves prohibitive, reduce epochs (not switch to Option B) and record new C2 magnitude.
- **Status**: LOCKED

---

## D-017: Experiment 2 — India Exclusion and Frozen Test Protection

- **Date**: 2026-10-03
- **Problem**: How to prevent India contamination in Experiment 2 training/validation?
- **Context**: Dataset B contains 7,706 India images. Experiment 2 must use only non-India Dataset B. The frozen 230-image India test set must remain completely isolated.
- **Evidence**: Country audit identified 7,706 India images in Dataset B. India exclusion removed all 7,706. Leakage audit verified 0 SHA256 overlap between Experiment 2 and frozen test. 4 near-duplicate pairs cross train/val (Dataset B non-India); 25 pairs within frozen test (not cross-contamination).
- **Decision**: Exclude ALL Dataset B India images (7,706). Use only non-India Dataset B (30,679 images). Frozen test (230 India images) is NEVER used during training.
- **Why**: Experiment 2 is a distribution-expansion experiment; adding India data back would confound the comparison. Frozen test is the measurement instrument for both experiments.
- **Consequences**: 7,706 India images excluded. Experiment 2 train = 1,071 (Dataset A) + 18,650 (Dataset B non-India) = 19,721 images.
- **Status**: LOCKED (with G15 residual leakage documented)

---

## D-018: Experiment 2 — Near-Duplicate Leakage Threshold

- **Date**: 2026-10-03
- **Problem**: What near-duplicate threshold defines train/val leakage?
- **Context**: RDD2022 uses random per-image splits. Near-duplicate frames from same video can land in different splits. Project standard: correlation ≥ 0.9 AND MAD ≤ 0.1 on 64×64 grayscale.
- **Evidence**: Initial audit found 106 train/val crossing pairs. Iterative removal reduced to 4 pairs. The 25 "frozen_test" pairs are within frozen test itself. Final resolution: excluded entire correlation clusters (39 images) from val selection pool.
- **Decision**: Correlation criterion (corr ≥ 0.9, MAD ≤ 0.1) is the hard failure threshold. dHash screen (Hamming ≤ 5) is secondary signal only. When cross-split near-duplicates form connected components, entire components are excluded from val selection.
- **Why**: Matches the project's established correlation methodology (analysis/verify_near_duplicates.py). Exact deduplication is insufficient for perceptual leakage.
- **Consequences**: 0 cross train/val near-duplicate pairs remain. Frozen test is clean. 39 images excluded from val pool (remain in train).
- **Status**: LOCKED (resolved)