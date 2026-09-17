# Database Schema (Conceptual)

## Technology Status

| Aspect | Status |
|--------|--------|
| Database technology | `OPEN` |
| Exact columns | `OPEN` |
| Migration strategy | `OPEN` |
| ORM / Query layer | `OPEN` |

No database engine has been selected yet. All schema details are intentionally left undefined to avoid premature commitment.

---

## Domain Model Overview

The following conceptual entities represent the domain model. They describe what must be persisted, not how.

```
Camera
  │
  ├── produces frames → (inference pipeline)
  │
PotholeEvent ← tracks + Event Engine
  │
  ├── evidence → Evidence
  │
  └── report → Report
  │
ModelVersion ← attributed by Inference
```

---

## Conceptual Entities

### Camera

**Purpose**: Source of video frames for inference.

| Attribute | Type | Description | Mutability | Status |
|-----------|------|-------------|------------|--------|
| `camera_id` | string | Identifier for the physical or logical camera source | Immutable | OPEN |
| `location` | object | GPS coordinates of the camera position (lat, lng) | Mutable | OPEN |
| `active` | boolean | Whether the camera is currently streaming | Mutable | OPEN |
| `metadata` | object | Key-value store for camera-specific settings | Mutable | OPEN |

**Invariants**: `camera_id` is unique. `location` may be updated if the camera is moved.

**Provenance**: Registered by operator; persists for the lifetime of the camera.

**Lifecycle**: Created → Active/Inactive → Retired.

---

### PotholeEvent

**Purpose**: A reportable occurrence resulting from the Event Engine.

| Attribute | Type | Description | Mutability | Status |
|-----------|------|-------------|------------|--------|
| `event_id` | string | Unique identifier | Immutable | OPEN |
| `timestamp` | datetime | Time the event was finalized | Immutable | OPEN |
| `status` | string | Current state (e.g., `pending`, `approved`, `rejected`, `resolved`) | Mutable | OPEN |
| `confidence` | float | Peak confidence across evidence | Immutable | OPEN |
| `camera_id` | string | Foreign key linking to the source Camera | Immutable | OPEN |
| `evidence_ref` | string | Reference to stored Evidence | Immutable | OPEN |

**Invariants**: 
- `event_id` is unique.
- Exactly one `Camera` per event.
- `status` transitions must follow the defined state machine (OPEN).

**Provenance**: 
- Track ID(s) that produced the event.
- Model artifact that produced the detections.
- Evidence references.

**Lifecycle**: Created → Pending → (Approved/Rejected) → Resolved/Closed.

---

### Report

**Purpose**: A human- or agency-initiated action derived from a PotholeEvent.

| Attribute | Type | Description | Mutability | Status |
|-----------|------|-------------|------------|--------|
| `report_id` | string | Unique identifier | Immutable | OPEN |
| `event_id` | string | Link to the originating PotholeEvent | Immutable | OPEN |
| `submitted_by` | string | Entity or user who created the report | Immutable | OPEN |
| `submitted_at` | datetime | Timestamp of report creation | Immutable | OPEN |
| `priority` | string | Service level or urgency classification | Mutable | OPEN |
| `resolution` | string | Status code or text for how the report was handled | Mutable | OPEN |

**Invariants**:
- `report_id` is unique.
- Exactly one `PotholeEvent` per report (an event may have zero or one report).
- `priority` and `resolution` follow defined enumerations (OPEN).

**Provenance**: 
- PotholeEvent ID.
- User or agency that created the report.

**Lifecycle**: Created → Pending → (Approved/In Progress) → Resolved.

---

### Evidence

**Purpose**: Media artifacts (images, video clips) associated with a PotholeEvent or Report.

| Attribute | Type | Description | Mutability | Status |
|-----------|------|-------------|------------|--------|
| `evidence_id` | string | Unique identifier | Immutable | OPEN |
| `pothole_event_id` | string | Link to the parent PotholeEvent | Immutable | OPEN |
| `media_type` | string | e.g., `image`, `video`, `thermal` | Immutable | OPEN |
| `storage_path` | string | Reference to object storage or database BLOB | Immutable | OPEN |
| `captured_at` | datetime | Timestamp of media capture | Immutable | OPEN |
| `verified` | boolean | Whether the evidence has been reviewed/verified | Mutable | OPEN |

**Invariants**:
- `evidence_id` is unique.
- Exactly one `PotholeEvent` (or `Report`) per evidence item.
- `storage_path` must be accessible.

**Provenance**: 
- Frame/clip IDs from the inference pipeline.
- Camera source and capture timestamp.

**Lifecycle**: Created → Stored → (Verified) → Retained/Archived.

---

### ModelVersion

**Purpose**: Tracks which model produced the inferences for a given event.

| Attribute | Type | Description | Mutability | Status |
|-----------|------|-------------|------------|--------|
| `model_version_id` | string | Unique identifier | Immutable | OPEN |
| `model_name` | string | e.g., "YOLOv8n", "EfficientDet-d0" | Immutable | OPEN |
| `weights_hash` | string | Hash of the model weights for provenance | Immutable | OPEN |
| `accuracy_metrics` | object | mAP, recall, precision on a validation set | Immutable | OPEN |
| `is_active` | boolean | Whether this version is the current default for new inferences | Mutable | OPEN |

**Invariants**:
- `model_version_id` is unique.
- `weights_hash` is the cryptographic hash of the model artifact.
- Only one `is_active` version at a time.

**Provenance**: 
- Training experiment ID.
- Dataset version and split.
- Git commit used for training.

**Lifecycle**: Registered → Active → Deprecated → Archived.

---

## Conceptual Relationships

| Relationship | Cardinality | Notes |
|--------------|-------------|-------|
| Camera → PotholeEvent | One-to-Many | A camera produces many events. |
| PotholeEvent → Report | One-to-One or One-to-Zero | An event may have zero or one report. |
| PotholeEvent → Evidence | One-to-Many | An event may have multiple evidence items. |
| ModelVersion → PotholeEvent | One-to-Many | A model version produces many events. |

**Note**: Relationships are described conceptually. Exact foreign key names, join tables, or ORM mappings have not been defined. The final schema (tables, columns, constraints, indexes) will be determined after the database technology is selected and the domain model is stabilized.

---

## Timestamp Semantics

| Entity | Timestamp Fields | Source | Notes |
|--------|------------------|--------|-------|
| Camera | N/A | N/A | Camera position may have a last-updated timestamp. |
| PotholeEvent | `timestamp` | Event Engine | Time the event was finalized. |
| Report | `submitted_at` | Backend API | Time the report was created. |
| Evidence | `captured_at` | Inference pipeline | Time the frame/clip was captured. |
| ModelVersion | N/A | Training | Registration time. |

All timestamps must use UTC with timezone information (ISO 8601).

---

## Evidence Relationship

Evidence is stored separately (object storage or database BLOB) and referenced by `storage_path`. The database stores the reference, not the media itself.

---

## Status Summary

| Entity | Status |
|--------|--------|
| Camera | `OPEN` |
| PotholeEvent | `OPEN` |
| Report | `OPEN` |
| Evidence | `OPEN` |
| ModelVersion | `OPEN` |
| Database technology | `OPEN` |
| Exact columns | `OPEN` |
| Migration strategy | `OPEN` |

---

*All entities and fields are placeholders. Do not fabricate columns to make the document appear complete. The schema will be defined in coordination with the database technology selection and domain model stabilization phases. See PROJECT.md for the source-of-truth map.*