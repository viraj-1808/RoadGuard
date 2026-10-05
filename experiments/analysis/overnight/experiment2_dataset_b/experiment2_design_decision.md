# Experiment 2 — Design Decision: Initialization for the Distribution-Expansion Run

**Document type:** Phase 12 analytical decision record (no training performed)
**Date:** 2026-10-02
**Status:** DECISION — single run authorized design
**Scope:** Initialization selection only. Companion document: `experiment2_training_config.md`

---

## 1. The Question

Experiment 2 has one stated purpose, quoted verbatim:

> "Measure the effect of expanding the training distribution with verified non-India RDD2022 data."

That sentence defines a **data ablation**. The independent variable is the *training
distribution*. Everything else should be a control, not a treatment.

The decision on the table is where Experiment 2 starts from:

| Option | Initialization checkpoint |
|--------|--------------------------|
| **A** | `yolo11s.pt` — original Ultralytics COCO-pretrained weights (identical to Experiment 1) |
| **B** | Experiment 1's frozen `best.pt` — Dataset-A-trained weights (SHA256 `721277b9…9823`) |

---

## 2. Frozen Baseline (Experiment 1) — Reference Facts

All values below were read from the frozen artifacts and are treated as ground truth for
this decision.

| Property | Value | Source |
|----------|-------|--------|
| Model | YOLO11s from `yolo11s.pt` (COCO pretrained) | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/args.yaml:3` |
| Data | `experiments/dataset/yolo_rdd2022_india/` (Dataset A only) | `args.yaml:4` |
| Dataset A size | 1,530 images — train 1,071 / val 229 / test 230 | split manifest v2.0.0 |
| Dataset A objects | 4,360 retained | conversion manifest |
| Best checkpoint | epoch 86 of 100, max val mAP50-95 = 0.08344 | `results.csv` |
| Best-checkpoint val metrics | precision 0.2972, recall 0.2384, mAP50 0.2218 | `results.csv` epoch 86 |
| Checkpoint SHA256 | `721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823` | `baseline_audit.md` |
| Frozen test result (230 images, 679 GT) | precision 0.299, recall 0.312, mAP50 0.252, mAP50-95 **0.0903**, mAP75 0.120 | `test_eval/test_metrics.json` |
| Optimization budget | 100 epochs, batch 16, imgsz 720 | `args.yaml:5,8,9` |
| Effective batch | `nbs=64` ÷ batch 16 → gradient accumulation 4 | `args.yaml:95` |
| Total mini-batch iterations | 67/epoch × 100 = **6,700** | derived from `results.csv` |
| Total optimizer steps | **1,675** | 6,700 ÷ 4 |
| Wall clock | 10,379.3 s = **2.88 h** | `results.csv` epoch 100 `time` |
| Augmentation | mosaic 1.0, close_mosaic 10, fliplr 0.5, translate 0.1, scale 0.5, hsv_h 0.015, hsv_s 0.7, hsv_v 0.4 | `args.yaml:96-108` |
| Other | seed 42, deterministic true, optimizer auto, amp true, device 0, workers 0, patience 50 | `args.yaml:20-26` |

**Provenance correction recorded here.** `baseline_audit.md` §3 states that the best epoch
was 100 with val mAP50-95 = 0.07558. Direct inspection of `results.csv` contradicts this:
epoch 86 is the argmax at **0.08344**. The frozen figures given in this document (epoch 86,
0.08344) are the verified ones. The audit document is wrong on this point and should not be
used as the source for "best epoch". This matters for Experiment 2 because the best-epoch
*location* (86/100) is evidence about convergence, used in §5 below.

---

## 3. Experiment 2 Definition

| Property | Value |
|----------|-------|
| Purpose | Measure the effect of expanding the training distribution with verified non-India RDD2022 data |
| Train composition | Dataset A train (1,071 India images) + Dataset B non-India (~30,679 images, `dronefreak/RDD2022`) |
| Combined train size | **~31,750 images** (≈29.6× Experiment 1) |
| Architecture | YOLO11s — unchanged |
| Taxonomy | 4 classes, unchanged: `longitudinal_crack`, `transverse_crack`, `alligator_crack`, `pothole` |
| Dataset B provenance | RDD2022 (Arya et al., arXiv:2209.08538) → `dronefreak/RDD2022`, CC BY-SA 4.0, two-hop |
| India exclusion | 7,706 India images excluded from Dataset B (all India images are excluded by prefix filter) |
| Frozen test | 230 India images, **unchanged and still the primary comparison metric** |

### 3.1 Composition facts that change how the result must be read

These are properties of the treatment itself, and they are the reason the confound discussion
in §7 is not academic.

| Property | Dataset A alone | A + B | Change |
|----------|-----------------|-------|--------|
| Dataset A share of train images | 100% | **~3.4%** (1,071 / 31,750) | A becomes a minority domain |
| Pothole : transverse instances | **106.2 : 1** (3,187 : 30) | **~1.2 : 1** (~9,772 : ~8,366) | imbalance numerically resolved |
| Transverse instances | 30 | ~8,366 | ~279× increase |
| Negative (empty-label) images | **0%** | ~33.8% | first genuine background diversity |
| Pothole coverage | India only | India + Japan + China only | Norway / US / Czech contribute **zero** potholes |
| Countries | 1 | 6 | 5 new domains |

Three consequences follow, and they must be stated before any result is read:

1. **Experiment 2 is not "Dataset A plus extra data".** It is ~96.6% non-India data. The
   frozen India test set is, for Experiment 2, a genuinely out-of-distribution evaluation.
   A *drop* in test mAP50-95 is a plausible and interpretable outcome that does **not**
   falsify the hypothesis — it may mean domain shift dominated the benefit.
2. **The class-imbalance fix is numerical, not semantic, for `pothole`.** Dataset A is the
   only source of the D40→`pothole` convention, and it now supplies 3.4% of training images.
   Meanwhile Norway, US and Czech carry **0** pothole annotations. `pothole` is 512 of the
   679 frozen-test ground-truth objects — 75% of the evaluation. Whatever "pothole" means to
   the Experiment 2 model is being learned mostly from non-D40 sources that do not use that
   label convention.
3. **Transverse-crack is no longer a 5-instance test question.** The frozen test contains
   only 5 transverse objects. Dataset B adds ~8,366 transverse training instances, but the
   test set can barely measure the effect. Expect large train/val movement on this class
   with little corresponding movement on the test metric.

---

## 4. Option A — Initialize from `yolo11s.pt` (COCO pretrained)

### 4.1 Held constant vs. changed, relative to Experiment 1

| Element | Status | Notes |
|---------|--------|-------|
| Initialization weights | **HELD** | Same `yolo11s.pt` file, same COCO provenance |
| Architecture / scale | **HELD** | YOLO11s, identical head structure and class count |
| Taxonomy | **HELD** | Same 4 classes, same class IDs |
| All hyperparameters | **HELD** | epochs, batch, imgsz, optimizer, LR schedule, augmentation, seed — identical (see `experiment2_training_config.md`) |
| Determinism | **HELD** | seed 42, `deterministic=true` |
| Evaluation set | **HELD** | Same frozen 230-image India test set, same metrics |
| Training distribution | **CHANGED (treatment)** | 1,071 → ~31,750 train images |
| Training budget in *passes* over data | **HELD** | 100 epochs in both |
| Training budget in *steps* | **CHANGED (unavoidable)** | 6,700 → ~198,400 iterations (29.6×) — see §7 |
| Validation set | **CHANGED (unavoidable)** | 229 India images → non-India hold-out — see §7 |

**Number of changed factors: exactly one that is under experimental control (the
distribution), plus two that are structurally inseparable from the treatment (step count and
validation-set composition).**

### 4.2 Is it a clean controlled comparison of "Dataset A vs Dataset A+B"?

**Yes, with two named qualifications.**

It is a clean comparison in the sense that matters most: **initialization is identical**, so
any difference in frozen-test performance between the Experiment 1 checkpoint and the
Experiment 2 checkpoint cannot be attributed to where the weights started. The comparison is
"same starting point, same recipe, same schedule, same test set — different training data".
That is the canonical form of a data ablation, and it is the only form in which the stated
purpose can be evaluated at all.

The two qualifications:

- **Steps are not matched** (§7.2). 100 epochs over a 29.6× larger set is 29.6× more
  optimization. "More data" and "more gradient steps" are the same manipulation at fixed
  epochs and cannot be separated in a single run.
- **The validation set is not matched** (§7.3). Experiment 1 selected its best checkpoint on
  229 India images; Experiment 2 will select on a non-India hold-out. The two `best.pt` files
  are chosen by different criteria, so the *checkpoint-selection* step is itself an
  uncontrolled variable.

Neither qualification is a consequence of the initialization choice. Option A does not create
either one; Option B would add a third, larger one on top.

### 4.3 Training-budget fairness

Experiment 1 spent **1,675 optimizer steps** (6,700 mini-batch iterations at accumulation 4).
Option A on Experiment 2 spends approximately **49,600 optimizer steps** (198,400 iterations).

So the comparison is *not* budget-matched in the direction that would disadvantage Option A.
Option A is given ~30× more optimization than the baseline it is being compared against.
The honest reading: **the budget asymmetry runs against Option A, not for it.** If Option A
still beats the baseline, the result is conservative. If Option A loses, the loss cannot be
blamed on insufficient training — it would have had 30× the baseline's steps.

Is 100 epochs enough for a 29.6× larger dataset? In terms of *passes over the data*, yes —
100 passes is exactly what Dataset A got, and Dataset A's best epoch was 86/100, i.e. it had
essentially converged within that budget. In terms of *number of distinct samples seen*, the
question is different: Experiment 1 saw 1,071 distinct images; Experiment 2 sees ~31,750.
More distinct data at the same number of passes is a harder optimization problem, so 100
epochs is more likely to be the binding constraint here than it was for Experiment 1. This
raises the risk of an under-converged Experiment 2 — see the wall-clock analysis in
`experiment2_training_config.md`, where a non-trivially long run makes this unavoidable.

**Conclusion for 4.3: Option A is not advantaged by the budget. If anything the budget favors
the baseline, which makes the comparison conservative.**

### 4.4 Does Option A contaminate the "distribution expansion" signal with an unrelated variable?

**No.** Initialization is held at the Experiment 1 value, so it is a control, not a
treatment. There is no contamination to manage here. This is Option A's decisive structural
advantage and it is worth stating plainly: Option A introduces **zero** new degrees of freedom
between the two experiments.

### 4.5 Prior-domination risk vs. discarded-learning risk

**Risk of an A-trained prior dominating the new distribution: not applicable.** Option A holds
no Dataset-A-specific weights to dominate anything.

**Risk of discarding 100 epochs of Dataset-A-specific learning: real but small, and
quantifiable.**

- What is discarded: 1,675 optimizer steps' worth of Dataset-A structure.
- What Option A gets instead: ~49,600 optimizer steps, with all 1,071 Dataset A images still
  present in the training set. Dataset A is not removed from training — it is re-learned
  in-context, surrounded by ~30,679 other images.
- The discarded learning is therefore worth at most **~3.4% of Option A's total optimization
  budget**. An initialization advantage worth ~3% of the available optimization is not a threat
  to the validity of a distribution-ablation conclusion.
- The residual genuine risk is *optimization efficiency*: Option A will take more epochs to
  reach the same loss. Given the 30× step surplus, this does not plausibly change the
  ranking of the two options on final test performance.

**Conclusion for 4.5: the cost of Option A is efficiency, which is not what Experiment 2 is
measuring.**

### 4.6 Interaction with the class-imbalance fix

Option A carries **no prior calibrated to the 106:1 pothole-heavy regime**. Its
classification head starts from COCO features with no exposure to the Dataset A class
distribution at all. When the expanded, near-balanced data arrives, there is no suppressed
logit to unlearn and no imbalanced prior to unwind.

This is a genuine, specific advantage of Option A that is usually missed: the Experiment 1
checkpoint's `transverse_crack` head is measurably degenerate — on the frozen test it scores
precision 0.0, recall 0.0, mAP50 0.0113, mAP50-95 0.00923 across 5 GT instances. That is
the signature of a class whose logit has been driven down by extreme imbalance. Carrying that
head into a set with ~8,366 transverse instances means starting Experiment 2 in a
*wrong-signed* regime for the very class the expansion was designed to fix. Option A does not
have this problem.

**Does the imbalance fix itself bias Option A's result?** No, and it is worth separating the
two effects cleanly:

- The imbalance fix (106:1 → ~1.2:1) is **part of the treatment**. It is one of the two
  mechanisms by which "expanding the distribution" acts. Whether it helps or hurts on the
  frozen India test is *the experimental result*, not a bias in the design.
- The only way the imbalance fix could bias the measurement is if it interacted with the
  initialization. Under Option A there is no Dataset-A-specific initialization for it to
  interact with, so that channel is closed.

Note the honest caveat from §3.1: the imbalance is fixed in *counts* but not in *semantics*
for `pothole`, and `pothole` is 75% of the frozen test. Option A is at least not further
biased by an inherited pothole prior.

**Conclusion for 4.6: Option A is the neutral observer of the imbalance fix.**

---

## 5. Option B — Initialize from Experiment 1's frozen `best.pt`

### 5.1 Held constant vs. changed, relative to Experiment 1

| Element | Status | Notes |
|---------|--------|-------|
| Architecture / scale | **HELD** | YOLO11s |
| Taxonomy | **HELD** | Same 4 classes |
| All hyperparameters | **HELD** | Same schedule, augmentation, seed |
| Evaluation set | **HELD** | Same frozen 230-image India test set |
| **Initialization weights** | **CHANGED** | Dataset-A-trained weights replace COCO-pretrained weights |
| **Effective starting skill** | **CHANGED** | Starts from a model already fitted to the target domain |
| Training distribution | **CHANGED (treatment)** | 1,071 → ~31,750 train images |
| Training budget in steps | **CHANGED (unavoidable)** | 6,700 → ~198,400 iterations |
| Validation set | **CHANGED (unavoidable)** | 229 India images → non-India hold-out |

**Number of changed factors: three under experimenter awareness (distribution,
initialization, starting skill) plus the two unavoidable ones.**

### 5.2 Is it a clean controlled comparison of "Dataset A vs Dataset A+B"?

**No.** Option B is not a controlled comparison of datasets. It is a comparison of
**pipelines**: "train from COCO on A, then continue from that result on A+B" versus "train
from COCO on A".

This distinction is not pedantic. Under Option B, a measured improvement over the frozen
baseline is consistent with at least three different stories:

1. The expanded distribution genuinely helped (the hypothesis).
2. Initialization on a target-domain checkpoint helped, independent of the new data.
3. Simple continuation helped — i.e. the result would have been similar if Experiment 1 had
   simply been trained longer, which would make "distribution expansion" a misnomer for
   "more training".

There is no way to distinguish these from a single Option B run, because stories 1–3 all
predict the same observation. Note in particular story 3: Experiment 1's best epoch was 86
of 100 and its training loss was still decreasing through epoch 100 (`results.csv`), which is
exactly the signature of a run that was not converged. Continuing from it would partly
reproduce the effect of simply not stopping.

### 5.3 Training-budget fairness

Option B arrives carrying 1,675 optimizer steps of Dataset-A-specific learning. Option A
arrives carrying 0 project-specific steps.

Is Option B therefore advantaged? **Marginally, and much less than it looks.**

- The inherited head start is ~1,675 steps against Option A's ~49,600. The pre-existing
  advantage is **~3.4% of the total budget**.
- With ~49,600 optimizer steps available, the model travels far from its initialization
  whichever initialization is used. Empirically, on non-toy vision datasets a few thousand
  full-network updates substantially overwrite backbone and head features. The convergence
  advantage of a warm start decays as (total steps / warm-start steps) grows, and here that
  ratio is ~30×.
- So the *performance* gap between A and B at convergence is expected to be small.

But note the asymmetry in what "small" means here: **a small performance gap combined with a
large attribution gap is the worst possible outcome for an ablation.** Option B does not
meaningfully outperform Option A; it just makes the result uninterpretable. Option A
delivers the same expected performance with a defensible causal claim.

**Is Option A disadvantaged by starting from generic COCO features?** It is, in the sense
that it must learn road-crack structure from scratch instead of inheriting it. On Dataset A
alone that cost was total — Experiment 1 never exceeded 0.08344 val mAP50-95. But the
relevant comparison is not "COCO vs Dataset-A weights on Dataset A" (which Experiment 1
already answered). It is "COCO vs Dataset-A weights on A+B", and on A+B the difference in
inherited knowledge is one domain's worth of features against 30,679 fresh images of gradient
signal.

**Conclusion for 5.3: Option B's budget advantage is real but small (~3% of budget); its
attribution cost is large. That trade is bad.**

### 5.4 Does Option B contaminate the "distribution expansion" signal with an unrelated variable?

**Yes — decisively, and this is the disqualifying objection.**

Initialization is a textbook confounder: a second causal factor, distinct from the treatment,
that varies systematically between the two arms of the comparison. Option B introduces it
into a comparison whose entire stated purpose is to isolate one factor.

Two aggravating properties make it worse than an ordinary confound:

- **It is a post-treatment-confounder-shaped confound.** The initialization for the
  *treatment* arm is derived from the *outcome* of the control arm. Whatever the Experiment 1
  run happened to learn — its pothole over-specialization, its near-zero transverse head, its
  specific India texture bias — is injected into Experiment 2 by construction. The design
  becomes partly circular: the treatment inherits the control's fitted parameters.
- **It is not orthogonal to the treatment.** The thing being injected is Dataset-A-specific
  learning, and the treatment *changes* how Dataset-A-specific learning should look (§3.1:
  Dataset A becomes 3.4% of training data). So the confound is not merely present, it is
  coupled to the very effect under study.

**Note on prior project record.** Two earlier gate documents recommend Option B:
`dataset_b_gate/experiment2_pretraining_gate.md` (G15) and `dataset_b_hf_gate/decision.md`
(G15: "Initialize from baseline best.pt and continue training"). Those recommendations were
made under G1 = BLOCKED, when no Dataset B data existed and no wall-clock estimate was
available; they were framed as an *efficiency* choice for a run that was not yet
costed. This document **supersedes both on G15**, on the grounds that the efficiency benefit
is small (§5.3) while the attribution cost is total (§5.4). The G15 decision should be
treated as revised.

### 5.5 Prior-domination risk vs. discarded-learning risk

Here the trade-off is genuinely two-sided, and this is the strongest argument *for* Option B.
It deserves a fair statement.

**Risk that the A-trained prior dominates the new, differently-composed dataset.** This is
Option B's real hazard, and it is not hypothetical:

- The inherited weights encode a **73.1% pothole** prior learned from data with **zero**
  negative images. The new training set is ~33.8% negatives. The prior is not merely stale,
  it is **anti-aligned**: it says "road surface → probably pothole", and the new data says
  "road surface → often nothing at all".
- The inherited `transverse_crack` head is measurably degenerate (precision 0.0, recall 0.0 on
  the frozen test). Entering the new distribution with a suppressed transverse logit means
  the early epochs run in a wrong-signed regime for the class the expansion exists to fix.
- Anchoring is a real phenomenon in deep nets: initializations that are bad for the target
  distribution can converge to worse solutions than neutral ones, and the effect is not
  reliably self-correcting within a fixed budget.

**Honest assessment of that hazard's magnitude:** with ~49,600 optimizer steps and ~8,366
transverse instances, a degenerate head is almost certainly overwritten. The probability of
Option B producing a *catastrophically* worse model is low. The probability that Option B
produces a *different* solution whose quality cannot be attributed to the data is high.

**Risk of discarding 100 epochs of Dataset-A learning (the cost of Option A).** As computed
in §4.5, this is ~3.4% of Option A's budget, with Dataset A still present in training.
Small.

**Net:** the risk that Option B produces a bad model is low; the risk that Option B produces
an uninterpretable one is high. Because Experiment 2's deliverable is a *measurement*, not a
model, uninterpretability is the more damaging failure.

### 5.6 Interaction with the class-imbalance fix

This is where Option B is most clearly compromised.

The class-imbalance fix works by **changing the prior the data presents**. Dataset A taught
the model a 106:1 pothole-dominant world. Dataset B replaces that with a ~1:1 world. The
mechanism of the fix operates *directly on the weights that Option B carries over*.

- **Option A:** the new prior is presented to a neutral head. The imbalance fix acts on the
  model cleanly.
- **Option B:** the new prior is presented to a head that has already been pushed hard toward
  the old prior by 1,675 optimizer steps of deliberately imbalanced data. The
  optimization must first unwind a 106:1 calibration before the balanced signal can take
  effect. So the measured "effect of distribution expansion" would be the effect of
  distribution expansion **net of an inherited bias in the opposite direction**.

Does this bias the result? **Yes, and in a direction that cannot be signed in advance.** Two
plausible outcomes, indistinguishable a priori:

- The inherited pothole prior causes excess pothole false positives during and potentially
  after training → *understates* the benefit of the negative-diversity component.
- The inherited India-specific features accelerate adaptation to the new data → *overstates*
  the benefit.

There is no way to know which happened without the Option A run. Since `pothole` is 512 of
679 frozen-test objects, this is not a rounding error — it plausibly dominates the headline
metric.

**Conclusion for 5.6: Option B entangles the imbalance fix with an inherited anti-aligned
prior, on the class that dominates the evaluation metric.**

---

## 6. Head-to-Head Summary

| Criterion | Option A (`yolo11s.pt`) | Option B (`best.pt`) |
|-----------|-------------------------|----------------------|
| 1. Controlled variables | All held except distribution | Initialization **also varied** |
| 2. Clean "A vs A+B" comparison | **Yes** | **No** — pipeline comparison |
| 3. Training-budget fairness | Disadvantaged (30× fewer inherited steps) — conservative | Slight advantage (~3% of budget) |
| 4. Contamination of the signal | **None introduced** | **Severe** — post-treatment-shaped confound |
| 5. Prior-domination risk | Not applicable | Low probability of bad model, high probability of uninterpretable result |
| 5b. Discarded-learning cost | ~3.4% of budget | n/a |
| 6. Imbalance-fix interaction | **Clean** — neutral observer | Entangled with inherited anti-aligned prior on `pothole` |
| Circularity | None | Treatment initialized from control's outcome |
| Supersedes earlier gate record | Yes (revises G15) | Retains G15 |

**The asymmetry is one-sided: Option A has no advantage that threatens validity; Option B has
a disadvantage that destroys it.**

---

## 7. RECOMMENDATION

### 7.0 Recommendation statement

**Initialize Experiment 2 from original pretrained `yolo11s.pt` (COCO weights) — OPTION A.**

### 7.1 Initialization chosen

`yolo11s.pt`, the same Ultralytics COCO-pretrained checkpoint Experiment 1 used
(`args.yaml:3`). Experiment 1's frozen `best.pt`
(SHA256 `721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823`) is **not** used
as an initialization and is **not** modified. It is referenced only as the comparison arm.

### 7.2 Reason

1. **The hypothesis is a data ablation, and only Option A runs one.** Experiment 2's stated
   purpose is to measure the effect of the training distribution. Option A holds
   initialization, architecture, taxonomy, every hyperparameter, and the evaluation set fixed
   against the frozen baseline. The single changed factor is the training data. Option B
   changes the data *and* the initialization, which makes the measurement a pipeline
   comparison whose result cannot be attributed (§5.2, §5.4).
2. **Option B's confound is post-treatment-shaped and therefore not merely inconvenient.**
   The treatment's initialization is derived from the control's outcome, so every artifact of
   the Experiment 1 run — pothole over-specialization from 0% negatives, the degenerate
   transverse head (recall 0.0 on the frozen test), India-specific texture bias — is
   injected into the treatment arm by construction (§5.4).
3. **Option B's efficiency benefit does not justify its attribution cost.** The inherited
   head start is ~1,675 optimizer steps against Option A's ~49,600 — about 3.4% of the
   budget. Against ~30× more optimization than the baseline received, that head start is
   expected to produce a near-identical converged model. Option B would therefore take on a
   total interpretive cost to buy a ~3% efficiency gain, on a project whose deliverable is a
   measurement (§5.3).
4. **The efficiency question is out of scope anyway.** "Would continuing from the baseline
   have been better?" is a deployment-optimization question. It is not what Experiment 2 was
   commissioned to answer, and answering it incorrectly — as a by-product — is worse than not
   answering it.
5. **The class-imbalance fix is best observed from a neutral head.** The imbalance fix works
   by changing the presented prior from 106:1 to ~1.2:1. Option A observes that change
   cleanly; Option B observes it net of an inherited anti-aligned prior, on `pothole`, which
   is 512 of 679 frozen-test objects (§5.6).

### 7.3 The variable actually being tested by Experiment 2

Strictly stated, Experiment 2 tests:

> **"Does replacing Dataset A with Dataset A + non-India RDD2022 — as a training
> distribution — change frozen India-test performance, when initialization, architecture,
> taxonomy, hyperparameters, schedule, seed, determinism, and evaluation set are held fixed?"**

What that bundles together, and cannot separate:

- **Data quantity** — 1,071 → ~31,750 distinct training images (~29.6×).
- **Optimization budget** — 6,700 → ~198,400 mini-batch iterations (~29.6×), because epochs
  are fixed and the data grew.
- **Target-domain share** — Dataset A goes from 100% of training to **3.4%**.
- **Class balance** — pothole:transverse 106.2:1 → ~1.2:1.
- **Negative/background diversity** — 0% → ~33.8% empty-label images.
- **Geographic domain** — 1 country → 6.
- **Evaluation regime** — the frozen India test set goes from in-distribution to
  out-of-distribution for the model being trained.

The last point deserves emphasis for the reader who will interpret the result: **a drop in
frozen-test mAP50-95 does not by itself mean the distribution expansion failed.** Because
Dataset A is only 3.4% of Experiment 2's training data, that test set is now OOD. Both
directions of movement are consistent with the hypothesis being true.

### 7.4 The confound that remains regardless of choice

Choosing Option A removes the initialization confound. **It does not remove the other two.**
Both survive any single training run, under either option.

**CONFOUND C2 — Optimization-budget / step-count confound. (Cannot be eliminated with one run.)**

Epochs are fixed at 100 in both experiments, but the dataset is 29.6× larger, so Experiment 2
performs ~29.6× more optimization:

| | Experiment 1 | Experiment 2 (est.) | Ratio |
|---|---|---|---|
| Mini-batch iterations | 6,700 | ~198,400 | 29.6× |
| Optimizer steps (accum 4) | 1,675 | ~49,600 | 29.6× |
| Distinct training images | 1,071 | ~31,750 | 29.6× |

"More data" and "more gradient steps" are the same manipulation at fixed epochs. No
single-run design separates them. To separate them you would need either a step-matched
control (Experiment 1 trained for 100 × 29.6 epochs, ≈ 2,960 epochs) or an
epochs-matched-but-subsampled control (A+B subsampled to 1,071 images per epoch for 100
epochs) — either of which costs a full additional run (~82 h, §7.5).

*Partial mitigation available at zero cost.* Because Experiment 1 ran with `save_period=1`,
its 100 per-epoch checkpoints still exist in
`runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/`. Evaluating those
checkpoints' `results.csv` trajectory shows where Dataset A plateaued — best at epoch 86 of
100 (0.08344), with train loss still falling at epoch 100. This bounds, but does not
eliminate, C2: it shows the baseline was near-converged at 1,675 optimizer steps, so most of
Experiment 2's step surplus is spent on a problem the baseline never faced. **This
trajectory analysis must be reported alongside the Experiment 2 result**, or the reader will
mistake a step-count effect for a data effect.

**CONFOUND C3 — Validation-set-composition / checkpoint-selection confound. (Cannot be eliminated with one run.)**

| | Experiment 1 | Experiment 2 |
|---|---|---|
| Validation set | 229 images, **India only** | non-India hold-out (~2,500–4,600 images) |
| Domain | In-distribution w.r.t. training | Out-of-distribution w.r.t. training |
| Best-checkpoint criterion | val mAP50-95 on India | val mAP50-95 on non-India |

Two problems follow. First, **validation mAP is not comparable across the two experiments** —
the numbers measure different things on different domains, so Experiment 2's val mAP50-95
must never be compared to Experiment 1's 0.08344. Second, and more subtly, **the two
`best.pt` checkpoints are selected by different criteria.** Experiment 1's best.pt maximizes
India performance; Experiment 2's best.pt maximizes non-India performance and is then scored
on India. A checkpoint selected for non-India performance may be a poor India performer for
reasons that have nothing to do with training data.

*Partial mitigation available at very low cost.* This one is measurable rather than merely
acknowledged: evaluate **both** checkpoints on **both** validation sets plus the frozen test
set. That is three inference passes over ~3,000–5,000 images at ~11.8 ms/image
(`test_eval/test_metrics.json`) — on the order of 1–3 minutes of GPU time per pass, well
under an hour total, and **no additional training**. It does not retire C3, but it converts
an invisible confound into a reported quantity, which is the difference between a claim and a
measurement.

**Consequence for interpretation.** Even under Option A, Experiment 2 does not deliver a clean
single-cause causal claim. It delivers a *composite* claim about replacing the training
distribution, with C2 and C3 attached and documented. That is acceptable **provided** C2 and
C3 are stated explicitly in the Experiment 2 report and the zero-cost mitigations above are
actually run. Reporting a delta without them would be misleading.

### 7.5 Cost of a follow-up controlled run that retires the initialization confound

Running **Option A and Option B both** retires C1 properly: same distribution, both
initializations, two arms.

| Item | Value |
|---|---|
| Additional training runs | **1** (Option B), in addition to the authorized Option A run |
| Estimated wall clock, Option B | ~82 h central (range ~65–103 h) — same dataset size, same config |
| Central estimate, both runs | **~164 h ≈ 6.8 days** continuous compute |
| Range, both runs | ~130–206 h (**5.4–8.6 days**) |
| Extra disk | ~7.5 GB of per-epoch checkpoints plus outputs |
| Effective batch/schedule | identical (`nbs=64` → accumulation 4) |

**Verdict on affordability: affordable, but not cheap.** It is roughly a week of
uninterrupted laptop GPU time, with a real interruption risk over that span. It is therefore
**not** recommended for this phase.

**Recommended sequencing:**

1. **Now:** run Option A only. It delivers the stated measurement with C2 and C3 documented
   and C2/C3 partially mitigated at near-zero cost.
2. **Immediately after, at near-zero training cost:** run the three-way evaluation described
   in §7.4 (both checkpoints on both val sets + frozen test) and the Experiment 1
   per-epoch checkpoint trajectory analysis. These convert two invisible confounds into
   reported numbers.
3. **Later, only if the decision it informs is worth ~82 h:** run Option B as an explicitly
   labelled *engineering* experiment — "is continued training from the baseline more
   compute-efficient than retraining from COCO on the expanded distribution?" — and **not**
   as a second arm of the data ablation. Its result must never be reported as a
   confirmation or refutation of the Experiment 2 hypothesis.

**C1 can be retired later; C2 and C3 cannot be retired by the Option B run either.** Running
both initializations fixes only the initialization variable. The step-count and
validation-set confounds would persist in a two-arm design just as they do in a one-arm
design. Retiring those would cost two *further* runs (a step-matched control and a
subsampled control), i.e. a further ~164 h. Anyone budgeting for "full experimental closure"
of Experiment 2 should budget **~246 h total (three runs, ~10 days)**, not ~82 h.

---

## 8. Intellectual Honesty Statement

**The confound cannot be eliminated with a single training run.** Option A eliminates the
initialization confound (C1) and nothing else. Two confounds — the 29.6× step-count
surplus (C2) and the changed validation set and checkpoint-selection criterion (C3) — are
structurally inseparable from the treatment itself: they are caused by the dataset being
larger, which is precisely what the experiment is about. No choice of initialization, and no
single run, removes them.

What Option A buys is the best available single-run design:

- It removes the one confound that *was* an artifact of a design choice rather than of the
  treatment.
- It makes the remaining confounds **nameable and quantifiable**, and two of the three
  mitigations are free (no additional training).
- It is the option under which a negative result is interpretable. If Experiment 2
  underperforms the frozen baseline, Option A lets you say "expanding the distribution to
  96.6% non-India data did not help on the India test set, and here is the evidence that the
  step budget was not the cause." Under Option B that sentence would be unprovable.

**Recommendation for the reader: run Option A, and report C2 and C3 alongside the result
whether or not the result is favourable.**

### 8.1 What would change this recommendation

| Condition | Would change the recommendation to |
|---|---|
| Experiment 1's checkpoint had to be preserved under a policy forbidding any re-use of baseline weights | Option A anyway — no viable alternative |
| The stated purpose were restated as "maximise India-test performance at minimum compute" | Option B — that is an engineering objective, and the warm start is the right tool |
| Compute were essentially unlimited (>250 h) and a strict ablation were required | Both A and B, plus step-matched and subsampled controls (§7.5) |
| The wall-clock estimate in `experiment2_training_config.md` proved prohibitive (>150 h) and the run had to be shortened | Reduce epochs — **not** switch to Option B — and document the new C2 magnitude |

Note the third row of the last two tables: the recurrence of Option B in every case where the
objective changes is the tell. Option B is the right answer to a *deployment* question. It is
the wrong answer to the *measurement* question that was actually asked.

---

## 9. Provenance of This Decision

| Item | Value |
|---|---|
| Document type | Analytical decision record, Phase 12 |
| Training performed | **None.** No model was trained, loaded, or modified. |
| Baseline artifacts | Read-only. `best.pt` SHA256 not recomputed, not modified |
| Dataset A | Not accessed for writing; not modified |
| `experiments/dataset/raw_hf_rdd2022/` | Not accessed (download in progress) |
| Facts sourced from | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/{args.yaml,results.csv}`, `experiments/analysis/overnight/{baseline_audit.md,training_environment.md,dataset_b_hf_gate/*}` |
| Supersedes | `dataset_b_gate/experiment2_pretraining_gate.md` G15; `dataset_b_hf_gate/decision.md` G15 (both recommended Option B) |
| Companion document | `experiment2_training_config.md` |
| Environment at time of writing | Python 3.12.10, PyTorch 2.14.0+cu126, Ultralytics 8.4.138, RTX 4050 Laptop (5.997 GB), i5-13420H (8C/12T), 167.2 GB free on C: |