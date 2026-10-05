# Experiment 2 — Pre-Training Gate Checklist (Phase 14)

**Applies to:** the Experiment 2 training run, the distribution-expansion ablation
(Dataset A train + non-India Dataset B → YOLO → train).

**Status of this document:** all gates are `PENDING`. **Nothing has been run yet.** No
Dataset B download has been verified, no conversion has been performed, no split has been
built, and no audit has been executed. Every `PENDING` below is the literal current state, not
a placeholder.

To use this checklist: run the chain in `scripts/experiment2/README.md`, then fill in each
gate from the named artifact, and only then decide whether to train.

---

> ## AUTHORISATION RULE — READ BEFORE ANYTHING ELSE
>
> **1. Training is authorised ONLY if all 13 gates below are `PASS`.** Thirteen out of
> thirteen. Not twelve. There is no partial authorisation and no "critical subset".
>
> **2. If any critical gate fails: DO NOT TRAIN.**
> The critical gates — a failure in any of these is an unconditional stop — are
> **G1, G2, G3, G4, G5, G9, G10, G11**. G4 (frozen test protection) and G11 (leakage audit)
> are the hardest stops: a failure there means the headline metric is already contaminated and
> no amount of further compute can recover the experiment.
>
> **3. Do NOT train on a partial Dataset B.** If step 3 was run with `--allow-missing`, or the
> conversion is otherwise incomplete, the build is a *diagnostic artifact*, not a training
> corpus. G1 and G2 cannot pass on a partial download. A smaller-but-clean corpus is a
> different experiment with a different number in it; silently training on one and reporting
> the result as "Dataset A + B" is a false claim.
>
> **4. If leakage is discovered: STOP.** A non-empty `REMOVAL_REQUIRED` in the leakage
> report means Dataset B images are byte-identical to frozen test images. The frozen test set
> is the measurement instrument. Stop, remove the offending files manually (the audit script
> will not do it for you), re-run the chain from step 4, and re-audit. Do not proceed to
> training "just to see", and do not re-derive a test set to make the problem go away.
>
> **5. These gates are a stop condition, not a formality.** A gate exists because the failure
> mode it catches is invisible in the final metrics. A run that trains through a red gate
> produces a number that looks fine and means nothing.

---

## Gate table

| Gate | Name | Passing requires | Produced by | Evidence artifact | Status |
|---|---|---|---|---|---|
| **G1** | Full Dataset B acquired | The complete RDD2022 Arrow `DatasetDict` is present and its metadata contains all 38,385 images. A partial download is a **FAIL**, not a partial pass. | `scripts/experiment2/country_index.py` | `country_index.json` (`totals`, `per_split_country`) | `PENDING` |
| **G2** | Dataset B integrity verified | Every expected total matches exactly: grand total 38,385; train 26,869 / validation 5,758 / test 5,758; Japan 10,506, Norway 8,161, India 7,706, United States 4,805, China 4,378, Czech 2,829. No unexpected country present. Script exited 0. | `scripts/experiment2/country_index.py` (verification block) | `country_index.json`; `ALL CHECKS PASSED` in the step 1 log | `PENDING` |
| **G3** | India exclusion verified | No entry classified non-India carries `country == "India"` (hard assert); partition is exhaustive; India count is exactly 7,706; **and** no `India_`-prefixed file appears in the Experiment 2 build other than the designed Dataset A train carry-over (audit check B, unexpected bucket == 0). | `scripts/experiment2/exclude_india.py`; independently re-verified by `scripts/experiment2/audit_leakage.py` (check B) | `india_excluded.json`, `non_india_allowlist.json`; `experiment2_leakage_report.json` → `checks.B.india_prefixed_unexpected` | `PENDING` |
| **G4** | Frozen test protection verified | **No Experiment 2 image is byte-identical to any of the 230 frozen test images.** Exact sha256 intersection == 0, and `REMOVAL_REQUIRED` is empty. | `scripts/experiment2/audit_leakage.py` (check B) | `experiment2_leakage_report.json` → `checks.B.duplicate_sha256_count == 0`, `REMOVAL_REQUIRED == []` | `PENDING` |
| **G5** | Duplicate audit passed | Check C passes: every Dataset A train / Dataset B collision is enumerated and classified, and `unexpected_pair_count == 0`. A non-zero `duplicate_pair_count` composed entirely of `expected_dataset_a_carry_over` is a **PASS** — see "Known behaviours" in the runbook. | `scripts/experiment2/audit_leakage.py` (check C) | `experiment2_leakage_report.json` → `checks.C.unexpected_pair_count == 0`, `checks.C.passed` | `PENDING` |
| **G6** | Taxonomy validated | The locked 4-class mapping is intact: `D00→0 longitudinal_crack`, `D10→1 transverse_crack`, `D20→2 alligator_crack`, `D40→3 pothole`. Every label row carries a class in `{0,1,2,3}`. **Zero `unknown_class_id` rejections** — class 4 was dropped upstream and must never appear. The D40 "other corruption" caveat is documented. | `scripts/experiment2/convert_arrow_to_yolo.py`; re-validated by `scripts/experiment2/validate_yolo.py` (row grammar) | `TAXONOMY_NOTE.md`; `rejection_report.csv` (must contain no `unknown_class_id` row); `experiment2_conversion_validation.json` → `valid_row_rule`, `summary.all_label_rows_valid` | `PENDING` |
| **G7** | Negative images preserved | Every image with zero objects is present with an **empty** label file, and the negative count and percentage are reported per split. Negatives are a deliberate design element; dropping them reintroduces the Experiment 1 pothole over-specialisation. | `scripts/experiment2/convert_arrow_to_yolo.py`; counted by `scripts/experiment2/validate_yolo.py` | `experiment2_conversion_validation.json` → `splits.<split>.statistics.negative_images`, `empty_label_files_count`; `split_manifest.json` | `PENDING` |
| **G8** | Dataset A + B composition verified | TRAIN contains Dataset A train (1,071) **plus** the non-India Dataset B train pool, and the composition, per-country and per-class, matches the design. Dataset A `val` and `test` are **excluded** from training. Dataset A train is ~3.4% of the train set. | `scripts/experiment2/build_splits.py` | `experiments/dataset/experiment2/split_manifest.json`; `experiments/analysis/overnight/dataset_b_gate/experiment2_dataset_report.md` | `PENDING` |
| **G9** | Experiment 2 train/val split validated | The hold-out is deterministic (seed 42, `--val-frac 0.11`), stratified by country on `(country, is_negative)`, drawn **only** from the non-India Dataset B train pool. No filename and no sha256 appears in both train and val. Val is 100% Dataset B pool members. `data.yaml` was written, and written **last**. | `scripts/experiment2/build_splits.py` | `val_holdout_manifest.json` (exact val list + per-image sha256); `split_manifest.json` (`seed`, `algorithm`, `manifest_sha256`); `experiments/dataset/experiment2/data.yaml` | `PENDING` |
| **G10** | YOLO conversion validated | Every image has a label and every label has an image (0 orphans both directions); 0 invalid rows; 0 degenerate boxes; 0 dimension mismatches vs the provenance manifest; `n_objects` agrees between labels and manifest; and the three sources — on-disk labels, `provenance_manifest.csv`, and the **Arrow store read directly via `pyarrow`** — reconcile. | `scripts/experiment2/validate_yolo.py` | `experiment2_conversion_validation.json` → `summary`, `reconciliation.all_sources_agree`; `experiment2_conversion_report.md` | `PENDING` |
| **G11** | Leakage audit passed | All of checks **A–F** are clean. A, B, D hard-clean. C has no unexpected pairs. E reports zero confirmed near-duplicates across the 64-bit dHash screen (Hamming ≤ 5) confirmed by pixel equality. F is documented as a known residual risk with its confirmed exp2 train/val crossing count reported. `all_hard_checks_passed: true`. **A run with `--skip-near-dup` does not satisfy this gate** — check E must actually have run. | `scripts/experiment2/audit_leakage.py` | `experiment2_leakage_report.json` → `summary.all_hard_checks_passed`, `hard_failures == []`; `experiment2_leakage_report.md` | `PENDING` |
| **G12** | Initialization strategy documented | The initialization choice is on record, reasoned, and consistent across every gate document. Currently: **Option A — original pretrained `yolo11s.pt`**, identical to Experiment 1. See "Design decision already on record" below. | Phase 12 analysis (documentation, not a script) | `experiments/analysis/overnight/experiment2_dataset_b/experiment2_design_decision.md` §7 | `PENDING` |
| **G13** | Training config frozen | Every hyperparameter is fixed and identical to Experiment 1 except the data: `epochs 100`, `patience 50`, `batch 16`, `imgsz 720`, `nbs 64` (accum 4), `amp true`, `cache false`, `save_period 1`, `close_mosaic 10`, `warmup_epochs 3.0`, model `yolo11s.pt`. No sweep, no retry at a different batch size, no second seed. The frozen baseline checkpoint is verified intact by SHA256 immediately before launch. | Phase 12/13 documentation; verified by pre-launch SHA256 check | `experiment2_training_config.md`; the frozen-baseline SHA256 assertion in that document | `PENDING` |

---

## Design decision already on record

**G12 is decided. This section is the decision; it is not reopened by this checklist.**

**The recommendation is Option A — initialise from the original pretrained `yolo11s.pt`**
(COCO weights), identical to Experiment 1.

**Why.** Experiment 2's stated purpose is to measure the effect of expanding the training
distribution. Option A is the only design that runs that measurement as a clean **data
ablation**: initialization, architecture, taxonomy, every hyperparameter, and the evaluation
set are all held fixed against the frozen baseline, and the single changed factor is the
training data. Anything that varies the data *and* the initialization simultaneously is not
a data ablation — it is a pipeline comparison whose result cannot be attributed to either
factor.

**Why not Option B** (continuing from Experiment 1's frozen `best.pt`):

- **It varies two things at once.** Data and initialization both change, so a measured delta
  is uninterpretable — improvement could come from the extra data, from the inherited head
  start, or from both, and a single run cannot separate them.
- **The treatment's initialization would be derived from the control's outcome.** That is
  post-treatment-shaped contamination: it is not merely an extra confound, it is one that is
  *coupled* to the effect under study.
- **It imports Experiment 1's pothole-heavy, zero-negative prior into a now-balanced training
  set.** The inherited weights encode a prior learned from data with **zero** negative images
  — effectively "road surface → probably pothole". The Experiment 2 training set is roughly a
  third negatives. The inherited prior is therefore not merely stale but **anti-aligned** with
  the new data. It also carries a measurably degenerate `transverse_crack` head (precision
  0.0, recall 0.0 on the frozen test), so early training would run in a wrong-signed regime
  for exactly the class the expansion exists to fix.
- **The efficiency it buys does not pay for it.** The inherited head start is ~1,675 optimizer
  steps against Option A's ~49,600 — about 3.4% of the budget. A ~3% efficiency gain is not
  worth a total interpretive cost on a project whose deliverable is a measurement.

**This supersedes the earlier G15 note.** `dataset_b_hf_gate/decision.md` (G15) recommended
**Option B** — "Initialize from baseline best.pt and continue training" — under an explicit
assumption that acquisition was blocked (G1 = `BLOCKED`), when no Dataset B data existed and
no wall-clock estimate was available. It was framed as an efficiency choice for a run that
had not been costed. With the data in hand and the run costed, the efficiency argument
collapses to ~3% while the attribution cost is total. **The G15 decision is revised. Treat
`dataset_b_hf_gate/decision.md` G15 as superseded by this section and by
`experiment2_design_decision.md` §7.** The same supersession applies to G15 in
`dataset_b_gate/experiment2_pretraining_gate.md`.

### Residual confounds that survive Option A

Choosing Option A removes the **initialization** confound. It does **not** remove these two.
Both survive any single training run, under either option, and both must be stated explicitly
in the Experiment 2 report. A delta reported without them is misleading.

**C2 — optimization-budget / step-count confound.** Epochs are fixed at 100 in both
experiments, but the dataset is ~30× larger, so Experiment 2 performs ~30× more optimization:
**1,675 optimizer steps in Experiment 1 versus roughly 198,400 (iterations) in Experiment 2** at
the same epoch budget.

| | Experiment 1 | Experiment 2 (est.) | Ratio |
|---|---|---|---|
| Mini-batch iterations | 6,700 | **~198,400** | ~29.6× |
| Optimizer steps (accum 4) | **1,675** | ~49,600 | ~29.6× |
| Distinct training images | 1,071 | ~31,750 | ~29.6× |

"More data" and "more gradient steps" are the same manipulation at fixed epochs. No
single-run design separates them. Separating them requires either a step-matched control
(~2,960 epochs on Dataset A) or an epochs-matched subsampled control (A+B subsampled to 1,071
images per epoch) — either costs a full additional run at ~82 h.

*Partial mitigation, near-zero cost.* Experiment 1 ran with `save_period=1`, so its 100
per-epoch checkpoints exist. Reading that trajectory shows where Dataset A plateaued (best at
epoch 86 of 100), bounding C2: most of Experiment 2's step surplus is spent on a problem the
baseline never faced. **This trajectory analysis must be reported alongside the Experiment 2
result**, or a reader will mistake a step-count effect for a data effect.

**C3 — validation-set-composition / checkpoint-selection confound.** Experiment 1 validated
on 229 **India-only** images (in-distribution w.r.t. its training set). Experiment 2 validates
on a **non-India** hold-out of ~2,500–4,600 images (out-of-distribution w.r.t. its training
set). Two consequences: Experiment 2's validation mAP50-95 is **not comparable** to
Experiment 1's 0.08344 and must never be compared to it; and the two `best.pt` checkpoints are
selected by different criteria — a checkpoint chosen for non-India performance may be a poor
India performer for reasons unrelated to the training data.

*Partial mitigation, near-zero cost.* Evaluate **both** checkpoints on **both** validation
sets plus the frozen test set. Three inference passes over ~3,000–5,000 images at ~11.8
ms/image — minutes of GPU time, no additional training.

---

## Scale warning

**This is an estimate, not a prediction, and not a gate.** It is a scheduling risk that the
operator must consciously accept before launching. It does not block or authorise training —
the 13 gates do that.

| | Experiment 1 | Experiment 2 (est.) | Ratio |
|---|---|---|---|
| Training images | 1,071 | **~31,750** | **~30×** |
| Config | batch 16, imgsz 720 | batch 16, imgsz 720 | identical |

At Experiment 1's **measured** throughput (~103.7 s per epoch steady state, derived from its
10,379.3 s total run time over 100 epochs), Experiment 2 is estimated at:

| Scenario | s/iter (train) | Epoch time | 100 epochs |
|---|---|---|---|
| Optimistic | ~1.15 | ~38 min | **~60 h** |
| **Central** | ~1.42 | **49.0 min** | **~82 h (3.4 days)** |
| Pessimistic | ~1.80 | 62.0 min | **~103 h (4.3 days)** |

Consequences the operator must accept:

- **The 100-epoch budget is unlikely to complete in a single sitting.** This is roughly
  three to four days of continuous GPU time. It requires the machine to stay available, awake
  and thermally unthrottled for that span.
- **`patience 50` will probably not trigger early stopping.** With ~1,984 iterations per
  epoch instead of 67, each epoch carries far more gradient signal, so the val metric is
  unlikely to go 50 epochs without improvement. Expect the full 100 epochs to run. It is kept
  at 50 anyway so that early stopping is not a new variable relative to Experiment 1.
- **`warmup_epochs 3.0` costs ~2.5 h** in Experiment 2 versus ~5 minutes in Experiment 1.
  **`close_mosaic 10` covers the last ~8 h** of the run. Both are correct; both are large in
  absolute terms.
- **Check the first two epochs and re-plan.** The first two epochs of the real run will
  confirm or refute the per-epoch estimate within about 2 hours. Measure the actual epoch time
  then and revise this section. Treat the ~60–103 h band as a factor-of-1.6 uncertainty band,
  not as a commitment.
- **VRAM use is unchanged.** GPU memory consumption depends on `batch` and `imgsz`, **not**
  on dataset size. Experiment 2 uses batch 16 and imgsz 720, identical to Experiment 1, which
  peaked at ~5.5 GB against 5.997 GB available. The 30× larger dataset does not increase VRAM
  demand. If epoch 1 OOMs, **stop and report** — do not silently drop to batch 8, which would
  be a different configuration and is not comparable to the frozen baseline.

**If the estimate proves prohibitive (>150 h), the documented remedy is to reduce epochs — not
to switch to Option B — and to record the new C2 magnitude.**

---

## Frozen baseline — do not modify

Everything in this list is an input to the comparison. Modifying any of it invalidates
Experiment 1 as a comparison arm and destroys the ablation. A failed run costs ~82 h; a
contaminated comparison costs the whole experiment.

| Artifact | Value |
|---|---|
| **Experiment 1 checkpoint** | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt` |
| **Checkpoint SHA256** | `721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823` |
| **Best epoch** | **86 of 100** |
| **Dataset A directory** | `experiments/dataset/yolo_rdd2022_india/` — do not modify, move, rename or regenerate |
| **Dataset A split** | train 1,071 / val 229 / test 230 — do not re-split |
| **Frozen test set** | **230 images**, `experiments/dataset/yolo_rdd2022_india/images/test` |
| **Frozen test GT objects** | **679** total, of which **512** are the broadened `pothole` (D40 "other corruption") class |
| **Official test metrics** | precision **0.299** · recall **0.312** · mAP50 **0.252** · mAP50-95 **0.0903** · mAP75 **0.120** |

**Before spending ~82 h, verify the frozen checkpoint is still intact:**

```powershell
(Get-FileHash "runs\detect\experiments\training\yol11s_dataset_v2_split_v2\weights\best.pt" -Algorithm SHA256).Hash.ToLower()
# expected: 721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823
```

A different hash means the baseline moved. Stop and resolve that before launching; do not
"just note it".

Note that `pothole` here is RDD2022's broad **D40 "Other Corruption"** category, not a
narrowly defined pothole class. Per-class `pothole` numbers must never be described as
pothole-specific performance, and because 512 of 679 frozen-test objects are that class, the
headline test metric is dominated by it. Norway, the United States and Czech carry **zero**
D40 annotations, so much of the added training distribution never exercises that class.

---

## Sign-off

Training may begin only when every row above reads `PASS`, G12 and G13 are documented and
frozen, the scale warning has been consciously accepted by the operator, and the frozen
baseline SHA256 has been re-verified.

| Field | Value |
|---|---|
| Gates passed | _/13 |
| Scale warning accepted by | _ |
| Frozen baseline SHA256 re-verified (Y/N) | _ |
| Date | _ |
