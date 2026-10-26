import torch
import os

checkpoints = [
    r"runs/detect/experiments/training/yol11s_experiment2/weights/best.pt",
    r"runs/detect/experiments/training/yol11s_experiment2/weights/last.pt",
    r"runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt",
    r"runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt",
    r"runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/last.pt",
    r"runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch99.pt",
]

for path in checkpoints:
    print(f"\n{'='*60}")
    print(f"Checkpoint: {path}")
    print(f"{'='*60}")
    
    if not os.path.exists(path):
        print(f"  FILE NOT FOUND")
        continue
    
    try:
        ckpt = torch.load(path, map_location='cpu', weights_only=False)
        
        # Handle case where checkpoint is just the model state dict or has different structure
        if isinstance(ckpt, dict):
            print(f"  epoch: {ckpt.get('epoch', 'NOT PRESENT')}")
            print(f"  best_fitness: {ckpt.get('best_fitness', 'NOT PRESENT')}")
            print(f"  date: {ckpt.get('date', 'NOT PRESENT')}")
            
            if 'optimizer' in ckpt and ckpt['optimizer'] is not None:
                opt = ckpt['optimizer']
                if isinstance(opt, dict):
                    state_entries = len(opt.get('state', {}))
                    param_groups = len(opt.get('param_groups', []))
                    print(f"  optimizer: PRESENT (state entries: {state_entries}, param_groups: {param_groups})")
                else:
                    print(f"  optimizer: PRESENT (non-dict type: {type(opt).__name__})")
            else:
                print(f"  optimizer: NOT PRESENT")
                
            print(f"  scaler: {'PRESENT' if ckpt.get('scaler') is not None else 'NOT PRESENT'}")
            print(f"  ema: {'PRESENT' if ckpt.get('ema') is not None else 'NOT PRESENT'}")
        else:
            print(f"  Type: {type(ckpt).__name__} (not a dict)")
            print(f"  epoch: NOT PRESENT")
            print(f"  best_fitness: NOT PRESENT")
            print(f"  date: NOT PRESENT")
            print(f"  optimizer: NOT PRESENT")
            print(f"  scaler: NOT PRESENT")
            print(f"  ema: NOT PRESENT")
        
    except Exception as e:
        print(f"  ERROR loading: {e}")