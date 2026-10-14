# Model Training

## Primary Strategy (LOCKED)

**Pretrained initialization → fine-tuning** of YOLOv11s on the project dataset. This is the locked architectural direction — it is not an empirically verified claim that it beats training from scratch on our exact dataset.

## Verified Training Commands

### Baseline Training (Experiment 1)

```bash
# Runs YOLO11s on Dataset A (1,071 India-only images, 3,049 objects)
python experiments/training/run_baseline.py
```

**Configuration**: `yolo11s.pt`, 100 epochs, batch 16, imgsz 720, seed 42, device 0, optimizer auto, AMP true, early stopping patience 50.

### Experiment 2 Training (Combined Dataset)

```bash
# Runs YOLO11s on Dataset A + Dataset B non-India (19,721 images, 36,358 objects)
python experiments/training/run_baseline.py
```

**Configuration**: Same hyperparameters as baseline; data config at `experiments/dataset/experiment2/data.yaml`. Training budget: ~81 hours (100 epochs, ~49,600 optimizer steps).

### Resume Training (Experiment 2 → 100 Epochs)

```bash
# Resumes from epoch-72 checkpoint, continues to epoch 82
python experiments/training/resume_realworld_finetune.py
```

**Configuration**: Loads `last.pt` from `runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt` with `resume=True` (restores optimizer state), lr0=0.001, batch 16, imgsz 720, device 0, workers 2, AMP true, seed 42, deterministic true, patience 20.

## Candidate Models (EXPERIMENTAL)

| Model      | Role         | Status     |
|------------|--------------|------------|
| YOLO11s    | Baseline     | Candidate  |
| YOLO26s    | Primary      | Candidate  |
| RF-DETR-S  | Transformer  | Candidate  |

**Critical**: The final production/deployment model has NOT yet been selected. These are candidate roles, not proof that any model is the final winner.

## Training Configuration (baseline_config.yaml)

| Parameter        | Value           | Notes                              |
|------------------|-----------------|------------------------------------|
| Model            | yolo11s.pt      | Pretrained COCO initialization     |
| Epochs           | 100             | Early stopping based on validation |
| Batch size       | 16              | Safe for RTX 4050 (~5.5 GB peak)   |
| Image size       | 720             | Must be consistent with preprocessing |
| Device           | 0 (GPU)         | CUDA device                        |
| Optimizer        | auto            | Default from Ultralytics           |
| Seed             | 42              | Required for reproducibility       |
| Workers          | 0               | Minimal (avoid data-loading issues) |
| Augmentation     | RandAugment     | Domain realism — must not break class semantics |
| Learning rate    | lr0=0.01, lrf=0.01 | Default first-step, cosine decay   |
| Warmup epochs    | 3.0             | Warmup momentum 0.8, bias lr 0.1   |
| Mosaic           | 1.0             | Domain realism augmentation        |
| Close mosaic     | 10              | Disabled late in training          |
| Verbose          | True            | Full experiment logging            |
| Deterministic    | True            | cuDNN deterministic mode           |
| Coordinate remap | True            | cls_remap enables D01/D11 → D00/D10 merge |
| Rect             | False           | No rectangular training            |
| Cache            | False           | No image caching during training   |
| Val              | True            | Validation split evaluation        |
| Plots            | True            | Training/loss/precision plots      |

## Experiment ID Naming Convention

```text
{model}_{dataset_v}{split_v}_{timestamp}
```

Example: `yolo11s_dataset_v1_split_a_20260917`

## Checkpoint Selection

"Best model" is defined by the evaluation protocol (see MODEL_EVALUATION.md), not by any single metric. Checkpoints must record:

- Validation metrics at that epoch.
- Training time and resource usage.
- Inference latency (post-training benchmark).

The checkpoint selected is the one that best satisfies the multi-criteria selection rule, not necessarily the one with the highest mAP.

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

- **Primary strategy**: LOCKED (pretrained initialization → fine-tuning)
- **Candidate models**: EXPERIMENTAL (candidate roles; final model OPEN)
- **Training implementation**: NOT STARTED
- **Experiments run**: NOT STARTED
- **Final model**: OPEN

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*