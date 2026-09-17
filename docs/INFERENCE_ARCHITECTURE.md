# Inference Architecture

## Overview

The inference pipeline converts source inputs (images, recorded video, live camera) into reportable PotholeEvents through a series of stages. Each stage is bounded by well-defined contracts:

```text
Source Input
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
PotholeEvent
```

## Capture Adapter

### Purpose

Hides source-specific camera/video APIs. The Frame Pipeline treats all sources uniformly, whether the input is a static image, a recorded video file, or a live camera feed.

### Inputs

- Image file path or stream.
- Video file path or stream.
- Camera device or network stream URL.

### Outputs

- Frame buffer with frame identity and timestamp semantics.
- Source metadata (type, device ID, timestamp source).

### States

| State | Description |
|-------|-------------|
| Idle | No active source. |
| Connecting | Establishing connection. |
| Streaming | Frames are available. |
| Error | Source failure; explicit failure state. |
| Disconnected | Source lost; retry or terminate. |

### Failure Behavior

- **Device disconnect**: Explicit failure state; retry with backoff or stop gracefully.
- **Invalid source**: Return explicit failure state; do not emit detections.
- **I/O error**: Log and attempt reconnect or graceful stop.

### Timing Semantics

- Frame capture is timestamped at the capture point.
- Timestamp semantics depend on source (camera hardware time, file metadata, or system time).

### Concurrency Expectations

- Async producer: captures frames independently of inference processing.
- Bounded buffer for live camera (see Frame Pipeline).

### Replacement Boundary

The Capture Adapter can be swapped if the source API changes (e.g., different camera SDK) without affecting downstream stages.

### Scaling Behavior

Single source initially; multiple sources may feed a single pipeline or separate pipelines.

### Status: OPEN (not started)

---

## Frame Pipeline

### Purpose

Coordinates the flow of frames from capture through preprocessing and inference. Manages frame ordering, timestamps, and buffering required for the source type.

### Inputs

- Captured frames from the Capture Adapter.

### Outputs

- Ordered, timestamped frame batches or individual frames.

### States

| State | Description |
|-------|-------------|
| Idle | No frames available. |
| Buffering | Collecting frames for a batch or sequence. |
| Streaming | Frames are being passed downstream. |
| Stale | Frame is too old; dropped or flagged. |
| Error | Pipeline failure; explicit failure state. |

### Failure Behavior

- **Frame loss**: Log and skip; do not invent frames.
- **Stale frame**: Drop frame (freshness priority) or flag it.
- **Buffer overflow**: Drop oldest frames (bounded buffer).

### Timing Semantics

- Frame timestamps are preserved from the Capture Adapter.
- Frame ordering is maintained.

### Concurrency Expectations

- Async producer/consumer between Capture Adapter and Preprocessing.
- Bounded buffer for live camera.

### Scaling Behavior

Single pipeline initially; multiple pipelines for multiple sources.

### Status: OPEN (not started)

---

## Preprocessing

### Purpose

Applies transformations to frames before inference consistent with the model's requirements.

### Inputs

- Raw frames from the Frame Pipeline.

### Outputs

- Preprocessed tensors ready for the Model Adapter.

### Relationship to Training Preprocessing

The preprocessing must match the training preprocessing exactly. Any mismatch degrades model performance. Document the training preprocessing in `docs/MODEL_TRAINING.md`.

### States

| State | Description |
|-------|-------------|
| Idle | No frames to process. |
| Processing | Frame being transformed. |
| Error | Preprocessing failure; explicit failure state. |

### Failure Behavior

- **Format mismatch**: Log and return failure state; do not emit invalid tensors.
- **Resize failure**: Log and skip frame.

### Timing Semantics

- Per-frame transformation.

### Concurrency Expectations

Stateless; can run in parallel with other frames.

### Scaling Behavior

Single process initially; batching may be added for throughput.

### Status: OPEN (not started)

---

## Model Adapter

### Purpose

Hides YOLO/RF-DETR-specific output types. The rest of the system operates on the project's Detection contract, not framework-specific model objects.

This is the model/application boundary. The model is not exposed throughout the rest of the repository.

### Inputs

- Preprocessed tensors from Preprocessing.
- Model-specific configuration (input size, etc.).

### Outputs

- Detections conforming to the Detection contract (see EVENT_SCHEMAS.md).

### States

| State | Description |
|-------|-------------|
| Idle | No inference requested. |
| Loading | Model weights being loaded. |
| Ready | Model loaded and warmed up. |
| Inferencing | Model processing a batch. |
| Error | Load failure, shape mismatch, runtime error; explicit failure state. |

### Failure Behavior

- **Load failure**: Explicit failure state; do not emit detections.
- **Shape mismatch**: Log and return failure state.
- **Runtime error**: Log and return failure state; do not emit false detections.

### Timing Semantics

- Model warm-up occurs once at startup.
- Inference latency is per-batch or per-frame.

### Concurrency Expectations

- Model inference may be batched for throughput; tracking is sequential per source.

### Replacement Boundary

The Model Adapter can be swapped when the model changes (e.g., YOLO26s → RF-DETR-S) without affecting downstream stages. Only the Detection contract is stable.

### Scaling Behavior

Single inference process initially; multiple inference workers may be added later.

### Status: OPEN (not started)

---

## Detection Normalization

### Purpose

Converts raw model output into the project's standard Detection format.

### Inputs

- Raw model outputs from the Model Adapter.

### Outputs

- Normalized Detections conforming to the Detection contract.

### Detection Contract (Conceptual)

| Field | Description | Status |
|-------|-------------|--------|
| `class` | Detected class label (e.g., `"pothole"`) | DRAFT |
| `confidence` | Model confidence score [0–1] | DRAFT |
| `bbox` | `[x1, y1, x2, y2]` in pixel coordinates (relative to frame) | DRAFT |
| `frame_id` | Identifier of the frame / capture context | DRAFT |
| `capture_timestamp` | Time the frame was captured | DRAFT |
| `track_id` | Optional track identifier if tracking is active | DRAFT |

### Status

- Detection schema: `DRAFT / TO BE FINALIZED`

---

## Tracker

### Purpose

Associates detections temporally across frames to form tracks. Tracking is a separate responsibility from detection. The tracker consumes normalized detections and produces tracks.

### Inputs

- Stream of normalized Detections.

### Outputs

- Tracks (temporal associations of detections).

### Tracking Responsibility (LOCKED)

The system separates detection from tracking. The detector does not perform tracking; the tracker is a downstream component.

### Tracking Algorithm (OPEN)

The specific tracking algorithm (e.g., SORT, DeepSORT, custom) is **OPEN**. The tracker must associate detections temporally and produce track identifiers. The algorithm choice is not locked at this stage.

### States

| State | Description |
|-------|-------------|
| Idle | No detections available. |
| Associating | Matching detections to existing tracks. |
| Creating | Starting new tracks for unassociated detections. |
| Expiring | Terminating tracks that have no recent detections. |
| Error | Tracker failure; explicit failure state. |

### Failure Behavior

- **Track loss**: Explicit failure state; log and continue.
- **ID switching**: Log; do not fabricate track associations.
- **No detections**: No tracks produced.

### Timing Semantics

- Per-frame tracking update.

### Concurrency Expectations

Sequential per source; tracks are per-source.

### Scaling Behavior

Single tracker initially; may be partitioned by source.

### Status: OPEN (not started)

---

## Event Engine

### Purpose

Converts tracks into reportable PotholeEvents. A detection is not automatically a pothole event. The Event Engine applies confirmation rules and produces PotholeEvents that are publishable to the Backend API.

### Lifecycle

```text
Detection
  ↓
Track
  ↓
Candidate Event
  ↓
Confirmed Event
  ↓
Closed Event
```

### Confirmation Rules (OPEN)

The rules for promoting a track to a confirmed PotholeEvent are **NOT defined yet**. They will be specified after design research and may include persistence thresholds, confidence thresholds, and spatial clustering.

### States

| State | Description |
|-------|-------------|
| Idle | No tracks to process. |
| Candidate | Track meets preliminary criteria for an event. |
| Confirmed | Event has passed confirmation rules. |
| Closed | Event is resolved or expired. |
| Error | Event Engine failure; explicit failure state. |

### Failure Behavior

- **Confirmation rule bug**: Explicit failure state; log; do not confirm false events.
- **State confusion**: Log and recover; do not emit ambiguous states.

### Timing Semantics

- Event confirmation is per-track, not per-detection.
- Events are emitted asynchronously after confirmation.

### Concurrency Expectations

Sequential per source; events are per-source.

### Scaling Behavior

Single event engine initially; may be partitioned by source.

### Status: OPEN (not started)

---

## Live-Camera Buffering

For live-camera inference:

- **Bounded buffer**: The frame pipeline uses a bounded FIFO buffer with a configurable maximum size.
- **Freshness priority**: Older frames are dropped before newer frames when the buffer is full. The system prioritizes current conditions over an unlimited backlog.
- **Dropped frame accounting**: Dropped frames are logged for debugging and performance analysis.

### Failure Behavior

- **Buffer overflow**: Drop oldest frame; log.
- **Source stall**: Explicit failure state; attempt reconnect or graceful stop.

### Status: LOCKED (principle); implementation OPEN

---

## GPS Semantics

Clearly distinguish between:

- **Camera/Vehicle location**: The GPS coordinates of the camera or vehicle at the time of capture.
- **Estimated pothole location**: An estimate of where the pothole is on the road, derived from the camera's position and the detection's location in the frame.

**Do not claim exact pothole coordinates until a validated localization method is introduced.**

### Status

- Camera/Vehicle location: `ASSUMED` (from capture source metadata)
- Estimated pothole location: `OPEN` (localization method not yet validated)

---

## Status Summary

| Component | Status |
|-----------|--------|
| Capture Adapter | OPEN |
| Frame Pipeline | OPEN |
| Preprocessing | OPEN |
| Model Adapter | OPEN |
| Trained Detector | OPEN (final model not selected) |
| Detection Normalization | DRAFT |
| Tracker | OPEN |
| Event Engine | OPEN |
| Event Publisher | OPEN |
| Live-camera buffering | LOCKED (principle); implementation OPEN |
| GPS semantics | ASSUMED / OPEN |