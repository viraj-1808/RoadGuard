# Experiment 2 — Frozen Training Configuration

**Document type:** Phase 12 configuration freeze (no training performed)
**Date:** 2026-10-02
**Status:** FROZEN — awaiting dataset readiness and authorization to run
**Companion document:** `experiment2_design_decision.md` (initialization: **Option A**)

---

## 1. Principle

Every hyperparameter is **HELD CONSTANT** from Experiment 1 unless a change is explicitly
marked **CHANGED** with a justification. The governing rule: *anything held constant is one
fewer confound*, and Experiment 2 already carries three confounds it cannot remove (§7.4 of the
design decision). No convenience change is permitted.

Source of truth for the Experiment 1 values:
`runs/detect/experiments/training/yol11s_dataset_v2_split_v2/args.yaml` (116 lines) and
`experiments/training/run_baseline.py`.

---

## 2. Hyperparameter Freeze Table

### 2.1 Core

| Parameter | Experiment 1 | Experiment 2 | Status | Rationale |
|-----------|-------------|-------------|--------|-----------|
| `task` | detect | detect | **HELD** | Same task |
| `model` | `yolo11s.pt` | `yolo11s.pt` | **HELD** | Option A — see design decision §7. Identical initialization is the entire basis of the controlled comparison |
| `data` | `experiments/dataset/yolo_rdd2022_india/data.yaml` | `experiments/dataset/experiment2/data.yaml` | **CHANGED (treatment)** | The independent variable. Dataset A train + Dataset B non-India |
| `epochs` | 100 | 100 | **HELD** | Same number of passes over the data. Changing this would add a confound and would also break comparability with the baseline's convergence trajectory |
| `patience` | 50 | 50 | **HELD** | See §6.3 — expected not to fire, but kept identical so early stopping is not a new variable |
| `batch` | 16 | 16 | **HELD** | VRAM-bound on a 5.997 GB card at imgsz 720. Also held so `nbs=64` accumulation (4) is unchanged |
| `imgsz` | 720 | 720 | **HELD** | Doubling resolution would change small-crack detectability — the exact capability under test for the thin `transverse_crack` class |
| `device` | `0` | `0` | **HELD** | Single GPU |
| `workers` | 0 | 0 | **HELD** | See §6.2 — this is the primary throughput limiter and changing it would alter the DataLoader RNG stream, forfeiting bitwise reproducibility against Experiment 1 |
| `seed` | 42 | 42 | **HELD** | Reproducibility |
| `deterministic` | true | true | **HELD** | Reproducibility |
| `optimizer` | auto | auto | **HELD** | `auto` resolves to SGD/Adam-family heuristics; identical value and identical dataset-size logic in Ultralytics 8.4.138 |
| `amp` | true | true | **HELD** | Halves VRAM; required for batch 16 at 720 on this card |

### 2.2 Optimizer / schedule / loss (all HELD)

| Parameter | Value | Status | Note |
|-----------|-------|--------|------|
| `lr0` | 0.01 | **HELD** | |
| `lrf` | 0.01 | **HELD** | Final LR fraction |
| `momentum` | 0.937 | **HELD** | |
| `weight_decay` | 0.0005 | **HELD** | |
| `warmup_epochs` | 3.0 | **HELD** | Warmup is a fixed 3 epochs in both. In wall-clock terms this is ~2.5 h in Experiment 2 vs ~5 min in Experiment 1 — see §6.4 |
| `warmup_momentum` | 0.8 | **HELD** | |
| `warmup_bias_lr` | 0.1 | **HELD** | |
| `box` | 7.5 | **HELD** | |
| `cls` | 0.5 | **HELD** | |
| `dfl` | 1.5 | **HELD** | |
| `cls_pw` | 0.0 | **HELD** | |
| `nbs` | 64 | **HELD** | Nominal batch 64 ÷ batch 16 → **gradient accumulation 4**. Not changing this keeps the optimizer step size identical |
| `cos_lr` | false | **HELD** | |
| `close_mosaic` | 10 | **HELD** | Mosaic disabled for the final 10 epochs. In wall-clock terms, those are the *last* ~8 h of a ~82 h run |

### 2.3 Augmentation (all HELD)

| Parameter | Value | Status | Note |
|-----------|-------|--------|------|
| `mosaic` | 1.0 | **HELD** | |
| `mixup` | 0.0 | **HELD** | |
| `cutmix` | 0.0 | **HELD** | |
| `copy_paste` | 0.0 | **HELD** | |
| `degrees` | 0.0 | **HELD** | |
| `translate` | 0.1 | **HELD** | |
| `scale` | 0.5 | **HELD** | |
| `shear` | 0.0 | **HELD** | |
| `perspective` | 0.0 | **HELD** | |
| `flipud` | 0.0 | **HELD** | |
| `fliplr` | 0.5 | **HELD** | |
| `bgr` | 0.0 | **HELD** | |
| `hsv_h` | 0.015 | **HELD** | |
| `hsv_s` | 0.7 | **HELD** | |
| `hsv_v` | 0.4 | **HELD** | |
| `auto_augment` | randaugment | **HELD** | Classification augmentation; inactive for `detect` |
| `erasing` | 0.4 | **HELD** | Classification augmentation; inactive for `detect` |

**Augmentation is held in full, and this matters more than usual.** Mosaic 1.0 with 33.8%
empty-label images means roughly one in three mosaic tiles contributes no positive boxes. That
is the mechanism by which Dataset B delivers its negative-diversity benefit, and it is the
reason no augmentation change is defensible here: tuning augmentation would optimise the very
effect being measured.

### 2.4 Runtime / IO / bookkeeping

| Parameter | Experiment 1 | Experiment 2 | Status | Rationale |
|-----------|-------------|-------------|--------|-----------|
| `save` | true | true | **HELD** | |
| `save_period` | 1 | 1 | **HELD** | ~71 MB per checkpoint (measured: Experiment 1's 102 weight files = 7.64 GB). 100 epochs ≈ **7.5 GB**. 167.2 GB free on C:, so affordable — and per-epoch checkpoints are what makes an ~82 h run crash-resumable. **Keep at 1.** |
| `cache` | false | false | **HELD (see note)** | `cache=ram` is impossible (31,750 × 720×720×3 ≈ **47.7 GB**). `cache=disk` would be feasible and is the single highest-leverage throughput knob, but it is **left at `false`** so the frozen config matches Experiment 1 exactly. Flagged in §6.2 as an optional decision to make *before* launch. |
| `exist_ok` | `true` | **NOT SET** | **CHANGED — mandatory** | See §3.3. Prevents overwriting an existing Experiment 2 run directory |
| `project` | `experiments/training` | `experiments/training` | **HELD** | Must stay *relative* — see §3.2 |
| `name` | `yol11s_dataset_v2_split_v2` | `yol11s_experiment2_datasetB` | **CHANGED (required)** | New run name; guarantees separation from Experiment 1's directory |
| `resume` | false | false | **HELD** | |
| `pretrained` | true | true | **HELD** | Redundant with the model arg but kept explicit to match Experiment 1 |
| `cls_remap` | true | true | **HELD** | |
| `fraction` | 1.0 | 1.0 | **HELD** | **Important:** do not use `fraction` to shorten the run. It is an explicit, logged dataset subset — a confound, not a budget control |
| `single_cls` | false | false | **HELD** | |
| `rect` | false | false | **HELD** | Fixed square aspect; avoids a variable train/val geometry |
| `multi_scale` | 0.0 | **HELD** | |
| `compile` | false | false | **HELD** | |
| `overlap_mask` | true | true | **HELD** | Inactive for `detect` |
| `mask_ratio` | 4 | 4 | **HELD** | Inactive for `detect` |
| `dropout` | 0.0 | 0.0 | **HELD** | |
| `freeze` | null | null | **HELD** | Freezing layers would be a new treatment |
| `val` | true | true | **HELD** | Needed for best-checkpoint selection |
| `split` | val | val | **HELD** | |
| `plots` | true | true | **HELD** | |
| `verbose` | true | true | **HELD** | |
| `conf` | null (default) | null (default) | **HELD** | |
| `iou` (NMS) | 0.7 | 0.7 | **HELD** | |
| `max_det` | 300 | 300 | **HELD** | |
| `profile` | false | false | **HELD** | |
| `dnn` | false | false | **HELD** | Inactive for train |

**Summary: 1 treatment change (data), 1 mandatory safety change (`exist_ok`), 1 required
bookkeeping change (`name`). Every learning-relevant hyperparameter is HELD.**

---

## 3. Output Path Safety

### 3.1 Required output directory

```
runs/detect/experiments/training/yol11s_experiment2_datasetB/
```

### 3.2 How Ultralytics resolves this path — the trap

Ultralytics resolves a **relative** `project` against `runs/detect/`. This is exactly why
Experiment 1's `args.yaml` records `project: experiments/training` but
`save_dir: C:\...\runs\detect\experiments\training\yol11s_dataset_v2_split_v2`.

Therefore:

- `--project experiments/training` (relative) → `runs/detect/experiments/training/<name>` ✅
- `--project runs/detect/experiments/training` → `runs/detect/runs/detect/experiments/training/<name>` ❌
- `--project C:\...\experiments\training` → an absolute path **outside** `runs/detect` ❌

The second failure mode has already happened in this repository: a stray
`runs/detect/runs/detect/experiments/training/yol11s_dataset_v2_split_v2/` tree exists on
disk. **Pass `project` relative and exactly as written below.**

### 3.3 `exist_ok` — must be false/absent

`exist_ok` is **NOT SET** in the command below, leaving the Ultralytics default of `false`.

Experiment 1 used `exist_ok: true` (`args.yaml:17`). **This is the one place Experiment 2
must deliberately diverge.**

**`exist_ok: false` prevents overwrite but does NOT prevent a silently different directory
name.** Ultralytics' `increment_path` does not raise on a collision — it appends a numeric
suffix. A second accidental run would write to
`runs/detect/experiments/training/yol11s_experiment2_datasetB2/`, leaving the first run's
directory intact but scattering the evidence and making it easy to report the wrong run.

**Mandatory pre-flight guard — run this before every launch:**

```powershell
$target = "runs\detect\experiments\training\yol11s_experiment2_datasetB"
if (Test-Path $target) { throw "ABORT: $target already exists. A prior Experiment 2 run is present. Refusing to overwrite or create a sibling directory." }
Write-Output "PREFLIGHT OK: $target does not exist."
```

Also verify Experiment 1's directory is untouched:

```powershell
Get-FileHash "runs\detect\experiments\training\yol11s_dataset_v2_split_v2\weights\best.pt" -Algorithm SHA256
# MUST equal: 721277B9D066715BC82D3D4FA34FCBFCF6147CB4265B216F41FC68C8BEB59823
```

### 3.4 ONE RUN ONLY

**Only one training run is permitted for Experiment 2.** This is a hard project constraint.

Consequences:

- The configuration in §2 is **frozen**. Any change after launch invalidates the run.
- No hyperparameter sweep, no retry-with-different-batch, no second seed.
- If the run crashes, it is **resumed** (`--resume` from the same `save_dir`), never restarted
  from scratch — `save_period=1` exists for this.
- If the run OOMs, that is a **finding to report**, not a licence to silently drop to
  batch 8. A batch-8 run is a different configuration and cannot be compared to the frozen
  baseline.
- All dataset readiness checks (conversion, class-ID range, India exclusion, frozen-test
  exclusion) must pass **before** launch. A failed run costs ~82 h.

---

## 4. The Exact Command

### 4.1 Primary form — Python launcher (matches the project's `run_baseline.py` pattern)

Run from the **repository root** (`C:\Users\viraj\Code_files\Github\RoadGuard AI`). The
relative `project`/`data` paths depend on the working directory.

```python
# experiments/training/run_experiment2.py
from pathlib import Path
import sys, os

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ultralytics import YOLO
import torch

SAVE_DIR = Path(project_root) / "runs/detect/experiments/training/yol11s_experiment2_datasetB"

# MANDATORY pre-flight: refuse to run if the target directory already exists.
# Ultralytics would otherwise silently create "yol11s_experiment2_datasetB2".
if SAVE_DIR.exists():
    raise SystemExit(f"ABORT: {SAVE_DIR} already exists. Refusing to start.")

DATA_YAML = "experiments/dataset/experiment2/data.yaml"
if not os.path.exists(DATA_YAML):
    raise SystemExit(f"ABORT: {DATA_YAML} not found.")

# Verify the frozen baseline is still intact before spending ~82 h.
import hashlib
BASELINE = "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt"
EXPECTED = "721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823"
h = hashlib.sha256(Path(project_root, BASELINE).read_bytes()).hexdigest()
if h != EXPECTED:
    raise SystemExit(f"ABORT: baseline SHA256 mismatch.\n  expected {EXPECTED}\n  got      {h}")
print(f"[OK] Baseline SHA256 verified: {h}")

print(f"[INFO] CUDA: {torch.cuda.is_available()}  GPU: {torch.cuda.get_device_name(0)}")
print(f"[INFO] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

config = {
    # ---- treatment ----
    'data':        DATA_YAML,
    # ---- initialization: OPTION A (see experiment2_design_decision.md) ----
    'model':       'yolo11s.pt',
    # ---- HELD from Experiment 1 ----
    'epochs':      100,
    'patience':    50,
    'batch':       16,
    'imgsz':       720,
    'optimizer':   'auto',
    'amp':         True,
    'seed':        42,
    'deterministic': True,
    'workers':     0,
    'device':      '0',
    'save':        True,
    'save_period': 1,
    'cache':       False,
    'pretrained':  True,
    'cls_remap':   True,
    'verbose':     True,
    'single_cls':  False,
    'rect':        False,
    'cos_lr':      False,
    'close_mosaic': 10,
    'resume':      False,
    'fraction':    1.0,
    'profile':     False,
    'freeze':      None,
    'multi_scale': 0.0,
    'compile':     False,
    'overlap_mask': True,
    'mask_ratio':  4,
    'dropout':     0.0,
    'val':         True,
    'split':       'val',
    'plots':       True,
    'agnostic_nms': False,
    # ---- output routing: MUST stay relative (see section 3.2) ----
    'project':     'experiments/training',
    'name':        'yol11s_experiment2_datasetB',
    # NOTE: 'exist_ok' is deliberately OMITTED -> defaults to False.
}

for k, v in config.items():
    print(f"         - {k}: {v}")

YOLO('yolo11s.pt').train(**config)
```

### 4.2 Equivalent CLI form

Equivalent to `yolo detect train ...` with the same arguments. Use **one or the other, never
both** — two invocations would be two runs (§3.4).

```powershell
yolo detect train `
  model=yolo11s.pt `
  data=experiments/dataset/experiment2/data.yaml `
  epochs=100 `
  patience=50 `
  batch=16 `
  imgsz=720 `
  device=0 `
  workers=0 `
  seed=42 `
  deterministic=True `
  optimizer=auto `
  amp=True `
  save=True `
  save_period=1 `
  cache=False `
  project=experiments/training `
  name=yol11s_experiment2_datasetB
```

Note what is **absent** from the CLI form: `exist_ok` (defaults to `false` — the requirement),
and `pretrained` / `cls_remap` / `single_cls` / `rect` / `cos_lr` / `close_mosaic` /
`fraction` / `freeze` / `multi_scale` / `compile` / `overlap_mask` / `mask_ratio` / `dropout` /
`split` / `plots` / `agnostic_nms`, all of which equal their Ultralytics defaults and are
already at their Experiment 1 values. Omitting them is safe **only because they match the
defaults Experiment 1 used** — `close_mosaic=10`, `cls_remap=True` and `pretrained=True` are
also defaults in Ultralytics 8.4.138, so both forms produce an identical `args.yaml`.

**`fraction` must be absent, not set to a value below 1.0.** Using `fraction` to fit the run
into available time would silently subsample the dataset and turn the treatment into a
different, undocumented one.

### 4.3 Verify the run landed in the right place

Immediately after launch, confirm:

```powershell
Test-Path "runs\detect\experiments\training\yol11s_experiment2_datasetB\args.yaml"   # expect True
Test-Path "runs\detect\experiments\training\yol11s_experiment2_datasetB2"            # expect False
Get-Content "runs\detect\experiments\training\yol11s_experiment2_datasetB\args.yaml"
```

The emitted `args.yaml` must show `model: yolo11s.pt`, `exist_ok: false`,
`project: experiments/training`, `name: yol11s_experiment2_datasetB`, and a
`save_dir` under `runs\detect\experiments\training\`. If `exist_ok` reads `true` or
`save_dir` points anywhere else, **stop the run immediately** — the wrong configuration is
running.

### 4.4 Resume (only after an interruption — not a second run)

If the process dies, resume the *same* run rather than starting a new one:

```powershell
yolo detect train resume model=runs/detect/experiments/training/yol11s_experiment2_datasetB/weights/last.pt
```

This restores optimizer state, epoch counter, RNG state, and the LR schedule. **Do not** resume
into a different directory, and do not change any hyperparameter before resuming — a resumed run
with modified settings is not the frozen configuration.

---

## 5. Environment Preconditions

| Requirement | Value | Source |
|-------------|-------|--------|
| Python | 3.12.10 | `training_environment.md` |
| PyTorch | 2.14.0+cu126 | `training_environment.md` |
| Ultralytics | 8.4.138 | `training_environment.md` |
| GPU | RTX 4050 Laptop, 5.997 GB | `training_environment.md` |
| Driver | 592.82 | `training_environment.md` |
| CPU | i5-13420H, 8C / 12T @ 2.1 GHz | measured 2026-10-02 |
| Free disk (C:) | 167.2 GB | measured 2026-10-02 |
| RAM | not audited | ⚠️ see §6.2 |

---

## 6. Risk Assessment: 100 Epochs, Batch 16, imgsz 720, ~31,750 Images, RTX 4050 Laptop (~6 GB)

### 6.1 ⚠️ These are ESTIMATES, explicitly not measurements

**No Experiment 2 training was performed, and no Experiment 2 timing data exists.** Every
number below is extrapolated from Experiment 1's measured `results.csv` under the explicit
assumption that per-iteration cost is independent of dataset size — an assumption that
section 6.2 shows is partly false. Treat these as **order-of-magnitude planning figures with a
factor-of-1.6 uncertainty band**, not as predictions. The first two epochs of the real run will
refute or confirm them within ~2 hours; check the actual epoch time then and re-plan.

### 6.2 VRAM risk: LOW — and importantly, *unchanged* from Experiment 1

**GPU memory consumption depends on `batch` and `imgsz`, not on dataset size.** Experiment 2
uses batch 16 and imgsz 720, identical to Experiment 1, which peaked at ~5.5 GB against 5.997 GB
total. **Dataset size contributes nothing to VRAM.** The ~30× increase in images changes the
number of iterations, not the memory footprint of any one of them.

| Metric | Experiment 1 | Experiment 2 | Change |
|--------|-------------|-------------|--------|
| Peak VRAM (est.) | ~5.5 GB | ~5.5 GB | **none** |
| Total VRAM | 5.997 GB | 5.997 GB | — |
| Headroom | ~0.5 GB | ~0.5 GB | **none** |
| Free at idle | 4.95 GB | 4.95 GB | — |

**Verdict: VRAM risk is identical to Experiment 1 and is a known, accepted condition.** It is
not made worse by Dataset B. Two pre-flight mitigations, both free:

- Close every other GPU application before launch. 4.95 GB was free at idle, so ~1 GB is
  already held by something — identify and release it.
- Watch epoch 1. If it OOMs, **stop and report** (§3.4). Do not silently drop to batch 8.

**Host RAM is a genuine new risk that Experiment 1 did not face.** Dataset A was 1,530 uniform
720×720 images (trivially page-cached). Dataset B is ~30,679 **variable-resolution** JPEGs
(RDD2022 originals, 640×480 or other) totalling roughly 3–5 GB on disk, plus mosaic 1.0 builds
a 2× canvas at 2 × 720 = 1440×1440 per mosaic sample. `workers=0` means no worker processes and
so no multiplied worker memory — **that is the one place `workers=0` helps.** But host RAM has
never been audited on this machine, and `cache=false` means the OS page cache will be doing
real work it could not do for 1,530 images.

### 6.3 Wall-clock estimate — the dominant risk

**Measured basis (Experiment 1, `results.csv`):**

| Quantity | Measured |
|----------|----------|
| Total run time, 100 epochs | 10,379.3 s = **2.88 h** |
| Mean steady-state epoch time | **~103.7 s** |
| Train images / iterations per epoch | 1,071 / **67** (ceil(1071/16)) |
| Val iterations per epoch | 229 / **15** |
| Implied train iteration cost | ~1.42 s (103.7 − 15×0.25 − ~5 overhead) ÷ 67 |
| Implied val iteration cost | ~0.25 s |

**Projected Experiment 2:**

| Scenario | s/iter (train) | Iters/epoch | Epoch time | 100 epochs |
|----------|---------------|-------------|------------|------------|
| Optimistic | 1.10 | 1,984 | 2,332 s = **38.9 min** | **~65 h** (2.7 d) |
| **Central** | **1.42** | **1,984** | **2,942 s = 49.0 min** | **~82 h** (3.4 d) |
| Pessimistic | 1.80 | 1,984 | 3,721 s = 62.0 min | **~103 h** (4.3 d) |

Iterations/epoch = ceil(31,750 ÷ 16) = **1,984**. Val contributes ~60–120 s/epoch
(~2,500–4,600 val images). Sanity check: 82 h ÷ 2.88 h = **28.5×**, against a data ratio of
29.6× — consistent.

**Low bound if a val hold-out is carved out of Dataset B.** If ~15% of the 30,679 non-India
images is reserved for validation rather than all being used for training, the train set is
~27,148 images → 1,697 iters/epoch → **~71 h** central. So the realistic central estimate is
**~71–82 h**, with a full range of **~60–103 h**.

**Assumptions this estimate rests on, each of which could be wrong:**

1. Per-iteration GPU cost is independent of which images are in the batch. Mostly true, but
   variable-resolution Dataset B images decode to different buffer sizes, and the mosaic
   assembly cost varies with source aspect ratio.
2. Validation set size. Not fixed by the specification. A 4,600-image val set adds ~2 min/epoch;
   a 20,000-image val set would add ~9 min/epoch and inflate the total by ~10 h.
3. `workers=0` holds at this data volume. **This is the weakest assumption.** Experiment 1's
   dataset was small enough for the OS page cache to serve every image from RAM. ~31,750
   variable-resolution JPEGs (~3–5 GB) will not stay resident on a laptop under memory
   pressure, so disk I/O becomes a per-iteration cost inside the 1.42 s figure. This is
   precisely what pushes the run from the optimistic to the pessimistic scenario.
4. Thermal throttling over days. A laptop GPU under sustained load for 80+ hours will throttle;
   the i5-13420H is a 35 W-class part. Not modelled.

**Optional decision to make before launch — `cache`.** `cache=disk` would decode and resize
every image once into `.npy` files at 720×720 (~47.7 GB; 167.2 GB free, so it fits) and remove
essentially all decode cost thereafter, plausibly recovering 20–40% of wall clock. **It changes
nothing about the optimization** — same images, same geometry, same augmentation, same RNG
stream — so it does not confound anything. It is nevertheless **left at `false`** in §2.4 to
keep the frozen config identical to Experiment 1. This is the one knob where trading a small
amount of strict config-identity for large wall-clock savings is defensible. **Decide before
launch; do not decide mid-run.** Note the one-time cache build will itself stall for
30–90 min before epoch 1.

**Related flag — `workers`.** Raising `workers` to 4–8 would likely help more than `cache`,
because the CPU is idle during GPU compute. It is **held at 0** deliberately: a nonzero
`workers` changes the DataLoader worker RNG streams and therefore the augmentation draws,
forfeiting reproducibility against Experiment 1 and making any future Option A / Option B
pairing less comparable. Determinism was chosen over throughput for this project.

### 6.4 `patience 50` — will it stop early?

**Probably not. Budget the full 100 epochs.**

| Evidence | Direction |
|----------|-----------|
| Experiment 1's best epoch was **86 of 100** — only 14 epochs without improvement. `patience 50` would have needed 50 consecutive non-improving epochs to fire and never came close | Strongly against early stop |
| Experiment 2 does **~29.6× more optimization per epoch-equivalent** and sees ~29.6× more distinct images. Convergence is far slower in epoch terms | Against early stop |
| The expansion introduces ~8,366 transverse instances where the baseline had 30. A newly learnable class does not plateau early | Against early stop |
| Validation set grows from 229 → ~2,500–4,600 images, cutting the sampling noise on val mAP. "No improvement" becomes harder to trigger spuriously | Against early stop |
| The target-domain share collapses to 3.4%, so a non-India val set is measured while the model is still far from India-optimal. If anything this could *stall* the val curve | Mildly for early stop |

**Estimated probability of early stop: low, on the order of 10% or less.** Note that even if
it fires, it fires late: `patience=50` means at minimum 51 epochs complete, i.e. **≥~42 h**
already spent.

**The real cost is not early stopping — it is interruption.** An ~82 h continuous run on a
laptop has a substantial chance of a power event, a Windows update, a driver reset, or
thermal shutdown. Mitigations, all of which should be in place before launch:

| Mitigation | Detail |
|---|---|
| Per-epoch checkpoints | `save_period=1` (~71 MB/epoch, ~7.5 GB total) means at most one epoch is lost |
| Resume path known | §4.4. Resume restores optimizer state, epoch, RNG, and LR schedule |
| Disable sleep | Windows power settings must prevent sleep/hibernate for the full run |
| AC power | Mains power only; no battery operation for 82 h |
| Stable target path | The pre-flight guard in §3.3 means a *second* run is impossible without deliberate action, so a crash-and-restart cannot silently produce a duplicate |

**Also note the schedule is now measured in days, which changes what the LR plan means:**
`warmup_epochs=3` is ~2.5 h of warmup rather than ~5 min, and the final
`close_mosaic=10` phase — during which mosaic is disabled and validation usually improves
most — is the **last ~8 h** of the run. If the run must be truncated for any reason, truncating
*before* the close-mosaic phase would forfeit the most valuable epochs. Do not truncate.

### 6.5 Risk Summary

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | Wall clock ~82 h (range ~60–103 h) exceeds available window | **HIGH** | Medium-High | Decide `cache=disk` before launch; run uninterrupted overnight×3 |
| 2 | Interruption (power / update / thermal) over days | **HIGH** | Medium-High | §6.4 — AC power, sleep off, `save_period=1`, known resume path |
| 3 | `workers=0` becomes I/O bound, inflating epoch time toward 62 min | MEDIUM | Medium-High | `cache=disk`; do **not** change `workers` (breaks reproducibility) |
| 4 | Host RAM exhaustion from mosaic 2× canvas on variable-resolution images | MEDIUM | Low-Medium | Audit RAM before launch; `workers=0` already minimises it; `cache=false` |
| 5 | GPU OOM at batch 16 / imgsz 720 | LOW | Low | **Unchanged from Experiment 1.** Free the ~1 GB held at idle. If it OOMs, stop and report — do not silently change batch |
| 6 | Wrong output directory (`runs/detect/runs/detect/...`) | LOW | Low | §3.2 — `project` stays relative. Verify `args.yaml` in epoch 1 |
| 7 | Silent duplicate run via Ultralytics auto-increment | LOW | Low | §3.3 pre-flight guard + §3.4 one-run rule |
| 8 | Under-convergence at 100 epochs on 29.6× more data | MEDIUM | Medium | Cannot be fixed without adding a confound (confound C2). Report epoch-100 loss and best-epoch location alongside the result |
| 9 | `patience 50` fires early | LOW | Low | Expected not to fire; budget full 100 epochs regardless |
| 10 | Accidentally evaluating on a wrong test split | LOW | Low | Frozen test is `experiments/dataset/yolo_rdd2022_india/images/test` (230 India images), unchanged; Dataset B test must be excluded from all Experiment 2 training and validation |

**Overall assessment: PROCEED, conditional on the dataset being fully downloaded and
converted, and on committing to a ~3.5-day uninterrupted compute block with the resume path
understood.** VRAM is not a new risk. Wall-clock continuity is the project-critical risk.

---

## 7. Pre-Launch Checklist

Every item must pass. A failure here costs ~82 h.

| # | Check | Command / evidence | Pass condition |
|---|-------|--------------------|---------------|
| 1 | Dataset B fully downloaded | `experiments/dataset/raw_hf_rdd2022/` (do not modify; download in progress) | all ~30,679 non-India images present |
| 2 | Arrow → YOLO conversion complete | conversion report | all 4 class IDs in `[0-3]`, normalized coords in `[0,1]` |
| 3 | India exclusion verified | country audit | **zero** `India_` images in Dataset B train/val |
| 4 | Frozen test untouched | `experiments/dataset/yolo_rdd2022_india/` unmodified | 230 test images, 679 GT, SHA256 of `data.yaml` still `67880aae1e0dd25ec8ebb2edbb397bc4a48229fcb83fe78eae22ff213b59947d` |
| 5 | Frozen test excluded from Experiment 2 | split manifest | no test image in Experiment 2 train **or** val |
| 6 | Dataset A val (229) excluded | split manifest | not in Experiment 2 train or val |
| 7 | Dataset A train included | split manifest | 1,071 images present |
| 8 | Taxonomy | `data.yaml` | `nc: 4`; names and order identical to Dataset A |
| 9 | Train size | manifest | ~27,100–31,750 (record the exact figure — it sets the wall-clock estimate) |
| 10 | Baseline SHA256 | §3.3 command | `721277b9…9823` |
| 11 | Target dir absent | §3.3 guard | `Test-Path` returns `False` |
| 12 | No sibling dir `…datasetB2` | §4.3 | `Test-Path` returns `False` |
| 13 | GPU otherwise idle | `nvidia-smi` | ~4.95 GB free before launch |
| 14 | AC power, sleep disabled | Windows settings | confirmed |
| 15 | Free disk | `Get-PSDrive C` | ≥60 GB free (~7.5 GB checkpoints + optional ~47.7 GB `cache=disk`) |
| 16 | Host RAM audited | Task Manager / `systeminfo` | ≥16 GB; record the figure — not currently audited |
| 17 | Authorization to run | project owner | explicit; one run only |
| 18 | Design decision read | `experiment2_design_decision.md` | initialization = Option A confirmed |

---

## 8. Post-Run Requirements

| # | Requirement | Why |
|---|-------------|-----|
| 1 | Evaluate on the **frozen 230-image India test set** only for the headline comparison | The only split common to both experiments. Val mAP is **not** comparable across experiments (confound C3) |
| 2 | Report precision / recall / mAP50 / mAP50-95 / mAP75 against the baseline's 0.299 / 0.312 / 0.252 / 0.0903 / 0.120 | Direct comparison basis |
| 3 | Record best epoch, best epoch value, and epoch-100 values | Convergence evidence for confound C2 |
| 4 | Report that Dataset A is **3.4%** of training data | A test-set drop is then interpretable as OOD shift, not automatically failure |
| 5 | Report `pothole` coverage caveat (Norway/US/Czech contribute 0 potholes; D40 convention preserved only in Dataset A) | §3.1 of the design decision. `pothole` is 512/679 of the frozen test |
| 6 | Evaluate Experiment 1's 100 per-epoch checkpoints' trajectory | Bounds confound C2 at zero training cost |
| 7 | Cross-evaluate both checkpoints on **both** val sets | Bounds confound C3 at near-zero training cost |
| 8 | State confounds **C2 and C3 explicitly**, whether or not the result is favourable | The design decision's §8 honesty requirement |
| 9 | Compute and record the new `best.pt` SHA256 | Provenance |
| 10 | Record the actual epoch time from epoch 1 | Validates or refutes the §6.3 estimate |
| 11 | Do **not** run a second configuration | One run only (§3.4) |

---

## 9. Provenance

| Item | Value |
|---|---|
| Document type | Configuration freeze, Phase 12 |
| Training performed | **None.** No model was trained, loaded, or modified |
| Baseline artifacts | Read-only; not modified, SHA256 not recomputed |
| `experiments/dataset/yolo_rdd2022_india/` | Not accessed for writing; not modified |
| `experiments/dataset/raw_hf_rdd2022/` | Not accessed (download in progress) |
| Experiment 1 values sourced from | `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/args.yaml` (116 lines), `results.csv` (101 rows), `experiments/training/run_baseline.py` |
| Environment values sourced from | `experiments/analysis/overnight/training_environment.md`; CPU, free disk measured 2026-10-02 |
| Companion document | `experiment2_design_decision.md` — initialization **Option A** |
| Timing basis | Experiment 1 `results.csv` `time` column: 10,379.3 s over 100 epochs, 67 iters/epoch |
| Estimate status | **Projected, not measured.** Uncertainty band ~1.6× (§6.1) |