# Deployment

## Overview

This document describes the conceptual deployment model for the Pothole Detection & Reporting System. The current deployment is a single-camera, single-machine topology with future scalability paths defined.

---

## Development Deployment

During development, all components run on a single machine with local infrastructure:

```text
Camera (simulated/recorded)
  ↓
Inference Engine (single process)
  ↓
Backend API (local server)
  ↓
Database (local)
  ↓
Frontend (local browser)
```

Development deployment uses local/ephemeral infrastructure. No production deployment is active.

## Initial Runtime Topology

```text
Camera
  ↓
Inference Machine
  ↓
Backend
  ↓
Database / evidence storage
  ↓
Frontend
```

### Process Boundaries

| Component | Process | Notes |
|-----------|---------|-------|
| Capture Adapter | Inference Engine | Logical boundary within inference process |
| Frame Pipeline | Inference Engine | Logical boundary within inference process |
| Preprocessing | Inference Engine | Logical boundary within inference process |
| Model Adapter + Detector | Inference Engine | Logical boundary within inference process |
| Tracker | Inference Engine | Logical boundary within inference process |
| Event Engine | Inference Engine | Logical boundary within inference process |
| Event Publisher | Inference Engine | Logical boundary within inference process |
| Backend API | Backend Server | Separate process |
| Database | Backend Server | Separate process or service |
| Frontend | Browser | Separate process (client) |

Components within the Inference Engine may be logically separated but initially run in the same process. The backend runs as a separate process/process group. The frontend runs in a browser.

## Hardware Assumptions

Exact hardware is configurable and must be documented per experiment. For inference:

- GPU with sufficient memory for model loading and inference.
- Sufficient RAM for bounded buffering.
- Network connectivity to backend.
- Storage for evidence (local or network-attached).

## Model Artifact Flow

```text
trained artifact
  ↓
verified artifact (hash check, provenance check)
  ↓
deployment (inference engine loads verified artifact)
```

1. **Training**: Produces a trained model artifact (checkpoint).
2. **Verification**: Cryptographic hash check and provenance verification (see SECURITY_ARCHITECTURE.md).
3. **Deployment**: The inference engine loads the verified artifact.

Only verified artifacts are loaded into the inference engine.

## Startup Sequence

Conceptually:

```text
load config
  ↓
verify model
  ↓
initialize runtime
  ↓
connect source
  ↓
start inference
```

### Detailed Steps

1. **Load config**: Read configuration for all components (source, model path, backend URL, etc.).
2. **Verify model**: Check model artifact hash and provenance. If verification fails, enter explicit failure state.
3. **Initialize runtime**: Initialize the Frame Pipeline, Tracker, Event Engine, and Event Publisher.
4. **Connect source**: Establish connection to the camera/video/source. If connection fails, retry with backoff or enter explicit failure state.
5. **Start inference**: Begin the frame pipeline and inference loop.

## Failure / Recovery

| Failure | Behavior | Recovery |
|---------|----------|----------|
| Camera disconnect | Explicit failure state; log | Retry with backoff; if persistent, graceful stop |
| Model loading failure | Explicit failure state; log | Do not start inference; report error |
| Backend unavailable | Buffer events up to bounded limit; queue for retry | Retry; if persistent, bounded buffer with idempotent replay |
| Storage failure | Continue processing; mark evidence as missing | Report error; do not halt inference |
| Frame pipeline overflow | Drop oldest frame (freshness priority) | Log; continue |

## Deployment / Update

### Model Versioning

- Model artifacts are versioned by `model_version_id`.
- The `is_active` flag indicates the current default.
- Model updates must follow the model artifact flow (verify → deploy).

### Rollback

- If a new model causes issues, revert to the previous `is_active` version.
- The inference engine must support loading a different `model_version_id`.

### Configuration Versioning

- Configuration files are versioned alongside the deployment.
- The inference engine loads the configuration at startup.

## Future Scale

### Multi-Camera

Multiple camera sources feeding a single inference machine or separate inference engines. Each source has its own pipeline (Capture Adapter → Frame Pipeline → ...).

### Inference Workers

Separate inference processes/workers for each camera source, with a central event aggregator. This is a future scalability path, not a current plan.

### Centralized Inference

A dedicated inference server serving multiple cameras or applications. This is a future scalability path, not a current plan.

Do not introduce Kubernetes, distributed queues, service meshes, or other distributed infrastructure in any stage below the future scalability stage.

## Status

- **Deployment model**: `PROVISIONAL`
- **Infrastructure**: `OPEN`
- **Containerization**: `NOT STARTED`
- **Monitoring**: `OPEN`

---

*Consistent with ARCHITECTURE.md and SECURITY_ARCHITECTURE.md. See PROJECT.md for the source-of-truth map.*