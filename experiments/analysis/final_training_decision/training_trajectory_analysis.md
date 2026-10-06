# Training Trajectory Analysis — YOLO11s Experiment 2

**Analysis date:** 2026-10-06
**Run directory:** `runs/detect/experiments/training/yol11s_experiment2/`
**Status:** ANALYSIS WAS NOT PREVIOUSLY COMPLETED — this is the first trajectory analysis
**Analyst note:** Timestamps on disk are interpreted as dd-MM-yyyy (consistent with system date 2026-10-06).

---

## 1. Data Availability Audit (critical finding)

| Expected artifact | Status | Consequence |
|---|---|---|
| `experiments/analysis/final_training_decision/training_trajectory_analysis.md` | **MISSING** (this report fills the gap) | Analysis had not been completed |
| `runs/detect/experiments/training/yol11s_experiment2/results.csv` | **MISSING** | Per-epoch loss/metric trajectory cannot be read directly |
| `yol11s_experiment2/results.png` | Present (2026-10-05 16:10) | Proves `results.csv` existed at training completion and was deleted afterward |
| `yol11s_experiment2/args.yaml` | Present (rewritten 2026-10-06 03:41) | Full config recoverable |
| `yol11s_experiment2/weights/epoch0.pt … epoch29.pt` | Present (30/30) | Run completed all 30 epochs; per-epoch val metrics are reconstructable |
| `yol11s_experiment2/weights/best.pt` | Present, SHA256 `E79F8103…DFDD791` | Matches checksum in `EXP2_FROZEN_DATASET_A_TEST.md` — verified |
| `yol11s_experiment2/weights/last.pt` | Present, SHA256 `1594D5E0…80AC2` | Different hash from best.pt (same file size is expected — same architecture) |

`results.csv` is the ONLY one missing among the four training runs on disk (`yol11s_batch_8/16/32`, `yol11s_smoke_test`, `yol11s_dataset_v2_split_v2` all retain theirs). Since Ultralytics requires `results.csv` to render `results.png` and the PR/Box curves (all timestamped 2026-10-05 16:10, immediately after the final epoch), the file existed at run completion and was deleted between 2026-10-05 16:10 and the time of this audit.

**Therefore:** the numerical per-epoch trajectory (train/val box_loss, cls_loss, dfl_loss, precision, recall, mAP50, mAP50-95 per epoch) is **not directly recoverable** from the run directory. This report reconstructs the trajectory from filesystem evidence and post-hoc evaluation, and specifies how to fully recover it (§10).

---

## 2. Training Configuration (from `args.yaml`)

| Parameter | Value |
|---|---|
| Model | `weights/yolo11s.pt` (COCO-pretrained, `pretrained: true`) |
| Dataset | `experiments/dataset/experiment2/data.yaml` (19,719 train / 2,301 val images) |
| Epochs | **30** (deviation from locked gate: 100 — see §7) |
| Batch / imgsz | 16 / 720 |
| Optimizer | auto (SGD), lr0=0.01, lrf=0.01, momentum=0.937, weight_decay=0.0005 |
| Warmup | 3.0 epochs |
| Patience | 50 (no early stopping possible within 30 epochs) |
| AMP | true, seed=42, deterministic=true |
| Augmentation | mosaic=1.0, close_mosaic=10, translate=0.1, scale=0.5, fliplr=0.5, erasing=0.4, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4 |
| nbs | 64 (→ gradient accumulation 4) |
| save_period | 1 (all 30 epoch checkpoints retained) |
| save_dir | `runs/detect/experiments/training/yol11s_experiment2` |

---

## 3. Run Timeline Reconstruction (from epoch checkpoint mtimes)

| Segment | Epochs | Time window (dd-MM-yyyy) | Cadence |
|---|---|---|---|
| A | 0 → 12 | Oct 04 01:37 → Oct 04 07:55 | ~31.5 min/epoch (steady) |
| — | **pause** | Oct 04 07:55 → Oct 05 00:56 | **17.0 h interruption** |
| B | 13 → 22 | Oct 05 00:56 → Oct 05 05:40 | ~31.5 min/epoch (steady) |
| — | **pause** | Oct 05 05:40 → Oct 05 06:52 | ~1.2 h interruption |
| C | 23 → 24 | Oct 05 06:52 → Oct 05 07:22 | ~31 min/epoch |
| — | **pause** | Oct 05 07:22 → Oct 05 14:00 | **6.6 h interruption** |
| D | 25 → 29 | Oct 05 14:00 → Oct 05 16:09 | ~31.5–33.5 min/epoch |

**Derived quantities:**
- Steady-state epoch time: **~31.5 min** (1,233 batches/epoch = 19,719 images / batch 16)
- Active compute: **~15.3 h** (29 intervals × ~31.6 min)
- Wall clock: **~38.5 h** (Oct 04 01:37 → Oct 05 16:09), dominated by 3 interruptions totaling ~24.8 h (pattern consistent with workstation suspend/restart cycles)
- Final artifacts (best.pt, last.pt, confusion matrix, PR curves, results.png) written 2026-10-05 16:09–16:10

**Sample-plot evidence:** `train_batch0–2.jpg` (epoch 0) and `train_batch24660–24662.jpg` (global batch 24,660 = epoch 20 × 1,233) confirm training progressed through at least epoch 20 in the original run.

---

## 4. Best-Epoch Forensic Inference

- `best.pt` mtime = **2026-10-05 16:09:56**, identical to `epoch29.pt` mtime. In Ultralytics, `best.pt` is rewritten only when validation improves; its mtime equals the epoch of the last improvement.
- **Inference (strong circumstantial): the best epoch was epoch 29 — the final epoch.** The metric trajectory was still rising when training stopped.
- Corroboration: `results.png` (rendered from `results.csv` at 16:10) exists; the run did not trigger early stopping (patience=50 > 30 epochs).
- **Conclusion: the 30-epoch run was cut short relative to its 100-epoch gate plan while still improving. The checkpoint is likely under-trained.**

---

## 5. Post-Training Evaluation (frozen Dataset A test, official Ultralytics)

Source: `experiments/evaluation/EXP2_FROZEN_DATASET_A_TEST.md` (audit-confirmed official `model.val()` on the frozen 230-image India test split; artifacts at `experiments/evaluation/exp2_frozen_dataset_a_test/eval/`).

| Metric | Experiment 2 (this run) | Experiment 1 (epoch 100) | Δ |
|---|---|---|---|
| Precision (B) | 0.299 | 0.285 | +4.9% |
| Recall (B) | 0.312 | 0.247 | +26.3% |
| mAP50 (B) | **0.252** | 0.219 | **+15.1%** |
| mAP75 (B) | 0.120 | — | — |
| mAP50-95 (B) | 0.0903 | 0.076 | +18.4% |

Per-class mAP50 (from `crack_localization_analysis.md`, same eval): longitudinal 0.233, transverse 0.0113 (5 GT instances only), alligator 0.374, pothole 0.388.

Custom diagnostic protocol (conf ≥ 0.25, NMS IoU 0.5): P 0.4695 / R 0.4398 / F1 0.4372; only 292/679 GT objects detected; mean TP IoU 0.687.

---

## 6. Experiment 1 Reference Trajectory (intact `results.csv`, for contrast)

From `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/results.csv` (100 epochs, Dataset A only):

| Epoch | train/box_loss | train/cls_loss | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| 1 | 2.299 | 3.527 | 0.404 | 0.076 | 0.030 | 0.009 |
| 10 | 2.151 | 2.425 | 0.100 | 0.126 | 0.086 | 0.027 |
| 30 | 1.954 | 2.051 | 0.206 | 0.183 | 0.143 | 0.051 |
| 50 | 1.816 | 1.792 | 0.476 | 0.197 | 0.170 | 0.060 |
| 70 | 1.650 | 1.445 | 0.471 | 0.244 | 0.197 | 0.068 |
| 100 | 1.362 | 1.008 | 0.285 | 0.247 | 0.219 | 0.076 |

Experiment 1 showed monotonic improvement through epoch 100 with no plateau — consistent with the inference in §4 that Experiment 2 at epoch 30 was still on the rising part of its curve.

---

## 7. Deviations from the Locked Training Gate

`FINAL_TRAINING_GATE.md` locked: **100 epochs**, budget ~81 h central estimate. Actual run: **30 epochs**, ~15.3 h active compute. All other locked parameters (batch 16, imgsz 720, seed 42, patience 50, close_mosaic 10, nbs 64, original yolo11s.pt init) match the gate. **The epoch-count reduction was not documented in any gate change record** — this is an undocumented deviation requiring sign-off.

---

## 8. Anomalies

1. **Missing `results.csv`** — the only training run on disk without it; per-epoch trajectory lost (see §1, §10).
2. **Aborted second invocation (2026-10-06 03:41)** — `args.yaml`, `labels.jpg`, `train_batch0–2.jpg` were rewritten this morning with no new epoch weights written. Since `resume: false`, any re-launch restarts from COCO-pretrained `yolo11s.pt`, NOT from epoch 29. The epoch0–29 checkpoints are untouched (still Oct 04–05) and remain the authoritative artifacts.
3. **Stray nested run tree** — `runs/detect/runs/detect/experiments/…` and `runs/detect/val`, `val-2…val-5` directories indicate project-path confusion during evaluation invocations; harmless but should be cleaned.
4. **best.pt vs last.pt** — identical file sizes (19,194,266 B) but different SHA256; do not infer best=last from size alone (§4 uses mtime, not size).

---

## 9. What Cannot Be Concluded From Available Evidence

- Per-epoch loss curves (train/val box/cls/dfl) — **unrecoverable** (losses are not stored in checkpoints).
- Exact best-epoch index (inferred = 29 from mtime, not proven), convergence point, overfitting onset, and val-domain (non-India) metric trajectory.
- Whether 30 epochs is sufficient — evidence (best.pt mtime, Exp 1's rising 100-epoch curve) indicates **no**.

---

## 10. Remediation / Recommended Actions

1. **Reconstruct the per-epoch metric trajectory:** run `model.val()` on the frozen Dataset A test split (and/or the non-India val split) for each of `weights/epoch0.pt … epoch29.pt` — all 30 checkpoints exist. Tabulate P/R/mAP50/mAP50-95 per epoch and archive as `training_trajectory_reconstructed.csv` alongside this report.
2. **Archive run records outside `runs/`** (gitignored): copy each run's `results.csv` + `args.yaml` into `experiments/training/records/<run_id>/` so trajectory data survives cleanup.
3. **Document the 30-vs-100 epoch deviation** in the gate record, with explicit accept/extend decision. Given §4, extending training (resume from `last.pt`, epochs to 100) is the evidence-backed recommendation.
4. **Update `experiments/training/reproducibility_record.md`** — it currently documents only the 1-epoch `yol11s_batch_16` baseline; add the experiment2 entry (config, checksums, timeline, final metrics).
5. **Kill any in-flight relaunch** before it overwrites artifacts; if re-training is intended, use `resume: true` from `weights/last.pt`.

---

## 11. Verdict

The training trajectory analysis was **not completed** previously, and its primary data source (`results.csv`) is missing from the run directory. The run itself **completed all 30 epochs** (verified: 30/30 epoch checkpoints, best.pt checksum matches the documented evaluation artifact). Reconstructed timeline: ~31.5 min/epoch, ~15.3 h active compute, three multi-hour interruptions, final epoch 2026-10-05 16:09. The model improved over Experiment 1 by +15.1% mAP50 on the frozen India test set, and the best checkpoint coincides with the final epoch — the run was stopped early relative to its 100-epoch plan and is likely under-trained. Full per-epoch trajectory recovery is possible by re-evaluating the 30 retained epoch checkpoints (§10.1).
