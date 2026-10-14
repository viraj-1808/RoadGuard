# System Resources Audit Report

**Generated:** 2026-10-11 09:33:51 UTC
**Repository:** C:\Users\viraj\Code_files\Github\RoadGuard AI

---

## 1. Disk Space (C: drive)
- **Total:** 475.84 GB
- **Free:** 107.72 GB (22.6%)
- **Used:** 368.12 GB

---

## 2. Memory (RAM)
- **Total:** 15.65 GB (16,409,092 KB)
- **Available:** 4.75 GB (4,979,136 KB)
- **Used:** 10.90 GB
- **Utilization:** 73.1%
- **Swap/Pagefile Total:** 47.99 GB
- **Swap/Pagefile Used:** 0.53 GB
- **Committed Bytes:** 18.98 GB
- **Commit Limit:** 68.33 GB

---

## 3. GPU
- **CUDA Visible:** Yes (CUDA 12.6)
- **GPU Name:** NVIDIA GeForce RTX 4050 Laptop GPU
- **Total VRAM:** 5.997 GiB (6,141 MB)
- **Used VRAM:** 0.0 GiB (95 MB allocated by system)
- **Reserved VRAM:** 0.0 GiB
- **Driver Version:** 592.82
- **GPU Utilization:** 33%

---

## 4. Running Training/Inference Processes
No Python/PyTorch/YOLO training or inference processes currently running.

```
INFO: No tasks are running which match the specified criteria.
```

---

## 5. Environment
- **Current Working Directory:** C:\Users\viraj\Code_files\Github\RoadGuard AI
- **Python Version:** 3.12.10
- **Platform:** Windows-11-10.0.26300-SP0
- **CPU Cores:** 12
- **PyTorch:** 2.14.0+cu126
- **Ultralytics:** 8.4.138

---

## 6. Diagnose Training Resources Script Output
The script `scripts/optimization/diagnose_training_resources.py` exists and was executed successfully.

```
======================================================================
RoadGuard Training Environment Diagnostic (READ-ONLY)
======================================================================

[ENV] Python: 3.12.10 | Platform: Windows-11-10.0.26300-SP0
[ENV] CPU cores: 12 | Ultralytics: 8.4.138
[ENV] PyTorch: 2.14.0+cu126 | CUDA: 12.6 | CUDA available: True

[INFO] Sampled for 7.9 seconds (1 samples)

======================================================================
SUMMARY (latest sample)
======================================================================
[RAM] Total: 15.649 GiB | Available: 4.207 GiB | Used: 11.442 GiB | Cached: unavailable GiB
[RAM] Utilization: 73.1% | Swap total: 47.992 GiB | Swap used: 0.526 GiB
[COMMIT] Committed bytes: 18984079360 | Commit limit: 68333981696
[PAGES] Pagefile: [{'name': 'C:\\pagefile.sys', 'allocated_bytes': 49143, 'usage_bytes': 537}]
[PROC] Main process: python.exe (PID 15960) RSS 0.519 GiB | Children RSS 0.0 GiB | Combined 0.519 GiB
[GPU] Device: NVIDIA GeForce RTX 4050 Laptop GPU | Total: 5.997 GiB | Allocated: 0.0 GiB | Reserved: 0.0 GiB
[GPU] Utilization: 33.0
[DISK] Drive \: Total 475.836 GiB | Used 368.119 GiB | Free 107.717 GiB (77.36%)

[INFO] JSON report written (default timestamped location): C:\Users\viraj\Code_files\Github\RoadGuard AI\cache\diagnose_training_resources_20261011_093351.json

[INFO] Diagnostic complete. No training, caching, or model loading performed.
```

---

## Summary
- **Disk:** Adequate free space (107 GB) for training artifacts
- **RAM:** Moderate pressure (73% used), 4.2 GB available for training
- **GPU:** RTX 4050 Laptop with 6 GB VRAM, CUDA 12.6 ready, no active training load
- **Environment:** Fully configured for PyTorch/YOLO training