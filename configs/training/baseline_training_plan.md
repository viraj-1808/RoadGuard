# Baseline Training Plan for RoadGuard AI

## Experiment Overview
- **Model**: YOLO11s (baseline candidate)
- **Initialization**: Pretrained weights (from YOLO11s model on COCO/ImageNet)
- **Training Strategy**: Pretrained initialization + fine-tuning (LOCKED strategy)
- **Hyperparameters**: Default values only (no tuning/sweep)
- **Parallel Training**: Single model, no parallel/distributed training
- **Dataset**: To be determined (RDD2022 India subset or combination under audit)
- **Experiment ID**: Following convention: `{model}_{dataset_v}{split_v}_{timestamp}`

## Reproducibility Requirements
All experiments must record the following metadata (per docs/MODEL_TRAINING.md):

### Required Metadata
1. experiment_id
2. dataset_version
3. split_version
4. model (architecture name: YOLO11s)
5. checkpoint (hash and external storage path)
6. image_size
7. batch_size
8. optimizer (default from YOLO11s framework)
9. learning_rate (default from YOLO11s framework)
10. epochs (actual, or early stopping epoch)
11. augmentation (configuration)
12. seed (fixed per experiment, recorded for reproducibility)
13. hardware (GPU/CPU model)
14. software versions (framework, CUDA, Python)
15. git_commit (repository commit used for training)
16. metrics (link to evaluation report)
17. artifact (link to checkpoint location)

## Baseline Definition (per docs/MODEL_TRAINING.md)
A baseline experiment must:
- Use the smallest viable candidate model (YOLO11s)
- Use default hyperparameters from the model's documentation (not tuned)
- Record all reproducibility metadata
- Report all required metrics (see MODEL_EVALUATION.md)
- Serve as the performance floor for more advanced experiments

## Initialization Strategy
- **Primary Strategy**: Pretrained + fine-tuning (LOCKED)
  - Start from pretrained weights
  - Fine-tune on pothole dataset
- **Secondary Strategy**: Random initialization (training from scratch) - only for controlled comparison after baseline

## Hardware & Software Requirements
To be recorded per experiment:
- GPU model and memory
- CPU model
- System RAM
- Framework version (Ultralytics YOLO or equivalent)
- CUDA version
- Python version
- Key library versions (PyTorch, OpenCV, etc.)

## Dataset Requirements
Per docs/DATA_PIPELINE.md and DATASET_AUDIT.md:
- Group-based leakage prevention (LOCKED principle)
- Dataset versioning with manifest
- Source provenance and license verification
- Annotation validation (no critical errors)
- Consistent class normalization (Strategy B for RDD2022 India: D00→0, D10→1, D20→2, D40→3)
- Coordinate normalization to project pixel format [x_min, y_min, x_max, y_max]

## Evaluation Protocol
Per docs/MODEL_EVALUATION.md:
### Required Metrics (all required):
- Precision
- Recall
- F1-score
- IoU
- AP
- mAP50
- mAP75
- mAP50-95

### Evaluation Levels:
- In-domain (validation set)
- Unseen Indian-domain set
- Cross-domain set
- Video sequences
- Live-camera (when applicable)

### Small-Object Evaluation:
- Size categories based on actual bounding box area distribution
- mAP per size category

### False-Positive/Negative Taxonomy:
- Framework for classification (to be finalized after dataset inspection)

## Checkpoint Selection
"Best model" defined by evaluation protocol (not single metric):
- Validation metrics at each epoch
- Training time and resource usage
- Inference latency (post-training benchmark)
- Multi-criteria selection rule (not necessarily highest mAP)

## Artifact Management
Per docs/MODEL_TRAINING.md and DATA_PIPELINE.md:
- Checkpoint files: Not committed to Git (external storage)
- Metadata files: JSON/YAML with reproducibility metadata (stored in experiments/training/)
- Artifact hash: Cryptographic hash of checkpoint for provenance
- Artifact location: Path to external storage
- Manifest files: Record metadata only (no binary artifacts in Git)

## Experiment Workflow
1. Dataset preparation and validation (per DATA_PIPELINE.md acceptance criteria)
2. Configuration of training run with default YOLO11s hyperparameters
3. Training execution with seed fixed for reproducibility
4. Periodic checkpoint saving during training
5. Final checkpoint selection based on evaluation protocol
6. Metadata recording and artifact hashing
7. Evaluation on validation/test sets
8. Runtime benchmarking
9. Documentation of results in experiments/training/

## Risk Mitigation
- Selection bias: Documented as limitation (100% D40-positive images in current artifact)
- Leakage risk: Group-based splitting with residual risk recorded as unquantifiable if grouping unavailable
- Hardware variability: Full hardware/software version recording
- Implementation bugs: Unit tests for data transformation pipeline (already implemented)

## Dependencies
- Ultralytics YOLO framework or equivalent YOLO11s implementation
- Python 3.8+
- PyTorch with CUDA support
- OpenCV
- yaml/json for metadata storage
- hashlib for artifact hashing