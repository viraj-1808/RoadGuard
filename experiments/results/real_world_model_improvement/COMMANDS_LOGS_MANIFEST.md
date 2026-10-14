# Commands & Logs Manifest
# Experiment: EXP-RWMI-001
# Generated: 2026-10-11T07:38:51Z

## Fine-Tuning Training Commands

### Initial Training Run (Crashed)
```bash
cd C:\Users\viraj\Code_files\Github\RoadGuard AI
yolo train model=runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt \
    data=experiments/dataset/yol11s_realworld_finetune/data.yaml \
    epochs=10 batch=16 imgsz=720 device=0 workers=2 \
    project=experiments/training name=yol11s_realworld_finetune \
    exist_ok=True save_period=1 seed=42 deterministic=True \
    amp=True cache=False lr0=0.001 lrf=0.01 \
    box=7.5 cls=0.5 dfl=1.5 close_mosaic=10 \
    hsv_h=0.015 hsv_s=0.7 hsv_v=0.4 \
    translate=0.1 scale=0.5 fliplr=0.5 mosaic=1.0 \
    val=True plots=True verbose=True
```
**Log**: `training.log` (lines 1-28)
**Result**: Completed epochs 0-2, crashed at epoch 3 (RAM 88.7% → 86.3%)

### Resume Attempt 1
```bash
yolo train resume=True model=runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt
```
**Log**: `training.log` (lines 29-33)
**Result**: Immediate crash - same RAM issue

### Resume Attempt 2
```bash
yolo train resume=True model=runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt
```
**Log**: `training.log` (lines 34-41)
**Result**: Immediate crash - same RAM issue

## Evaluation Commands

### Smoke Test (EXP-SMOKE-001)
```bash
python scripts/smoke_test_phase3.py \
    --model runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt \
    --input validation/manual/input \
    --images road001.webp road002.jpg road009.jpg road010.jpg \
    --conf-thresholds 0.05 0.1 0.15 0.2 0.25 0.3 \
    --iou-threshold 0.5 \
    --output experiments/results/real_world_model_improvement/smoke_test_results.json
```
**Output**: `smoke_test_results.json`, `smoke_test_report.md`
**Result**: 3/4 matched at conf=0.05 (TARGET ACHIEVED)

### Holdout Evaluation
```bash
python scripts/holdout_evaluation.py \
    --original-model runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt \
    --finetuned-model runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt \
    --holdout-images experiments/results/real_world_model_improvement/annotations/data_split.json \
    --ground-truth experiments/results/real_world_model_improvement/annotations/ground_truth_annotations.json \
    --conf-thresholds 0.05 0.1 0.15 0.2 0.25 0.3 \
    --iou-threshold 0.5 \
    --output experiments/results/real_world_model_improvement/holdout_evaluation_detailed.json
```
**Output**: `holdout_evaluation_detailed.json`, `HOLDOUT_EVALUATION.md`
**Result**: 0/5 CLEAR correct, 7/14 total accuracy (50%), identical for both models

### Batch Inference (Annotated Outputs)
```bash
python -c "
from ultralytics import YOLO
import os
model = YOLO(r'runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt')
input_dir = r'validation/manual/input'
output_dir = r'experiments/results/real_world_model_improvement/annotated_outputs'
images = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
for img in images:
    model.predict(os.path.join(input_dir, img), imgsz=720, conf=0.05, iou=0.5, device=0,
                  save=True, project=output_dir, name='epoch72_predictions', exist_ok=True)
"
```
**Output**: `annotated_outputs/epoch72_predictions/` (39 annotated images)
**Result**: All 39 images processed successfully

## Checkpoint Verification Commands

### SHA-256 Hashes
```powershell
certutil -hashfile "C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt" SHA256
certutil -hashfile "C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_realworld_finetune\weights\last.pt" SHA256
certutil -hashfile "C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_realworld_finetune\weights\best.pt" SHA256
```

### File Sizes
```powershell
Get-ChildItem "C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt" | Select-Object Name, Length
Get-ChildItem "C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_realworld_finetune\weights\*.pt" | Select-Object Name, Length
```

## Training Configuration Files

- `training_config.yaml` - Fine-tuning hyperparameters
- `experiments/dataset/yol11s_realworld_finetune/data.yaml` - Dataset config (train/val paths, classes)
- `experiments/dataset/yol11s_realworld_finetune_val.yaml` - Validation-only config

## Key Logs

| File | Description | Lines |
|------|-------------|-------|
| `training.log` | Fine-tuning training log (3 epochs + 2 resume attempts) | 41 |
| `smoke_test_results.json` | Detailed smoke test per-image, per-threshold results | 794 |
| `holdout_evaluation_detailed.json` | Full holdout evaluation with per-image details | 7970 |
| `HOLDOUT_EVALUATION.md` | Human-readable holdout report | 175 |
| `smoke_test_report.md` | Human-readable smoke test report | 84 |

## Inference Configuration (Best Operating Point)

```python
model = YOLO("runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt")
results = model.predict(
    source="image.jpg",
    imgsz=720,           # Note: YOLO auto-adjusts to 736 (multiple of stride 32)
    conf=0.05,           # Best threshold for pothole recall
    iou=0.5,             # NMS IoU threshold
    device=0,            # GPU 0
    save=True,           # Save annotated image
    save_txt=True,       # Save YOLO-format labels
    save_conf=True       # Save confidence scores
)
```

## Environment

- **OS**: Windows 10/11
- **Python**: 3.10+
- **PyTorch**: 2.x with CUDA
- **Ultralytics**: 8.x
- **GPU**: NVIDIA (device 0, ~5.4GB VRAM reserved)
- **RAM**: 16-32GB system (bottleneck at 88%+ during training)

## Reproduction Checklist

- [ ] Clone repository
- [ ] Install requirements: `pip install ultralytics`
- [ ] Verify checkpoint hashes match `CHECKPOINT_HASHES.txt`
- [ ] Run smoke test: `python scripts/smoke_test_phase3.py ...`
- [ ] Run holdout evaluation: `python scripts/holdout_evaluation.py ...`
- [ ] Run batch inference on 39 images
- [ ] Verify annotated outputs in `annotated_outputs/epoch72_predictions/`
- [ ] Compare metrics with `MODEL_COMPARISON.csv` and `THRESHOLD_COMPARISON.csv`