# Security Architecture

## Overview

This document turns the security checklist into a threat model. The current system is an engineering project. Security controls are planned but **not implemented**.

---

## Assets

| Asset | Description | Owner | Status |
|-------|-------------|-------|--------|
| Model artifacts | Trained model weights | Person 1 (produces), Person 4 (loads) | `OPEN` |
| Datasets | Raw and prepared data | Person 1 | `OPEN` |
| Camera streams | Live/recorded video feeds | Person 4 | `OPEN` |
| Evidence | Frames, clips, media artifacts | Person 2 | `OPEN` |
| Location metadata | GPS/camera location data | Person 2 | `OPEN` |
| Reports | Maintenance reports | Person 2 | `OPEN` |
| API credentials | Backend/frontend credentials | Person 2 | `OPEN` |

---

## Trust Boundaries

```text
[Camera] → [Inference Machine] → [Backend] → [Database]
                                      ↓
                                   [Frontend]
                                      ↓
                               [External Clients]
```

| Boundary | From | To | Risk |
|----------|------|-----|------|
| Camera → Inference | Camera | Inference Machine | Malicious input, resource exhaustion |
| Inference → Backend | Inference Machine | Backend | Unauthorized access, duplicate/replay requests |
| Backend → Database | Backend | Database | Unauthorized access, data corruption |
| Backend → Frontend | Backend | Frontend | Unauthorized access, data leakage |
| External Clients → Backend | External Clients | Backend | Unauthorized access, injection |

---

## Threat Categories

### 1. Malicious Input

- **Threat**: Malicious or malformed input to the inference pipeline or backend API.
- **Assets at risk**: Camera streams, datasets, inference engine, backend.
- **Control**: Input validation at all ingestion points.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 2. Resource Exhaustion

- **Threat**: Memory exhaustion, CPU/GPU exhaustion, unbounded queues.
- **Assets at risk**: Inference machine, backend, database.
- **Control**: Resource limits, bounded queues, timeout enforcement.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 3. Artifact Tampering

- **Threat**: Model weights or datasets are modified or replaced.
- **Assets at risk**: Model artifacts, datasets.
- **Control**: Cryptographic hash verification, provenance tracking, trusted model loading.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 4. Dataset Poisoning

- **Threat**: Malicious or incorrect data is introduced into the dataset.
- **Assets at risk**: Datasets, model artifacts.
- **Control**: Dataset provenance tracking, audit trails, checksum verification.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 5. Unauthorized Access

- **Threat**: Unauthorized users access the backend, frontend, or database.
- **Assets at risk**: Reports, location metadata, evidence, API credentials.
- **Control**: Authentication, authorization, TLS for remote communication.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 6. Media Leakage

- **Threat**: Sensitive media (video frames, evidence) is exposed in logs or to unauthorized users.
- **Assets at risk**: Camera streams, evidence, location metadata.
- **Control**: Sensitive-media logging restrictions, access control.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

### 7. Duplicate / Replay Requests

- **Threat**: Duplicate or replayed requests cause duplicate events or reports.
- **Assets at risk**: PotholeEvents, Reports, Evidence.
- **Control**: Idempotent event ingestion, request deduplication.
- **Status**: `PLANNED` / `NOT IMPLEMENTED`

---

## Controls

| Threat | Control | Implementation Status |
|--------|---------|----------------------|
| Malicious input | Input validation | `PLANNED` / `NOT IMPLEMENTED` |
| Resource exhaustion | Resource limits, bounded queues | `PLANNED` / `NOT IMPLEMENTED` |
| Artifact tampering | Hash verification, provenance tracking | `PLANNED` / `NOT IMPLEMENTED` |
| Dataset poisoning | Provenance tracking, audit trails | `PLANNED` / `NOT IMPLEMENTED` |
| Unauthorized access | Authentication, authorization, TLS | `PLANNED` / `NOT IMPLEMENTED` |
| Media leakage | Sensitive-media logging restrictions | `PLANNED` / `NOT IMPLEMENTED` |
| Duplicate / replay | Idempotent event ingestion | `PLANNED` / `NOT IMPLEMENTED` |

---

## Security Principles

- All user-supplied data must be validated before processing.
- Model artifacts must be verified before loading.
- Dataset provenance must be traceable.
- Communication must be encrypted when remote.
- Logs must not contain sensitive media without explicit consent.
- Event processing must be idempotent to handle retries safely.

## Status

- **Security architecture**: `DRAFTED` / `PLANNED`
- **Security controls**: `NOT IMPLEMENTED`
- **Security testing**: `NOT STARTED`

---

*Consistent with ARCHITECTURE.md and DEPLOYMENT.md. See PROJECT.md for the source-of-truth map.*