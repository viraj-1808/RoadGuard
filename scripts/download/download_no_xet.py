import os
import time
from pathlib import Path

os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['HF_DISABLE_XET'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

from huggingface_hub import snapshot_download

REPO_ID = 'dronefreak/RDD2022'
REVISION = 'd597e2962458f7242a72aaa1b7909118d40f5d29'
OUTPUT_DIR = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022'

base = Path(OUTPUT_DIR)

# Count current images before
train_images_before = list((base / 'data' / 'images' / 'train').rglob('*.jpg'))
valid_images_before = list((base / 'data' / 'images' / 'valid').rglob('*.jpg')) if (base / 'data' / 'images' / 'valid').exists() else []
test_images_before = list((base / 'data' / 'images' / 'test').rglob('*.jpg'))
print(f'Before download: train={len(train_images_before)}, valid={len(valid_images_before)}, test={len(test_images_before)}')

print('Starting snapshot_download with Xet disabled...')
try:
    result = snapshot_download(
        repo_id=REPO_ID,
        revision=REVISION,
        repo_type='dataset',
        local_dir=OUTPUT_DIR,
        local_dir_use_symlinks=False,
        max_workers=32,
        resume_download=True,
    )
    print(f'Download complete: {result}')
except Exception as e:
    print(f'Download error: {e}')
    import traceback
    traceback.print_exc()

# Count after
train_images = list((base / 'data' / 'images' / 'train').rglob('*.jpg'))
valid_images = list((base / 'data' / 'images' / 'valid').rglob('*.jpg')) if (base / 'data' / 'images' / 'valid').exists() else []
test_images = list((base / 'data' / 'images' / 'test').rglob('*.jpg'))
print(f'After download: train={len(train_images)}, valid={len(valid_images)}, test={len(test_images)}')
print(f'New files: train={len(train_images) - len(train_images_before)}, valid={len(valid_images) - len(valid_images_before)}, test={len(test_images) - len(test_images_before)}')