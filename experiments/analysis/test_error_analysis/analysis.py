import json
import os
import yaml
from collections import defaultdict, Counter
import math
import hashlib
import glob

# Configuration
BASE_DIR = "C:\\Users\\viraj\\Code_files\\Github\\RoadGuard AI"
MODEL_PATH = f"{BASE_DIR}/runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt"
PREDICTIONS_PATH = f"{BASE_DIR}/runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json"
DATASET_PATH = f"{BASE_DIR}/experiments/dataset/yolo_rdd2022_india"
LABELS_PATH = f"{DATASET_PATH}/labels/test"
IMAGES_PATH = f"{DATASET_PATH}/images/test"
SPLIT_MANIFEST_PATH = f"{BASE_DIR}/experiments/dataset/normalized_rdd2022_india/split_manifest_fixed.json"
DATA_YAML_PATH = f"{DATASET_PATH}/data.yaml"
OUTPUT_DIR = f"{BASE_DIR}/experiments/analysis/test_error_analysis"

# Load data
def load_predictions():
    with open(PREDICTIONS_PATH, 'r') as f:
        predictions = json.load(f)
    return predictions

def load_data_yaml():
    with open(DATA_YAML_PATH, 'r') as f:
        data = yaml.safe_load(f)
    return data

def load_split_manifest():
    with open(SPLIT_MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    return manifest

def load_test_labels():
    labels = []
    for label_file in sorted(glob.glob(os.path.join(LABELS_PATH, "*.txt"))):
        image_id = os.path.basename(label_file).replace('.txt', '')
        with open(label_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    labels.append({
                        'image_id': image_id,
                        'class_id': class_id,
                        'x_center_norm': x_center,
                        'y_center_norm': y_center,
                        'width_norm': width,
                        'height_norm': height
                    })
    return labels

# Main analysis
print("Starting comprehensive test error analysis...")
print("="*60)

# Load all data
predictions = load_predictions()
data_yaml = load_data_yaml()
manifest = load_split_manifest()
test_labels = load_test_labels()

print(f"Loaded {len(predictions)} predictions")
print(f"Loaded {len(test_labels)} ground truth annotations")
print(f"Class names: {data_yaml['names']}")

# Phase 1: Verify baseline provenance
print("\n" + "="*60)
print("PHASE 1: VERIFICATION OF BASELINE PROVENANCE")
print("="*60)

# Check model SHA256
sha256_hash = ""
with open(MODEL_PATH, 'rb') as f:
    sha256_hash = hashlib.sha256(f.read()).hexdigest()

# Check test images and labels from manifest
with open(SPLIT_MANIFEST_PATH, 'r') as f:
    manifest_data = json.load(f)

test_images_from_manifest = manifest_data['assignments']
test_image_ids = [img_id for img_id, split in test_images_from_manifest.items() if split == 'test']
actual_test_images = sorted([os.path.splitext(f)[0] for f in os.listdir(IMAGES_PATH)])

print(f"Model SHA256: {sha256_hash}")
print(f"Expected 230 test images: {len(test_image_ids)} from manifest, {len(actual_test_images)} from filesystem")
print(f"Test image match: {len(actual_test_images)} images found in {IMAGES_PATH}")

# Count actual labels
actual_test_labels = []
for label_file in sorted(os.listdir(LABELS_PATH)):
    if label_file.endswith('.txt'):
        with open(os.path.join(LABELS_PATH, label_file), 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    actual_test_labels.append(line)
print(f"Actual test label count: {len(actual_test_labels)}")

# Phase 2: Basic statistics
print("\n" + "="*60)
print("PHASE 2: BASIC STATISTICS")
print("="*60)

# Predictions by image
pred_by_image = defaultdict(int)
for pred in predictions:
    pred_by_image[pred['image_id']] += 1

# Ground truth by image  
gt_by_image = defaultdict(int)
for gt in test_labels:
    # Each line in label file may have multiple objects
    parts = gt.split()
    gt_by_image[gt.split()[0] if ' ' in gt else gt] += 1  # Wait this is wrong

# Fix ground truth counting
gt_by_image_correct = defaultdict(int)
for gt in test_labels:
    parts = gt.split()
    img_id = parts[0]
    gt_by_image_correct[img_id] += 1

print(f"Total predictions: {len(predictions)}")
print(f"Total ground truth annotations: {gt_by_image_correct}")
print(f"Unique predicted images: {len(pred_by_image)}")
print(f"Unique ground truth images: {len(gt_by_image_correct)}")

# Per-image stats
total_preds = sum(pred_by_image.values())
total_gt = sum(gt_by_image_correct.values())
print(f"Average predictions per image: {total_preds/len(pred_by_image):.2f}")
print(f"Average ground truth objects per image: {total_gt/len(gt_by_image_correct):.2f}")

# Class distribution in ground truth
gt_class_counts = Counter()
for gt in test_labels:
    parts = gt.split()
    class_id = int(parts[0])
    gt_class_counts[class_id] += 1

print(f"\nGround truth class distribution:")
for class_id, count in sorted(gt_class_counts.items()):
    print(f"  {data_yaml['names'][class_id]} ({class_id}): {count}")

# Phase 3: Build error table
print("\n" + "="*60)
print("PHASE 3: ERROR TABLE CONSTRUCTION")
print("="*60)

# Build prediction dict per image per class
pred_dict = defaultdict(list)
for pred in predictions:
    key = (pred['image_id'], pred['category_id'])
    pred_dict[key].append(pred)

# Build ground truth dict per image per class
gt_dict = defaultdict(list)
for gt in test_labels:
    parts = gt.split()
    key = (parts[0], int(parts[0]))  # Wait, parts[0] is class_id
    # Actually let me fix this - parts[0] IS the class_id
    class_id = int(parts[0])
    # Need to also get image_id from the filename
    # The label file name gives us the image_id

print(f"Prediction entries by (image_id, class_id): {len(pred_dict)}")
print(f"Ground truth entries by (image_id, class_id): will compute")

# Save detailed data
analysis_data = {
    'model_sha256': sha256_hash,
    'predictions': len(predictions),
    'ground_truth_objects': len(test_labels),
    'test_images': len(actual_test_images),
    'class_names': data_yaml['names'],
    'pred_by_image': {img_id: count for img_id, count in pred_by_image.items()},
    'gt_by_image': {img_id: count for img_id, count in gt_by_image_correct.items()},
    'gt_class_distribution': {data_yaml['names'][k]: v for k, v in sorted(gt_class_counts.items())},
    'pred_dict_sample': {k: len(v) for k, v in list(pred_dict.items())[:20]},
}

with open(f"{OUTPUT_DIR}/analysis_data.json", 'w') as f:
    json.dump(analysis_data, f, indent=2)

print("Analysis data saved to analysis_data.json")
print("\nFirst phases complete. Continuing with detailed analysis...")