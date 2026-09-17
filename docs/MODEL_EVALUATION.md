# Model Evaluation

## Overview

Model evaluation provides a rigorous, multi-dimensional assessment of candidate detectors. It is not limited to a single metric. The evaluation protocol is designed to support objective model comparison and to identify failure modes before deployment.

## Required Metrics

### Core Metrics

| Metric | Definition | Status |
|--------|-----------|--------|
| Precision | TP / (TP + FP) | Required |
| Recall | TP / (TP + FN) | Required |
| F1 | 2 × (Precision × Recall) / (Precision + Recall) | Required |
| IoU | Intersection over Union between predicted and ground-truth bounding boxes | Required |
| AP | Average Precision at a specific IoU threshold | Required |
| mAP50 | Mean AP at IoU = 0.50 | Required |
| mAP75 | Mean AP at IoU = 0.75 | Required |
| mAP50-95 | Mean AP averaged over IoU thresholds from 0.50 to 0.95 (step 0.05) | Required |

All metrics must be computed per class (pothole) and reported as an aggregate.

### Dataset-Level Evaluation

Evaluation is performed on:

- **Validation set**: Used for hyperparameter tuning, checkpoint selection, and model comparison.
- **Test set**: Used for final model selection and held-out evaluation (after model selection is complete).
- **Unseen Indian-domain set**: A separate held-out set from a different geographic region or source, used to assess generalization.
- **Cross-domain set**: A separate set with different camera/lighting/weather conditions, used to assess robustness.

## Small-Object Evaluation

Potholes are often small in the frame. Evaluation must include small-object analysis.

**Size category determination**: Size categories will be determined during dataset inspection based on the actual distribution of pothole bounding box areas in the dataset. Do not invent thresholds until dataset inspection is complete.

**Planned approach**:
- Compute bounding box area (width × height) for each annotation.
- Compute the distribution of areas.
- Define size categories (small, medium, large) based on percentiles or natural breaks in the distribution.
- Report mAP per size category.

## False-Positive Taxonomy

Candidate categories for false positives (not assumed actual distribution; framework for classification):

- **Shadow**: Dark regions on the road surface.
- **Manhole**: Circular or rectangular road features.
- **Road patch**: Repair patches or markings.
- **Water**: Puddles or standing water.
- **Crack**: Linear surface cracks.
- **Stain**: Discoloration or oil stains.
- **Other**: Unidentified false positives.

Each false positive should be classified into one of these categories during qualitative analysis. The taxonomy is **OPEN** pending dataset inspection.

## False-Negative Taxonomy

Candidate categories for false negatives:

- **Small/distant**: Pothole too small to detect reliably.
- **Low contrast**: Pothole blends with surrounding road.
- **Blur**: Motion blur or camera shake.
- **Occlusion**: Pothole partially hidden by vehicles, shadows, or objects.
- **Lighting**: Extreme lighting conditions (e.g., glare, darkness).
- **Shape**: Atypical pothole shape.
- **Other**: Unidentified false negatives.

The taxonomy is **OPEN** pending dataset inspection.

## Qualitative Analysis

Qualitative analysis includes:

- Visual inspection of detection overlays on sample images.
- Review of false-positive and false-negative examples.
- Assessment of detection stability across video frames.
- Annotation of qualitative observations.

Qualitative analysis is recorded in `experiments/evaluation/` reports (not in Git as media).

## Generalization

Generalization is assessed at multiple levels:

| Level | Description | Status |
|-------|-------------|--------|
| In-domain | Same dataset, same distribution as training | Required |
| Unseen Indian | Different Indian region or source not in training | Required |
| Cross-domain | Different camera/lighting/weather conditions | Required where feasible |
| Video | Performance on recorded video sequences | Required |
| Live-camera | Performance under real-time constraints | Required |

## Runtime Benchmarking

Runtime benchmarking must record:

- **Hardware**: GPU/CPU model, memory.
- **Resolution**: Model input resolution used.
- **Preprocessing latency**: Time from frame capture to tensor ready.
- **Inference latency**: Time for model forward pass.
- **Postprocessing latency**: Time for NMS and normalization.
- **End-to-end latency**: Total time from capture to detection.
- **Throughput**: Frames per second (FPS).
- **GPU memory**: Peak memory usage.
- **CPU/GPU utilization**: Resource utilization.

Benchmarking is recorded in `experiments/benchmarks/`.

## Model-Selection Rule

**No single metric automatically determines the winner.**

Model selection considers:

- Accuracy
- Recall
- False-positive behavior
- Small-object performance
- Generalization
- Latency
- Throughput
- Memory
- Deployment practicality

A model with slightly lower mAP but better recall on small potholes may be preferable for a safety-critical application.

## Status

- **Evaluation protocol**: `DRAFTED` (required metrics defined; exact thresholds OPEN)
- **Final model**: `OPEN`
- **Experiments run**: `NOT STARTED`

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*