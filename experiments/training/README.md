# Training Experiments

This directory contains training experiment records.

## Purpose

- Record all training runs for reproducibility
- Track model configurations and hyperparameters
- Store training metrics and logs (outside Git)
- Compare model candidates (YOLO11s, YOLO26s, RF-DETR-S)

## Reproducibility Metadata

Each experiment must record (see `docs/MODEL_TRAINING.md`):

- experiment_id
- dataset_version
- split_version
- model
- checkpoint (path/hash, not binary)
- image_size
- batch_size
- optimizer
- learning_rate
- epochs
- augmentation
- seed
- hardware
- software versions
- git commit
- metrics
- artifact location (external)

## Status

- Training: **NOT STARTED**
- First training run: **NOT STARTED**

## Important

Do not commit model checkpoints or large binary files to this directory. Store artifact paths/hashes and record them here.