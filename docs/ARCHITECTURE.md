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
Inference Adapter
  ↓
Capture / Preprocessing
  ↓
Detection
  ↓
Tracking
  ↓
Event Engine
  ↓
Backend
  ↓
Database / Evidence Storage
  ↓
Frontend
```

## Offline ML Architecture

```text
Raw Data
  ↓
Audit
  ↓
Preparation
  ↓
Split
  ↓
Training
  ↓
Validation
  ↓
Test
  ↓
Model Selection
```

### Stage: Raw Data

- Source images and videos from candidate datasets (see DATA_PIPELINE.md).
- Status: OPEN (exact dataset not yet locked).

### Stage: Audit

- Inspect actual dataset files, annotations, classes, source relationships, provenance, duplication, video grouping, licensing, and suitability before finalizing the dataset strategy.
- Verify annotation quality, class balance, label consistency, image quality, and source provenance.
- Status: OPEN (not started).

### Stage: Preparation

- Convert to training format (e.g., COCO/YOLO).
- Annotation normalization to a common class representation.
- Duplicate / near-duplicate investigation.
- Source/group identification for leakage prevention.
- Status: OPEN (not started).

### Stage: Split

- Group-based leakage prevention: frames from the same source video or strongly correlated source sequence must not cross train/test boundaries.
- Exact split proportions: OPEN (not currently locked to any numerical value).
- Grouping implementation: OPEN pending dataset audit.
- Status: ASSUMED (group-based principle); OPEN (exact proportions).

### Stage: Training

- Pretrained initialization → fine-tuning → our pothole dataset.
- Candidate models: YOLO11s (baseline), YOLO26s (primary candidate), RF-DETR-S (transformer challenger).
- All comparison experiments must use the same dataset, split, evaluation protocol, and comparable input conditions.
- Status: EXPERIMENTAL (strategy LOCKED as direction; experiments NOT started).

### Stage: Validation

- Compute metrics and conduct error analysis on the validation set.
- Status: OPEN (not started).

### Stage: Test

- Final evaluation on the held-out test set (to be run after model selection).
- Status: UNKNOWN (not yet performed).

### Stage: Model Selection

- Choose the final model based on the full selection criteria (see MODEL_EVALUATION.md).
- Final model is OPEN.
- Status: OPEN (not started).

## Online Runtime Architecture

```text
Source (Image / Video / Camera)
  ↓
Capture Adapter
  ↓
Frame Pipeline
  ↓
Preprocessing
  ↓
Model Adapter
  ↓
Trained Detector
  ↓
Detection Normalization
  ↓
Tracker
  ↓
Event Engine
  ↓
Event Publisher
  ↓
Backend
```

### Component: Source

- Inputs: static images, recorded video files, live camera feeds.
- Status: OPEN (exact source types not yet locked).

### Component: Capture Adapter

- Hides source-specific camera/video APIs.
- Frame pipeline treats all sources uniformly.
- Provides frame identity and timestamp semantics.
- Status: OPEN (not started).

### Component: Frame Pipeline

- Manages frame ordering, timestamps, buffering.
- For live camera: bounded buffer, freshness priority over backlog.
- Status: OPEN (not started).

### Component: Preprocessing

- Resize, normalize, convert tensor format per model requirements.
- Must be consistent with training preprocessing.
- Status: OPEN (not started).

### Component: Model Adapter

- Hides framework-specific model objects (YOLO, RF-DETR).
- Exposes only the project-owned detection contract.
- This is the model/application boundary.
- Status: OPEN (not started).

### Component: Trained Detector

- The actual model artifact producing raw detections.
- Swappable through the Model Adapter.
- Status: OPEN (final model not selected).

### Component: Detection Normalization

- Converts raw model output into the project Detection format.
- Status: OPEN (not started).

### Component: Tracker

- Associates detections temporally across frames to form tracks.
- Separates Tracking algorithm (OPEN) from the Tracking responsibility (LOCKED principle).
- Status: OPEN (tracking algorithm not selected).

### Component: Event Engine

- Converts tracks into reportable PotholeEvents.
- A detection is not automatically a pothole event.
- Status: OPEN (event confirmation rules not defined).

### Component: Event Publisher

- Publishes events to the backend via the Ingestion API.
- Ensures idempotent ingestion.
- Status: OPEN (not started).

### Component: Backend

- Receives events via API.
- Persists events and evidence.
- Status: LOCKED as boundary; implementation OPEN.

## Component Responsibility Matrix

| Component | Purpose | Owner | Input | Output | State | Dependencies | Failure | Timing | Concurrency | Status |
|-----------|---------|-------|-------|--------|-------|-------------|---------|--------|-------------|--------|
| Data Pipeline (Offline) | Prepare training/eval data | Person 1 | Raw datasets | Dataset versions | Dataset files | Dataset sources | Data corruption, leakage | Batch / offline | Single-process | OPEN |
| Training | Train model | Person 1 | Dataset split | Checkpoints, metrics | Model weights | Data pipeline, model | Training failure, OOM | Epoch-based | GPU-parallel | EXPERIMENTAL |
| Evaluation | Assess model | Person 1 | Test set, checkpoint | Metrics, reports | None (read-only) | Checkpoint, data | Mismatch | Batch | Single-process | OPEN |
| Capture Adapter | Acquire frames | Person 4 | Camera/video/image | Frame stream + metadata | Buffer (bounded) | Source API | Device disconnect, I/O | Real-time | Async producer | OPEN |
| Frame Pipeline | Coordinate frames | Person 4 | Captured frames | Ordered, timestamped frames | Buffer (bounded) | Capture adapter | Frame loss, staleness | Real-time | Async | OPEN |
| Preprocessing | Transform frames | Person 4 | Raw frames | Tensors ready for model | Stateless | Model requirements | Format mismatch | Per-frame | Parallel | OPEN |
| Model Adapter | Abstract model | Person 4 | Tensors | Detections (project contract) | Model weights (loaded) | Model framework | Load failure, shape error | Per-inference | Parallel (batched) | OPEN |
| Trained Detector | Run inference | Person 1 (produces), Person 4 (loads) | Tensors | Raw model output | Weights (immutable at runtime) | Model adapter, weights | RuntimeError, OOM | Per-batch | Parallel | OPEN |
| Tracking | Associate detections temporally | Person 4 | Detections stream | Tracks | Track state (history) | Detections | Track loss, mismatch | Per-frame | Sequential | OPEN |
| Event Engine | Generate events | Person 4 | Tracks | PotholeEvents | Event state (candidate/confirmed/closed) | Tracks, Event Publisher | State confusion | Per-frame | Sequential | OPEN |
| Event Publisher | Send events | Person 4 | PotholeEvents | Acknowledged/queued | Pending queue (bounded) | Backend API | Network errors, duplicates | Async | Async | OPEN |
| Backend API | Persist/query events | Person 2 | Events, queries | Responses, persistence | Database | Database, Evidence storage | DB errors, API errors | Request/response | Multi-threaded | LOCKED (boundary); impl OPEN | OPEN |
| Database | Store events/evidence | Person 2 | Events, evidence | Persistence | Data state | Backend | Corruption, connection | On-write | Concurrent | OPEN | OPEN |
| Evidence Storage | Store media | Person 2 | Frames/clips | Storage refs | Media blobs | Backend | Storage full, corruption | Async | Concurrent | OPEN | OPEN |
| Frontend | Display/ interact | Person 3 | API responses | UI state | Client-side state | Backend API | Network errors | Event-driven | Single-threaded (browser) | OPEN | OPEN |

## Boundary Diagram

```text
┌──────────────────────────────────┐
│           DATA                  │
│  (datasets, versioning)         │
└───────────┬─────────────────────┘
            │ Detection Contract
            ▼
┌──────────────────────────────────┐
│           MODEL                 │
│  (training, evaluation)         │
└───────────┬─────────────────────┘
            │ Model Adapter
            ▼
┌──────────────────────────────────┐
│        INFERENCE                │
│  (capture, detection, tracking) │
└───────────┬─────────────────────┘
            │ Event Contract
            ▼
┌──────────────────────────────────┐
│          EVENT                  │
│  (Event Engine output)          │
└───────────┬─────────────────────┘
            │ Event Ingestion (API)
            ▼
┌──────────────────────────────────┐
│        BACKEND                  │
│  (persistence, reporting)       │
└───────────┬─────────────────────┘
            │ API Contract
            ▼
┌──────────────────────────────────┐
│        FRONTEND                  │
│  (dashboard, reports)            │
└──────────────────────────────────┘
```

### What is allowed to cross each boundary:

- **DATA → MODEL**: Dataset versions, splits, manifests.
- **MODEL → INFERENCE**: Verified model artifacts, metadata, and the detection contract.
- **INFERENCE → EVENT**: Detection contract (frame-level), track contract (temporal).
- **EVENT → BACKEND**: PotholeEvent contract (idempotent ingestion).
- **BACKEND → FRONTEND**: API contract (queries, mutations).

No framework-specific model objects, dataset internals, or tracking implementations cross these boundaries.

## State Ownership

| State | Location | Owner | Notes |
|-------|----------|-------|-------|
| Model weights | Filesystem/object storage (verified artifact) | Person 1 (produces), Person 4 (loads) | Immutable at runtime after load |
| Stream frame buffer | Inference runtime (local memory) | Person 4 | Bounded, FIFO for live camera |
| Tracker state | Inference runtime (local memory) | Person 4 | Per-source track state |
| Event state | Inference runtime (local memory) | Person 4 | Candidate/Confirmed/Closed transitions |
| Backend persistence | Database/Evidence Storage | Person 2 | Authoritative source after ingestion |
| Frontend state | Client-side (browser) | Person 3 | Cache; not authoritative |

## Failure Behavior

| Failure Class | Examples | Impact | Strategy |
|---------------|----------|--------|----------|
| Resource exhaustion | OOM, unbounded buffer, disk full | Inference stalls, crashes | Bounded buffers, resource limits, Degraded mode |
| Source failure | Camera disconnect, file unreadable | Data loss for affected source | Explicit failure state, reconnect attempts, skip frame |
| Model failure | Load failure, shape mismatch, corrupted weights | No inference output | Fallback to explicit failure state, do not emit false detections |
| Tracker failure | Track loss, ID switching | Track fragmentation | Tracker reset, explicit error state |
| Backend failure | DB errors, network unreachable | Pothole events not persisted | Buffer up to bounded limit, queue for retry, idempotent replay |
| Event Engine failure | State confusion, threshold bug | False or missing events | Explicit event states, audit trail |
| Storage failure | Evidence storage unavailable | No evidence retained | Continue processing; mark evidence as missing |

## Scaling Model

```text
1 camera / 1 machine
  ↓ (multiple cameras, single machine)
multiple cameras
  ↓ (distributed workers, if justified)
partitioned inference workers
```

Scaling proceeds in stages:

1. **Single-camera, single-machine** (initial): All components run on one device.
2. **Multi-camera, single machine** (simple scale): Multiple capture sources feed one inference pipeline.
3. **Partitioned inference workers** (future): Separate processes or machines per camera/source, with a central event aggregator.

No distributed infrastructure (Kubernetes, service meshes, distributed queues) is introduced in any stage below the future scalability stage. Each stage adds complexity only when justified by operational requirements.

## Status Labels

| Label | Meaning |
|-------|---------|
| `LOCKED` | Fixed; will not change without major consensus. |
| `VERIFIED` | Tested and confirmed to work as expected. |
| `IMPLEMENTED` | Code written and integrated. |
| `TESTED` | Unit/integration tests pass. |
| `BENCHMARKED` | Performance measured against requirements. |
| `EXPERIMENTAL` | Under active investigation; may change. |
| `ASSUMED` | Placeholder assumption awaiting validation. |
| `OPEN` | Not yet started or decided. |
| `DEFERRED` | Postponed to a later phase. |
| `UNKNOWN` | Status to be determined. |
| `BLOCKED` | Impeded by missing dependency or decision. |

---

*All terminology and status labels are kept consistent across documentation, contracts, and code comments. See PROJECT.md for the source-of-truth map.*
