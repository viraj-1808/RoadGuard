# RoadGuard YOLO11s Training-Speed Optimization Report

## Scope

- Historical launcher preserved: `experiments/training/run_baseline.py` is unchanged.
- Continuation source: `runs/detect/experiments/training/yol11s_experiment2/weights/epoch53.pt`.
- Target: continue from completed displayed epoch 54 to displayed epoch 100.
- Learning problem locked: Dataset A+B train/val membership, YOLO11s, batch 16, AMP, AdamW optimizer-state resume, seed 42, deterministic behavior, and augmentation settings.

## Project-local path layout

| Purpose | Path | Git status |
|---|---|---|
| Decoded-image cache mirror | `cache/decoded_images/experiment2_ultralytics_disk_cache/` | ignored |
| Temporary benchmark/runtime data | `cache/benchmarks/`, `cache/runtime/` | ignored |
| Optimization scripts | `scripts/optimization/` | tracked |
| Reports and small benchmark summaries | `experiments/optimization/` | tracked |

## Baseline evidence

Historical baseline, supplied by the prior run context and not re-measured in this pass:

- workers=6, cache=False
- epoch train time approximately 26:06 plus approximately 37s validation
- mAP50 approximately 0.581
- mAP50-95 approximately 0.318

These values are treated as historical evidence until reproduced by a new benchmark.

## Measured gate evidence in this pass

The inspection gate measured the canonical Dataset A+B source directly:

- train images: 19,719
- val images: 2,301
- train labels present: 19,719
- val labels present: 2,301
- checkpoint: `epoch53.pt`, internal epoch index 53, displayed completed epoch 54
- checkpoint SHA256: `7c23b4e1cd12fe4ffe27638d7f837297851f1a70dde10484b9354b9a69a157e4`
- AdamW optimizer state: present, 255 state entries, 3 parameter groups
- decoded train+val cache estimate: 136.473 GiB
- Ultralytics 50% disk safety-margin requirement: 204.709 GiB
- free C: space during inspection: 146.090 GiB

Conclusion: full Ultralytics `cache='disk'` is rejected for this machine right now. It would be project-local if used, but the hard disk-space gate fails.

## Ultralytics 8.4.138 inspection

- `cache='disk'` is supported.
- Default disk-cache behavior writes `Path(image).with_suffix(".npy")` beside each image.
- That default would scatter large `.npy` files into the canonical dataset, so it is rejected.
- Project-level solution: create a clean mirror under `cache/decoded_images/` using links/copies to the unchanged images and labels, then point the optimized continuation script to the mirror data YAML.
- Resume behavior restores `data` from the checkpoint and only allows selected overrides. The optimized continuation script patches that resume restoration in-process so an equivalent mirror `data.yaml` can be used while preserving checkpoint optimizer-state resume. Site-packages are not patched.

## Tier decisions

### Tier 1: SSD decoded-image cache

Decision: tooling implemented via project-local mirror + Ultralytics `cache='disk'`, but not selected for the final continuation because the measured disk gate fails.

Gate commands:

```powershell
python scripts/optimization/training_speed_optimization.py inspect --estimate-cache
python scripts/optimization/training_speed_optimization.py prepare-cache-mirror
python scripts/optimization/training_speed_optimization.py verify-cache-mirror
python scripts/optimization/training_speed_optimization.py benchmark-dataloader --data cache/decoded_images/experiment2_ultralytics_disk_cache/data.yaml --cache disk --workers 6
python scripts/optimization/training_speed_optimization.py verify-cache-mirror --require-npy
```

Do not run the cache-generation benchmark unless more disk space is available or a smaller cache design is separately approved.

### Tier 2: RAM

Decision: do not implement whole-dataset RAM cache on 16GB RAM. Use SSD `.npy` cache plus OS filesystem cache and DataLoader prefetch first.

Custom bounded shared RAM cache is rejected unless measured Tier 1 results remain insufficient. No such evidence has been produced yet.

### Tier 3: CPU data pipeline

Decision: benchmark worker count instead of assuming.

Required comparison now uses `cache=false`, because Tier 1 disk cache failed the space gate:

```powershell
python scripts/optimization/training_speed_optimization.py benchmark-dataloader --cache false --workers 6
python scripts/optimization/training_speed_optimization.py benchmark-dataloader --cache false --workers 8
```

Select the fastest stable setting. Current known historical evidence favors workers=6.

Measured dataloader-only benchmark in this pass:

| Setting | Mean batch load | Mean GPU transfer | Total measured | Result |
|---|---:|---:|---:|---|
| cache=false, workers=6 | 0.1392s | 0.0070s | 5.8482s / 40 batches | stable |
| cache=false, workers=8 | 0.0994s | 0.0069s | 4.2526s / 40 batches | stable, fastest measured |

Selected final worker setting: `workers=8`, pending the user's approval before a long continuation run. Use `--workers 6` to retain the historical setting.

### Tier 4: CPU to GPU transfer

Inspection result: Ultralytics 8.4.138 already uses `pin_memory=True` for CUDA DataLoaders and non-blocking transfer in `DetectionTrainer.preprocess_batch`.

Decision: no code change unless benchmark evidence shows a defect.

### Tier 5: GPU

Decision: keep YOLO11s, batch 16, AMP, AdamW resume, deterministic seed behavior, augmentation, and compile disabled.

TF32/cuDNN/compile changes are not enabled because they would need separate reproducibility and speed evidence. Simpler wins.

## Integrity gates

Required before continuation:

- train image count = 19,719
- val image count = 2,301
- every image has a label
- label content fingerprint unchanged
- split membership fingerprint unchanged
- `epoch53.pt` exists and has SHA256 recorded
- checkpoint internal epoch = 53
- optimizer state exists and is AdamW-compatible
- `last.pt` equals `epoch53.pt`
- no Dataset A frozen test split is used for tuning
- optimized diff contains no changes to `experiments/training/run_baseline.py`

Final review performed in this pass:

- continuation dry-run gate passed with `cache=false`, `workers=8`, `will_run=false`
- `experiments/training/run_baseline.py` diff is empty
- repository tests passed: `155 passed`
- script compilation passed for both optimization scripts
- no full epoch-55 to epoch-100 continuation was started

## Important note on image size

The historical launcher passes `imgsz=720`, but checkpoint metadata stores `imgsz=736`. This is consistent with Ultralytics adjusting image size to a stride-compatible value internally. The continuation script passes `imgsz=720` to preserve the requested configuration surface while allowing Ultralytics to apply the same internal adjustment.

## Exact dry-run command

```powershell
python scripts/optimization/continue_yol11s_experiment2_optimized.py
```

## Disk-cache continuation command, not approved on current disk state

```powershell
python scripts/optimization/continue_yol11s_experiment2_optimized.py --require-npy --run
```

The command above is intentionally not approved on the current machine state because the decoded-cache disk gate failed. The approved continuation command is instead:

```powershell
python scripts/optimization/continue_yol11s_experiment2_optimized.py --cache false --workers 6 --run
```

Fastest measured command from this pass:

```powershell
python scripts/optimization/continue_yol11s_experiment2_optimized.py --cache false --workers 8 --run
```

This command refuses to train if any hard gate fails.

## Rollback

Delete generated cache artifacts only:

```powershell
Remove-Item -Recurse -Force cache/decoded_images/experiment2_ultralytics_disk_cache
Remove-Item -Recurse -Force cache/benchmarks
Remove-Item -Recurse -Force cache/runtime
```

The canonical dataset and historical launcher are not modified by the optimization workflow.
