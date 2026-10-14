# YOLO11s Real-World Fine-Tuning v2 - Training Configuration

## Experiment Details
- **Experiment Name**: yol11s_realworld_finetune_v2
- **Source Checkpoint**: runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt (SHA-256: e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5)
- **Source Epoch**: 72
- **Target Epochs**: 82 (10 additional epochs)
- **Current Progress**: Epoch 8/82 (as of 2026-10-11)

## Dataset
- **Training**: Combined Exp2 train (19,719) + 20 verified manual images = 19,739 images
- **Validation**: Dataset A val (229 images) + 8 manual val images
- **Data YAML**: experiments/dataset/yol11s_realworld_finetune_v2/data.yaml
- **Val Data YAML**: experiments/dataset/yol11s_realworld_finetune_v2_val.yaml

## Training Configuration (Reduced Memory)
- **Batch Size**: 8 (reduced from 16)
- **Image Size**: 640 (reduced from 720)
- **Workers**: 1 (reduced from 2)
- **Device**: 0 (GPU)
- **AMP**: True
- **Cache**: False
- **Seed**: 42
- **Deterministic**: True
- **Epochs**: 82
- **Patience**: 20
- **LR**: 0.001
- **LR Final**: 0.01
- **Momentum**: 0.937
- **Weight Decay**: 0.0005
- **Close Mosaic**: 10
- **Save Period**: 1
- **Resume**: True (from last.pt with optimizer state)

## Class Weights
- longitudinal_crack (0): 1.0
- transverse_crack (1): 1.0
- alligator_crack (2): 2.0 (upweighted)
- pothole (3): 0.5 (downweighted)

## Output Directory
- **Results**: experiments/results/real_world_model_improvement/finetune_v2/
- **Training Log**: experiments/results/real_world_model_improvement/finetune_v2/training.log
- **Best Checkpoint Info**: experiments/results/real_world_model_improvement/finetune_v2/best_checkpoint_info.json

## Monitoring
- **RAM Threshold**: >90% auto-stop
- **Current RAM**: ~79-85% (stable)
- **GPU Memory**: ~300MB allocated, ~2.7GB reserved

## Validation Metrics (per epoch)
| Epoch | Precision | Recall | mAP50 | mAP50-95 |
|-------|-----------|--------|-------|----------|
| 0 (initial) | 0.6095 | 0.5228 | 0.5513 | 0.2932 |
| 0 (resumed) | 0.6370 | 0.5620 | 0.5975 | 0.3285 |
| 1 | 0.6190 | 0.5370 | 0.5747 | 0.3130 |
| 2 | 0.6174 | 0.5242 | 0.5633 | 0.3054 |
| 3 | 0.6061 | 0.5472 | 0.5676 | 0.3074 |
| 4 | 0.6054 | 0.5563 | 0.5704 | 0.3119 |
| 5 | 0.6236 | 0.5610 | 0.5848 | 0.3180 |
| 6 | 0.6179 | 0.5503 | 0.5744 | 0.3126 |
| 7 | 0.6135 | 0.5565 | 0.5781 | 0.3158 |
| 8 | 0.6396 | 0.5535 | 0.5917 | 0.3198 |

## Resume Command
```bash
python experiments/training/resume_realworld_finetune_v2.py
```

## Checkpoints
- best.pt: Best model so far (epoch 0 resumed)
- last.pt: Latest model (epoch 8)
- epoch{N}.pt: Per-epoch checkpoints

## Next Steps
1. Continue training by running the resume script until epoch 82
2. Monitor RAM usage (currently stable at ~80%)
3. Best mAP50-95 so far: 0.3285 at epoch 0 (resumed)
4. Expected completion: ~25-30 more hours of training