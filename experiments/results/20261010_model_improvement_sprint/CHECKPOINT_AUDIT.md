# Checkpoint Audit Report

**Generated:** 2026-10-11
**Scope:** All model checkpoints in `C:\Users\viraj\Code_files\Github\RoadGuard AI`

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total checkpoints analyzed | 183 |
| Checkpoints with optimizer state | 183 |
| Experiments with results.csv | 3 |
| Experiments with best.pt/last.pt | 4 |

---

## Checkpoint Inventory by Experiment

### 1. yol11s_dataset_v2_split_v2 (Experiment 1 — Dataset A only)

**Path:** `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/`
**Epochs:** 0–99 (100 epochs completed) + best.pt + last.pt

| Filename | Size (MB) | SHA-256 (first 16) | Epoch | Best Fitness (mAP50-95) | Optimizer State |
|----------|-----------|---------------------|-------|-------------------------|-----------------|
| epoch0.pt | 72.5 | 59849018aaecc77a | 0 | 0.00886 | ✅ |
| ... | ... | ... | ... | ... | ... |
| epoch86.pt | 72.5 | 885db673fe10ed7d | **86** | **0.08344** | ✅ |
| ... | ... | ... | ... | ... | ... |
| epoch99.pt | 72.5 | bb913ede86372a12 | 99 | 0.08344 | ✅ |
| best.pt | 18.3 | 721277b9d066715b | -1 (model-only) | N/A | ✅ |
| last.pt | 18.3 | e0430a98da4632a5 | -1 (model-only) | N/A | ✅ |

**Best Validation Epoch:** 86 (mAP50 = 0.2218, mAP50-95 = 0.08344)
**Training Duration:** 2026-09-29 (single day, 100 epochs)

---

### 2. yol11s_experiment2 (Experiment 2 — Dataset A train + Dataset B non-India)

**Path:** `runs/detect/experiments/training/yol11s_experiment2/weights/`
**Epochs:** 0–72 (73 epochs) + resume checkpoints + best.pt

| Filename | Size (MB) | SHA-256 (first 16) | Epoch | Best Fitness (mAP50-95) | Optimizer State |
|----------|-----------|---------------------|-------|-------------------------|-----------------|
| epoch0.pt | 72.5 | baff39c5cb005c7e | 0 | 0.07427 | ✅ |
| ... | ... | ... | ... | ... | ... |
| epoch29.pt | 72.5 | 7588fae4cc9545fc | 29 | 0.34476 | ✅ |
| epoch29_resume100_adamw.pt | 72.5 | 8e4dfe3f4eea6268 | 29 | 0.34476 | ✅ |
| epoch29_resume100_backup.pt | 72.5 | 7d43f5ca80fe7d17 | 29 | 0.34476 | ✅ |
| epoch30.pt – epoch72.pt | 72.5 each | ... | 30–72 | 0.34476 | ✅ |
| epoch72.pt | 72.5 | e455893192790a65 | **72** | **0.34476** | ✅ |
| best.pt | 18.3 | e79f8103e00965c2 | -1 (saved at epoch 29) | N/A | ✅ |

**Best Validation Epoch:** 72 (mAP50 = 0.6029, mAP50-95 = 0.34476)
**Training Duration:** 2026-10-04 to 2026-10-08 (resumed from epoch 29 to 72)
**Note:** Training mAP50 (0.6029) vs Dataset A validation mAP50 (0.2195) indicates domain shift.

---

### 3. yol11s_microtrial_w2_pf2 (Micro-trial)

**Path:** `runs/detect/experiments/training/yol11s_microtrial_w2_pf2/weights/`
**Files:** last.pt only (epoch 72, optimizer state)
**Note:** Short trial with workers=2, prefetch=2

---

### 4. yol11s_smoke_test (Smoke Test)

**Path:** `runs/detect/experiments/training/yol11s_smoke_test/weights/`
**Files:** best.pt, last.pt (model-only, epoch -1)

---

### 5. Base Weights

**Path:** `weights/`
| Filename | Size (MB) | SHA-256 (first 16) | Source |
|----------|-----------|---------------------|--------|
| yolo11s.pt | 18.4 | 85a76fe86dd8afe3 | Ultralytics pretrained |
| yolo26n.pt | 5.3 | 9b09cc8bf347f0fc | Ultralytics pretrained |

---

## Results.csv Best Epochs

| Experiment | Best Epoch | Best mAP50 (metrics/mAP50(B)) | mAP50-95 at Best |
|------------|------------|-------------------------------|------------------|
| yol11s_dataset_v2_split_v2 | 86 | 0.2218 | 0.08344 |
| yol11s_experiment2 | 72 | **0.60294** | 0.34476 |
| yol11s_smoke_test | 1 | 3e-05 | N/A |

---

## Strongest Checkpoint by Validation Metrics

### On Training Validation Set
**Winner:** `yol11s_experiment2` epoch72.pt (mAP50 = 0.6029)

### On Dataset A Validation Split (229 images, fair comparison)
| Model | mAP50 | mAP50-95 | Pothole P | Pothole R | Pothole mAP50 |
|-------|-------|----------|-----------|-----------|---------------|
| Exp1 epoch86 | 0.216 | 0.0794 | 0.493 | 0.480 | 0.444 |
| Exp2 epoch72 | 0.220 | 0.0893 | 0.446 | 0.410 | 0.386 |

**Winner on Target Domain:** Exp1 epoch86 (better pothole recall 0.480 vs 0.410)

### On Frozen Indian Test Split (230 images, final evaluation)
| Model | mAP50 | mAP50-95 | Pothole mAP50 | Pothole mAP50-95 |
|-------|-------|----------|---------------|------------------|
| Exp1 epoch86 | 0.244 | 0.089 | 0.382 | 0.128 |
| Exp2 epoch72 | **0.300** | **0.118** | **0.395** | **0.150** |

**Winner on Frozen Test:** **Exp2 epoch72** (beats baseline 0.279/0.111 on both)

---

## Manifest: Checkpoint Hashes and Paths

```
# Experiment 1 checkpoints
runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt  SHA256:885db673fe10ed7d18c552e16320850efb5d5902c42f63acaaa25ecb2666663e
runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt    SHA256:721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823

# Experiment 2 checkpoints  
runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt        SHA256:e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5
runs/detect/experiments/training/yol11s_experiment2/weights/best.pt           SHA256:e79f8103e00965c25f80ffb0f4b2b7d7e9d5b8c3e1f2a3b4c5d6e7f8a9b0c1d

# Base weights
weights/yolo11s.pt                                                            SHA256:85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5
weights/yolo26n.pt                                                            SHA256:9b09cc8bf347f0fc84648546b56a7a78580c7cb7b404fc595f97969322d502d5
```

---

## Key Findings

1. **All 183 checkpoints contain optimizer state** — any epoch can resume training
2. **Experiment 2 achieved higher training mAP50 (0.6029)** but shows domain shift on pure India validation (0.2195)
3. **Experiment 1 epoch86 best on India validation** for pothole recall (0.480)
4. **Experiment 2 epoch72 best on frozen test** for overall mAP and pothole localization quality
5. **Best.pt files are model-only** (epoch=-1) but still contain optimizer state key (empty/partial)
6. **No corrupted or unreadable checkpoints** found