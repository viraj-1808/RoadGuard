# Audit v2 Commands

## Checkpoint Verification
```powershell
Get-FileHash runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt -Algorithm SHA256
```

## Evaluation Command
```powershell
python scripts/audit_v2_evaluation.py
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
