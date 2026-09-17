# Decision Log

This document records major architectural decisions for the project.

Use a structured format for each decision.

---

## D-001: Object Detection as Core Task

- **Date**: 2026-09-17
- **Problem**: What is the core technical problem the system must solve?
- **Context**: Potholes need to be identified in road imagery automatically.
- **Options considered**: Classification, segmentation, object detection.
- **Evidence**: Object detection provides both classification and localization, which is necessary for bounding-box output and event generation.
- **Decision**: Use object detection as the core ML task.
- **Why**: Detection outputs bounding boxes and class labels, which are needed for downstream tracking and event generation.
- **Rejected alternatives**: Pure classification (no localization), segmentation (too expensive for real-time inference).
- **Consequences**: The entire system is built around bounding-box detections.
- **Risks**: Detection quality depends heavily on dataset and training.
- **Revisit conditions**: If 3D measurement becomes a goal, segmentation may be revisited.
- **Status**: LOCKED

---

## D-002: Training/Fine-Tuning is Central ML Contribution

- **Date**: 2026-09-17
- **Problem**: What is the ML project's core technical contribution?
- **Context**: The system needs a pothole detector.
- **Options considered**: Train from scratch, fine-tune pretrained, use off-the-shelf detector.
- **Evidence**: Fine-tuning pretrained weights on a pothole dataset provides the best balance of performance and development speed.
- **Decision**: Training/fine-tuning is the central ML contribution.
- **Why**: The project must own the model and its training process to ensure it works on the target domain.
- **Rejected alternatives**: Using an off-the-shelf detector without customization.
- **Consequences**: Significant effort is invested in dataset preparation and training.
- **Risks**: Dataset quality and size may limit fine-tuning effectiveness.
- **Revisit conditions**: If dataset is too small, training from scratch may be evaluated as a secondary experiment.
- **Status**: LOCKED

---

## D-003: Transfer Learning as Primary Training Strategy

- **Date**: 2026-09-17
- **Problem**: What is the primary training approach?
- **Context**: Training a model from scratch requires large amounts of data and compute.
- **Options considered**: Training from scratch, transfer learning/fine-tuning, ensemble of pretrained models.
- **Evidence**: Pretrained weights on large-scale datasets provide strong feature extractors that adapt well to pothole detection with fine-tuning.
- **Decision**: Pretrained initialization followed by fine-tuning is the primary training strategy.
- **Why**: Transfer learning reduces data requirements and training time.
- **Rejected alternatives**: Training from scratch as the primary approach (may be evaluated as a controlled comparison).
- **Consequences**: Model selection is constrained to architectures with available pretrained weights.
- **Risks**: Pretrained weights may not generalize well to pothole-specific features.
- **Revisit conditions**: If fine-tuning underperforms significantly, training from scratch may be evaluated.
- **Status**: LOCKED

---

## D-004: Candidate-Model Comparison

- **Date**: 2026-09-17
- **Problem**: Which model architectures should be evaluated?
- **Context**: Multiple detector architectures exist with different trade-offs.
- **Options considered**: YOLO11s, YOLO26s, RF-DETR-S, other architectures.
- **Evidence**: YOLO26 is a recent candidate, YOLO11 provides a baseline, RF-DETR offers a transformer-based challenger.
- **Decision**: Evaluate YOLO11s, YOLO26s, and RF-DETR-S as candidate models.
- **Why**: These represent different architectural paradigms (CNN-based YOLO, newer YOLO, transformer-based DETR).
- **Rejected alternatives**: Locking a single model prematurely.
- **Consequences**: The final model is not yet selected; evaluation will determine the best candidate.
- **Risks**: Evaluation must be fair and rigorous to avoid bias toward one architecture.
- **Revisit conditions**: After evaluation, the final model is selected based on the full criteria.
- **Status**: LOCKED (candidates selected; final model OPEN)

---

## D-005: Indian + Forward-Camera Dataset Priority

- **Date**: 2026-09-17
- **Problem**: What dataset characteristics are required?
- **Context**: The system must work on Indian roads with forward-facing cameras.
- **Options considered**: Any dataset, Indian-specific datasets, forward-camera datasets, both.
- **Evidence**: The deployment target is Indian roads with forward-facing vehicle cameras.
- **Decision**: Prioritize datasets with Indian relevance and forward-camera relevance.
- **Why**: The system must generalize to the target deployment environment.
- **Rejected alternatives**: Using datasets from unrelated domains without validation.
- **Consequences**: Dataset candidates must be audited for Indian road conditions and forward-camera imagery.
- **Risks**: Available Indian datasets may be limited in size or quality.
- **Revisit conditions**: After dataset audit, the exact dataset combination may be adjusted.
- **Status**: LOCKED (priority direction; exact dataset OPEN)

---

## D-006: Group-Based Leakage Prevention

- **Date**: 2026-09-17
- **Problem**: How should data be split to prevent information leakage?
- **Context**: Frames from the same source video are strongly correlated.
- **Options considered**: Random split, group-based split, time-based split.
- **Evidence**: Random splits can leak correlated frames into both training and test sets, inflating metrics.
- **Decision**: Use group-based splitting where frames from the same source video do not cross train/test boundaries.
- **Why**: Prevent overoptimistic evaluation metrics from correlated data.
- **Rejected alternatives**: Random splitting (leads to leakage).
- **Consequences**: Train/test splits must be constructed at the video/source level.
- **Risks**: May reduce effective training data if sources are few.
- **Revisit conditions**: After source identification and grouping are complete.
- **Status**: LOCKED

---

## D-007: Model/Application Adapter Boundary

- **Date**: 2026-09-17
- **Problem**: How to protect the application from framework-specific model details?
- **Context**: The model could be YOLO, RF-DETR, or a future architecture.
- **Options considered**: Expose model objects directly, use an adapter/boundary, use a framework-agnostic inference server.
- **Evidence**: Exposing framework-specific objects throughout the repository creates tight coupling and prevents model swapping.
- **Decision**: Place a project-owned model adapter between the model and the rest of the system.
- **Why**: The detector can later be replaced without rewriting the rest of the application.
- **Rejected alternatives**: Direct dependency on framework-specific model objects.
- **Consequences**: The inference module owns the adapter; other modules depend on the project's detection contract.
- **Risks**: The adapter must be well-designed to avoid becoming a bottleneck.
- **Revisit conditions**: When the final model is selected and the adapter is implemented.
- **Status**: LOCKED

---

## D-008: Detection vs Tracking Separation

- **Date**: 2026-09-17
- **Problem**: How to separate detection and tracking responsibilities?
- **Context**: Detection and tracking are distinct technical problems with different requirements.
- **Options considered**: Combine detection and tracking, separate them into distinct modules.
- **Evidence**: Detection is a per-frame problem; tracking is a temporal association problem. They have different interfaces and can evolve independently.
- **Decision**: Keep detection and tracking as separate responsibilities.
- **Why**: Each component can be developed, tested, and replaced independently.
- **Rejected alternatives**: Combining detection and tracking into a single module.
- **Consequences**: The detector outputs detections; the tracker consumes detections and produces tracks.
- **Risks**: Interface between detection and tracking must be well-defined.
- **Revisit conditions**: When the tracker is designed.
- **Status**: LOCKED

---

## D-009: Detection vs Event Separation

- **Date**: 2026-09-17
- **Problem**: Is every detection a reportable pothole event?
- **Context**: A frame-level detection is not automatically a reportable event.
- **Options considered**: Treat every detection as an event, add an event engine to filter/aggregate detections.
- **Evidence**: Detections are noisy and temporary; events represent logical occurrences that warrant reporting.
- **Decision**: A frame-level detection is NOT automatically a reportable pothole event. An event engine handles the conversion.
- **Why**: Prevents flooding the system with transient detections that are not real pothole occurrences.
- **Rejected alternatives**: Directly promoting every detection to an event.
- **Consequences**: The event engine is a separate downstream component that must be designed.
- **Risks**: Event confirmation rules are not yet defined.
- **Revisit conditions**: When the event engine is designed.
- **Status**: LOCKED

---

## D-010: Live-Camera Freshness Principle

- **Date**: 2026-09-17
- **Problem**: How to handle live-camera inference?
- **Context**: For live inference, freshness is more important than preserving an unlimited backlog of stale frames.
- **Options considered**: Unbounded queues, bounded buffering, drop-frame strategies.
- **Evidence**: Unbounded queues can lead to memory exhaustion and processing stale data.
- **Decision**: Use bounded buffering and prioritize freshness over an unlimited backlog.
- **Why**: Live inference must respond to current conditions, not old frames.
- **Rejected alternatives**: Unbounded queues (risk of resource exhaustion).
- **Consequences**: The inference runtime must implement bounded buffers.
- **Risks**: May drop frames under high load.
- **Revisit conditions**: When the runtime is designed.
- **Status**: LOCKED

---

## D-011: Explicit Failure States

- **Date**: 2026-09-17
- **Problem**: How should the system handle failures?
- **Context**: The system must handle errors gracefully and explicitly.
- **Options considered**: Silent failures, generic error handling, explicit failure states.
- **Evidence**: Explicit failure states make debugging and monitoring easier.
- **Decision**: Include explicit failure states in the system design.
- **Why**: Reliability requires that failures are visible and handled.
- **Rejected alternatives**: Silent failures or unhandled exceptions.
- **Consequences**: All components must define and handle their failure states.
- **Risks**: May add complexity to component interfaces.
- **Revisit conditions**: When reliability engineering begins.
- **Status**: LOCKED

---

## D-012: Initial Scalability Strategy

- **Date**: 2026-09-17
- **Problem**: What is the initial deployment architecture?
- **Context**: The system must start somewhere and scale later.
- **Options considered**: Distributed from day one, single-machine first, cloud-native from the start.
- **Evidence**: A single-camera, single-machine deployment is the simplest starting point.
- **Decision**: Start with single-camera, single-machine deployment. Future paths include centralized inference, multiple cameras, and partitioned inference workers.
- **Why**: Simplicity at the start reduces risk and allows the core ML pipeline to be validated.
- **Rejected alternatives**: Distributed or Kubernetes-based deployment from the start.
- **Consequences**: The initial deployment is simple; scalability is a future concern.
- **Risks**: May need to refactor for distributed deployment later.
- **Revisit conditions**: When operational requirements demand scaling.
- **Status**: LOCKED

---

*All decisions are recorded with their status. Open items are explicitly marked. Evidence is distinguished from empirical results where appropriate. Decisions reflect strategy selection, not empirical proof unless stated otherwise.*