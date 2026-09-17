# Model Training

## Primary Training Philosophy

```text
pretrained initialization
  ↓
fine-tuning
  ↓
our pothole dataset
```

The primary training strategy is to start from pretrained weights and fine-tune on the project's pothole dataset. This leverages general visual features learned on large-scale datasets and adapts them to the specific characteristics of pothole detection.

**Status**: This is a LOCKED STRATEGY. It is the chosen architectural direction for training. It is **not** an empirically verified claim that it beats training from scratch on our exact dataset. A controlled comparison with training from scratch may be evaluated later as a secondary experiment.

## Secondary Experiment

Training from scratch may be evaluated as a controlled comparison. This is a secondary experiment to be run **only when**:

- The fine-tuning baseline shows room for improvement.
- The dataset characteristics suggest transfer learning is insufficient.
- The project has sufficient data and compute to justify the comparison.

**Status**: NOT STARTED. This is not currently being performed.

## Model Candidates

The current candidate models are:

| Model | Role | Status |
|-------|------|--------|
| YOLO11s | Baseline | Candidate |
| YOLO26s | Primary candidate | Candidate |
| RF-DETR-S | Transformer challenger | Candidate |

**Critical**: YOLO26 is the primary candidate; YOLO11 is the baseline; RF-DETR is the transformer challenger. The final production/deployment model has NOT yet been selected. These are candidate roles, not proof that any model is the final winner.

## Experiment Discipline

For model comparison, all experiments must use:

- Same dataset (version)
- Same split (group-based, same version)
- Comparable input conditions (image size, preprocessing)
- Same evaluation protocol (see MODEL_EVALUATION.md)

This ensures that differences in performance are attributable to the model architecture rather than experimental setup.

## Baseline Definition

A baseline experiment must:

- Use the smallest viable candidate model (e.g., YOLO11s).
- Use default hyperparameters from the model's documentation (not tuned).
- Record all reproducibility metadata.
- Report all required metrics (see MODEL_EVALUATION.md).
- Serve as the performance floor for more advanced experiments.

The first experiment to complete is the baseline. Subsequent candidate models are compared against this baseline.

## Initialization Strategy

| Strategy | Description | Status | When Used |
|----------|-------------|--------|-----------|
| Pretrained + fine-tuning | Start from pretrained weights, fine-tune on pothole dataset | LOCKED (strategy) | Default |
| Random initialization | Initialize weights randomly, train from scratch | OPEN (secondary) | Controlled comparison only |

## Training Variables Table

| Parameter | Current State | How Decided | Notes |
|-----------|---------------|-------------|-------|
| model size | OPEN | benchmark | Smallest adequate model preferred |
| input size | OPEN | dataset + runtime | Must be consistent with training |
| batch size | OPEN | hardware | Constrained by GPU memory |
| epochs | OPEN | validation/early stopping | Early stopping based on validation metrics |
| optimizer | OPEN/default-first | training behavior | Default from model framework first |
| augmentation | OPEN | domain realism | Must not break class semantics |
| learning rate | OPEN | baseline recipe/tuning | Start with documented defaults |
| seed | required for reproducibility | fixed per experiment | Record seed for reproducibility |
| checkpoint path | OPEN | training output | Not committed to Git |
| hardware | OPEN | available | Record for reproducibility |
| software versions | OPEN | available | Record for reproducibility |

## Checkpoint Selection

"Best model" is defined by the evaluation protocol (see MODEL_EVALUATION.md), not by any single metric. Checkpoints must record:

- Validation metrics at that epoch.
- Training time and resource usage.
- Inference latency (post-training benchmark).

The checkpoint selected is the one that best satisfies the multi-criteria selection rule, not necessarily the one with the highest mAP.

## Experiment ID Naming Convention

```text
{model}_{dataset_v}{split_v}_{timestamp}
```

Example: `yol26s_dataset_v1_split_a_20260917`

Experiment IDs must be used consistently across `experiments/training/`, `experiments/evaluation/`, and `experiments/benchmarks/`.

## Artifact Metadata

Model artifacts include:

- **Checkpoint file**: Contains trained weights (not committed to Git).
- **Metadata file**: JSON/YAML with all reproducibility metadata (see Reproducibility Metadata section below).
- **Artifact hash**: Cryptographic hash of the checkpoint for provenance verification.
- **Artifact location**: Path to external storage (not in Git).

Artifact metadata is recorded in `experiments/training/` manifest files (metadata only; binary artifacts excluded from Git).

## Reproducibility Metadata

Each serious experiment must record the following metadata (stored in experiment manifest, not in Git as binary):

- experiment_id
- dataset_version
- split_version
- model (architecture name)
- checkpoint (hash and external path)
- image_size
- batch_size
- optimizer
- learning_rate
- epochs (actual, or early stopping epoch)
- augmentation (configuration)
- seed
- hardware (GPU/CPU model)
- software versions (framework, CUDA, Python)
- git_commit (the repository commit used for training)
- metrics (link to evaluation report)
- artifact (link to checkpoint location)

## Conditional Experiments

The following experiments are conditional on observed failure modes:

- **YOLO26 P2**: A different variant of YOLO26 (if available).
- **Larger model size**: If small model underfits.
- **Different augmentation**: If current augmentations are insufficient for domain diversity.
- **Different optimizer**: If default optimizer behaves poorly.

These are NOT committed experiments at this stage. They are only considered after observed failure modes justify them.

## Status Summary

- **Primary strategy**: `LOCKED` (pretrained initialization → fine-tuning)
- **Candidate models**: `EXPERIMENTAL` (candidate roles; final model `OPEN`)
- **Training implementation**: `NOT STARTED`
- **Experiments run**: `NOT STARTED`
- **Final model**: `OPEN`

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*