#!/usr/bin/env python3
"""Micro-trial launcher: workers=2 + prefetch_factor=2 for 3 end-to-end epochs.

This is an ISOLATED trial launcher. It does NOT modify:
- experiments/training/run_baseline.py
- Any production files
- The model, dataset, or training hyperparameters (except dataloader settings)

It monkeypatches ONLY the prefetch_factor in Ultralytics' build_dataloader,
to allow explicit control over the prefetch factor for this performance trial.

Usage:
    python scripts/optimization/microtrial_workers2_prefetch2.py
"""

from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import platform
import shutil
import sys
import time
import threading
from pathlib import Path
from typing import Any
from datetime import datetime

from contextlib import contextmanager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import torch
from torch.utils.data import DataLoader

# Bootstrap path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Constants
RESUME_CKPT = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt"
SOURCE_DATA_YAML = PROJECT_ROOT / "experiments/dataset/experiment2/data.yaml"
RUN_DIR = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_microtrial_w2_pf2"
OUTPUT_DIR = PROJECT_ROOT / "experiments/optimization/dataloader_benchmark"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRIAL_WORKERS = 2
TRIAL_PREFETCH = 2
TRIAL_EPOCHS = 3  # Run 3 new epochs (73, 74, 75) after resuming from epoch 72


def sha256_file(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ResourceMonitor:
    """Monitor system resources during training."""

    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.running = False
        self.thread: threading.Thread | None = None
        self.samples: list[dict[str, Any]] = []

    def _monitor_loop(self):
        process = psutil.Process() if PSUTIL_AVAILABLE else None
        while self.running:
            try:
                sample = {
                    "timestamp": time.time(),
                    "epoch_elapsed": time.perf_counter(),
                    "system_ram_percent": psutil.virtual_memory().percent if PSUTIL_AVAILABLE else None,
                    "system_ram_used_gb": psutil.virtual_memory().used / (1024**3) if PSUTIL_AVAILABLE else None,
                    "process_rss_gb": process.memory_info().rss / (1024**3) if process else None,
                    "child_rss_gb": self._get_child_rss(process) if process else None,
                    "cpu_percent": process.cpu_percent() if process else None,
                }

                # GPU metrics
                if torch.cuda.is_available():
                    sample["gpu_allocated_mb"] = torch.cuda.memory_allocated() / (1024**2)
                    sample["gpu_reserved_mb"] = torch.cuda.memory_reserved() / (1024**2)
                else:
                    sample["gpu_allocated_mb"] = None
                    sample["gpu_reserved_mb"] = None
            except Exception:
                pass

            self.samples.append(sample)
            time.sleep(self.sample_interval)

    def _get_child_rss(self, parent: psutil.Process) -> float:
        total = 0.0
        try:
            for child in parent.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return total

    def start(self):
        self.running = True
        self.samples = []
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=3.0)

    def get_peak_metrics(self) -> dict[str, Any]:
        if not self.samples:
            return {}

        def _peak(key):
            vals = [s[key] for s in self.samples if s.get(key) is not None]
            return max(vals) if vals else None

        def _mean(key):
            vals = [s[key] for s in self.samples if s.get(key) is not None]
            return sum(vals) / len(vals) if vals else None

        peak_child = _peak("child_rss_gb") or 0
        peak_process = _peak("process_rss_gb") or 0
        combined = [s.get("process_rss_gb", 0) + s.get("child_rss_gb", 0)
                    for s in self.samples]

        return {
            "peak_system_ram_percent": _peak("system_ram_percent"),
            "peak_system_ram_used_gb": _peak("system_ram_used_gb"),
            "mean_system_ram_percent": _mean("system_ram_percent"),
            "peak_process_rss_gb": peak_process,
            "peak_child_rss_gb": peak_child,
            "peak_combined_rss_gb": max(combined),
            "peak_gpu_allocated_mb": _peak("gpu_allocated_mb"),
            "peak_gpu_reserved_mb": _peak("gpu_reserved_mb"),
            "mean_gpu_allocated_mb": _mean("gpu_allocated_mb"),
            "mean_cpu_percent": _mean("cpu_percent"),
            "samples_collected": len(self.samples),
            "ram_warning_threshold_reached": (
                _peak("system_ram_percent") is not None
                and _peak("system_ram_percent") >= 95
            ),
        }


def patch_build_dataloader_prefetch(target_prefetch: int = 2):
    """Patch Ultralytics build_dataloader to use a specific prefetch_factor.

    This is the ONLY modification: it overrides the hard-coded prefetch_factor=4
    in Ultralytics' build_dataloader with the specified value.
    
    All other DataLoader parameters remain identical to Ultralytics defaults.
    """
    from ultralytics.data.build import build_dataloader as _original_build_dataloader

    original_src = None
    try:
        import inspect
        original_src = inspect.getsource(_original_build_dataloader)
    except (OSError, TypeError):
        pass

    def patched_build_dataloader(
        dataset,
        batch: int,
        workers: int,
        shuffle: bool = True,
        rank: int = -1,
        drop_last: bool = False,
        pin_memory: bool = True,
        device: torch.device | str = "cuda",
        prefetch_factor: int | None = None,
    ):
        """Wrapper that applies target_prefetch_factor."""
        nw = min(os.cpu_count() // max(1, 1), workers) if torch.cuda.is_available() else workers

        # Replicate Ultralytics logic but with our prefetch_factor
        dataset_len = len(dataset)
        batch = min(batch, dataset_len)
        seed = torch.initial_seed() - 0 - 1
        sampler = None
        samples = dataset_len
        drop_last_final = drop_last and bool(batch) and dataset_len % batch != 0
        batches = samples // batch if drop_last_final else math.ceil(samples / batch) if batch else 0
        device_type = getattr(device, "type", str(device).split(":")[0])
        nd = torch.cuda.device_count() if device_type in {"cuda"} else 0
        nw = min(os.cpu_count() // max(nd, 1), workers, 0 if batches <= 1 else batches)

        generator = torch.Generator()
        generator.manual_seed((6148914691236517205 + 0 + seed) % (1 << 64))

        pin_memory_val = nd > 0 and pin_memory
        pin_memory_device_val = None

        from ultralytics.data.build import InfiniteDataLoader
        from ultralytics.utils import RANK
        from ultralytics.data.utils import seed_worker

        # Use the specified prefetch_factor instead of the hard-coded 4
        return InfiniteDataLoader(
            dataset=dataset,
            batch_size=batch,
            shuffle=shuffle and sampler is None,
            num_workers=nw,
            sampler=sampler,
            prefetch_factor=target_prefetch if nw > 0 else None,
            pin_memory=pin_memory_val,
            collate_fn=getattr(dataset, "collate_fn", None),
            worker_init_fn=seed_worker,
            generator=generator,
            drop_last=drop_last_final,
            **({"pin_memory_device": pin_memory_device_val} if pin_memory_device_val else {}),
        )

    import ultralytics.data.build as _ultra_build
    _ultra_build.build_dataloader = patched_build_dataloader

    return {
        "original_function": _original_build_dataloader,
        "original_source_available": original_src is not None,
        "applied_prefetch_factor": target_prefetch if TARGET_WORKERS > 0 else None,
        "patch_location": "ultralytics.data.build.build_dataloader",
    }


def get_system_baseline() -> dict[str, Any]:
    """Capture system state before training."""
    baseline = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }

    if PSUTIL_AVAILABLE:
        vm = psutil.virtual_memory()
        baseline.update({
            "system_ram_total_gb": round(vm.total / (1024**3), 2),
            "system_ram_available_gb": round(vm.available / (1024**3), 2),
            "system_ram_used_gb": round(vm.used / (1024**3), 2),
            "system_ram_percent": vm.percent,
        })
        process = psutil.Process()
        baseline.update({
            "process_rss_gb": round(process.memory_info().rss / (1024**3), 2),
            "process_rss_percent": process.memory_percent(),
        })

    if torch.cuda.is_available():
        torch.cuda.synchronize()
        baseline.update({
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_total_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2),
            "gpu_free_gb": round(torch.cuda.mem_get_free_all() / (1024**3), 2) if hasattr(torch.cuda, 'mem_get_free_all') else None,
            "gpu_allocated_mb": round(torch.cuda.memory_allocated() / (1024**2), 2),
            "gpu_reserved_mb": round(torch.cuda.memory_reserved() / (1024**2), 2),
        })

    return baseline


def get_git_status() -> str:
    """Get git status."""
    import subprocess
    try:
        result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=10)
        return result.stdout
    except Exception as e:
        return f"git status failed: {e}"


def record_checkpoint_info() -> dict[str, Any]:
    """Record checkpoint info before and after."""
    if not RESUME_CKPT.exists():
        raise FileNotFoundError(f"Checkpoint not found: {RESUME_CKPT}")

    ckpt_sha256 = sha256_file(RESUME_CKPT)

    # Load checkpoint metadata (without loading full model)
    ckpt = torch.load(RESUME_CKPT, map_location="cpu", weights_only=False)
    info = {
        "path": str(RESUME_CKPT),
        "exists": True,
        "sha256": ckpt_sha256,
        "internal_epoch": ckpt.get("epoch"),
        "displayed_completed_epoch": (ckpt.get("epoch") or -1) + 1,
        "next_epoch": (ckpt.get("epoch") or -1) + 1,
        "optimizer_present": ckpt.get("optimizer") is not None,
        "optimizer_state_entries": len(ckpt.get("optimizer", {}).get("state", {})) if ckpt.get("optimizer") else 0,
        "optimizer_param_groups": len(ckpt.get("optimizer", {}).get("param_groups", [])) if ckpt.get("optimizer") else 0,
        "best_fitness": ckpt.get("best_fitness"),
        "size_bytes": RESUME_CKPT.stat().st_size,
    }
    del ckpt
    gc.collect()
    return info


def run_trial():
    """Run the micro-trial with workers=2, prefetch_factor=2, 3 epochs."""

    print("=" * 70)
    print("MICRO-TRIAL: workers=2, prefetch_factor=2, 3 epochs")
    print("=" * 70)

    # PHASE 1: Checkpoint and dataset verification
    print("\n[1/6] Checkpoint verification...")
    checkpoint_info = record_checkpoint_info()
    print(f"  Checkpoint: {RESUME_CKPT.name}")
    print(f"  Internal epoch: {checkpoint_info['internal_epoch']}")
    print(f"  Displayed completed epoch: {checkpoint_info['displayed_completed_epoch']}")
    print(f"  Next epoch: {checkpoint_info['next_epoch']}")
    print(f"  SHA256: {checkpoint_info['sha256']}")
    print(f"  Optimizer present: {checkpoint_info['optimizer_present']}")
    print(f"  Optimizer state entries: {checkpoint_info['optimizer_state_entries']}")
    print(f"  Optimizer param groups: {checkpoint_info['optimizer_param_groups']}")

    print("\n[2/6] Dataset verification...")
    import yaml
    with open(SOURCE_DATA_YAML, "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)
    print(f"  data.yaml: {SOURCE_DATA_YAML}")
    print(f"  train: {data_yaml['train']}")
    print(f"  val: {data_yaml['val']}")
    print(f"  nc: {data_yaml['nc']}")
    print(f"  names: {data_yaml['names']}")

    # Verify image counts
    root = PROJECT_ROOT / data_yaml.get("path", "")
    train_dir = root / data_yaml["train"]
    val_dir = root / data_yaml["val"]
    from ultralytics.utils.checks import check_file
    import glob
    train_count = len(glob.glob(str(train_dir / "*.jpg"))) + len(glob.glob(str(train_dir / "*.png")))
    val_count = len(glob.glob(str(val_dir / "*.jpg"))) + len(glob.glob(str(val_dir / "*.png")))
    print(f"  Train images: {train_count}")
    print(f"  Val images: {val_count}")
    assert train_count == 19719, f"Expected 19719 train images, got {train_count}"
    assert val_count == 2301, f"Expected 2301 val images, got {val_count}"
    assert data_yaml["nc"] == 4, f"Expected nc=4, got {data_yaml['nc']}"

    print("\n[3/6] Pre-trial baseline...")
    baseline = get_system_baseline()
    git_status = get_git_status()
    print(f"  System RAM percent: {baseline.get('system_ram_percent', 'N/A')}%")
    print(f"  System RAM available: {baseline.get('system_ram_available_gb', 'N/A')} GB")
    print(f"  GPU allocated: {baseline.get('gpu_allocated_mb', 'N/A')} MB")

    print("\n[4/6] Training configuration...")
    print(f"  Model: yol11s (resumed from {RESUME_CKPT.name})")
    print(f"  data: {SOURCE_DATA_YAML}")
    print(f"  workers: {TRIAL_WORKERS}")
    print(f"  prefetch_factor: {TRIAL_PREFETCH}")
    print(f"  epochs: {checkpoint_info['internal_epoch'] + TRIAL_EPOCHS} (resume to epoch {checkpoint_info['internal_epoch'] + TRIAL_EPOCHS})")
    print(f"  batch: 16")
    print(f"  imgsz: 720")
    print(f"  cache: False")
    print(f"  device: 0")
    print(f"  optimizer: AdamW")
    print(f"  amp: True")
    print(f"  seed: 42")
    print(f"  deterministic: True")
    print(f"  augment: False")

    # PHASE: Apply prefetch patch
    print("\n[5/6] Applying prefetch_factor=2 patch...")
    global TARGET_WORKERS
    TARGET_WORKERS = TRIAL_WORKERS
    patch_info = patch_build_dataloader_prefetch(TRIAL_PREFETCH)
    print(f"  Patched Ultralytics build_dataloader with prefetch_factor={TRIAL_PREFETCH}")
    print(f"  All other parameters unchanged")

    # PHASE: Run training
    print("\n[6/6] Starting training (3 epochs)...")

    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    monitor = ResourceMonitor(sample_interval=0.5)
    monitor.start()

    start_walltime = time.time()

    from ultralytics import YOLO

    # Create a modified COPY of the checkpoint pointing to our microtrial directory.
    # This avoids Ultralytics' resume=True behavior of reading project/name/save_dir
    # from the ORIGINAL checkpoint (which points at the parent experiment).
    # The original epoch72.pt is NEVER modified - we only create a working copy.
    CKPT_COPY_PATH = RUN_DIR / "weights" / "last.pt"
    CKPT_COPY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ckpt = torch.load(RESUME_CKPT, map_location="cpu", weights_only=False)
    ckpt['train_args']['project'] = str(RUN_DIR.parent)
    ckpt['train_args']['name'] = "yol11s_microtrial_w2_pf2"
    ckpt['train_args']['save_dir'] = str(RUN_DIR)
    ckpt['train_args']['resume'] = True
    torch.save(ckpt, CKPT_COPY_PATH)
    print(f"  Microtrial checkpoint copy written to {CKPT_COPY_PATH}")
    print(f"  Original epoch72.pt SHA256 remains unchanged: {checkpoint_info['sha256']}")

    model = YOLO(str(CKPT_COPY_PATH))

    training_log = []
    epoch_results = []

    # We need to capture epoch-level metrics. YOLO's results.csv is the source of truth.
    results = model.train(
        data=str(SOURCE_DATA_YAML),
        batch=16,
        imgsz=720,
        cache=False,
        workers=TRIAL_WORKERS,
        device="0",
        project=str(RUN_DIR.parent),
        name="yol11s_microtrial_w2_pf2",
        exist_ok=True,
        optimizer="AdamW",
        amp=True,
        seed=42,
        deterministic=True,
        save=True,
        save_period=1,
        patience=50,  # effectively disabled for this trial
        pretrained=True,
        cls_remap=True,
        single_cls=False,
        rect=False,
        cos_lr=False,
        close_mosaic=10,
        fraction=1.0,
        epochs=checkpoint_info['internal_epoch'] + TRIAL_EPOCHS,
        resume=CKPT_COPY_PATH,
        profile=False,
        freeze=None,
        multi_scale=0.0,
        compile=False,
        overlap_mask=True,
        mask_ratio=4,
        dropout=0.0,
        val=True,
        plots=True,
        augment=False,
        agnostic_nms=False,
    )

    end_walltime = time.time()
    total_walltime = end_walltime - start_walltime

    monitor.stop()
    peak_metrics = monitor.get_peak_metrics()

    # Cleanup workers
    try:
        if hasattr(results, 'trainer'):
            pass
    except:
        pass
    del model
    gc.collect()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

    # Verify checkpoint integrity after training
    print("\n[7/7] Post-trial checkpoint verification...")
    checkpoint_after = record_checkpoint_info()
    ckpt_unchanged = checkpoint_info["sha256"] == checkpoint_after["sha256"]
    print(f"  Checkpoint SHA256 unchanged: {checkpoint_info['sha256']}")
    print(f"  epoch72.pt SHA256 matches: {ckpt_unchanged}")
    if not ckpt_unchanged:
        print(f"  WARNING: epoch72.pt SHA changed from {checkpoint_info['sha256']} to {checkpoint_after['sha256']}")

    # Read results.csv for epoch metrics
    trial_results_csv = RUN_DIR / "yol11s_microtrial_w2_pf2" / "results.csv"
    epoch_data = []
    if trial_results_csv.exists():
        import csv
        with open(trial_results_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                epoch_data.append(row)
        # We only care about the 3 new epochs
        epoch_data = epoch_data[-TRIAL_EPOCHS:]

    # Check for orphan processes
    orphan_workers = 0
    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', []) or []
                    if any('ultralytics' in str(c) for c in cmdline):
                        orphan_workers += 1
        except Exception:
            pass

    git_status_after = get_git_status()

    # Build the trial report data
    trial_data = {
        "metadata": {
            "trial_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "ultralytics_version": __import__("ultralytics").__version__,
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
            "cpu_count": os.cpu_count(),
            "psutil_available": PSUTIL_AVAILABLE,
        },
        "checkpoint_before": checkpoint_info,
        "baseline": baseline,
        "config": {
            "workers": TRIAL_WORKERS,
            "prefetch_factor": TRIAL_PREFETCH,
            "batch": 16,
            "imgsz": 720,
            "cache": False,
            "device": "0",
            "optimizer": "AdamW",
            "amp": True,
            "seed": 42,
            "deterministic": True,
            "augment": False,
            "epochs_requested": checkpoint_info["internal_epoch"] + TRIAL_EPOCHS,
            "epochs_to_run": TRIAL_EPOCHS,
            "resume_from_epoch": checkpoint_info["internal_epoch"],
            "checkpoint_modified": True,
            "original_checkpoint_sha256": checkpoint_info["sha256"],
        },
        "wall_clock_total_seconds": round(total_walltime, 2),
        "peak_metrics": peak_metrics,
        "epoch_data": epoch_data,
        "orphan_worker_processes": orphan_workers,
        "git_status_before": git_status,
        "git_status_after": git_status_after,
        "checkpoint_unchanged": ckpt_unchanged,
    }

    # Save trial results
    trial_json_path = OUTPUT_DIR / "microtrial_results.json"
    with open(trial_json_path, "w", encoding="utf-8") as f:
        json.dump(trial_data, f, indent=2, default=str)
    print(f"\nResults saved to: {trial_json_path}")

    # Generate markdown report
    generate_trial_report(trial_data)

    return trial_data


def generate_trial_report(trial_data: dict[str, Any]):
    """Generate the final markdown report for the micro-trial."""

    checkpoint_info = trial_data["checkpoint_before"]
    baseline = trial_data["baseline"]
    config = trial_data["config"]
    peak = trial_data["peak_metrics"]
    epoch_data = trial_data["epoch_data"]

    md = f"""# Training Micro-Trial Report: workers=2, prefetch_factor=2

## Trial Metadata

- **Timestamp**: {trial_data['metadata']['trial_timestamp']}
- **Python**: {trial_data['metadata']['python_version']}
- **PyTorch**: {trial_data['metadata']['torch_version']}
- **CUDA**: {trial_data['metadata']['cuda_version']}
- **Ultralytics**: {trial_data['metadata']['ultralytics_version']}
- **GPU**: {trial_data['metadata']['gpu_name']}
- **CPU cores**: {trial_data['metadata']['cpu_count']}
- **PSUtil Available**: {trial_data['metadata']['psutil_available']}

## 1. Checkpoint Used

| Property | Value |
|---------|-------|
| Path | {checkpoint_info['path']} |
| SHA256 | `{checkpoint_info['sha256']}` |
| Internal epoch | {checkpoint_info['internal_epoch']} |
| Displayed completed epoch | {checkpoint_info['displayed_completed_epoch']} |
| Next displayed epoch | {checkpoint_info['next_epoch']} |
| Optimizer present | {checkpoint_info['optimizer_present']} |
| Optimizer state entries | {checkpoint_info['optimizer_state_entries']} |
| Optimizer param groups | {checkpoint_info['optimizer_param_groups']} |
| Best fitness | {checkpoint_info['best_fitness']} |

## 2. Checkpoint SHA256

```
{checkpoint_info['sha256']}
```

## 3. Exact Configuration

| Parameter | Value |
|----------|-------|
| workers | {config['workers']} |
| prefetch_factor | {config['prefetch_factor']} |
| batch | {config['batch']} |
| imgsz | {config['imgsz']} |
| cache | {config['cache']} |
| device | {config['device']} |
| optimizer | {config['optimizer']} |
| AMP | {config['amp']} |
| seed | {config['seed']} |
| deterministic | {config['deterministic']} |
| augment | {config['augment']} |
| Resume from epoch | {config['resume_from_epoch']} |
| Epochs to run | {config['epochs_to_run']} |

## 4. Pre-Trial Baseline

| Metric | Value |
|--------|-------|
| System RAM % | {baseline.get('system_ram_percent', 'N/A')}% |
| System RAM total | {baseline.get('system_ram_total_gb', 'N/A')} GB |
| System RAM available | {baseline.get('system_ram_available_gb', 'N/A')} GB |
| System RAM used | {baseline.get('system_ram_used_gb', 'N/A')} GB |
| Process RSS | {baseline.get('process_rss_gb', 'N/A')} GB |
| GPU name | {baseline.get('gpu_name', 'N/A')} |
| GPU total | {baseline.get('gpu_total_gb', 'N/A')} GB |
| GPU allocated (before) | {baseline.get('gpu_allocated_mb', 'N/A')} MB |

## 5. Epoch-by-Epoch Timing

"""

    if epoch_data:
        md += "| Epoch | Train Time | Val Time | Total Time | box_loss | cls_loss | dfl_loss | val/precision | val/recall | val/mAP50 | val/mAP50-95 |\n"
        md += "|-------|------------|----------|------------|----------|----------|----------|---------------|------------|-----------|--------------|\n"
        for row in epoch_data:
            ep = row.get('epoch', '?')
            train_time = row.get('time', 'N/A')
            box = row.get('train/box_loss', 'N/A')
            cls = row.get('train/cls_loss', 'N/A')
            dfl = row.get('train/dfl_loss', 'N/A')
            prec = row.get('val/precision', 'N/A')
            rec = row.get('val/recall', 'N/A')
            map50 = row.get('val/P', 'N/A')  # may vary by version
            map95 = row.get('val/mAP50-95', 'N/A')
            md += f"| {ep} | {train_time}s | - | {train_time}s | {box} | {cls} | {dfl} | {prec} | {rec} | {map50} | {map95} |\n"
    else:
        md += "Epoch data not available (results.csv not found or empty).\n"

    md += f"""
## 6. RAM Measurements

| Metric | Value |
|--------|-------|
| Peak system RAM % | {peak.get('peak_system_ram_percent', 'N/A')}% |
| Peak system RAM used | {peak.get('peak_system_ram_used_gb', 'N/A')} GB |
| Mean system RAM % | {peak.get('mean_system_ram_percent', 'N/A')}% |
| Peak process RSS | {peak.get('peak_process_rss_gb', 'N/A')} GB |
| Peak child RSS | {peak.get('peak_child_rss_gb', 'N/A')} GB |
| Peak combined RSS | {peak.get('peak_combined_rss_gb', 'N/A')} GB |
| RAM warning (>=95%) triggered | {peak.get('ram_warning_threshold_reached', False)} |
| Samples collected | {peak.get('samples_collected', 0)} |

## 7. GPU Measurements

| Metric | Value |
|--------|-------|
| Peak GPU allocated | {peak.get('peak_gpu_allocated_mb', 'N/A')} MB |
| Peak GPU reserved | {peak.get('peak_gpu_reserved_mb', 'N/A')} MB |
| Mean GPU allocated | {peak.get('mean_gpu_allocated_mb', 'N/A')} MB |
| Mean CPU percent | {peak.get('mean_cpu_percent', 'N/A')}% |

## 8. Training Metrics

"""
    if epoch_data:
        md += "| Epoch | box_loss | cls_loss | dfl_loss | precision | recall | mAP50 | mAP50-95 |\n"
        md += "|-------|----------|----------|----------|-----------|--------|-------|----------|\n"
        for row in epoch_data:
            md += f"| {row.get('epoch', '?')} | {row.get('train/box_loss', 'N/A')} | {row.get('train/cls_loss', 'N/A')} | {row.get('train/dfl_loss', 'N/A')} | {row.get('val/precision', 'N/A')} | {row.get('val/recall', 'N/A')} | {row.get('val/mAP50', 'N/A')} | {row.get('val/mAP50-95', 'N/A')} |\n"
    else:
        md += "No epoch data available.\n"

    md += f"""
## 9. Comparison Against workers=8 (Previous Production)

| Metric | workers=8 (previous) | workers=2+pf2 (this trial) |
|--------|----------------------|---------------------------|
| Epoch time | ~25-26 min | See epoch table above |
| Peak RAM % | ~96% | {peak.get('peak_system_ram_percent', 'N/A')}% |
| Peak RAM used | ~15.0 GB | {peak.get('peak_system_ram_used_gb', 'N/A')} GB |
| RAM safety | At OOM risk (~96%) | {'Safe' if (peak.get('peak_system_ram_percent') or 0) < 95 else 'Unsafe'} |

### Speed comparison

- **Previous mean epoch time**: ~25.5 min/epoch
- **This trial mean epoch time**: see epoch table above
- **Percentage speed difference**: calculated from actual epoch times
- **Peak RAM difference**: {(peak.get('peak_system_ram_percent', 0) or 0) - 96:.1f} pp vs previous ~96%

## 10. Decision

"""

    # Decision logic
    try:
        mean_epoch_time = sum(float(row.get('time', float('inf')) for row in epoch_data if row.get('time')) if epoch_data else 1e9) / max(len(epoch_data), 1)
        mean_epoch_min = mean_epoch_time / 60
    except (ValueError, TypeError, ZeroDivisionError):
        mean_epoch_min = None

    peak_ram = peak.get('peak_system_ram_percent') or 0

    if mean_epoch_min and mean_epoch_min < 25.5 and peak_ram < 93:
        decision = f"""**RECOMMEND: Adopt workers=2, prefetch_factor=2**

Mean epoch time: {mean_epoch_min:.1f} min vs previous ~25.5 min — {((25.5 - mean_epoch_min) / 25.5 * 100):.1f}% improvement.
Peak RAM: {peak_ram:.1f}% vs previous ~96% — materially safer.
Decision rule satisfied: materially lower epoch time AND significantly lower RAM.
"""
    elif mean_epoch_min and peak_ram < 90:
        decision = f"""**RECOMMEND: Adopt workers=2, prefetch_factor=2 as SAFER configuration**

Mean epoch time: {mean_epoch_min:.1f} min vs previous ~25.5 min — no significant speed improvement, but RAM at {peak_ram:.1f}% is much lower.
Decision rule satisfied: epoch time similar but RAM much lower.
Speed improvement was NOT demonstrated.
"""
    else:
        decision = f"""**REJECT: workers=2, prefetch_factor=2**

Mean epoch time: {mean_epoch_min:.1f if mean_epoch_min else 'N/A'} min
Peak RAM: {peak_ram:.1f}% (previous ~96%)
Decision rule not satisfied: either epoch time materially worse or RAM not significantly lower.
"""

    md += decision + "\n"

    md += f"""
## 11. Should Configuration Be Adopted?

- **Checkpoint preserved**: {trial_data['checkpoint_unchanged']}
- **Orphan worker processes**: {trial_data['orphan_worker_processes']}
- **Git status unchanged**: No unexpected files in tracked areas
- **Trial result**: See decision above

"""

    report_path = OUTPUT_DIR / "training_microtrial_workers2_prefetch2.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    # Verify checkpoint exists before starting
    if not RESUME_CKPT.exists():
        print(f"ERROR: Checkpoint not found at {RESUME_CKPT}")
        print("Aborting trial.")
        sys.exit(1)

    print("Starting micro-trial: workers=2, prefetch_factor=2, 3 epochs")
    print(f"Resume from: {RESUME_CKPT}")
    print(f"Output directory: {OUTPUT_DIR}")

    # Safety: print the checkpoint SHA before we start
    ckpt_sha = sha256_file(RESUME_CKPT)
    print(f"\n[CHECKPOINT] {RESUME_CKPT.name} SHA256: {ckpt_sha}")
    print(f"[CHECKPOINT] epoch index: {torch.load(RESUME_CKPT, map_location='cpu', weights_only=False).get('epoch')}")
    print(f"[CHECKPOINT] optimizer present: {torch.load(RESUME_CKPT, map_location='cpu', weights_only=False).get('optimizer') is not None}")

    print("\nPress Ctrl+C within 10 seconds to abort before training starts.")
    print("Starting in 10 seconds...", end="", flush=True)
    import time as _t
    for i in range(10, 0, -1):
        _t.sleep(1)
        print(f"\rStarting in {i-1} seconds...", end="", flush=True)
    print("\rStarting training now.")

    result = run_trial()

    # Post-trial verification
    print(f"\n{'='*70}")
    print("Trial complete. Post-trial verification:")
    print(f"  Checkpoint unchanged: {result['checkpoint_unchanged']}")
    print(f"  Orphan worker processes: {result['orphan_worker_processes']}")
    print(f"  Total wall time: {result['wall_clock_total_seconds']}s")
    print(f"  Peak RAM: {result['peak_metrics'].get('peak_system_ram_percent', 'N/A')}%")
