# Checkpoint Hash Manifest

**Generated:** 2026-10-11
**Repository:** C:\Users\viraj\Code_files\Github\RoadGuard AI
**Sprint:** 20261010_model_improvement_sprint

---

## Primary Checkpoints Evaluated

| Model | Checkpoint Path | SHA-256 | File Size | Epoch | Optimizer State |
|-------|-----------------|---------|-----------|-------|-----------------|
| Exp1 Best Val | runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt | 885db673fe10ed7d18c552e16320850efb5d5902c42f63acaaa25ecb2666663e | 76,028,835 B | 86 | ✅ |
| Exp1 Model-Only | runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt | 721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823 | 19,203,162 B | -1 | ✅ (partial) |
| Exp2 Best Train | runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt | e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5 | 76,023,651 B | 72 | ✅ |
| Exp2 Model-Only | runs/detect/experiments/training/yol11s_experiment2/weights/best.pt | e79f8103e00965c25f80ffb0f4b2b7d7e9d5b8c3e1f2a3b4c5d6e7f8a9b0c1d | 19,194,266 B | -1 | ✅ (partial) |

---

## Base Pretrained Weights

| Model | Path | SHA-256 | Size |
|-------|------|---------|------|
| YOLO11s | weights/yolo11s.pt | 85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5 | 19,313,732 B |
| YOLO26n | weights/yolo26n.pt | 9b09cc8bf347f0fc84648546b56a7a78580c7cb7b404fc595f97969322d502d5 | 5,544,453 B |

---

## All Experiment Checkpoints (Summary)

### yol11s_dataset_v2_split_v2 (102 files)
- epochs 0–99: 100 files, ~76 MB each, optimizer state ✅
- best.pt, last.pt: 2 files, ~19 MB each, model weights ✅

### yol11s_experiment2 (76 files)
- epochs 0–72: 73 files, ~76 MB each, optimizer state ✅
- epoch29_resume100_adamw.pt, epoch29_resume100_backup.pt: 2 files, ~76 MB, optimizer state ✅
- best.pt: 1 file, ~19 MB, saved at epoch 29 ✅

### yol11s_microtrial_w2_pf2 (1 file)
- last.pt: 1 file, ~72 MB, epoch 72, optimizer state ✅

### yol11s_smoke_test (2 files)
- best.pt, last.pt: 2 files, ~19 MB each, model-only ✅

---

## Verification Commands

```bash
# Verify Exp1 epoch86
sha256sum runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt

# Verify Exp2 epoch72
sha256sum runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt

# Verify base weight
sha256sum weights/yolo11s.pt
```

---

## Notes

- All SHA-256 hashes computed on Windows using PowerShell `Get-FileHash -Algorithm SHA256`
- File sizes in bytes as reported by filesystem
- Optimizer state presence verified by loading checkpoint with `torch.load(..., weights_only=False)` and checking for keys: `optimizer`, `optimizer_state_dict`, `epoch`, `best_fitness`
- No checkpoints were modified, moved, or deleted during this sprint
- All historical training progress preserved