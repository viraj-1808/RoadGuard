# Event Contracts

This directory contains draft and placeholder contract documents for the event interface.

## Authoritative Source

The authoritative event contract documentation is in `docs/`:

- `docs/EVENT_SCHEMAS.md` — Distinguishes Detection, Track, and PotholeEvent
- `docs/INFERENCE_ARCHITECTURE.md` — Event Engine role
- `docs/API_CONTRACTS.md` — Backend → Frontend contract

## Purpose

Event contracts define the interface between:
- Event Engine → Backend API
- Backend API → Frontend

### Detection vs Track vs PotholeEvent

| Concept | Description |
|---------|-------------|
| **Detection** | Single frame-level observation (see `contracts/detection/`) |
| **Track** | Temporal association of detections across frames |
| **PotholeEvent** | Logical/reportable occurrence derived from tracks |

### PotholeEvent Conceptual Fields

- `event_id` — Unique identifier
- `source_id` — Camera/source identifier
- `timestamp` — Time the event was finalized
- `confidence` — Peak confidence across evidence
- `bbox` / `evidence_ref` — Bounding box or reference to stored artifacts
- `location_metadata` — GPS/location information (coarse)
- `status` — Current state (pending, approved, etc.)

## Status

- PotholeEvent schema: **OPEN**
- Track schema: **OPEN**
- Event Engine → Backend contract: **TO BE FINALIZED**