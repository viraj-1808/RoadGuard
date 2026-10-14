#!/usr/bin/env python3
"""Read-only diagnostic script for Windows training environment resources.

This script inspects:
- Physical RAM, committed memory, commit limit, pagefile
- Python process RSS (main + recursive child processes)
- Disk free space and throughput
- GPU memory and utilization

NO model training, NO checkpoint modification, NO cache creation.
No model loading is performed.

Usage:
    python scripts/optimization/diagnose_training_resources.py [--json-path JSON_PATH]

A JSON report is written to a timestamped location if --json-path is provided.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def to_gb(value_bytes: float | None) -> float | str:
    """Convert bytes to GiB, or return 'unavailable' if None."""
    if value_bytes is None:
        return "unavailable"
    return round(value_bytes / (1024 ** 3), 3)


def to_mb(value_bytes: float | None) -> float | str:
    """Convert bytes to MiB, or return 'unavailable' if None."""
    if value_bytes is None:
        return "unavailable"
    return round(value_bytes / (1024 ** 2), 2)


def bounded_sample(interval_seconds: float, max_duration_seconds: float):
    """Sample repeatedly until max duration is exceeded."""
    start = time.perf_counter()
    while True:
        yield time.perf_counter() - start
        elapsed = time.perf_counter() - start
        if elapsed >= max_duration_seconds:
            break
        time.sleep(interval_seconds)


def collect_windows_memory():
    """Collect Windows physical and committed memory metrics."""
    result = {"note": "windows_memory"}

    if PSUTIL_AVAILABLE:
        vm = psutil.virtual_memory()
        result["physical_total_gb"] = to_gb(vm.total)
        result["physical_available_gb"] = to_gb(vm.available)
        result["physical_used_gb"] = to_gb(vm.used)
        result["physical_cached_gb"] = to_gb(vm.cached) if hasattr(vm, "cached") else "unavailable"
        result["physical_percent_used"] = vm.percent
        result["swap_total_gb"] = to_gb(psutil.swap_memory().total)
        result["swap_used_gb"] = to_gb(psutil.swap_memory().used)
    else:
        result["physical_total_gb"] = "unavailable (psutil not installed)"

    # Windows committed bytes and commit limit via Get-System-Information WMI
    try:
        import win32com.client

        wmi = win32com.client.GetObject("winmgmts:")
        for sys_info in wmi.ExecQuery("SELECT * FROM Win32_PerfRawData_PerfOS_Memory"):
            try:
                commit_total = sys_info.CommittedBytes
                committed_kb = sys_info.CommitLimit
                if commit_total is not None and committed_kb is not None:
                    result["committed_bytes"] = int(commit_total)
                    result["commit_limit_bytes"] = int(committed_kb)
                    break
            except (AttributeError, TypeError, ValueError):
                pass
        result["windows_committed_bytes"] = result.pop("committed_bytes", "unavailable")
        result["windows_commit_limit_bytes"] = result.pop("commit_limit_bytes", "unavailable")
    except Exception as e:
        result["windows_committed_bytes"] = f"unavailable: {type(e).__name__}"
        result["windows_commit_limit_bytes"] = f"unavailable: {type(e).__name__}"
        result["commit_limit_error"] = str(e)

    # Pagefile configuration via WMI Win32_PageFile
    result["pagefile"] = []
    try:
        import win32com.client

        wmi = win32com.client.GetObject("winmgmts:")
        for pf in wmi.ExecQuery("SELECT * FROM Win32_PageFileUsage"):
            result["pagefile"].append(
                {"name": pf.Name, "allocated_bytes": int(pf.AllocatedBaseSize) if pf.AllocatedBaseSize else None,
                 "usage_bytes": int(pf.CurrentUsage) if pf.CurrentUsage else None}
            )
    except Exception as e:
        result["pagefile"] = f"unavailable: {type(e).__name__}"
    return result


def collect_gpu_metrics():
    """Collect GPU metrics via torch.cuda if available, else nvidia-smi."""
    result = {"note": "gpu"}
    if torch.cuda.is_available():
        result["gpu_available"] = True
        result["gpu_device"] = torch.cuda.get_device_name(0)
        result["gpu_total_memory_gb"] = to_gb(torch.cuda.get_device_properties(0).total_memory)
        try:
            result["gpu_allocated_bytes"] = torch.cuda.memory_allocated()
            result["gpu_reserved_bytes"] = torch.cuda.memory_reserved()
        except Exception as e:
            result["gpu_allocated_bytes"] = f"unavailable: {type(e).__name__}: {e}"
            result["gpu_reserved_bytes"] = f"unavailable: {type(e).__name__}: {e}"
        result["gpu_allocated_gb"] = to_gb(torch.cuda.memory_allocated() if torch.cuda.is_available() else None)
        result["gpu_reserved_gb"] = to_gb(torch.cuda.memory_reserved() if torch.cuda.is_available() else None)
    else:
        result["gpu_available"] = False
        result["gpu_error"] = "No CUDA device"

    # GPU utilization via nvidia-smi
    try:
        output = subprocess.check_output(["nvidia-smi", "-q", "-d", "UTILIZATION"], text=True, timeout=15)
        result["gpu_utilization_percent"] = output
    except subprocess.CalledProcessError as e:
        result["gpu_utilization_percent"] = f"nvidia-smi exited with code {e.returncode}"
    except FileNotFoundError:
        result["gpu_utilization_percent"] = "unavailable: nvidia-smi not found"
    except subprocess.TimeoutExpired:
        result["gpu_utilization_percent"] = "unavailable: nvidia-smi timed out"
    except Exception as e:
        result["gpu_utilization_percent"] = f"unavailable: {type(e).__name__}: {e}"
    return result


def collect_disk_metrics():
    """Collect disk free space metrics."""
    result = {"note": "disk"}
    # Find the drive containing the dataset
    dataset_path = PROJECT_ROOT / "experiments/dataset"
    if dataset_path.exists():
        drive_root = Path(dataset_path.root)
        try:
            import shutil

            total, used, free = shutil.disk_usage(str(drive_root))
            result["drive"] = str(drive_root)
            result["disk_total_gb"] = to_gb(total)
            result["disk_used_gb"] = to_gb(used)
            result["disk_free_gb"] = to_gb(free)
            result["disk_used_percent"] = round(used / total * 100, 2)
        except OSError as e:
            result["disk"] = f"unavailable: {type(e).__name__}: {e}"
    return result


def collect_disk_throughput():
    """Collect disk throughput via performance counters (may require permissions)."""
    result = {"note": "disk_throughput"}
    try:
        output = subprocess.check_output(
            "wmic path Win32_LogicalDisk get Size,FreeSpace,DeviceID | more", text=True, timeout=15
        )
        result["wmic_disk_info"] = output
    except Exception as e:
        result["wmic_disk_info"] = f"unavailable: {type(e).__name__}: {e}"
    return result


def collect_process_memory():
    """Collect Python process memory (main + recursive children)."""
    result = {"note": "process_memory"}

    if not PSUTIL_AVAILABLE:
        result["main_rss_gb"] = "unavailable (psutil not installed)"
        result["children_rss_gb"] = "unavailable (psutil not installed)"
        return result

    try:
        process = psutil.Process()
        main_rss = process.memory_info().rss
        main_vms = process.memory_info().vms
        main_pagefile = None
        try:
            main_pagefile = process.memory_full_info().uss  # upper set size (peak private)
        except Exception:
            pass

        result["main_process_name"] = process.name()
        result["main_pid"] = process.pid
        result["main_rss_gb"] = to_gb(main_rss)
        result["main_vms_gb"] = to_gb(main_vms)

        children = []
        children_rss_total = 0
        try:
            for child in process.children(recursive=True):
                try:
                    rss = child.memory_info().rss
                    children.append({"pid": child.pid, "name": child.name(), "rss_gb": to_gb(rss)})
                    children_rss_total += rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        result["child_processes"] = children
        result["children_rss_total_gb"] = to_gb(children_rss_total)
        result["combined_rss_gb"] = to_gb(main_rss + children_rss_total)
    except Exception as e:
        result["main_process_name"] = f"error: {type(e).__name__}"
        result["main_pid"] = None
        result["main_rss_gb"] = f"unavailable: {e}"
        result["children_rss_total_gb"] = f"unavailable: {e}"
        result["combined_rss_gb"] = f"unavailable: {e}"
    return result


def collect_gpu_utilization():
    """Get GPU utilization percentage via nvidia-smi."""
    result = {"note": "gpu_utilization_percent"}
    try:
        output = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], text=True, timeout=15)
        result["gpu_utilization_percent"] = float(output.strip()) if output.strip().isdigit() else output.strip()
    except Exception as e:
        result["gpu_utilization_percent"] = f"unavailable: {type(e).__name__}: {e}"
    return result


def collect_environment():
    """Collect environment information."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "ultralytics_version": __import__("ultralytics").__version__,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "checkpoint_sha256": None,
        "checkpoint_path": str(PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt"),
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only diagnostic of training environment resources")
    parser.add_argument("--interval", type=float, default=0.5, help="Sampling interval in seconds")
    parser.add_argument("--duration", type=float, default=5.0, help="Maximum sampling duration in seconds")
    parser.add_argument("--json-path", type=str, default=None, help="Path to write JSON report (timestamped filename if omitted)")
    args = parser.parse_args()

    print("=" * 70)
    print("RoadGuard Training Environment Diagnostic (READ-ONLY)")
    print("=" * 70)
    print()

    env = collect_environment()
    env["checkpoint_sha256"] = None  # intentionally not loaded during diagnostic
    print(f"[ENV] Python: {env['python_version']} | Platform: {env['platform']}")
    print(f"[ENV] CPU cores: {env['cpu_count']} | Ultralytics: {env['ultralytics_version']}")
    print(f"[ENV] PyTorch: {env['torch_version']} | CUDA: {env['cuda_version']} | CUDA available: {env['cuda_available']}")
    print()

    # Collect metrics with bounded sampling
    samples = []
    start_walltime = time.time()
    for _ in bounded_sample(args.interval, args.duration):
        sample = {}
        # Memory
        memory = collect_windows_memory()
        sample["physical_memory"] = memory
        # GPU
        gpu = collect_gpu_metrics()
        sample["gpu"] = gpu
        # Process memory
        pm = collect_process_memory()
        sample["process_memory"] = pm
        # Disk
        dm = collect_disk_metrics()
        sample["disk"] = dm
        # Disk throughput
        dt = collect_disk_throughput()
        sample["disk_throughput"] = dt
        # GPU utilization
        gu = collect_gpu_utilization()
        sample["gpu_utilization_percent"] = gu
        samples.append(sample)
        time.sleep(args.interval)

    total_walltime = time.time() - start_walltime
    print(f"[INFO] Sampled for {total_walltime:.1f} seconds ({len(samples)} samples)")
    print()

    # Print latest sample human-readable
    latest = samples[-1] if samples else {}
    pm = latest.get("process_memory", {})
    mem = latest.get("physical_memory", {})
    gpu = latest.get("gpu", {})
    disk = latest.get("disk", {})

    print("=" * 70)
    print("SUMMARY (latest sample)")
    print("=" * 70)
    print(f"[RAM] Total: {mem.get('physical_total_gb', 'N/A')} GiB | Available: {mem.get('physical_available_gb', 'N/A')} GiB | "
          f"Used: {mem.get('physical_used_gb', 'N/A')} GiB | Cached: {mem.get('physical_cached_gb', 'N/A')} GiB")
    print(f"[RAM] Utilization: {mem.get('physical_percent_used', 'N/A')}% | Swap total: {mem.get('swap_total_gb', 'N/A')} GiB | Swap used: {mem.get('swap_used_gb', 'N/A')} GiB")
    print(f"[COMMIT] Committed bytes: {mem.get('windows_committed_bytes', 'N/A')} | Commit limit: {mem.get('windows_commit_limit_bytes', 'N/A')}")
    print(f"[PAGES] Pagefile: {mem.get('pagefile', 'N/A')}")
    print(f"[PROC] Main process: {pm.get('main_process_name', 'N/A')} (PID {pm.get('main_pid', 'N/A')}) RSS {pm.get('main_rss_gb', 'N/A')} GiB | "
          f"Children RSS {pm.get('children_rss_total_gb', 'N/A')} GiB | Combined {pm.get('combined_rss_gb', 'N/A')} GiB")
    print(f"[GPU] Device: {gpu.get('gpu_device', 'N/A')} | Total: {gpu.get('gpu_total_memory_gb', 'N/A')} GiB | "
          f"Allocated: {gpu.get('gpu_allocated_gb', 'N/A')} GiB | Reserved: {gpu.get('gpu_reserved_gb', 'N/A')} GiB")
    print(f"[GPU] Utilization: {latest.get('gpu_utilization_percent', {}).get('gpu_utilization_percent', 'N/A')}")
    print(f"[DISK] Drive {disk.get('drive', 'N/A')}: Total {disk.get('disk_total_gb', 'N/A')} GiB | Used {disk.get('disk_used_gb', 'N/A')} GiB | "
          f"Free {disk.get('disk_free_gb', 'N/A')} GiB ({disk.get('disk_used_percent', 'N/A')}%)")
    print()

    # Write JSON report
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "parameters": {"interval_seconds": args.interval, "duration_seconds": args.duration},
        "environment": env,
        "samples": samples,
    }

    json_path = Path(args.json_path) if args.json_path else None
    if json_path:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"[INFO] JSON report written to: {json_path}")
    else:
        timestamped = PROJECT_ROOT / "cache" / f"diagnose_training_resources_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with timestamped.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"[INFO] JSON report written (default timestamped location): {timestamped}")

    print()
    print("[INFO] Diagnostic complete. No training, caching, or model loading performed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
