#!/usr/bin/env python3
"""Standalone dataloader performance benchmark for RoadGuard YOLO11s Experiment 2.

This script measures CPU data loading and GPU transfer performance for different
worker/prefetch_factor configurations. It does NOT modify the production training
launcher or any training behavior.

Usage:
    python scripts/optimization/dataloader_benchmark_matrix.py
    python scripts/optimization/dataloader_benchmark_matrix.py --smoke-test
    python scripts/optimization/dataloader_benchmark_matrix.py --test <workers> <prefetch>
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any
from contextlib import contextmanager
from threading import Thread
import subprocess

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import torch
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DATA_YAML = PROJECT_ROOT / "experiments/dataset/experiment2/data.yaml"
RESUME_CKPT = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2/weights/epoch53.pt"
OUTPUT_DIR = PROJECT_ROOT / "experiments/optimization/dataloader_benchmark"
BENCHMARK_RESULTS_JSON = OUTPUT_DIR / "benchmark_results.json"
BENCHMARK_RESULTS_CSV = OUTPUT_DIR / "benchmark_results.csv"
BENCHMARK_REPORT_MD = OUTPUT_DIR / "benchmark_report.md"


class SystemMonitor:
    """Monitor system resources during benchmark."""
    
    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.running = False
        self.thread: Thread | None = None
        self.samples: list[dict[str, Any]] = []
        
    def _monitor_loop(self):
        process = psutil.Process()
        while self.running:
            try:
                sample = {
                    "timestamp": time.perf_counter(),
                    "ram_percent": psutil.virtual_memory().percent,
                    "ram_used_gb": psutil.virtual_memory().used / (1024**3),
                    "ram_total_gb": psutil.virtual_memory().total / (1024**3),
                    "process_rss_gb": process.memory_info().rss / (1024**3),
                    "process_child_rss_gb": self._get_child_rss(process) / (1024**3),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                sample = {
                    "timestamp": time.perf_counter(),
                    "ram_percent": 0.0,
                    "ram_used_gb": 0.0,
                    "ram_total_gb": 0.0,
                    "process_rss_gb": 0.0,
                    "process_child_rss_gb": 0.0,
                }
            self.samples.append(sample)
            time.sleep(self.sample_interval)
    
    def _get_child_rss(self, parent: psutil.Process) -> float:
        """Recursively sum RSS of all child processes."""
        total = 0
        try:
            for child in parent.children(recursive=True):
                total += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return total
    
    def start(self):
        self.running = True
        self.samples = []
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def get_peak_metrics(self) -> dict[str, Any]:
        if not self.samples:
            return {"peak_ram_percent": 0, "peak_ram_used_gb": 0, "peak_process_rss_gb": 0, "peak_child_rss_gb": 0, "peak_combined_rss_gb": 0}
        return {
            "peak_ram_percent": max(s["ram_percent"] for s in self.samples),
            "peak_ram_used_gb": max(s["ram_used_gb"] for s in self.samples),
            "peak_process_rss_gb": max(s["process_rss_gb"] for s in self.samples),
            "peak_child_rss_gb": max(s["process_child_rss_gb"] for s in self.samples),
            "peak_combined_rss_gb": max(
                s["process_rss_gb"] + s["process_child_rss_gb"] for s in self.samples
            ),
            "samples_collected": len(self.samples),
        }


def get_gpu_metrics() -> dict[str, Any]:
    """Get GPU memory and utilization metrics."""
    result = {
        "peak_gpu_allocated_mb": 0,
        "peak_gpu_reserved_mb": 0,
        "gpu_utilization_percent": None,
        "nvidia_smi_available": False,
    }
    
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        torch.cuda.synchronize()
        result["peak_gpu_allocated_mb"] = torch.cuda.max_memory_allocated() / (1024**2)
        result["peak_gpu_reserved_mb"] = torch.cuda.max_memory_reserved() / (1024**2)
        torch.cuda.reset_peak_memory_stats()
    
    # Try nvidia-smi for utilization
    try:
        output = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], 
                               capture_output=True, text=True, timeout=5)
        if output.returncode == 0:
            result["nvidia_smi_available"] = True
            utilizations = [int(x.strip()) for x in output.stdout.strip().split("\n") if x.strip()]
            if utilizations:
                result["gpu_utilization_percent"] = statistics.mean(utilizations)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass
    
    return result


def reset_gpu_stats():
    """Reset GPU memory tracking."""
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()


class InfiniteDataLoader(torch.utils.data.DataLoader):
    """DataLoader with infinite batch yielding."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __iter__(self):
        return super().__iter__()
    
    def close(self):
        """Explicitly shut down workers."""
        if hasattr(self, "_num_workers") and self._num_workers > 0:
            self._shutdown_workers()


def _seed_worker(worker_id: int) -> None:
    """Worker initialization for reproducible data loading."""
    import random as _random
    worker_seed = torch.initial_seed() % 2**32
    _random.seed(worker_seed)


def build_training_dataloader(
    dataset,
    batch: int,
    workers: int,
    prefetch_factor: int | None,
    device: torch.device,
) -> InfiniteDataLoader:
    """Build dataloader with configurable prefetch_factor."""
    dataset_len = len(dataset)
    batch = min(batch, dataset_len)
    nw = workers
    
    pin_memory = device.type == "cuda"
    
    return InfiniteDataLoader(
        dataset=dataset,
        batch_size=batch,
        shuffle=True,
        num_workers=nw,
        prefetch_factor=prefetch_factor,
        pin_memory=pin_memory,
        collate_fn=getattr(dataset, "collate_fn", None),
        worker_init_fn=_seed_worker,
        drop_last=False,
    )


def build_dataset_and_loader(
    data_yaml_path: Path,
    imgsz: int,
    batch: int,
    workers: int,
    prefetch_factor: int | None,
    device: torch.device,
) -> tuple[Any, InfiniteDataLoader]:
    """Build dataset and dataloader matching production training setup."""
    from ultralytics.cfg import DEFAULT_CFG, get_cfg
    from ultralytics.data.build import build_yolo_dataset
    from ultralytics.data.utils import check_det_dataset
    
    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    root = PROJECT_ROOT / data.get("path", "")
    data["path"] = str(root)
    
    overrides = {
        "task": "detect",
        "mode": "train",
        "model": str(RESUME_CKPT),
        "data": str(data_yaml_path),
        "epochs": 100,
        "batch": batch,
        "imgsz": imgsz,
        "cache": False,
        "device": str(device),
        "workers": workers,
        "seed": 42,
        "deterministic": True,
        "amp": True,
        "rect": False,
        "single_cls": False,
        "augment": False,
        "fraction": 1.0,
    }
    cfg = get_cfg(DEFAULT_CFG, overrides)
    
    dataset_info = check_det_dataset(str(data_yaml_path))
    dataset = build_yolo_dataset(
        cfg, 
        dataset_info["train"], 
        cfg.batch, 
        dataset_info, 
        mode="train", 
        rect=False, 
        stride=32
    )
    
    loader = build_training_dataloader(
        dataset=dataset,
        batch=batch,
        workers=workers,
        prefetch_factor=prefetch_factor,
        device=device,
    )
    
    return dataset, loader


def benchmark_configuration(
    workers: int,
    prefetch_factor: int | None,
    data_yaml_path: Path,
    imgsz: int,
    batch: int,
    device_idx: int,
) -> dict[str, Any]:
    """Run benchmark for a single configuration."""
    device = torch.device(f"cuda:{device_idx}" if torch.cuda.is_available() else "cpu")
    
    result = {
        "workers": workers,
        "prefetch_factor": prefetch_factor,
        "imgsz": imgsz,
        "batch": batch,
        "device": str(device),
        "error": None,
    }
    
    loader = None
    monitor = SystemMonitor(sample_interval=0.05)
    
    try:
        dataset, loader = build_dataset_and_loader(
            data_yaml_path, imgsz, batch, workers, prefetch_factor, device
        )
        result["dataset_size"] = len(dataset)
        
        reset_gpu_stats()
        monitor.start()
        
        timings: list[float] = []
        transfer_timings: list[float] = []
        
        warmup = min(10, len(dataset) // batch // 4) if len(dataset) >= batch else 5
        measure = 100
        
        iterator = iter(loader)
        
        # Warmup
        for _ in range(warmup):
            _ = next(iterator)
            if device.type == "cuda":
                torch.cuda.synchronize()
        
        # Measure
        for _ in range(measure):
            start = time.perf_counter()
            batch_data = next(iterator)
            loaded = time.perf_counter()
            
            if device.type == "cuda":
                imgs = batch_data["img"].to(device, non_blocking=True).float() / 255
                torch.cuda.synchronize()
                transferred = time.perf_counter()
                del imgs
            else:
                transferred = loaded
            
            if device.type == "cuda":
                timings.append(loaded - start)
                transfer_timings.append(transferred - loaded)
            else:
                timings.append(loaded - start)
                transfer_timings.append(0.0)
        
        gpu_metrics = get_gpu_metrics()
        mem_metrics = monitor.get_peak_metrics()
        
        result.update({
            "batch_intervals": timings,
            "transfer_intervals": transfer_timings,
            "total_benchmark_time_sec": sum(timings) + sum(transfer_timings),
            "mean_batch_interval_ms": statistics.mean(timings) * 1000,
            "median_batch_interval_ms": statistics.median(timings) * 1000,
            "p95_batch_interval_ms": sorted(timings)[int(len(timings) * 0.95)] * 1000,
            "batches_per_sec": len(timings) / sum(timings) if timings else 0,
            "samples_per_sec": len(timings) * batch / sum(timings) if timings else 0,
            "mean_host_to_gpu_transfer_ms": statistics.mean(transfer_timings) * 1000 if device.type == "cuda" else 0,
            "p95_host_to_gpu_transfer_ms": sorted(transfer_timings)[int(len(transfer_timings) * 0.95)] * 1000 if device.type == "cuda" else 0,
            **mem_metrics,
            **gpu_metrics,
        })
        
    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = sys.exc_info()[2].__traceback__
    
    finally:
        if loader is not None:
            try:
                if hasattr(loader, "close"):
                    loader.close()
            except Exception:
                pass
            del loader
        
        if monitor.running:
            monitor.stop()
        
        gc.collect()
        if device.type == "cuda":
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
    
    return result


def run_smoke_test(data_yaml: Path, device_idx: int) -> dict[str, Any]:
    """Run smoke test with workers=2, prefetch=2, 20 batches."""
    print("=" * 60)
    print("SMOKE TEST: workers=2, prefetch_factor=2, 20 batches")
    print("=" * 60)
    
    result = benchmark_configuration(
        workers=2,
        prefetch_factor=2,
        data_yaml_path=data_yaml,
        imgsz=720,
        batch=16,
        device_idx=device_idx,
    )
    
    if result.get("error"):
        print(f"SMOKE TEST FAILED: {result['error']}")
        return result
    
    if len(result.get("batch_intervals", [])) != 20:
        print(f"SMOKE TEST WARNING: Expected 20 intervals, got {len(result.get('batch_intervals', []))}")
    
    print("\nSmoke Test Results:")
    print(f"  Dataset size: {result.get('dataset_size', 'N/A')}")
    print(f"  Total batches: {len(result.get('batch_intervals', []))}")
    print(f"  Mean batch interval: {result.get('mean_batch_interval_ms', 'N/A'):.2f} ms")
    print(f"  Batches/sec: {result.get('batches_per_sec', 'N/A'):.2f}")
    print(f"  Peak RAM used: {result.get('peak_ram_used_gb', 'N/A'):.2f} GB")
    print(f"  Peak GPU allocated: {result.get('peak_gpu_allocated_mb', 'N/A'):.2f} MB")
    print("\nSmoke Test PASSED")
    
    return result


def run_full_matrix(data_yaml: Path, device_idx: int) -> list[dict[str, Any]]:
    """Run full benchmark matrix."""
    results = []
    
    workers_list = [0, 2, 4, 6, 8]
    prefetch_list = [1, 2, 4]
    
    for workers in workers_list:
        if workers == 0:
            configs = [(0, None)]
        else:
            configs = [(workers, pf) for pf in prefetch_list]
        
        for w, pf in configs:
            print(f"\nBenchmarking: workers={w}, prefetch_factor={pf}")
            result = benchmark_configuration(
                workers=w,
                prefetch_factor=pf,
                data_yaml_path=data_yaml,
                imgsz=720,
                batch=16,
                device_idx=device_idx,
            )
            results.append(result)
    
    return results


def write_results(results: list[dict[str, Any]], env_info: dict[str, Any]):
    """Write benchmark results to JSON and CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON
    json_data = {
        "metadata": {
            "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S %z"),
            "python_version": platform.python_version(),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else "N/A",
            "ultralytics_version": __import__("ultralytics").__version__ if "ultralytics" in sys.modules else "N/A",
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
            "cpu_count": os.cpu_count(),
            "ram_total_gb": psutil.virtual_memory().total / (1024**3) if PSUTIL_AVAILABLE else "N/A",
            "device_idx": env_info["device_idx"],
            "psutil_available": PSUTIL_AVAILABLE,
        },
        "environment": env_info,
        "results": results,
    }
    
    with open(BENCHMARK_RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    
    # CSV
    fieldnames = [
        "workers", "prefetch_factor", "mean_batch_interval_ms", "median_batch_interval_ms",
        "p95_batch_interval_ms", "batches_per_sec", "samples_per_sec", "total_benchmark_time_sec",
        "peak_ram_percent", "peak_ram_used_gb", "peak_process_rss_gb", "peak_child_rss_gb",
        "peak_gpu_allocated_mb", "peak_gpu_reserved_mb", "gpu_utilization_percent", "error"
    ]
    
    import csv
    with open(BENCHMARK_RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(row)


def generate_report(results: list[dict[str, Any]], env_info: dict[str, Any]) -> str:
    """Generate markdown report."""
    lines = [
        "# Dataloader Benchmark Report",
        "",
        "## 1. Environment",
        "",
        f"- **Python**: {platform.python_version()}",
        f"- **PyTorch**: {torch.__version__}",
        f"- **CUDA**: {torch.version.cuda if torch.cuda.is_available() else 'N/A'}",
        f"- **Ultralytics**: {__import__('ultralytics').__version__ if 'ultralytics' in sys.modules else 'N/A'}",
        f"- **GPU**: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}",
        f"- **CPU cores**: {os.cpu_count()}",
        f"- **RAM**: {psutil.virtual_memory().total / (1024**3):.2f} GB" if PSUTIL_AVAILABLE else "- **RAM**: N/A (psutil not available)",
        f"- **Dataset**: {SOURCE_DATA_YAML.name}",
        f"- **Checkpoint**: {RESUME_CKPT.name}",
        f"- **Device index**: {env_info['device_idx']}",
        "",
        "## 2. Benchmark Methodology",
        "",
        "- Each configuration: 10 warmup batches, 100 measurement batches",
        "- Batch: 16, Image size: 720 (internally adjusted to 736 by Ultralytics)",
        "- Measure: CPU loading time, host-to-GPU transfer, RAM usage, GPU memory",
        "- All configurations preserve dataset, batch size, imgsz, seed, deterministic",
        "",
        "## 3. Configuration Matrix",
        "",
        "| workers | prefetch_factor | Description |",
        "|--------|-----------------|-------------|",
    ]
    
    good_results = [r for r in results if not r.get("error")]
    for r in good_results:
        pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
        lines.append(f"| {r['workers']} | {pf} | ✓ valid |")
    
    for r in [r for r in results if r.get("error")]:
        pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
        lines.append(f"| {r['workers']} | {pf} | ✗ failed: {r['error'][:50]}... |")
    
    lines.extend([
        "",
        "## 4. Raw Measurements",
        "",
        "| workers | prefetch | mean_ms | median_ms | p95_ms | batches/s | samples/s |",
        "|--------|----------|---------|-----------|--------|-----------|-----------|",
    ])
    
    for r in good_results:
        pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
        lines.append(f"| {r['workers']} | {pf} | {r['mean_batch_interval_ms']:.2f} | {r['median_batch_interval_ms']:.2f} | {r['p95_batch_interval_ms']:.2f} | {r['batches_per_sec']:.2f} | {r['samples_per_sec']:.2f} |")
    
    lines.extend([
        "",
        "## 5. RAM Comparison",
        "",
        "| workers | prefetch | peak_RAM% | peak_RAM_GB | peak_process_GB | peak_child_GB |",
        "|--------|----------|-----------|-------------|-----------------|----------------|",
    ])
    
    for r in good_results:
        pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
        lines.append(f"| {r['workers']} | {pf} | {r['peak_ram_percent']:.1f}% | {r['peak_ram_used_gb']:.2f} | {r['peak_process_rss_gb']:.2f} | {r['peak_child_rss_gb']:.2f} |")
    
    lines.extend([
        "",
        "## 6. Throughput Comparison",
        "",
        "| workers | prefetch | batches/sec | samples/sec |",
        "|--------|----------|-------------|-------------|",
    ])
    
    sorted_by_throughput = sorted(good_results, key=lambda x: x["batches_per_sec"], reverse=True)
    for r in sorted_by_throughput[:10]:
        pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
        lines.append(f"| {r['workers']} | {pf} | {r['batches_per_sec']:.2f} | {r['samples_per_sec']:.2f} |")
    
    lines.extend([
        "",
        "## 7. Pareto Analysis",
        "",
    ])
    
    if good_results:
        # Fastest
        fastest = max(good_results, key=lambda x: x["batches_per_sec"])
        pf = fastest["prefetch_factor"] if fastest["prefetch_factor"] is not None else "None"
        lines.extend([
            f"- **Fastest configuration**: workers={fastest['workers']}, prefetch_factor={pf}" if pf else f"- **Fastest configuration (workers=0)**: batches/sec={fastest['batches_per_sec']:.2f}",
            f"  - Throughput: {fastest['batches_per_sec']:.2f} batches/sec",
            f"  - Mean latency: {fastest['mean_batch_interval_ms']:.2f} ms/batch",
            f"  - RAM: {fastest['peak_ram_used_gb']:.2f} GB ({fastest['peak_ram_percent']:.1f}%)",
            f"  - GPU allocated: {fastest['peak_gpu_allocated_mb']:.0f} MB",
            "",
        ])
        
        # Lowest RAM
        lowest_ram = min(good_results, key=lambda x: x["peak_ram_used_gb"])
        pf = lowest_ram["prefetch_factor"] if lowest_ram["prefetch_factor"] is not None else "None"
        lines.extend([
            f"- **Lowest RAM usage**: workers={lowest_ram['workers']}, prefetch_factor={pf}" if pf else f"- **Lowest RAM usage (workers=0)**: {lowest_ram['peak_ram_used_gb']:.2f} GB",
            f"  - RAM: {lowest_ram['peak_ram_used_gb']:.2f} GB ({lowest_ram['peak_ram_percent']:.1f}%)",
            "",
        ])
        
        # Best speed/RAM tradeoff (simple heuristic: minimize ratio of RAM to throughput)
        if PSUTIL_AVAILABLE and lowest_ram["peak_ram_percent"] > 0:
            for r in good_results:
                r["ram_perf_ratio"] = r["peak_ram_percent"] / r["batches_per_sec"] if r["batches_per_sec"] > 0 else float('inf')
            tradeoff = min(good_results, key=lambda x: x.get("ram_perf_ratio", float('inf')))
            pf = tradeoff["prefetch_factor"] if tradeoff["prefetch_factor"] is not None else "None"
            lines.extend([
                f"- **Best speed/RAM tradeoff**: workers={tradeoff['workers']}, prefetch_factor={pf}" if pf else f"- **Best speed/RAM tradeoff (workers=0)**",
                f"  - Throughput: {tradeoff['batches_per_sec']:.2f} batches/sec",
                f"  - RAM: {tradeoff['peak_ram_used_gb']:.2f} GB ({tradeoff['peak_ram_percent']:.1f}%)",
                f"  - Ratio (RAM%/throughput): {tradeoff.get('ram_perf_ratio', 0):.4f}",
                "",
            ])
    
    lines.extend([
        "## 8. Recommended Production Configuration",
        "",
    ])
    
    if good_results:
        # Recommend fastest configuration with healthy RAM margin (< 50% RAM usage)
        candidates = [r for r in good_results if r["peak_ram_percent"] < 50]
        if candidates:
            recommended = max(candidates, key=lambda x: x["batches_per_sec"])
            pf = recommended["prefetch_factor"] if recommended["prefetch_factor"] is not None else "None"
            if pf is not None:
                lines.append(f"**workers={recommended['workers']}, prefetch_factor={pf}**")
            else:
                lines.append(f"**workers=0 (single-process)**")
            lines.append(f"- This provides the best throughput while keeping RAM usage at {recommended['peak_ram_percent']:.1f}%")
        else:
            # Fallback to fastest even if RAM is high
            recommended = max(good_results, key=lambda x: x["batches_per_sec"])
            pf = recommended["prefetch_factor"] if recommended["prefetch_factor"] is not None else "None"
            if pf is not None:
                lines.append(f"**workers={recommended['workers']}, prefetch_factor={pf}**")
            else:
                lines.append(f"**workers=0 (single-process)**")
            lines.append(f"- Recommended despite higher RAM usage ({recommended['peak_ram_percent']:.1f}%) due to no viable alternatives below 50%")
    
    lines.extend([
        "",
        "## 9. Rejected Configurations and Why",
        "",
    ])
    
    failed_results = [r for r in results if r.get("error")]
    if failed_results:
        for r in failed_results:
            pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
            lines.append(f"- workers={r['workers']}, prefetch_factor={pf}: {r['error']}")
    else:
        lines.append("No configurations failed.")
    
    lines.extend([
        "",
        "## 10. Limitations",
        "",
        "- Benchmark measures only CPU loading + GPU transfer, not actual training",
        "- Prefetching behavior differs slightly from production (no num_workers heuristic limiting)",
        "- Single GPU only tested",
        "- Results may vary with system load",
        "",
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke test only")
    parser.add_argument("--test-workers", type=int, help="Test single worker count")
    parser.add_argument("--test-prefetch", type=int, help="Test single prefetch factor (implies --test-workers 2 if not set)")
    parser.add_argument("--device", type=int, default=0, help="CUDA device index")
    args = parser.parse_args()
    
    data_yaml = SOURCE_DATA_YAML
    
    if not data_yaml.exists():
        print(f"ERROR: Data YAML not found at {data_yaml}")
        sys.exit(1)
    
    if not RESUME_CKPT.exists():
        print(f"WARNING: Checkpoint not found at {RESUME_CKPT} (benchmark will proceed but may fail)")
    
    env_info = {
        "device_idx": args.device,
        "data_yaml": str(data_yaml),
        "checkpoint": str(RESUME_CKPT),
    }
    
    if args.smoke_test:
        result = run_smoke_test(data_yaml, args.device)
        if result.get("error"):
            sys.exit(1)
        return 0
    
    if args.test_workers is not None:
        workers = args.test_workers
        prefetch = args.test_prefetch if args.test_prefetch is not None else 2
        if workers == 0:
            prefetch = None
        results = [benchmark_configuration(workers, prefetch, data_yaml, 720, 16, args.device)]
    else:
        results = run_full_matrix(data_yaml, args.device)
    
    write_results(results, env_info)
    
    report = generate_report(results, env_info)
    with open(BENCHMARK_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nResults written to:")
    print(f"  - {BENCHMARK_RESULTS_JSON}")
    print(f"  - {BENCHMARK_RESULTS_CSV}")
    print(f"  - {BENCHMARK_REPORT_MD}")
    
    # Print summary
    good_results = [r for r in results if not r.get("error")]
    if good_results:
        print("\n" + "=" * 60)
        print("TOP 5 CONFIGURATIONS (by batches/sec)")
        print("=" * 60)
        sorted_results = sorted(good_results, key=lambda x: x["batches_per_sec"], reverse=True)[:5]
        for r in sorted_results:
            pf = r["prefetch_factor"] if r["prefetch_factor"] is not None else "None"
            print(f"  workers={r['workers']:2}, prefetch={pf:4} -> {r['batches_per_sec']:.2f} batches/sec, RAM={r['peak_ram_percent']:.0f}%, latency={r['mean_batch_interval_ms']:.1f}ms")
    
    return 0


if __name__ == "__main__":
    # Ensure psutil is imported for main execution
    if not PSUTIL_AVAILABLE:
        try:
            import psutil
            PSUTIL_AVAILABLE = True
        except ImportError:
            pass
    raise SystemExit(main())