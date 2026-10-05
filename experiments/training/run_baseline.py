#!/usr/bin/env python3
"""
Experiment 2 Training Script for YOLO11s on RoadGuard Combined Dataset
RoadGuard AI Project

This script runs Experiment 2 training with the following configuration:
- Model: YOLO11s pretrained (original COCO initialization)
- Dataset: experiments/dataset/experiment2/data.yaml (Dataset A TRAIN + Dataset B non-India)
- Task: Object detection
- Classes: 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole
- Image size: 720
- Batch size: 16 (safe for RTX 4050, ~5.5GB peak)
- Epochs: 30 (controlled run for data-distribution experiment)
- Seed: 42
- Device: 0 (GPU)
- Optimizer: auto
- Workers: 0 (minimal)
- Pretrained: True
- Resume: False
- Patience: 50 (early stopping)
- Save: True
- Save_period: 1
- Project: experiments/training
- Name: yol11s_experiment2
"""

import os
import sys
from pathlib import Path

def main():
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from ultralytics import YOLO
        import torch
        
        print("=" * 60)
        print("RoadGuard AI - Experiment 2 Training: YOLO11s on Combined Dataset")
        print("=" * 60)
        print()
        
        # Check CUDA availability
        print(f"[INFO] CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[INFO] GPU Count: {torch.cuda.device_count()}")
            print(f"[INFO] GPU Name: {torch.cuda.get_device_name(0)}")
            print(f"[INFO] GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB")
        print()
        
        # Check if model exists
        model_path = "weights/yolo11s.pt"
        if not os.path.exists(model_path):
            print(f"[INFO] Model {model_path} not found. Will download from Ultralytics model zoo.")
        
        # Check dataset config
        data_yaml = "experiments/dataset/experiment2/data.yaml"
        if not os.path.exists(data_yaml):
            print(f"[ERROR] Dataset config not found: {data_yaml}")
            return 1
        
        print(f"[INFO] Dataset: {data_yaml}")
        print(f"[INFO] Output: experiments/training/yol11s_experiment2")
        
        # Training configuration
        config = {
            'model': model_path,
            'data': data_yaml,
            'epochs': 30,
            'patience': 50,
            'batch': 16,
            'imgsz': 720,
            'save': True,
            'save_period': 1,
            'cache': False,
            'device': 0,
            'workers': 0,
            'project': 'experiments/training',
            'name': 'yol11s_experiment2',
            'exist_ok': True,
            'pretrained': True,
            'cls_remap': True,
            'optimizer': 'auto',
            'verbose': True,
            'seed': 42,
            'deterministic': True,
            'single_cls': False,
            'rect': False,
            'cos_lr': False,
            'close_mosaic': 10,
            'resume': False,
            'amp': True,
            'fraction': 1.0,
            'profile': False,
            'freeze': None,
            'multi_scale': 0.0,
            'compile': False,
            'overlap_mask': True,
            'mask_ratio': 4,
            'dropout': 0.0,
            'val': True,
            'split': 'val',
            'plots': True,
            'augment': False,
            'agnostic_nms': False,
        }
        
        print("[INFO] Starting baseline training with configuration:")
        for key, value in config.items():
            print(f"         - {key}: {value}")
        print()
        
        # Load model and start training
        print("[INFO] Loading YOLO11s model...")
        model = YOLO(model_path)
        
        print("[INFO] Starting training...")
        results = model.train(**config)
        
        print()
        print("=" * 60)
        print("Experiment 2 training completed successfully!")
        print(f"Results saved to: experiments/training/yol11s_experiment2")
        print("=" * 60)
        
        return 0
        
    except ImportError as e:
        print(f"[ERROR] Failed to import required modules: {e}")
        print("[INFO] Please install required packages:")
        print("       pip install ultralytics")
        return 1
    except Exception as e:
        print(f"[ERROR] Training failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())