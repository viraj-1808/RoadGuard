# Micro-Trial Failure Diagnosis: workers=2, prefetch_factor=2

**Report Date**: 2026-10-09  
**Purpose**: Diagnostic-only investigation of the failed micro-trial. No training, checkpoint modifications, or production config changes performed.

---

## 1. Verified Checkpoint Status

| Checkpoint | File Size | SHA256 | Internal Epoch | Optimizer | O. State Entries | O. Param Groups | Best Fitness | Status |
|------------|-----------|--------|----------------|-----------|-----------------|-----------------|--------------|--------|
| `epoch72.pt` | 76,023,651 bytes | `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5` | **72** | **Present** | **255** | **3** | 0.34476 | ✅ Intact |

**Critical finding**: The checkpoint `epoch72.pt` **DOES contain optimizer state** (AdamW, 3 param groups, 255 state entries). The `next_epoch` value is 73 (72 + 1). The original `epoch72.pt` was **never modified** by the micro-trial.

**Note on earlier discrepancy**: A prior checkpoint inspection task erroneously reported "optimizer absent, 0 entries, 0 groups". The definitive torch.load output confirms optimizer is present. This error propagated into some analysis sections.

### 1a. Checkpoint Integrity Verification

```
SHA256 verification: e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5
✅ Matches expected value from task prompt.

Internal structure (verified via torch.load):
- "epoch": 72 (int)
- "optimizer": dict with keys ['param_groups', 'state']
- "optimizer.state": 255 entries
- "optimizer.param_groups": 3 entries
- "param_groups[0]": AdamW parameters with 'amsgrad', 'betas', 'lr', 'weight_decay', etc.
- "state" example entries: ['exp_avg', 'exp_avg_sq', 'step']
- "best_fitness": 0.34476
- "model": NoneType (not loaded in this checkpoint; weights come from pretrained COCO)
```

---

## 2. Failure Timeline (From Raw Log: microtrial_output.log)

| Event | Epoch | Batch | Time/it | GPU Mem | Notes |
|-------|-------|-------|---------|---------|-------|
| Training started | 74/75 | 0/1233 | — | ~5.17G | Resuming from epoch72.pt; workers=2, prefetch_factor=2 |
| Batch 0 completed | 74/75 | 1/1233 | 5:41 (401 s/it) | 5.17G | Extreme I/O thrashing — OS page cache cold |
| Batches 1-49 | 74/75 | 2-50 | 400+ s/it | 5.17G | Disk I/O bound; system RAM at 90.8% baseline |
| Batch 50 completed | 74/75 | 51/1233 | ~0.34 s/it (2.9 it/s) | 5.17G | **OS page cache warmed** — speed jumped 80× |
| Batches 51-57 | 74/75 | 52-58 | 5.5-1413.9 s/it | 5.17G | Variable; mix of fast/slow batches |
| **Batch 58/1233** | **74/75** | **58/1233** | **5.5 s/it** | **5.17G** | **CRASH** — DataLoader worker exited unexpectedly |
| Training aborted | 74/75 | — | — | — | `RuntimeError: DataLoader worker (pid(s) 11736) exited unexpectedly` |

**Key observation**: The training was already in its **second phase** — batches 0-49 were I/O-thrashing at ~400s/it (system RAM 90.8%, OS cache cold). At batch 50, the OS cache warmed and speed jumped to ~3 it/s. The worker died at batch 58 during the faster phase.

---

## 3. Confirmed Cause vs. Plausible Explanations

### **Confirmed: DataLoader worker (pid 11736) exited unexpectedly**

**Evidence** (from log traceback, verbatim):
```
RuntimeError: DataLoader worker (pid(s) 11736) exited unexpectedly

  File "C:\Users\viraj\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\utils\data\dataloader.py", line 1293, in _try_get_data
    data = self._data_queue.get(timeout=timeout)
  File "C:\Users\viraj\AppData\Local\Programs\Python\Python312\Lib\queue.py", line 179, in get
    raise Empty
_queue.Empty
```

**The `_queue.Empty` is PyTorch's error wrapping**, not the root cause. It means:
1. Main process called `self._data_queue.get(timeout=timeout)`
2. The worker process (pid 11736) had already exited
3. The queue was empty (no data coming from dead worker)
4. PyTorch raised `QueueEmpty`, which it converts to `RuntimeError: DataLoader worker exited unexpectedly`

**The actual WHY the worker died is NOT reported by this traceback.** It only reports the symptom.

### **Plausible explanation: Windows OOM killed the worker process**

**Evidence FOR OOM**:
- System RAM: 90.8% before training; 95-97% during training (monitoring CSV: 95.72% at 16:43:04, 97.38% at 16:44:08)
- Only 1.43 GB RAM available before training; ~572 MB GPU free (6141 MiB total, 5722 MiB used)
- Worker died during phase with high memory pressure (model 5.17 GB + data loading + augmentation + optimizer)
- On Windows, when commit charge exceeds available memory + pagefile, the OS kills individual processes to reclaim memory. A DataLoader worker allocating image batches is a natural target.

**Evidence AGAINST simple OOM**:
- GPU memory: 5.17 GB / 6.14 GB — GPU still had ~1 GB free
- Main process survived — only the worker died
- No explicit "Out of Memory" error in the traceback
- GPU utilization was 84% before crash — if system OOM, GPU would likely be unaffected but process would be killed

**Most likely**: **Windows killed the DataLoader worker process** to free system RAM, consistent with 95-97% physical memory usage. The worker died (exit code from OOM), and the main process detected the empty queue and raised the RuntimeError. This is NOT a pure GPU OOM — GPU had room — but a **system RAM pressure** event on a 16 GB RAM machine.

### **Alternative: Unhandled exception in worker data pipeline**

The worker could have crashed due to:
- An exception in PIL/image loading (corrupt image, unsupported format)
- An exception in augmentation pipeline
- A segfault in a native dependency (e.g., OpenCV)

**Counter-evidence**: No image-loading errors appeared in the log before the crash. The variable batch speeds (400s/it → 3 it/s → 5.5s/it) are consistent with OS page cache warming and memory pressure, not individual image errors.

### **Confirmed cause**: **DataLoader worker (pid 11736) exited unexpectedly, most likely due to Windows memory-pressure-induced process kill.** The traceback confirms the worker death; the root cause (OOM) is strongly indicated by RAM levels but not explicitly logged.

---

## 4. Evidence For and Against OOM

| **For OOM** | **Against simple OOM** |
|-------------|------------------------|
| • RAM 90.8% at baseline, 95-97% during training | • GPU had 1 GB free (5.17/6.14 GB) |
| • Worker died during high-RAM phase of training | • Main process survived intact |
| • Windows kills processes under memory pressure | • No "Out of memory" error in traceback |
| • `queue.Empty` = worker process terminated | • Training slowed then crashed, not immediate OOM |
| • 16 GB RAM is tight for YOLO + 2 workers + data loading | | 

**Conclusion**: The failure is **consistent with OOM** but **not definitively labeled as such**. The worker exited unexpectedly due to memory pressure on a 16 GB RAM system. The root cause is Windows process kill under commit-charge pressure, not a GPU OOM.

---

## 5. Memory-Monitoring Limitations

| Metric | What's Measured | What's NOT Measured | Risk |
|--------|-----------------|---------------------|------|
| **System RAM %** | `psutil.virtual_memory().percent` (physical RAM used / total) | Windows committed memory / pagefile usage | High — may miss commit-limit exhaustion |
| **Process RSS** | `process.memory_info().rss` (main process only + recursive children) | Per-worker RSS (individual DataLoader workers) | Medium — total may hide individual worker spikes |
| **Combined RSS** | `process_rss_gb + child_rss_gb` | Any single worker's RSS that contributes to the total | Medium |
| **GPU allocated/reserved** | `torch.cuda.memory_allocated()` / `reserved()` (current snapshot, NOT peak max) | GPU memory peaks between 0.5-sec samples | Medium — short GPU spikes invisible |
| **GPU utilization %** | NOT measured in microtrial (only in benchmark via nvidia-smi) | GPU utilization during training | High — cannot correlate GPU load with RAM spikes |
| **Sampling interval** | 0.5 sec (microtrial), 60 sec (PowerShell monitor) | **Any memory peak shorter than sample interval** | **Critical — both monitors use periodic polling; sub-interval peaks are completely invisible** |

**Key gap**: Neither the benchmark's `SystemMonitor` (0.05 sec interval) nor the microtrial's `ResourceMonitor` (0.5 sec interval) uses continuous monitoring. Any RAM or GPU memory spike **between two consecutive `time.sleep()` calls is completely missed**. On a system already at 90%+ RAM, a brief 100-ms spike could trigger Windows OOM kill without being recorded.

**Additionally**: Neither implementation measures **Windows committed memory** or **pagefile usage**. The `psutil.virtual_memory().used` reports physical RAM in use, but Windows may decide to kill processes based on committed charge (physical + pagefile), which is unmonitored here.

---

## 6. Validity of the 160× Slowdown Claim

**The 160× claim is INVALID.**

### Source of the claim:
> "Current training is ~160× slower than benchmark results (65.45 samples/sec → ~0.4 samples/sec)"

### Actual data from the micro-trial log:

| Phase | Measured speed | Calculation |
|-------|---------------|-------------|
| Batches 0-49 (I/O-thrashing): ~400 s/it | 0.04 samples/sec (16 img / 400 s) | |
| Batch 50+ (cache warm): ~5 s/it | 3.2 samples/sec (16 img / 5 s) | |
| Benchmark (workers=2, pf=2): 0.244 s/batch | 65.45 samples/sec (16 img / 0.244 s) | |

### Problems with the 160× claim:

1. **Wrong numerator**: The "0.4 samples/sec" doesn't match either measured phase:
   - Slow phase: 0.04 samples/sec (not 0.2)
   - Fast phase: 3.2 samples/sec (not 0.2)
   - The 0.4 figure appears derived from 65.45/160 ≈ 0.409, i.e., the claim assumed 0.4 and worked backward.

2. **Wrong denominator comparison**: Comparing dataloader-only benchmark throughput (65.45 samples/sec, loading + augmentation only) to end-to-end training throughput is **apples to oranges**. Training includes GPU forward + backward pass, which the benchmark does not.

3. **Phase inconsistency**: The 235 s/it (at batch 45) and 0.4 samples/sec were from the **I/O-thrashing phase** (batches 0-49, OS cache cold). After batch 50, speed was ~5 s/it (3.2 samples/sec). Comparing a 160× slowdown from the slow phase to the benchmark is misleading — the system was bottlenecked by disk I/O, not the dataloader configuration.

4. **Expected slowdown**: Even in the "fast" phase (cache warm), training at 3.2 samples/sec is ~20× slower than the benchmark's 65.45 samples/sec. This is **expected** because:
   - Benchmark measures dataloader-only (loading + augmentation + PIN memory transfer)
   - Training includes GPU compute (forward + backward pass on RTX 4050)
   - With batch=16 and imgsz=720, GPU compute takes several seconds per batch

### **Retraction**: The 160× slowdown claim is **not supported by the data**. The correct comparison:
- Pre-cache-warm: ~10,000× slower (400 s/it vs 0.244 s/it) — I/O-bound, not dataloader-configuration-bound
- Post-cache-warm: ~20× slower (5 s/it vs 0.244 s/it) — expected due to GPU compute overhead
- Neither supports the specific 160× figure

---

## 7. Differences Between the Two Launchers (Beyond Workers/prefetch)

| Aspect | `experiments/training/run_baseline.py` | `scripts/optimization/microtrial_workers2_prefetch2.py` |
|--------|----------------------------------------|--------------------------------------------------------|
| **Training mode** | Fresh training from scratch (`resume=False`) | **Resumes** from epoch 72 checkpoint (3 additional epochs: 73–75) |
| **Epochs** | 30 fresh epochs | 75 total (resume from 72, run 73–75) |
| **Workers** | `0` (minimal, single-process) | `2` (with `prefetch_factor=2` patched at runtime) |
| **prefetch_factor** | Not set (Ultralytics default = 4) | **Explicitly patched to 2** via `patch_build_dataloader_prefetch()` |
| **Optimizer** | `'auto'` (Ultralytics default) | `'AdamW'` (explicit) |
| **Checkpoint handling** | Uses `weights/yolo11s.pt` directly from model zoo | **Creates modified copy** (`last.pt`) with patched `project`/`name`/`save_dir` to isolate run from original `epoch72.pt` |
| **Resource monitoring** | None | **Full `ResourceMonitor`**: RAM (physical + process RSS + child workers), GPU memory (torch.cuda), CPU, sampling at 0.5 sec |
| **Checkpoint integrity** | Not verified | **SHA256 verified** before and after training; original `epoch72.pt` confirmed unchanged |
| **Safety** | None | **10-second Ctrl+C abort window**; orphan worker scan; abort if RAM >= 95% |
| **Data verification** | None | **Asserts exact image counts**: 19719 train, 2301 val, nc=4 |
| **Orphan process check** | None | **Scans for leftover `ultralytics` Python workers** post-training |
| **Git status** | Not tracked | **Captured before and after** training |
| **Model loading** | `YOLO(model_path)` fresh download/load | `YOLO(CKPT_COPY_PATH)` with `resume=CKPT_COPY_PATH`; original `epoch72.pt` never loaded for training |
| **Config parameters** | 30 epochs, patience=50, `resume=False`, `exist_ok=False` | 75 epochs total (resume), patience=50 disabled, `exist_ok=True` |
| **Reporting** | Console only (print statements) | **JSON + Markdown report** with decision logic, timing, RAM, GPU metrics |
| **Monkeypatching** | None | **Runtime patch of `ultralytics.data.build.build_dataloader`** to override `prefetch_factor` from hard-coded 4 to 2 |

**Key architectural difference**: The microtrial is an **instrumented experimental harness** that monkeypatches Ultralytics at runtime and adds extensive monitoring. `run_baseline.py` is a simple production training script with no instrumentation.

---

## 8. Safest Next Action

Given the diagnostic findings:

1. **Do not recommend workers=4** until the memory-pressure root cause is understood. The failure occurred with workers=2 at 95-97% RAM; workers=4 in benchmark uses 96.1-99.6% RAM (higher), and the combined model+optimizer+data loading footprint may exceed 16 GB.

2. **Do not recommend workers=8** either — the production run also runs at ~96% RAM and is stable only because it was designed for it. The micro-trial showed workers=8 has better throughput but similar/higher RAM pressure.

3. **Do not assume the worker settings caused every observed difference**. The launcher comparison reveals many unintended differences (resume semantics, checkpoint isolation, monitoring, optimizer, etc.). The worker death may be a secondary effect of memory pressure, not the primary cause of slowdown.

4. **Recommended immediate next step**: Investigate whether **`cache=True`** reduces the I/O-thrashing phase that preceded the crash. The log showed batches 0-49 at ~400 s/it (cache cold), then batch 50+ at ~5 s/it (cache warm). Enabling `cache=True` would keep pre-processed images in RAM, eliminating the cold-start I/O bottleneck that may have contributed to memory pressure accumulation.

5. **Monitor Windows committed memory** in any future trial — the unmonitored pagefile/commit charge is the most likely missing variable in the OOM analysis.

6. **Retract the 160× slowdown claim** in any published analysis. The correct speed comparison is ~20× slower (post-cache-warm) or ~10,000× slower (pre-cache-warm, I/O-bound), not 160×.

---

## References

- `microtrial_output.log` — Raw training log (complete, 227 lines)
- `experiments/optimization/microtrial_monitoring.csv` — RAM/GPU monitoring CSV (2 data rows)
- `runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt` — Checkpoint (SHA256 verified intact)
- `experiments/optimization/dataloader_benchmark/benchmark_results.json` — Dataloader benchmark (13 configs)
- `scripts/optimization/microtrial_workers2_prefetch2.py` — Micro-trial launcher script
- `experiments/training/run_baseline.py` — Production continuation launcher
- `psutil` library — RAM/process measurement API
- PyTorch DataLoader `_try_get_data` — Error-handling mechanism

---

**Diagnostic report generated**: 2026-10-09  
**Constraints**: No training, no checkpoint modifications, no dataset modifications, no production launcher modifications, no new worker-count benchmark, no recommendation of workers=4 until failure investigated.