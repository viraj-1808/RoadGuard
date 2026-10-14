import torch
import hashlib
import os
from pathlib import Path

weights_dir = Path(r"runs\detect\experiments\training\yol11s_experiment2\weights")
checkpoint_files = sorted(weights_dir.glob("*.pt"))

print(f"{'File':<45} {'Epoch':<8} {'Optimizer':<10} {'Opt States':<12} {'Param Groups':<14} {'SHA256'}")
print("-" * 120)

for ckpt_file in checkpoint_files:
    try:
        ckpt = torch.load(ckpt_file, map_location="cpu", weights_only=False)
        
        if ckpt is None:
            epoch = "N/A"
            has_optimizer = False
            opt_state_count = 0
            param_groups = 0
        else:
            epoch = ckpt.get("epoch", "N/A")
            optimizer = ckpt.get("optimizer")
            has_optimizer = optimizer is not None
            opt_state_count = len(optimizer.get("state", {})) if has_optimizer else 0
            param_groups = len(optimizer.get("param_groups", [])) if has_optimizer else 0
        
        with open(ckpt_file, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()[:16]
        
        print(f"{ckpt_file.name:<45} {str(epoch):<8} {str(has_optimizer):<10} {str(opt_state_count):<12} {str(param_groups):<14} {sha256}")
    except Exception as e:
        print(f"{ckpt_file.name:<45} ERROR: {e}")