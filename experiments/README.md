# Experiments

This directory tracks all experimental work for the project.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `dataset/` | Dataset audits, manifests, split records |
| `training/` | Training experiment records |
| `evaluation/` | Evaluation results and reports |
| `benchmarks/` | Runtime/performance measurements |

## Experiment Discipline

All experiments must follow the discipline documented in:

- `docs/MODEL_TRAINING.md` — Reproducibility metadata requirements
- `docs/MODEL_EVALUATION.md` — Required metrics and evaluation protocol
- `docs/DATA_PIPELINE.md` — Dataset preparation and leakage prevention

## Recording Experiments

Each experiment should record the metadata specified in `docs/MODEL_TRAINING.md#Reproducibility Metadata`.

## Status

- Experiment tracking infrastructure: **NOT STARTED**
- First experiments: **NOT STARTED**