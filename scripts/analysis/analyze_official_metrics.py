import os
import json
from collections import Counter
import glob

# Load the official test metrics
metrics_path = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_dataset_v2_split_v2\test_eval\test_metrics.json'
with open(metrics_path, 'r') as f:
    metrics = json.load(f)

print("=" * 70)
print("OFFICIAL ULTRALYTICS METRICS")
print("=" * 70)
print(f"Model: {metrics['model']}")
print(f"Dataset: {metrics['dataset']}")
print(f"Split: {metrics['split']}")
print()
print("Overall Metrics:")
print(f"  precision: {metrics['metrics']['box']['mp']:.3f}")
print(f"  recall:    {metrics['metrics']['box']['mr']:.3f}")
print(f"  mAP50:     {metrics['metrics']['box']['map50']:.3f}")
print(f"  mAP50-95:  {metrics['metrics']['box']['map']:.3f}")
print()
print("Per-Class Metrics:")
for class_name, class_metrics in metrics['per_class'].items():
    print(f"  {class_name}:")
    print(f"    precision: {class_metrics['precision']:.3f}")
    print(f"    recall:    {class_metrics['recall']:.3f}")
    print(f"    map50:     {class_metrics['map50']:.3f}")
    print(f"    map:       {class_metrics['map']:.3f}")
print(f"\nTotals: {metrics['totals']['images']} images, {metrics['totals']['instances']} instances")

# Load ground truth to verify the official numbers make sense
label_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\yolo_rdd2022_india\labels\test'

# Count GT per class
class_names = {
    0: 'longitudinal_crack',
    1: 'transverse_crack',
    2: 'alligator_crack',
    3: 'pothole'
}

# Load data.yaml to get class names
data_yaml_path = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\yolo_rdd2022_india\data.yaml'
import yaml
with open(data_yaml_path, 'r') as f:
    data_yaml = yaml.safe_load(f)

gt_class_counts = Counter()
for label_file in sorted(glob.glob(os.path.join(label_dir, "*.txt"))):
    with open(label_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split()
                class_id = int(parts[0])
                gt_class_counts[class_id] += 1

print("\n" + "=" * 70)
print("GROUND TRUTH ANALYSIS")
print("=" * 70)
print(f"Total GT objects: {sum(gt_class_counts.values())}")
for class_id in range(4):
    name = class_names[class_id]
    count = gt_class_counts[class_id]
    official_count = metrics['per_class'][name]['instances']
    print(f"  {name} (class {class_id}): {count} GT objects, {official_count} instances in metrics")
