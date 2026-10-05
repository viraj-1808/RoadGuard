#!/usr/bin/env python3
import hashlib
import os
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Collect reproducibility data
data = {}

# 1. Git commit
try:
    data['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
except:
    data['git_commit'] = ""

# 2. Python version
data['python_version'] = subprocess.check_output(['python', '--version'], text=True).strip()

# 3. PyTorch version
try:
    result = subprocess.run(['python', '-c', 'import torch; print(f"PyTorch: {torch.__version__}")'], 
                          capture_output=True, text=True)
    data['pytorch_version'] = result.stdout.strip()
except:
    data['pytorch_version'] = ""

# 4. CUDA version reported by PyTorch
try:
    result = subprocess.run(['python', '-c', 'import torch; print(f"CUDA: {torch.version.cuda}")'], 
                          capture_output=True, text=True)
    data['cuda_version'] = result.stdout.strip()
except:
    data['cuda_version'] = ""

# 5. NVIDIA driver version
try:
    result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'], 
                          capture_output=True, text=True)
    data['nvidia_driver_version'] = result.stdout.strip()
except:
    data['nvidia_driver_version'] = ""

# 6. GPU model
try:
    result = subprocess.run(['python', '-c', 'import torch; print(f"GPU: {torch.cuda.get_device_name(0)}")'], 
                          capture_output=True, text=True)
    data['gpu_model'] = result.stdout.strip()
except:
    data['gpu_model'] = ""

# 7. Ultralytics version
try:
    result = subprocess.run(['python', '-c', 'import ultralytics; print(f"Ultralytics: {ultralytics.__version__}")'], 
                          capture_output=True, text=True)
    data['ultralytics_version'] = result.stdout.strip()
except:
    data['ultralytics_version'] = ""

# 8. Dataset path (from args.yaml of baseline training)
data['dataset_path'] = str(PROJECT_ROOT / "experiments/dataset/yolo_rdd2022_india")

# 9. data.yaml checksum (SHA256)
try:
    with open(PROJECT_ROOT / 'experiments/dataset/yolo_rdd2022_india/data.yaml', 'rb') as f:
        data['data_yaml_checksum'] = hashlib.sha256(f.read()).hexdigest()
except:
    data['data_yaml_checksum'] = ""

# 10. split_manifest_fixed.json checksum (SHA256)
try:
    with open(PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json', 'rb') as f:
        data['split_manifest_checksum'] = hashlib.sha256(f.read()).hexdigest()
except Exception as e:
    data['split_manifest_checksum'] = ""

# 11. conversion_manifest checksum (SHA256)
try:
    with open(PROJECT_ROOT / 'experiments/dataset/yolo_rdd2022_india/conversion_manifest.json', 'rb') as f:
        data['conversion_manifest_checksum'] = hashlib.sha256(f.read()).hexdigest()
except:
    data['conversion_manifest_checksum'] = ""

# 12. Model checkpoint/name (from args.yaml of baseline training)
data['model_checkpoint'] = "weights/yolo11s.pt"

# 13. Image size (from args.yaml of baseline training)
data['image_size'] = 720

# 14. Batch size (from args.yaml of baseline training - yolo11s_batch_16 is the baseline)
data['batch_size'] = 16

# 15. Seed (from args.yaml of baseline training)
data['seed'] = 42

# 16. Number of epochs (from args.yaml of baseline training)
data['epochs'] = 1

# 17. Output directory (from args.yaml of baseline training)
baseline_dir = str(PROJECT_ROOT / "experiments/training/yol11s_dataset_v2_split_v2_20260928")
data['output_directory'] = baseline_dir

# Write JSON file
output_path = PROJECT_ROOT / 'experiments/training/reproducibility_record.json'
with open(output_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Reproducibility record saved to {output_path}")
print(json.dumps(data, indent=2))