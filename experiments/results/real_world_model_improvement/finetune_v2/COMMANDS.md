# Fine-tuned v2 Evaluation Commands

## Checkpoint Verification
```powershell
Get-FileHash runs/detect/experiments/training/yol11s_realworld_finetune_v2/weights/best.pt -Algorithm SHA256
```

## Evaluation Command
```powershell
python scripts/finetune_v2_evaluation.py
```

## Model Classes
```
{
  "0": "longitudinal_crack",
  "1": "transverse_crack",
  "2": "alligator_crack",
  "3": "pothole"
}
```
