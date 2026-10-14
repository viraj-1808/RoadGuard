# RoadGuard AI - Development Guide

## Setup Instructions

### 1. Prerequisites

- **Python**: 3.12.10 (verified), 3.10+ compatible
- **OS**: Windows 11 (AMD64) or Linux
- **Disk Space**: 206GB+ free on drive C:
- **Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM) or CPU-only

### 2. Clone / Get the Repository

```bash
git clone https://github.com/your-org/roadguard-ai.git
cd roadguard-ai
```

### 3. Create a Virtual Environment (Recommended)

```bash
# Create venv
python -m venv .venv

# Activate on Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Or activate on Windows CMD
.\.venv\Scripts\activate.bat

# Or activate on macOS / Linux
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# For GPU training (reinstall PyTorch with CUDA):
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify installation
python -c "import ultralytics, torch, cv2, numpy, PIL, psutil, pandas; print('All dependencies OK')"
```

### 5. Project Structure

```
roadguard-ai/
├── docs/                    # Documentation (TRAINING.md, DEVELOPMENT.md, etc.)
├── experiments/
│   ├── training/            # Training scripts and configs
│   ├── dataset/             # Dataset YAML and image directories
│   └── results/             # Training results and logs
├── ml/
│   ├── training/            # ML training pipeline modules
│   └── preprocessing/       # Data preprocessing scripts
├── scripts/                 # General project scripts
├── runs/                    # Training output directories
├── weights/                 # Model checkpoints
└── src/                     # Source code (if applicable)
```

### 6. Running Training Scripts

#### Baseline Training (Experiment 1)

```bash
# Using baseline config file
python -m ultralytics train --cfg experiments/training/baseline_config.yaml

# Or via batch script (Windows)
.\experiments\training\run_baseline.bat

# Or via PowerShell script
.\experiments\training\run_baseline.ps1
```

#### Experiment 2 Controlled Training

```bash
python experiments/training/run_baseline.py
```

#### Real-World Fine-Tuning from Epoch72

```bash
# Standard fine-tuning (10 additional epochs)
python experiments/training/run_realworld_finetune.py

# Reduced memory fine-tuning v2
python experiments/training/run_realworld_finetune_v2.py

# True resume from epoch72 (verified command)
python -c "
from ultralytics import YOLO
model = YOLO('runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt')
model.train(
    data='experiments/dataset/yolo_rdd2022_india/data.yaml',
    epochs=82,
    batch=16,
    imgsz=720,
    device=0,
    resume=True,
    project='experiments/training',
    name='yol11s_experiment2_resume',
    exist_ok=True,
    seed=42,
    deterministic=True,
    amp=True,
    cache=False,
    optimizer='auto',
    lr0=0.001,
    lrf=0.01,
    momentum=0.937,
    weight_decay=0.0005,
    close_mosaic=10,
    val=True,
    split='val',
    plots=True,
    verbose=True,
)
```

#### Resume from Last Checkpoint (True Resume)

```bash
# Resume from last.pt with full optimizer state
python experiments/training/resume_realworld_finetune.py

# Resume from last.pt with reduced memory settings
python experiments/training/resume_realworld_finetune_v2.py
```

### 7. Dataset Management

#### Dataset Structure (RDD2022 India)

```
experiments/dataset/yolo_rdd2022_india/
├── data.yaml                   # Class definitions and paths
├── images/
│   ├── train/                  # 1071 training images
│   ├── val/                    # 229 validation images
│   └── test/                   # 230 test images
└── labels/
    ├── train/                  # YOLO label files (train)
    ├── val/                    # YOLO label files (val)
    └── test/                   # YOLO label files (test)
```

#### data.yaml Format

```yaml
path: experiments/dataset/yolo_rdd2022_india
train: images/train
val: images/val
test: images/test
nc: 4
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
```

#### Adding New Classes or Images

1. Add images to the appropriate directory (train/val/test)
2. Generate/update YOLO label files (.txt)
3. Update `data.yaml` if class count changes
4. Re-run dataset validation script:
   ```bash
   python scripts/analysis/validate_yolo_conversion.py
   ```

### 8. Environment Configuration

#### Python Path Setup

Training scripts add the project root to sys.path:

```python
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
```

#### Environment Variables (Optional)

- **CUDA_VISIBLE_DEVICES**: Set which GPU to use (e.g., `0` or `0,1`)
- **PYTHONPATH**: Can be set to include the project root
- **SEED**: Can be overridden (default=42) in training scripts

#### VS Code / IDE Setup

If using VS Code, the `.vscode/` directory may contain:
- `settings.json` with Python path configuration
- `tasks.json` with build/training commands
- `launch.json` for debugger configuration

### 9. Verifying the Installation

Run the verification script:

```bash
python -c "
import ultralytics, torch, cv2, numpy, PIL, psutil, pandas
import json, hashlib

# Print package versions
print('Package Versions:')
print(f'  ultralytics: {ultralytics.__version__}')
print(f'  torch: {torch.__version__}')
print(f'  torch.cuda.is_available(): {torch.cuda.is_available()}')
print(f'  cv2: {cv2.__version__}')
print(f'  numpy: {numpy.__version__}')
print(f'  PIL: {PIL.__version__}')
print(f'  psutil: {psutil.__version__}')
print(f'  pandas: {pandas.__version__}')
print()

# Verify ultralytics YOLO works
from ultralytics import YOLO
print('Ultralytics YOLO import: OK')
print()

# Verify torch CUDA status
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**2:.0f} MB')
else:
    print('Running on CPU (CUDA not available in this PyTorch build)')
print()

print('Installation verified successfully!')
"
```

### 10. Known Environment Issues

#### CPU-Only PyTorch Installation

**Problem**: The installed PyTorch (2.14.0+cpu) does not include CUDA support, so `torch.cuda.is_available()` returns `false`.

**Solution**: Reinstall PyTorch with CUDA support:

```bash
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Verification after fix**:
```bash
python -c "import torch; print(torch.cuda.is_available())"
# Should return True if CUDA is properly installed
```

#### VRAM Headroom

**Current Status**: 6.0GB total VRAM, 5.7GB free (99MB used by system)
**Recommendation**: Do not exceed batch=16 for imgsz=720 on RTX 4050

### 11. Development Workflow

#### Adding New Training Configurations

1. Create a new YAML config file in `experiments/training/`
2. Reference it via `python -m ultralytics train --cfg experiments/training/your_config.yaml`
3. Document the new configuration in `docs/TRAINING.md`
4. Add required metadata to `experiments/training/reproducibility_record.md`

#### Adding New Scripts

1. Follow the pattern of existing scripts in `experiments/training/`
2. Include psutil and torch imports for resource monitoring
3. Add SHA-256 hash verification for checkpoints
4. Log training progress to files in `experiments/results/`

#### Running Tests (if applicable)

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/ml/test_yolo_adapter.py -v
```

### 12. Script Import Summary

Training scripts typically import:

```python
import os        # Environment/path operations
import sys       # Python path manipulation
import json      # JSON configuration and logging
import time      # Timing measurements
import hashlib   # SHA-256 checksums for checkpoint integrity
import psutil    # RAM/GPU memory monitoring
import torch     # Deep learning framework
from pathlib import Path  # Path manipulation
from datetime import datetime  # Timestamp logging
```

These dependencies are tracked in `requirements.txt`.