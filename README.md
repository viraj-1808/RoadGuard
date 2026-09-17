# Pothole Detection & Reporting System

The Pothole Detection & Reporting System trains a pothole object detector, evaluates it rigorously, supports eventual image/video/live-camera inference, converts temporal detections into pothole events, and exposes those events through a backend/reporting system.

## Architecture Summary

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
Inference
↓
Tracking
↓
Event
↓
Backend
↓
Frontend
```

## Repository Structure

- `docs/` – Documentation, including project overview, team workstreams, architecture, and research register.
- `contracts/` – Interface definitions (detection, event, API) that enable parallel development.
- `ml/` – Machine learning code: data preprocessing, training, evaluation, and model utilities.
- `inference/` – Runtime components for capture, preprocessing, model adaptation, detection, tracking, and event engine.
- `backend/` – API server, database models, services, and reporting logic.
- `frontend/` – User interface: dashboard, live detection view, and report management.
- `experiments/` – Tracking of training runs, benchmarks, and ablation studies.
- `tests/` – Unit, integration, and system tests for all components.
- `scripts/` – Utility and automation scripts.

## Team Ownership

Detailed responsibilities are outlined in `docs/TEAM_WORKSTREAMS.md`.

## Current State

- **Research/architecture phase**: COMPLETE
- **Repository foundation**: INITIALIZED
- **Implementation**: NOT STARTED
- **Dataset composition**: NOT YET LOCKED
- **Final model**: NOT YET LOCKED
- **Backend/frontend technology**: NOT YET LOCKED

## Source of Truth

| Topic | Document |
|-------|----------|
| Project scope | `docs/PROJECT.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Dataset pipeline | `docs/DATA_PIPELINE.md` |
| Training | `docs/MODEL_TRAINING.md` |
| Evaluation | `docs/MODEL_EVALUATION.md` |
| Inference | `docs/INFERENCE_ARCHITECTURE.md` |
| Event schema | `docs/EVENT_SCHEMAS.md` |
| API contracts | `docs/API_CONTRACTS.md` |
| Database | `docs/DATABASE_SCHEMA.md` |
| Security | `docs/SECURITY_ARCHITECTURE.md` |
| Deployment | `docs/DEPLOYMENT.md` |
| Research evidence | `docs/RESEARCH_REGISTER.md` |
| Major decisions | `docs/DECISION_LOG.md` |
| Engineering lessons | `docs/ENGINEERING_LOG.md` |

If two authoritative sources conflict: STOP. Resolve the conflict explicitly. Do not silently pick one.

## Authoritative Contract Sources

- Detection: `docs/EVENT_SCHEMAS.md#Detection`
- Track: `docs/EVENT_SCHEMAS.md#Track`
- PotholeEvent: `docs/EVENT_SCHEMAS.md#PotholeEvent`
- Report: `docs/EVENT_SCHEMAS.md#Report`
- API: `docs/API_CONTRACTS.md`

---

*See PROJECT.md for project definition and ARCHITECTURE.md for detailed architecture.*