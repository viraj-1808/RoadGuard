# Training Environment Audit Report

**Generated:** 2026-09-29
**Audit Type:** READ-ONLY (no modifications made)

---

## 1. Python Version
- **Version:** Python 3.12.10
- **Status:** ✅ Available and functional

---

## 2. PyTorch Version and CUDA Support
- **PyTorch Version:** 2.14.0+cu126
- **CUDA Available:** ✅ True
- **CUDA Version (PyTorch):** 12.6
- **Status:** ✅ CUDA-enabled PyTorch installed and GPU accessible

---

## 3. NVIDIA GPU Model and VRAM
- **GPU Model:** NVIDIA GeForce RTX 4050 Laptop GPU
- **GPU Count:** 1
- **Total VRAM:** 5.997 GB (6.0 GB advertised)
- **Free VRAM (at idle):** 4.95 GB
- **VRAM Status:** ⚠️ **Borderline** – Total VRAM is ~6 GB, which meets the minimum 6 GB threshold but leaves limited headroom

---

## 4. NVIDIA Driver Version
- **Driver Version:** 592.82
- **Status:** ✅ Current and compatible with CUDA 12.6

---

## 5. Ultralytics Version
- **Version:** 8.4.138
- **Status:** ✅ Installed and importable

---

## 6. Available Disk Space
- **Drive:** C:
- **Free Space:** 152.43 GB
- **Status:** ✅ Ample space for training logs, checkpoints, and datasets

---

## 7. Current Training Launcher Scripts

### 7.1 Primary Training Script: `run_baseline.py`
**Path:** `experiments/training/run_baseline.py`
**Configuration:**
- Model: `yolo11s.pt` (pretrained, auto-downloaded from Ultralytics hub)
- Dataset: `experiments/dataset/yolo_rdd2022_india/data.yaml`
- Task: Object detection (4 classes: longitudinal_crack, transverse_crack, alligator_crack, pothole)
- Image size: 720
- Batch size: 16 (marked as "safe for RTX 4050, ~5.5GB peak")
- Epochs: 100 (with early stopping, patience=50)
- Seed: 42
- Device: 0 (GPU)
- Workers: 0 (minimal)
- Optimizer: auto
- AMP: True (mixed precision)
- Project: `experiments/training`
- Name: `yol11s_dataset_v2_split_v2`
- Deterministic: True

### 7.2 Configuration File: `baseline_config.yaml`
**Path:** `experiments/training/baseline_config.yaml`
- Full Ultralytics training configuration matching run_baseline.py
- Includes all hyperparameters (lr0=0.01, momentum=0.937, weight_decay=0.0005, etc.)

### 7.3 Execution Wrappers:
- `run_baseline.bat` – Windows batch file
- `run_baseline.ps1` – PowerShell script

### 7.4 Missing Scripts (referenced but not found):
- `yol11s_launcher.py` – **NOT FOUND**
- `benchmark_batch_size.py` – **NOT FOUND**

### 7.5 Reproducibility Script:
- `compute_reproducibility.py` – Collects environment metadata for reproducible runs
- Output: `reproducibility_record.json`

### 7.6 Existing Training Artifacts:
- `baseline_run.log` – Previous training run log
- `smoke_test_output.log` – Smoke test log
- `preflight_report.md` – Preflight check report (dated 2026-09-28)
- `reproducibility_record.json` / `.md` – Reproducibility records

---

## 8. GPU Training Safety Assessment

### VRAM Analysis:
| Metric | Value |
|--------|-------|
| Total VRAM | 5.997 GB |
| Free VRAM (idle) | 4.95 GB |
| Minimum Recommended for YOLO11s | ~6 GB |
| Estimated Peak Usage (batch=16, imgsz=720) | ~5.5 GB |

### Verdict: **⚠️ MARGINALLY SAFE – Proceed with Caution**

**Reasoning:**
1. Total VRAM (5.997 GB) is technically at the 6 GB minimum threshold
2. Estimated peak usage (~5.5 GB) leaves only ~0.5 GB headroom
3. Free VRAM at idle (4.95 GB) suggests other processes may be using GPU memory
4. The training script itself notes batch=16 is "safe for RTX 4050, ~5.5GB peak"

**Recommendations:**
- Use batch size 16 as baseline (validated in config)
- Monitor VRAM during first epoch; reduce batch size to 8 if OOM occurs
- Enable AMP (mixed precision) – already enabled in config
- Consider gradient accumulation if batch reduction needed
- Close unnecessary GPU applications before training

---

## 9. Dataset Configuration

**Dataset Path:** `experiments/dataset/yolo_rdd2022_india`
- **Train:** 1071 images
- **Val:** 229 images
- **Test:** 230 images
- **Classes:** 4 (longitudinal_crack, transverse_crack, alligator_crack, pothole)
- **Image Dimensions:** 720×720 (uniform)

**data.yaml Checksum (SHA256):** `67880aae1e0dd25ec8ebb2edbb397bc4a48229fcb83fe78eae22ff213b59947d`

---

## 10. Reproducibility Metadata

| Parameter | Value |
|-----------|-------|
| Git Commit | `312d4f4dcbc41254c2f644d355a3627b60e20990` |
| Python Version | 3.12.10 |
| PyTorch Version | 2.14.0+cu126 |
| CUDA Version | 12.6 |
| NVIDIA Driver | 592.82 |
| GPU Model | RTX 4050 Laptop GPU |
| Ultralytics Version | 8.4.138 |
| Model Checkpoint | yolo11s.pt |
| Image Size | 720 |
| Batch Size | 16 |
| Seed | 42 |
| Epochs | 100 |

---

## 11. Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Python | ✅ | 3.12.10 |
| PyTorch + CUDA | ✅ | 2.14.0+cu126, CUDA 12.6 |
| GPU Hardware | ✅ | RTX 4050 Laptop GPU |
| GPU VRAM | ⚠️ | 5.997 GB (marginal) |
| Driver | ✅ | 592.82 |
| Ultralytics | ✅ | 8.4.138 |
| Disk Space | ✅ | 152 GB free |
| Training Scripts | ✅ | run_baseline.py + config |
| Dataset | ✅ | Validated, 4 classes, 720×720 |

**Overall Readiness:** **READY WITH CAUTION** – Environment is functional for GPU training, but VRAM headroom is minimal. Monitor closely during initial epochs and be prepared to reduce batch size.

---

*End of Training Environment Audit*