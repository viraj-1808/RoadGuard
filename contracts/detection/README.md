# Detection Contracts

This directory contains draft and placeholder contract documents for the detection interface.

## Authoritative Source

The authoritative detection contract documentation is in `docs/`:

- `docs/ARCHITECTURE.md` — Detection pipeline architecture
- `docs/INFERENCE_ARCHITECTURE.md` — Detection normalization and model adapter
- `docs/EVENT_SCHEMAS.md` — Detection schema (frame-level observation)
- `docs/API_CONTRACTS.md` — Inference → Event contract

## Purpose

Detection contracts define the interface between:
- Model Adapter → Frame Pipeline
- Frame Pipeline → Tracker/Event Engine

A **Detection** is a single frame-level observation containing:
- `class` — Detected class label (e.g., "pothole")
- `confidence` — Model confidence score [0–1]
- `bbox` — Bounding box `[x1, y1, x2, y2]` in pixel coordinates
- `frame_id` — Identifier of the frame / capture context
- `capture_timestamp` — Time the frame was captured

## Status

- Detection schema: **DRAFT / TO BE FINALIZED**
- Model adapter interface: **OPEN**

When finalized, the detection contract will be the single authoritative source for the Detection type used across the system.