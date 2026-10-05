# Preflight Training Report

**Generated:** 2026-09-28

## 1. Ultralytics version
- **8.4.138** (installed and importable)

## 2. Python environment
- **Python 3.12.10** (via `python --version`)
- Running on Windows 11 (AMD64)

## 3. GPU availability
- **GPU present:** NVIDIA GeForce RTX 4050 Laptop GPU (as reported by `nvidia-smi`).
- **PyTorch CUDA status:** **CPU‑only** – `torch.cuda.is_available()` returns `false`.  
  The installed PyTorch build (`2.14.0+cpu`) does not include CUDA support, so the GPU cannot be used for training despite the hardware being present.

## 4. Available VRAM
From `training_environment_report.json`:
- Total VRAM: **6.0 GB**
- Free VRAM: **5.7 GB**
- Used VRAM: **99 MB**
- VRAM sufficient for YOLO11s: **yes** (estimated ~325 MB FP16, headroom ~5139 MB)

## 5. Dataset paths (`yolo_rdd2022_india`)
- **Path:** `experiments/dataset/yolo_rdd2022_india`
- Structure:
  - `images/train` (1071 images)
  - `images/val` (229 images)
  - `images/test` (230 images)
  - `labels/train`, `labels/val`, `labels/test` (corresponding YOLO labels)
- `data.yaml` resides in the dataset root.

## 6. `data.yaml` existence & correctness
```
path: experiments/dataset/yolo_rdd2022_india
train: images/train
val: images/val
test: images/test
nc: 4
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
```
- File **exists** and contains the expected fields.
- Class count `nc=4` matches the four crack/pothole categories.

## 7. Class count (`nc=4`)
- Confirmed: `nc: 4` in `data.yaml`.

## 8. Image dimensions
- Sample images measured with Pillow: **720 × 720** pixels (e.g., `India_000017.jpg`).
- The data.yaml does not specify a fixed `img_size`, but all images in the dataset are 720×720.

## 9. Model availability (`YOLO11s` pretrained checkpoint)
- Ultralytics reports `download_status: successful` and `inference_status: tested_on_cpu`.
- Model size: **9.46 M parameters**, ~37.8 MB FP32.
- The YOLO11s model is available in the Ultralytics model hub and will be auto‑downloaded on first run.
- **Note:** Because PyTorch is CPU‑only, inference will run on the CPU (slower than GPU but functional).

## 10. Disk space
From `training_environment_report.json` (drive `C:`):
- Total: **510.92 GB**
- Used: **304.87 GB**
- Free: **206.06 GB** – **more than enough** for training logs, checkpoints, and the dataset.

## Expected output directory
- Convention: `experiments/training/yol11s_dataset_v2_split_v2_20260928` (or a timestamp‑based variant).
- This directory does **not** exist yet; it will be created by the Ultralytics `train` command.

---

## Baseline Configuration
- **Model:** `yolo11s` pretrained (downloaded from Ultralytics hub)
- **Dataset:** Converted RDD2022 India subset (`experiments/dataset/yolo_rdd2022_india`)
- **Task:** Object detection (4 classes: longitudinal_crack, transverse_crack, alligator_crack, pothole)
- **Image size:** 720×720
- **Epochs / batch size:** To be decided (default 100, batch=16)

## Issues / Warnings
1. **CRITICAL – PyTorch CPU‑only installation**  
   The system has an NVIDIA RTX 4050 GPU but PyTorch was installed without CUDA support. Training will be significantly slower on CPU.  
   **Recommendation:** Re‑install a CUDA‑enabled PyTorch build, e.g.:  
   ```
   pip install torch==2.14.0+cu121 torchvision==0.29.0+cu121 --index-url https://download.pytorch.org/whl/cu121
   ```

2. **POTENTIAL – CUDA version mismatch**  
   The driver reports CUDA 13.1, but no CUDA‑enabled PyTorch is currently installed to verify compatibility. After reinstalling PyTorch with CUDA, run `torch.cuda.is_available()` to confirm.

3. **VRAM headroom is ample** – no memory‑related blockers once CUDA PyTorch is in place.

## Recommended Training Command (do NOT run)
```bash
cd C:\Users\viraj\Code_files\Github\RoadGuard AI

# If CUDA PyTorch is installed, you can enable GPU training:
python -m ultralytics train \
    data=experiments/dataset/yolo_rdd2022_india/data.yaml \
    model=yolo11s.pt \
    epochs=100 \
    imgsz=720 \
    batch=16 \
    name=yol11s_dataset_v2_split_v2 \
    project=experiments/training
```

If only CPU PyTorch is available, omit any GPU‑specific flags; the command will still run on the CPU.

---
*End of preflight report.*