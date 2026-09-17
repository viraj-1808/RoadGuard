# Research Register

This document records research evidence independently from architectural decisions. It provides a transparent record of what research was performed, what was found, and what engineering implications were drawn.

## Purpose

To ensure that engineering decisions are traceable to research evidence and to enable future researchers to understand the reasoning behind architectural choices.

## Template

```text
Research ID:
Question:
Topic:
Source:
Source date:
Technology / Dataset:
Version:
Finding:
Evidence:
Engineering implication:
Confidence:
Affected decision:
Date checked:
Revisit condition:
Status:
```

---

## Research Entries

### R-001: Dataset Candidate Survey

- **Question**: Which dataset sources are viable for pothole detection in India?
- **Topic**: Dataset survey
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: RDD2022, BharatPotHole, RAD, RDD2020, HRP4K
- **Version**: As listed in candidate survey
- **Finding**: Each candidate has strengths; exact suitability requires annotation audit and leakage analysis.
- **Evidence**: `docs/DATA_PIPELINE.md` lists candidate sources with required properties.
- **Engineering implication**: Dataset audit phase is required before dataset version can be locked.
- **Confidence**: MEDIUM
- **Affected decision**: D-005 (Indian + forward-camera priority), D-006 (group-based leakage prevention)
- **Date checked**: 2026-09-17
- **Revisit condition**: After dataset audit is performed.
- **Status**: UNDER AUDIT

---

### R-002: Model Candidate Survey

- **Question**: Which detector architectures are reasonable candidates for pothole detection?
- **Topic**: Model survey
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: YOLO11s, YOLO26s, RF-DETR-S
- **Version**: As listed in candidate survey
- **Finding**: Each candidate has trade-offs in architecture, latency, and performance. Empirical comparison is required.
- **Evidence**: `docs/MODEL_TRAINING.md` lists candidate models; `docs/MODEL_EVALUATION.md` defines evaluation protocol.
- **Engineering implication**: Experiments must follow the same dataset, split, and evaluation protocol for fair comparison.
- **Confidence**: MEDIUM
- **Affected decision**: D-004 (candidate-model comparison)
- **Date checked**: 2026-09-17
- **Revisit condition**: After experiments are completed.
- **Status**: PENDING

---

### R-003: Pretraining / Fine-Tuning Effectiveness

- **Question**: Does pretrained initialization + fine-tuning outperform training from scratch on pothole detection?
- **Topic**: Transfer learning evaluation
- **Source**: Research/architecture discovery phase (internal)
- **Source date**: 2026-09-17
- **Technology / Dataset**: Not yet evaluated
- **Version**: N/A
- **Finding**: Transfer learning is the primary training strategy; a controlled comparison with training from scratch may be evaluated as a secondary experiment.
- **Evidence**: `docs/MODEL_TRAINING.md` documents the primary training philosophy.
- **Engineering implication**: All experiments must begin with pretrained initialization; training from scratch is secondary.
- **Confidence**: HIGH (architectural decision; not empirically verified on our dataset)
- **Affected decision**: D-003 (transfer learning as primary training strategy)
- **Date checked**: 2026-09-17
- **Revisit conditions**: After the controlled comparison experiment (if performed).
- **Status**: LOCKED (strategy direction)

---

---

*This register is intentionally minimal at project inception. Entries will be added as research is performed.*

*See PROJECT.md and DECISION_LOG.md for related source-of-truth documents.*