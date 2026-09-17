# API Contracts

## Overview

This document defines the contracts between system stages. Each stage owns its contract. Downstream stages must not assume implementation details of upstream stages beyond the defined contract boundary.

**IMPORTANT**: All exact field schemas are marked DRAFT or OPEN. Do not implement production schemas from these documents. The exact schemas will be finalized after the relevant research is complete.

---

## Contract Flow

```text
Detection Contract
      ↓
Track Contract
      ↓
PotholeEvent Contract
      ↓
Backend Ingestion API
      ↓
Frontend Query API
```

Each section below documents the contract at that boundary. Exact schemas remain DRAFT/OPEN.

---

## 1. Detection Contract

### Purpose

Defines the interface between the Detection Normalization stage and the Tracker. A Detection is a single frame-level observation.

### Owner

Person 4 (Inference).

### Direction

Detection Normalization → Tracker.

### Fields (DRAFT)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `class` | string | Detected object class (e.g., `"pothole"`) | DRAFT |
| `confidence` | float | Model confidence score [0–1] | DRAFT |
| `bbox` | array[4] | `[x1, y1, x2, y2]` in pixel coordinates (relative to frame) | DRAFT |
| `frame_id` | string | Identifier of the frame / capture context | DRAFT |
| `capture_timestamp` | datetime | Time the frame was captured | DRAFT |

### Key Constraint

The Detection contract must NOT include framework-specific model output types (e.g., no YOLO output format, no RF-DETR specific types).

### Authoritative Source

`docs/EVENT_SCHEMAS.md#Detection`

### Status

DRAFT / TO BE FINALIZED

---

## 2. Track Contract

### Purpose

Defines the interface between the Tracker and the Event Engine. A Track is a temporal association of detections.

### Owner

Person 4 (Inference).

### Direction

Tracker → Event Engine.

### Fields (DRAFT)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `track_id` | string | Unique identifier for the track | DRAFT |
| `source_id` | string | Identifier of the capture source | DRAFT |
| `first_seen` | datetime | Timestamp of first detection in the track | DRAFT |
| `last_seen` | datetime | Timestamp of most recent detection | DRAFT |
| `status` | string | Track state (e.g., `active`, `expired`, `confirmed`) | DRAFT |

### Authoritative Source

`docs/EVENT_SCHEMAS.md#Track`

### Status

DRAFT / TO BE FINALIZED

---

## 3. PotholeEvent Contract

### Purpose

Defines the interface between the Event Engine and the Backend Ingestion API. A PotholeEvent is a logical/reportable occurrence.

### Owner

Person 4 (Inference, produces), Person 2 (Backend, consumes).

### Direction

Event Engine → Backend Ingestion API.

### Fields (OPEN)

| Field | Type | Description | Status |
|-------|------|-------------|--------|
| `event_id` | string | Unique identifier for the pothole event | OPEN |
| `source_id` | string | Identifier of the capture source | OPEN |
| `timestamp` | datetime | Time the event was finalized | OPEN |
| `confidence` | float | Confidence across evidence | OPEN |
| `bbox` | array[4] | Bounding box or null | OPEN |
| `location` | object | GPS/location metadata | OPEN |
| `evidence` | array | References to frames/clips | OPEN |
| `status` | string | Current state | OPEN |
| `report_id` | string | Optional link to a Report | OPEN |

### Key Constraints

- The PotholeEvent must NOT contain framework-specific detector types.
- Ingestion must be idempotent (see SECURITY_ARCHITECTURE.md).

### Authoritative Source

`docs/EVENT_SCHEMAS.md#PotholeEvent`

### Status

OPEN

---

## 4. Backend Ingestion API

### Purpose

Defines the interface between the Event Publisher (Inference) and the Backend API. Responsible for receiving PotholeEvents from the inference pipeline.

### Owner

Person 2 (Backend).

### Direction

Event Publisher (Inference) → Backend API.

### Endpoints (Conceptual)

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/api/events` | Ingest a PotholeEvent | OPEN |
| GET | `/api/events/{id}` | Retrieve a PotholeEvent | OPEN |
| GET | `/api/events` | List/query events | OPEN |
| PATCH | `/api/events/{id}/status` | Update event status | OPEN |

### Key Constraints

- Must accept PotholeEvent contract only.
- Must NOT depend on detector/framework-specific types.
- Must be idempotent.
- Must handle network failures gracefully.

### Authoritative Source

This document + `docs/API_CONTRACTS.md` (this section).

### Status

OPEN

---

## 5. Frontend Query API

### Purpose

Defines the interface between the Frontend and the Backend API. Responsible for serving event data, reports, and dashboard information.

### Owner

Person 2 (Backend, provides), Person 3 (Frontend, consumes).

### Direction

Frontend → Backend API.

### Endpoints (Conceptual)

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/api/events` | List events with filters | OPEN |
| GET | `/api/events/{id}` | Get event details | OPEN |
| GET | `/api/events/{id}/evidence` | Get event evidence | OPEN |
| POST | `/api/reports` | Create a report | OPEN |
| GET | `/api/reports` | List reports | OPEN |
| PATCH | `/api/reports/{id}` | Update report | OPEN |

### Key Constraints

- Must NOT expose backend/database internals to the frontend.
- Must serve only data described by the Frontend Query API contract.
- Must NOT depend on detector/framework-specific types.
- Authentication/authorization to be defined (see SECURITY_ARCHITECTURE.md).

### Authoritative Source

This document + `docs/API_CONTRACTS.md` (this section).

### Status

OPEN

---

## Summary of Status Markers

- `DRAFT` – Early conceptual placeholder, subject to change.
- `TO BE FINALIZED` – Awaiting design decision or research input.
- `OPEN` – Schema not yet started; may be defined later in the project.

---

*All terminology and status labels are consistent with ARCHITECTURE.md, EVENT_SCHEMAS.md, and SECURITY_ARCHITECTURE.md. See PROJECT.md for the source-of-truth map.*