#!/usr/bin/env python3
"""
Resume YOLO11s Real-World Fine-Tuning from last.pt
"""

import os
import sys
import json
import time
import hashlib
import psutil
import torch
from pathlib import Path
from datetime import datetime

def get_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1024**2
        reserved = torch.cuda.memory_reserved(0) / 1024**2
        return allocated, reserved
    return 0, 0

def get_ram_usage():
    return psutil.virtual_memory().percent

def compute_sha256(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main():
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from ultralytics import YOLO
    except ImportError as e:
        print(f"[ERROR] Failed to import ultralytics: {e}")
        return 1
    
    # Configuration - resume from last.pt
    LAST_CHECKPOINT = project_root / "runs/detect/experiments/training/yol11s_realworld_finetune/weights/last.pt"
    DATA_YAML = project_root / "experiments/dataset/yol11s_realworld_finetune/data.yaml"
    PROJECT_DIR = "experiments/training"
    EXP_NAME = "yol11s_realworld_finetune"
    LOG_FILE = project_root / "experiments/results/real_world_model_improvement/training.log"
    
    print("=" * 60)
    print("Resuming YOLO11s Real-World Fine-Tuning")
    print("=" * 60)
    print(f"Checkpoint: {LAST_CHECKPOINT}")
    print(f"Log: {LOG_FILE}")
    print()
    
    if not LAST_CHECKPOINT.exists():
        print(f"[ERROR] Checkpoint not found: {LAST_CHECKPOINT}")
        return 1
    
    actual_hash = compute_sha256(LAST_CHECKPOINT)
    print(f"Checkpoint SHA-256: {actual_hash}")
    print()
    
    # Log resume
    with open(LOG_FILE, "a") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"Resumed: {datetime.now().isoformat()}\n")
        f.write(f"Resume checkpoint: {LAST_CHECKPOINT}\n")
        f.write(f"Resume SHA-256: {actual_hash}\n")
        f.write("=" * 60 + "\n\n")
    
    # Load model from last checkpoint (resumes optimizer state automatically)
    print("[INFO] Loading model from last checkpoint...")
    model = YOLO(str(LAST_CHECKPOINT))
    
    # Training configuration - resume=True to continue from last.pt
    config = {
        'data': str(DATA_YAML),
        'epochs': 82,  # Target epoch (72 + 10)
        'patience': 20,
        'batch': 16,
        'imgsz': 720,
        'device': 0,
        'workers': 2,
        'amp': True,
        'cache': False,
        'seed': 42,
        'deterministic': True,
        'project': PROJECT_DIR,
        'name': EXP_NAME,
        'exist_ok': True,
        'save': True,
        'save_period': 1,
        'resume': True,  # Resume from last.pt with optimizer state
        'optimizer': 'auto',
        'lr0': 0.001,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'close_mosaic': 10,
        'val': True,
        'split': 'val',
        'plots': True,
        'rect': False,
        'verbose': True,
    }
    
    print("[INFO] Training configuration:")
    for k, v in config.items():
        print(f"         {k}: {v}")
    print()
    
    # Custom callback for logging RAM/VRAM per epoch
    def on_train_epoch_end(trainer):
        epoch = trainer.epoch
        ram_pct = get_ram_usage()
        gpu_alloc, gpu_reserved = get_gpu_memory()
        
        log_entry = f"[Epoch {epoch}] RAM: {ram_pct:.1f}% | GPU Alloc: {gpu_alloc:.0f}MB | GPU Reserv: {gpu_reserved:.0f}MB"
        print(log_entry)
        
        with open(LOG_FILE, "a") as f:
            f.write(log_entry + "\n")
        
        if ram_pct > 90:
            warning = f"[WARNING] RAM usage > 90% ({ram_pct:.1f}%) - stopping training"
            print(warning)
            with open(LOG_FILE, "a") as f:
                f.write(warning + "\n")
            trainer.stop = True
    
    def on_fit_epoch_end(trainer):
        if hasattr(trainer, 'metrics') and trainer.metrics:
            metrics = trainer.metrics
            log_entry = f"[Epoch {trainer.epoch}] Metrics: {metrics}"
            print(log_entry)
            with open(LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
    
    model.add_callback("on_train_epoch_end", on_train_epoch_end)
    model.add_callback("on_fit_epoch_end", on_fit_epoch_end)
    
    # Resume training
    print("[INFO] Resuming fine-tuning...")
    start_time = time.time()
    
    try:
        results = model.train(**config)
        training_time = time.time() - start_time
        
        print(f"\n[INFO] Training completed in {training_time:.1f}s")
        
        # Find best and last checkpoints
        exp_dir = project_root / PROJECT_DIR / EXP_NAME
        best_pt = exp_dir / "weights" / "best.pt"
        last_pt = exp_dir / "weights" / "last.pt"
        
        print(f"\nCheckpoints:")
        if best_pt.exists():
            best_hash = compute_sha256(best_pt)
            print(f"  Best: {best_pt}")
            print(f"  Best SHA-256: {best_hash}")
        if last_pt.exists():
            last_hash = compute_sha256(last_pt)
            print(f"  Last: {last_pt}")
            print(f"  Last SHA-256: {last_hash}")
        
        # Log final results
        with open(LOG_FILE, "a") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"Training completed: {datetime.now().isoformat()}\n")
            f.write(f"Duration: {training_time:.1f}s\n")
            if best_pt.exists():
                f.write(f"Best checkpoint: {best_pt}\n")
                f.write(f"Best SHA-256: {best_hash}\n")
            if last_pt.exists():
                f.write(f"Last checkpoint: {last_pt}\n")
                f.write(f"Last SHA-256: {last_hash}\n")
            f.write("=" * 60 + "\n")
        
        # Write best checkpoint info
        if best_pt.exists():
            best_info = {
                "best_checkpoint": str(best_pt),
                "best_sha256": best_hash,
                "last_checkpoint": str(last_pt) if last_pt.exists() else None,
                "last_sha256": last_hash if last_pt.exists() else None,
                "training_epochs": 82,
                "fine_tune_epochs": 10,
                "source_checkpoint": "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt",
                "source_sha256": "e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5",
                "source_epoch": 72,
                "completed_at": datetime.now().isoformat()
            }
            info_path = project_root / "experiments/results/real_world_model_improvement/best_checkpoint_info.json"
            with open(info_path, "w") as f:
                json.dump(best_info, f, indent=2)
            print(f"\n[INFO] Best checkpoint info saved to: {info_path}")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        
        with open(LOG_FILE, "a") as f:
            f.write(f"\n[ERROR] Training failed: {e}\n")
            traceback.print_exc(file=f)
        return 1

if __name__ == "__main__":
    sys.exit(main())