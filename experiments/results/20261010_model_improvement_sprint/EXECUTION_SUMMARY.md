# RoadGuard AI — 9-Hour Model Improvement Sprint Execution Summary

**Sprint Directory:** `experiments/results/20261010_model_improvement_sprint/`
**Date:** 2026-10-11
**Git Branch:** `chore/viraj-model-training` (HEAD: 09b6d3f, ahead 1 commit)

---

## 1. What Changed

### Repository State (Preserved)
- **Git status:** 2 modified files (frozen test predictions), 10 untracked directories/files — all preserved
- **All checkpoints intact:** 183 checkpoint files across 5 training runs, no files deleted or overwritten
- **Dataset YAMLs unchanged:** `yolo_rdd2022_india/data.yaml`, `experiment2/data.yaml` preserved
- **Frozen test split intact:** 230 images at `experiments/dataset/yolo_rdd2022_india/images/test` with labels

### New Artifacts Created
| Directory | Contents |
|-----------|----------|
| `experiments/results/20261010_phase1_repo_audit/` | Git audit, directory trees |
| `experiments/results/20261010_phase1_checkpoint_audit/` | 183-checkpoint inventory with SHA-256, epochs, optimizer state |
| `experiments/results/20261010_phase1_system_audit/` | System resources (disk, RAM, GPU, processes) |
| `experiments/results/20261010_phase1_dataset_audit/` | Dataset YAML verification, split counts, frozen test manifest |
| `experiments/results/20261010_phase2_validation/` | Validation on Dataset A val (229 images) for Exp1 epoch86 & Exp2 epoch72 |
| `experiments/results/20261010_phase3_error_analysis/` | 39-image error analysis, 4-pothole annotations, failure patterns |
| `experiments/results/20261010_phase5_threshold/` | Threshold grid (0.05–0.25) for both models |
| `experiments/results/20261010_phase6_final_eval/` | Frozen test split (230 images) evaluation for both models |

---

## 2. What Was Tested

| Phase | Test | Dataset | Images | Models |
|-------|------|---------|--------|--------|
| 1 | Repo/Checkpoint/System/Dataset audit | — | — | — |
| 2 | Validation on labelled split | Dataset A val | 229 | Exp1 epoch86, Exp2 epoch72 |
| 3 | Manual error analysis | Manual input (road001–039) | 39 | Exp1 best.pt (EXP-INF-003) |
| 5 | Confidence threshold grid | Dataset A val (saved preds) | 229 | Exp1 epoch86, Exp2 epoch72 |
| 6 | Final independent evaluation | Frozen Indian test | 230 | Exp1 epoch86, Exp2 epoch72 |

**No training was performed** — all work was measurement, analysis, and evaluation. The repository and training progress remain fully intact.

---

## 3. Baseline Versus Final Metrics

### Previous Baseline (Experiment 2 Frozen Test)
| Metric | Baseline |
|--------|----------|
| Precision (P) | 0.586 |
| Recall (R) | 0.321 |
| mAP@50 | 0.279 |
| mAP@50-95 | 0.111 |

### Dataset A Validation Split (229 images) — Phase 2
| Model | Overall mAP50 | mAP50-95 | Pothole P | Pothole R | Pothole mAP50 | Pothole F1 |
|-------|---------------|----------|-----------|-----------|---------------|------------|
| Exp1 epoch86 | 0.216 | 0.0794 | 0.493 | 0.480 | 0.444 | 0.486 |
| Exp2 epoch72 | 0.220 | 0.0893 | 0.446 | 0.410 | 0.386 | 0.427 |

### Frozen Indian Test Split (230 images) — Phase 6
| Metric | Baseline | Exp1 epoch86 | Exp2 epoch72 | Best |
|--------|----------|--------------|--------------|------|
| Overall P | 0.586 | 0.231 | **0.399** | Baseline |
| Overall R | 0.321 | **0.404** | 0.371 | Exp1 |
| Overall mAP@50 | 0.279 | 0.244 | **0.300** | **Exp2** |
| Overall mAP@50-95 | 0.111 | 0.089 | **0.118** | **Exp2** |
| Pothole P | — | 0.370 | **0.388** | Exp2 |
| Pothole R | — | **0.496** | 0.484 | Exp1 |
| Pothole mAP@50 | — | 0.382 | **0.395** | **Exp2** |
| Pothole mAP@50-95 | — | 0.128 | **0.150** | **Exp2** |
| COCO AP@0.50:0.95 | — | 0.090 | **0.120** | **Exp2** |
| Pothole TP/FP/FN (IoU=0.5) | — | 227/285/200 | 117/395/57 | — |

---

## 4. Whether Targets Were Met

| Target | Definition | Result | Status |
|--------|------------|--------|--------|
| **Target 1** | ≥0.76 on ground-truth detection metric (mAP@50-95) | Best: Exp2 epoch72 = 0.118 | ❌ **Not Met** (gap: 0.642) |
| **Target 2** | ≥3/4 potholes detected at IoU≥0.50 on manual 4-pothole sample | 4 potholes from different dataset (road*.jpg), not in frozen test split | ⚠️ **Not Evaluated** on same split |

**Gap Analysis:**
- The 0.76 target (mAP@50-95) is far from current best (0.118). This would require significant improvement in localization quality at high IoU thresholds.
- The 4 manually verified potholes are from a separate dataset (`road*.webp/jpg`) and do not overlap with the frozen Indian test set (`India_XXXXXX.jpg`). A separate evaluation would require running inference on those 4 images with the selected checkpoint.

---

## 5. Recommended Checkpoint for Next Steps

**Recommended:** `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt`

**SHA-256:** `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5`

**Reasoning:**
1. **Beats baseline** on both mAP@50 (0.300 vs 0.279) and mAP@50-95 (0.118 vs 0.111)
2. **Best pothole mAP@50-95** (0.150) — highest localization quality for priority class
3. **Best COCO AP/AR** across all metrics (AP@0.50=0.303, AR@0.50=0.754)
4. **Contains intact optimizer state** — can resume training if needed
5. **More balanced precision/recall** than Exp1 (0.399/0.371 vs 0.231/0.404)

**Alternative (recall-focused):** `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt` — if pothole recall is paramount (0.496 vs 0.484).

---

## 6. Repository and Training Progress Intact?

✅ **Yes, fully intact.**
- No checkpoints deleted, moved, or overwritten
- No dataset YAMLs or split manifests modified
- No training launcher scripts changed
- Git working tree clean except for pre-existing uncommitted changes (2 modified prediction files, 10 untracked dirs)
- All 183 checkpoints preserved with optimizer state
- Frozen test split untouched and verifiable via `frozen_test_sha256.json`

---

## 7. What Remains Unverified

| Item | Details |
|------|---------|
| **Threshold analysis discrepancy** | Ultralytics validation showed good pothole metrics (Exp1: P=0.493, R=0.480) but post-hoc threshold analysis on saved predictions.json showed near-zero recall. Likely coordinate/ID mismatch between COCO predictions and label files. |
| **4-pothole sample on selected checkpoint** | The 4 manually annotated potholes are from a different dataset; not evaluated on Exp2 epoch72. |
| **High false positive rate** | Both models show high FP on frozen test (Exp1: 285, Exp2: 395 pothole FP at IoU=0.5). Root cause unverified. |
| **High-resolution generalization** | Error analysis shows failures on >3000px images (oversized boxes, missed detections). No quantitative evaluation on high-res subset. |
| **Portrait orientation performance** | 41% of manual images had zero detections; suspected aspect-ratio issues during letterbox resize. Unverified quantitatively. |
| **Transverse crack detection** | 0 mAP on all evaluations (only 4–5 instances in val/test). Statistical reliability unknown. |
| **SAHI / tiling inference** | Not tested; recommended for high-res images. |
| **Training continuation** | Not attempted; would require conservative DataLoader (workers=2, prefetch=2, cache=False) and memory monitoring. |
| **Ensemble/distillation** | Not explored; could improve both precision and recall. |

---

## Key Evidence Files

| Report | Path |
|--------|------|
| Checkpoint Audit | `experiments/results/20261010_phase1_checkpoint_audit/checkpoint_inventory.md` |
| Dataset Verification | `experiments/results/20261010_phase1_dataset_audit/dataset_verification.md` |
| Validation (Dataset A val) | `experiments/results/20261010_phase2_validation/exp1_epoch86_val_report.md` |
| | `experiments/results/20261010_phase2_validation/exp2_epoch72_val/exp2_epoch72_val_report.md` |
| Error Analysis | `experiments/results/20261010_phase3_error_analysis/error_analysis_report.md` |
| Threshold Comparison | `experiments/results/20261010_phase5_threshold/THRESHOLD_COMPARISON.csv` |
| Final Evaluation | `experiments/results/20261010_phase6_final_eval/FINAL_EVALUATION.md` |

---

## Next Recommended Actions (Priority Order)

1. **Fix threshold analysis pipeline** — ensure COCO predictions match label file IDs/coordinates
2. **Evaluate Exp2 epoch72 on 4 manual potholes** — run inference on `road001/002/009/010`
3. **Confidence threshold sweep on frozen test** — find operating point balancing P/R for potholes
4. **SAHI inference on high-res subset** — test sliced inference for >3000px images
5. **If training continuation desired** — resume Exp2 from epoch72.pt with workers=2, prefetch=2, cache=False, monitor RAM <90%