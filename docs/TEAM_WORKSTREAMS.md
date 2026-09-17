# Team Workstreams (4-Person Split)

## Person 1 → ML/Data

### Owns

- Dataset audit (quality, coverage, labeling consistency)
- Dataset preparation (cleaning, format conversion)
- Annotation normalization (to a common detection contract)
- Train/validation/test construction (splits, stratification)
- Training (hyperparameter search, experiment tracking)
- Evaluation (metrics, error analysis, benchmarking)
- Model artifacts (export, versioning)
- Experiment tracking (logs, metrics, artifacts)

### Inputs

- Raw datasets from candidate sources
- Dataset audit results
- Annotation files
- Training configurations

### Outputs

- Versioned datasets
- Dataset manifests
- Split records
- Trained model checkpoints
- Evaluation reports
- Experiment records

### Contracts Consumed

- Detection contract (to understand model output format)
- Dataset versioning metadata

### Contracts Allowed to Change

- Detection contract (only via cross-workstream agreement)
- Dataset pipeline documentation

### Primary Areas

`ml/`, `experiments/`

---

## Person 2 → Backend

### Owns

- API design and implementation (per contract)
- Database schema and migrations
- Event persistence and retrieval services
- Reporting services (aggregations, exports)
- Backend tests (unit, integration, contract)

### Inputs

- PotholeEvent contract (from Person 4)
- Frontend Query API contract (with Person 3)
- Database technology decision

### Outputs

- Backend API
- Database schema
- Event persistence
- Reporting services
- Backend tests

### Contracts Consumed

- PotholeEvent contract (from Person 4)
- Frontend Query API contract (with Person 3)
- Security architecture (authentication/authorization)

### Contracts Allowed to Change

- API contract (only via cross-workstream agreement)
- Database schema (conceptual, with Person 4/3 agreement)

### Primary Area

`backend/`

---

## Person 3 → Frontend

### Owns

- Dashboard (map view, event list, filters)
- Live detection UI (video overlay, controls)
- Pothole/report creation and detail views
- Frontend integration (state management, API client)
- Frontend tests (unit, integration, e2e)

### Inputs

- Frontend Query API contract (from Person 2)
- PotholeEvent schema (from Person 4)
- Backend API responses

### Outputs

- Frontend UI
- Frontend API client
- Frontend tests

### Contracts Consumed

- Frontend Query API contract (from Person 2)
- PotholeEvent schema (from Person 4)

### Contracts Allowed to Change

- API contract (only via cross-workstream agreement)
- Frontend Query API contract (with Person 2)

### Primary Area

`frontend/`

---

## Person 4 → Inference/Integration

### Owns

- Camera capture (device abstraction, frame buffering)
- Frame pipeline (resizing, normalization, format conversion)
- Model adapter (loading, warm-up, inference call)
- Inference runtime (optimizations, batching, device selection)
- Tracking (association of detections over time)
- Event engine (turning tracks into pothole events)
- Deployment/integration (scripts, edge-device considerations)

### Inputs

- Detection contract (from Person 1)
- Model artifacts (from Person 1)
- Event contract (with Person 2)
- Deployment documentation

### Outputs

- Inference engine
- Detection contract (project-owned)
- Event contract (project-owned)
- Inference runtime
- Tracking implementation
- Event engine implementation

### Contracts Consumed

- Detection contract (from Person 1)
- Model artifacts (from Person 1)
- Backend ingestion API (with Person 2)
- Security architecture (input validation, resource limits)

### Contracts Allowed to Change

- Detection contract (only via cross-workstream agreement)
- Event contract (only via cross-workstream agreement)
- Inference architecture documentation

### Primary Area

`inference/`

---

## Shared Areas

- `docs/` – Documentation that all members maintain.
- `contracts/` – Interface definitions (detection, event, API) that are version-controlled and evolve via explicit agreement.
- `tests/` – Shared test utilities and contract-level tests; each workstream writes tests for its own code but may rely on shared helpers.

---

## Dependency Graph

```
ML → Detection Contract → Inference → Event Contract → Backend → API Contract → Frontend
```

- ML produces a model that conforms to the detection contract.
- Inference depends only on the detection contract (not on ML internals).
- Inference outputs detections that must satisfy the event contract.
- Backend depends only on the event contract.
- Frontend depends only on the API contract.

---

## Parallel-Development Principle

Developers should work against **stable contracts and mocks** instead of waiting for unfinished implementations.

### Mock Dependencies

| Workstream | Mock Dependency | Purpose |
|------------|-----------------|---------|
| ML | Mock dataset (synthetic or minimal) | Validate data pipeline code |
| Inference | MockDetector | Returns fixed detections obeying the detection contract |
| Backend | MockEventProducer | Emits events respecting the event contract |
| Frontend | Mock API | Serves responses respecting the API contract |

### Notes

- Synthetic data can be used as a future experiment, not the default ML workflow.
- Mocks must conform to the documented contracts.
- Do not wait for upstream implementations to begin contract-driven development.

---

## Team Rule

No major cross-component contract change should be made silently. Any change to a contract (detection, event, API) must:

1. Be proposed in the relevant documentation (`docs/` or `contracts/`).
2. Be reviewed and agreed upon by all affected workstreams.
3. Be versioned (e.g., v2 of the detection contract) and communicated explicitly.
4. Be accompanied by migration steps or backward-compatibility shims if needed.

---

*Consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*