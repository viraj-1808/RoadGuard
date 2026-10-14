# System Architecture

## System Purpose

The Pothole Detection & Reporting System provides an end-to-end pipeline for detecting potholes in road imagery and converting those detections into reportable maintenance events. The system's core technical contribution is a pothole object-detection model that the team trains and rigorously evaluates, then deploys for image, recorded-video, and live-camera inference.

## Scope / Non-Scope

| In Scope | Not In Scope (Current) |
|----------|----------------------|
| Pothole object detection | 3D pothole measurement (volume/depth) |
| Model training and fine-tuning | Scientifically validated depth estimation |
| Image, recorded-video, and live-camera inference | Exact GPS pothole localization |
| Temporal detection tracking | Pothole severity prediction |
| Pothole event generation and reporting | Distributed multi-region deployment |
| Backend API for event persistence | Authentication/authorization implementation |
| Frontend dashboard and reporting UI | |

## High-Level Architecture

```text
Dataset
  ↓
Data Pipeline
  ↓
Training
  ↓
Evaluation
  ↓
Final Model
  ↓
Inference Adapter (Model/Detection Boundary)
  ↓
Capture Adapter / Frame Pipeline / Preprocessing
  ↓
Trained Detector
  ↓
Detection Normalization
  ↓
Tracker
  ↓
Event Engine
  ↓
Backend
  ↓
Database / Evidence Storage
  ↓
Frontend
```

The offline pipeline (Dataset → Training → Evaluation → Final Model) produces model artifacts. The online runtime converts images/video/camera input into reportable `PotholeEvent` records through bounded, contract-separated stages. See docs/ARCHITECTURE.md for the full component breakdown and docs/INFERENCE_ARCHITECTURE.md for the inference workflow.

### Team Ownership (4-Person Split)

| Person | Role                    | Areas         |
|--------|-------------------------|---------------|
| P1     | ML / Data               | `ml/`, `experiments/` |
| P2     | Backend                 | `backend/`    |
| P3     | Frontend                | `frontend/`   |
| P4     | Inference / Integration | `inference/`  |

See docs/TEAM_WORKSTREAMS.md for the full responsibility matrix and contract flow.

## Technology Stack

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Language           | Python 3.12                                     |
| Model framework    | Ultralytics YOLO (YOLO11s / YOLO26s baseline)   |
| Image processing   | OpenCV (cv2)                                    |
| Data audit         | imagehash, Pillow, hashlib (SHA-256)            |
| Dataset format     | Pascal VOC XML (norm) → YOLO .txt (training)    |
| Annotation format  | `[x1, y1, x2, y2]` pixel coordinates, top-left  |
| Hardware target    | CUDA GPU (RTX 4050-class or better)             |

Candidate models: YOLO11s (baseline), YOLO26s (primary candidate), RF-DETR-S (transformer challenger). Final model selection is `OPEN` and determined by the evaluation protocol in docs/EVALUATION.md.

## Inference

Run manual inference on images placed in the fixed input directory:

```bash
# Default inference — uses epoch-72 protected baseline checkpoint
python predict.py

# Custom options
python predict.py --source <image_or_dir> --weights <path/to/best.pt> \
    --conf 0.25 --iou 0.7 --imgsz 720 --device 0 --experiment-id MYRUN

# Omit any flag to keep defaults
```

**Defaults:** input `validation/manual/input`, output `validation/manual/output/`, weights `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt`, conf 0.25, iou 0.7, imgsz 720, device 0.

Each run creates a unique timestamped directory containing `predictions.json`, `results.csv`, `summary.txt`, `run_metadata.json`, and annotated images.

### Model Adapter

The `inference/adapters/yolo_adapter.py` wraps Ultralytics YOLO behind a project-owned adapter. It exposes `Detection`, `InferenceResult`, and `ModelInfo` dataclasses and is the single boundary where framework-specific objects cross into the project. This adapter can be swapped when the model changes without affecting downstream stages.

See docs/INFERENCE_ARCHITECTURE.md and the [Inference CLI](inference/cli.py) for details.

## Training

The primary training strategy (LOCKED) is **pretrained initialization → fine-tuning** of YOLOv11s on the project dataset. See docs/TRAINING.md for the verified training and resume commands and docs/EVALUATION.md for known metrics and unresolved discrepancies.

### Resume Training

To resume Experiment 2 fine-tuning from the epoch-72 checkpoint:

```bash
python experiments/training/resume_realworld_finetune.py
```

This loads `last.pt` from `runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt` with `resume=True` (restores optimizer state) and continues to epoch 82 with the documented configuration.

## Dataset

- **Primary candidate**: RDD2022 (47,420 images, 6 countries, Pascal VOC XML, D40 pothole class). India subset: 9,665 images.
- **Supplementary candidate**: BharatPotHole / iWatchRoad (Indian dashcam, >7,000 frames, YOLO format).
- **External evaluation**: HRP4K (Chinese 4K, 6,003 images — cross-domain only).
- **Excluded**: RAD (600 images, too small for training).

Dataset composition is **RECOMMENDED, not locked** pending annotation quality inspection and license verification. The class-mapping transformation (v1.0.0) covering 1,530 images / 4,524 objects is fully implemented and verified — 4,360 retained, 164 excluded, all 16 invariants pass. See docs/DATASET_AUDIT.md and docs/DATA_PIPELINE.md for full details.

## Evaluation

Evaluation metrics and protocol are defined in docs/MODEL_EVALUATION.md. See docs/EVALUATION.md for known metrics and unresolved discrepancies from completed experiments.

## Known Limitations & Unresolved Discrepancies

1. **Selection bias**: 100% of the RDD2022 India artifact (1,530 images) contains D40. Zero pothole-negative and zero crack-only images exist — no negative-class samples for training or evaluation.
2. **D40 semantic breadth**: CRDDC D40 covers rutting, bump, pothole, and separation — the project class name `pothole` is broader than a strict physical pothole.
3. **Residual leakage risk**: RDD2022 India artifact has no sequence/video/trip/GPS metadata. State C — no reliable grouping can be established. Five verified near-duplicate clusters (121 images) are treated as atomic units; all other images' group membership is **UNKNOWN**. Residual leakage risk is **unquantifiable, not zero**. D-006-R1 refinement proposed but not applied.
4. **transverse_crack zero recall**: On the frozen 230-image India test set, transverse_crack achieves **0.000 recall** — the model fails to detect transverse cracks from the India domain entirely. Dataset B provides 7,313 transverse examples (347× Dataset A's 21), but continued training has not resolved this yet.
5. **Domain gap**: mAP50-95 drops ~68% from Dataset B validation (0.344) to the India test set (0.111). Dataset B validation metrics are **not predictive** of India-domain performance.
6. **No val/test splits for RDD2022 India normalized artifact**: splitting has not been performed; the normalized output mirrors the raw source's `train/` split only.
7. **Official data access**: `RDD2022_India.zip` S3 returns 403 Access Denied; the project relies on a Kaggle-derived filtered subset (15.8% of the India train set), not the official release.
8. **Checkpoint verification**: The protected epoch-72 baseline has SHA-256 `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5`. The model is epoch-72 of an under-trained run (30/100 epochs) — further training is required for production readiness.
9. **Inference accuracy unverified**: Manual inference (`predict.py`) runs correctly on unseen images but **does not establish real-world precision/recall** — the manual input set has no ground-truth annotations.
10. **Database, API, and frontend**: All are `OPEN` / not started. Only conceptual schemas exist (see docs/DATABASE_SCHEMA.md).

## Repository Structure

| Path | Description |
|------|-------------|
| `predict.py` | Manual inference entry point (Phase 4 deliverable) |
| `baseline_discovery.py` | Repository facts collector |
| `docs/` | Authoritative documentation |
| `contracts/` | Interface definitions (detection, event, API) |
| `ml/` | Data preprocessing, training, evaluation, model utilities |
| `inference/` | Runtime: capture, preprocessing, model adapter, tracking, event engine |
| `backend/` | API server, database models, reporting (not started) |
| `frontend/` | Dashboard UI (not started) |
| `experiments/` | Training runs, evaluation results, analysis reports |
| `tests/` | Unit, integration, and contract tests |
| `scripts/` | Utility, analysis, download, validation scripts |
| `configs/` | Training config files |
| `runs/` | Training output checkpoints (not committed) |

## Authoritative Source of Truth

| Topic | Document |
|-------|----------|
| Project scope | docs/PROJECT.md |
| System architecture | docs/ARCHITECTURE.md |
| Inference workflow | docs/INFERENCE_ARCHITECTURE.md |
| Class mapping | docs/CLASS_MAPPING.md |
| Dataset audit | docs/DATASET_AUDIT.md |
| Data pipeline | docs/DATA_PIPELINE.md |
| Training | docs/TRAINING.md |
| Evaluation | docs/EVALUATION.md |
| Event schemas | docs/EVENT_SCHEMAS.md |
| API contracts | docs/API_CONTRACTS.md |
| Database schema | docs/DATABASE_SCHEMA.md |
| Security model | docs/SECURITY_ARCHITECTURE.md |
| Deployment | docs/DEPLOYMENT.md |
| Team workstreams | docs/TEAM_WORKSTREAMS.md |
| Decisions | docs/DECISION_LOG.md |
| Engineering lessons | docs/ENGINEERING_LOG.md |
| Research evidence | docs/RESEARCH_REGISTER.md |

**Conflict resolution**: If two authoritative sources disagree, STOP and resolve explicitly. Do not silently pick one.

---

*RoadGuard AI — automated road-damage detection for safer streets.*