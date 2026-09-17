# Event Schemas

## Schema Hierarchy

The project's event domain follows this hierarchy:

```text
Detection
  ↓
Track
  ↓
PotholeEvent
  ↓
Report
```

Each entity has a distinct purpose, identity, lifecycle, and ownership. A Detection is a single frame-level observation. A Track is a temporal association of detections. A PotholeEvent is a logical/reportable occurrence derived from tracks. A Report is a human or agency-initiated action derived from a PotholeEvent.

---

## 1. Detection

### Purpose

A single frame-level observation produced by the detector. It represents what the model believes is present in one frame at one time.

### Identity

- `detection_id`: Unique identifier for the detection (ephemeral; may not be persisted).
- `frame_id`: Identifier of the frame / capture context.

### Owner

- **Produced by**: Model Adapter / Detection Normalization (Person 4).
- **Consumed by**: Tracker (Person 4).

### Lifecycle

```text
Raw model output
  ↓
Detection Normalization
  ↓
Detection (in memory / ephemeral)
  ↓
Consumed by Tracker
```

Detections are ephemeral and are not persisted to the database. They may be referenced by a Track or Evidence.

### Required Fields (DRAFT)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `class` | string | Detected object class (e.g., `"pothole"`) | DRAFT |
| `confidence` | float | Model confidence score [0–1] | DRAFT |
| `bbox` | array[4] | `[x1, y1, x2, y2]` in pixel coordinates (relative to frame) | DRAFT |
| `frame_id` | string | Identifier of the frame / capture context | DRAFT |
| `capture_timestamp` | datetime | Time the frame was captured | DRAFT |

### Optional Fields (DRAFT)

- `track_id`: Optional track identifier if tracking is active.
- `source_id`: Identifier of the capture source.

### Provenance

- Model artifact (model version) that produced the detection.
- Preprocessing version.
- Source frame identifier.

### State Transitions

- `created` → `consumed` (by tracker) → `retained` (if referenced by track/evidence) → `purged` (after retention period).

### Failure Behavior

- **Invalid confidence**: Clamp or reject; do not emit detections with invalid confidence.
- **Invalid bbox**: Reject; do not emit detections with invalid bounding boxes.
- **Missing frame_id**: Reject; do not emit detections without frame identity.

### Status

- Detection schema: `DRAFT / TO BE FINALIZED`
- Detection implementation: `NOT STARTED`

---

## 2. Track

### Purpose

Temporal association of detections across frames. A track represents a hypothesized object trajectory over time.

### Identity

- `track_id`: Unique identifier for the track.
- `source_id`: Identifier of the capture source (camera/vehicle).

### Owner

- **Produced by**: Tracker (Person 4).
- **Consumed by**: Event Engine (Person 4).

### Lifecycle

```text
First Detection
  ↓
Track Created
  ↓
Track Updated (detections added)
  ↓
Track Expired (no recent detections) or Promoted to PotholeEvent
```

### Required Fields (DRAFT)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `track_id` | string | Unique identifier for the track | DRAFT |
| `source_id` | string | Identifier of the capture source | DRAFT |
| `first_seen` | datetime | Timestamp of first detection in the track | DRAFT |
| `last_seen` | datetime | Timestamp of most recent detection | DRAFT |
| `detections` | array | References to constituent Detection events | DRAFT |

### Optional Fields (DRAFT)

- `avg_confidence`: Average confidence across detections.
- `max_confidence`: Peak confidence across detections.
- `bbox_history`: Bounding box history over time.
- `status`: Track state (e.g., `active`, `expired`, `confirmed`).

### Provenance

- List of detection IDs that constitute the track.
- Model artifact that produced the detections.

### State Transitions

- `active` → `confirmed` (promoted to candidate event) → `closed` (event confirmed/closed).
- `active` → `expired` (no recent detections).
- `active` → `invalid` (track failure).

### Failure Behavior

- **Track loss**: Log and continue; do not fabricate track associations.
- **ID switching**: Log; do not fabricate track associations.
- **No recent detections**: Mark as expired.

### Status

- Track schema: `DRAFT / TO BE FINALIZED`
- Tracker implementation: `NOT STARTED`

---

## 3. PotholeEvent

### Purpose

A logical/reportable occurrence. A track may be promoted to a PotholeEvent if it satisfies persistence and confidence thresholds. The Event Engine converts tracks into PotholeEvents.

**Critical**: The exact final schema of PotholeEvent is **OPEN**. Fields may be added, removed, or restructured as the Event Engine and reporting workflow are implemented. No production schema should be locked in until the research and design phase is complete.

### Identity

- `event_id`: Unique identifier for the pothole event.
- `source_id`: Identifier of the capture source (camera/vehicle).

### Owner

- **Produced by**: Event Engine (Person 4).
- **Consumed by**: Backend API (Person 2).

### Lifecycle

```text
Track
  ↓
Candidate Event
  ↓
Confirmed Event
  ↓
Closed Event
```

### Conceptual Fields (OPEN)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `event_id` | string | Unique identifier for the pothole event | OPEN |
| `source_id` | string | Identifier of the capture source | OPEN |
| `timestamp` | datetime | Time the event was finalized / reported | OPEN |
| `confidence` | float | Confidence across evidence | OPEN |
| `bbox` | array[4] | Bounding box or null if location is estimated | OPEN |
| `location` | object | GPS/location metadata | OPEN |
| `evidence` | array | References to frames, clips, or stored media | OPEN |
| `status` | string | Current state | OPEN |
| `report_id` | string | Optional link to a downstream Report entity | OPEN |

### OPEN Fields (Not Yet Decided)

- `location semantics`: How camera/vehicle location maps to estimated pothole location.
- `confidence aggregation`: How confidence is aggregated across detections.
- `event confirmation`: Rules for promoting a track to a confirmed event.
- `event closure`: Rules for closing events.
- `status transitions`: Full state machine for events.
- `evidence model`: How evidence (frames, clips) is stored and referenced.
- `duplicate suppression`: How duplicate events are identified and suppressed.

### Provenance

- Track ID(s) that produced the event.
- Model artifact that produced the detections.
- Evidence references (frame IDs, clip IDs).

### State Transitions (OPEN)

- `candidate` → `confirmed` → `closed` (provisional; exact transitions OPEN).
- `candidate` → `rejected` (provisional; exact transitions OPEN).

### Failure Behavior

- **Confirmation rule failure**: Log and do not confirm; do not emit false events.
- **Event creation failure**: Log and do not emit; do not fabricate event IDs.
- **Duplicate event**: Suppress or deduplicate according to rules (OPEN).

### Status

- PotholeEvent schema: `OPEN`
- Event Engine implementation: `NOT STARTED`

---

## 4. Report

### Purpose

A human or agency-initiated action derived from a PotholeEvent. A Report is created when a human or agency decides to act on a PotholeEvent (e.g., schedule repair).

### Identity

- `report_id`: Unique identifier for the report.
- `event_id`: Link to the originating PotholeEvent.

### Owner

- **Produced by**: Backend API (Person 2) or external agency.
- **Consumed by**: Frontend (Person 3).

### Lifecycle

```text
PotholeEvent
  ↓
Report Created
  ↓
Report Updated (status changes)
  ↓
Report Resolved
```

### Required Fields (DRAFT)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `report_id` | string | Unique identifier for the report | DRAFT |
| `event_id` | string | Link to the originating PotholeEvent | DRAFT |
| `submitted_by` | string | Entity or user who created the report | DRAFT |
| `submitted_at` | datetime | Timestamp of report creation | DRAFT |

### Optional Fields (DRAFT)

- `priority`: Service level or urgency classification.
- `resolution`: Status code or text for how the report was handled.
- `status`: Current state (e.g., `pending`, `approved`, `resolved`).

### Provenance

- PotholeEvent ID that produced the report.
- User or agency that created the report.

### State Transitions (DRAFT)

- `pending` → `approved` → `resolved` (provisional; exact transitions OPEN).

### Failure Behavior

- **Invalid event reference**: Reject; do not create report.
- **Duplicate report**: Reject or deduplicate according to rules (OPEN).

### Status

- Report schema: `DRAFT / TO BE FINALIZED`
- Report implementation: `NOT STARTED`

---

## Status Legend

| Status | Meaning |
|--------|---------|
| `DRAFT` | Early conceptual placeholder, subject to change. |
| `TO BE FINALIZED` | Awaiting design decision or research input. |
| `OPEN` | Schema not yet started; subject to change as the project evolves. |

---

*Consistent with ARCHITECTURE.md, API_CONTRACTS.md, and DATABASE_SCHEMA.md terminology. See PROJECT.md for the source-of-truth map.*