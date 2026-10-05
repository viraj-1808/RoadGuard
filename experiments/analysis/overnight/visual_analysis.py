#!/usr/bin/env python3
"""
Visual Error Analysis - Agent C (READ-ONLY analysis mode).
Analyzes representative test cases to identify visual patterns in errors.
"""

import os
import json
import csv
import numpy as np
from collections import defaultdict, Counter
from PIL import Image, ImageDraw, ImageFont
import shutil

# Paths
BASE = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
PRED_FILE = os.path.join(BASE, "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json")
LABEL_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/labels/test")
IMAGE_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/images/test")
OUTPUT_DIR = os.path.join(BASE, "experiments/analysis/overnight")
VIS_DIR = os.path.join(OUTPUT_DIR, "visual_cases")

# Class mapping
CLASS_NAMES = {
    0: 'longitudinal_crack',
    1: 'transverse_crack',
    2: 'alligator_crack',
    3: 'pothole'
}
PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}

CONFIDENCE_THRESHOLD = 0.25
NMS_IOU_THRESHOLD = 0.5
IMAGE_SIZE = 720

os.makedirs(VIS_DIR, exist_ok=True)

def load_ground_truth(label_dir):
    gt_data = {}
    class_counts = Counter()
    total_objects = 0
    for filename in os.listdir(label_dir):
        if not filename.endswith('.txt'):
            continue
        image_id = filename.replace('.txt', '')
        gt_objects = []
        with open(os.path.join(label_dir, filename), 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                try:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    x = (x_center - width/2) * IMAGE_SIZE
                    y = (y_center - height/2) * IMAGE_SIZE
                    w = width * IMAGE_SIZE
                    h = height * IMAGE_SIZE
                    gt_objects.append({
                        'class_id': class_id,
                        'bbox': [x, y, w, h],
                        'area': w * h,
                        'matched': False
                    })
                    class_counts[class_id] += 1
                    total_objects += 1
                except (ValueError, IndexError):
                    continue
        gt_data[image_id] = gt_objects
    return gt_data, total_objects, dict(class_counts)

def load_predictions(pred_file):
    with open(pred_file, 'r') as f:
        raw_preds = json.load(f)
    pred_by_image = defaultdict(list)
    for pred in raw_preds:
        image_id = pred['image_id']
        class_id = PRED_CLASS_MAP.get(pred['category_id'], pred['category_id'] - 1)
        pred_by_image[image_id].append({
            'class_id': class_id,
            'bbox': pred['bbox'],
            'score': pred['score']
        })
    return pred_by_image

def nms(boxes, scores, iou_threshold):
    """Apply NMS to boxes."""
    if len(boxes) == 0:
        return []
    x1 = np.array([b[0] for b in boxes])
    y1 = np.array([b[1] for b in boxes])
    x2 = np.array([b[0] + b[2] for b in boxes])
    y2 = np.array([b[1] + b[3] for b in boxes])
    areas = (x2 - x1) * (y2 - y1)
    order = np.argsort(scores)[::-1]
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        remaining = np.where(iou <= iou_threshold)[0]
        order = order[remaining + 1]
    return keep

def bbox_iou(box1, box2):
    x1_1, y1_1 = box1[0], box1[1]
    x2_1, y2_1 = box1[0] + box1[2], box1[1] + box1[3]
    x1_2, y1_2 = box2[0], box2[1]
    x2_2, y2_2 = box2[0] + box2[2], box2[1] + box2[3]
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    return intersection / union if union > 0 else 0.0

def compute_matches(gt_objects, pred_objects, iou_threshold=0.5):
    matches = []
    iou_matrix = np.zeros((len(gt_objects), len(pred_objects)))
    for i, gt in enumerate(gt_objects):
        for j, pred in enumerate(pred_objects):
            if gt['class_id'] == pred['class_id']:
                iou_matrix[i, j] = bbox_iou(gt['bbox'], pred['bbox'])
    indices = np.where(iou_matrix >= iou_threshold)
    if len(indices[0]) > 0:
        ious = iou_matrix[indices]
        sort_idx = np.argsort(ious)[::-1]
        matched_gt = set()
        matched_pred = set()
        for idx in sort_idx:
            gt_idx = indices[0][idx]
            pred_idx = indices[1][idx]
            if gt_idx not in matched_gt and pred_idx not in matched_pred:
                matches.append((gt_idx, pred_idx, iou_matrix[gt_idx, pred_idx]))
                matched_gt.add(gt_idx)
                matched_pred.add(pred_idx)
    return matches

# Load data
print("Loading data...")
gt_data, total_gt, gt_class_counts = load_ground_truth(LABEL_DIR)
raw_pred_data = load_predictions(PRED_FILE)

# Apply confidence threshold + NMS
print("Applying confidence threshold and NMS...")
filtered_pred_data = {}
total_after_filter = 0
for image_id, preds in raw_pred_data.items():
    # Filter by confidence
    filtered = [p for p in preds if p['score'] >= CONFIDENCE_THRESHOLD]
    if not filtered:
        continue
    # Apply NMS per class
    kept_preds = []
    for class_id in range(4):
        class_preds = [p for p in filtered if p['class_id'] == class_id]
        if not class_preds:
            continue
        boxes = [p['bbox'] for p in class_preds]
        scores = [p['score'] for p in class_preds]
        keep_indices = nms(boxes, scores, NMS_IOU_THRESHOLD)
        kept_preds.extend([class_preds[i] for i in keep_indices])
    filtered_pred_data[image_id] = kept_preds
    total_after_filter += len(kept_preds)

print(f"Predictions after filter: {total_after_filter} (from {sum(len(v) for v in raw_pred_data.values())})")

# Compute matches with filtered predictions
print("Computing matches...")
error_table = []
fn_objects = []
fp_objects = []
matched_objects = []

for image_id in sorted(set(gt_data.keys()) & set(filtered_pred_data.keys())):
    gt_objects = gt_data[image_id]
    pred_objects = filtered_pred_data[image_id]
    matches = compute_matches(gt_objects, pred_objects, NMS_IOU_THRESHOLD)
    matched_gt_indices = {m[0] for m in matches}
    matched_pred_indices = {m[1] for m in matches}
    
    tp_count = len(matches)
    fp_count = len(pred_objects) - len(matched_pred_indices)
    fn_count = len(gt_objects) - len(matched_gt_indices)
    
    for i, gt in enumerate(gt_objects):
        if i not in matched_gt_indices:
            fn_objects.append({
                'image_id': image_id,
                'class_id': gt['class_id'],
                'class_name': CLASS_NAMES[gt['class_id']],
                'bbox': gt['bbox'],
                'area': gt['area']
            })
    for i, pred in enumerate(pred_objects):
        if i not in matched_pred_indices:
            fp_objects.append({
                'image_id': image_id,
                'class_id': pred['class_id'],
                'class_name': CLASS_NAMES[pred['class_id']],
                'bbox': pred['bbox'],
                'score': pred['score'],
                'area': pred['bbox'][2] * pred['bbox'][3]
            })
    for gt_idx, pred_idx, iou in matches:
        gt_obj = gt_objects[gt_idx]
        pred_obj = pred_objects[pred_idx]
        matched_objects.append({
            'image_id': image_id,
            'class_id': gt_obj['class_id'],
            'class_name': CLASS_NAMES[gt_obj['class_id']],
            'iou': iou,
            'gt_bbox': gt_obj['bbox'],
            'pred_bbox': pred_obj['bbox'],
            'gt_area': gt_obj['area'],
            'pred_area': pred_obj['bbox'][2] * pred_obj['bbox'][3],
            'pred_score': pred_obj['score']
        })
    
    error_table.append({
        'image_id': image_id,
        'gt_count': len(gt_objects),
        'pred_count': len(pred_objects),
        'tp': tp_count,
        'fp': fp_count,
        'fn': fn_count,
    })

# Compute metrics
total_tp = len(matched_objects)
total_fp = len(fp_objects)
total_fn = len(fn_objects)
precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
print(f"TP={total_tp}, FP={total_fp}, FN={total_fn}")

# Per-class
class_stats = {}
for class_id in range(4):
    class_gt = sum(1 for objs in gt_data.values() for obj in objs if obj['class_id'] == class_id)
    class_tp = sum(1 for obj in matched_objects if obj['class_id'] == class_id)
    class_fp = sum(1 for obj in fp_objects if obj['class_id'] == class_id)
    class_fn = sum(1 for obj in fn_objects if obj['class_id'] == class_id)
    class_precision = class_tp / (class_tp + class_fp) if (class_tp + class_fp) > 0 else 0
    class_recall = class_tp / (class_tp + class_fn) if (class_tp + class_fn) > 0 else 0
    class_stats[class_id] = {
        'name': CLASS_NAMES[class_id],
        'gt_count': class_gt, 'tp': class_tp, 'fp': class_fp, 'fn': class_fn,
        'precision': class_precision, 'recall': class_recall
    }
    print(f"  {CLASS_NAMES[class_id]}: P={class_precision:.3f}, R={class_recall:.3f}, FN={class_fn}")

# === ANALYSIS 1: False Negative Patterns ===
print("\n=== FALSE NEGATIVE PATTERNS ===")
fn_by_class = defaultdict(list)
for obj in fn_objects:
    fn_by_class[obj['class_id']].append(obj)

fn_size_analysis = {}
for class_id in range(4):
    fn_list = fn_by_class[class_id]
    if not fn_list:
        fn_size_analysis[class_id] = "No FNs"
        continue
    areas = [obj['area'] for obj in fn_list]
    avg_area = np.mean(areas)
    min_area = np.min(areas)
    max_area = np.max(areas)
    # Normalize by image size
    norm_areas = [a / (IMAGE_SIZE * IMAGE_SIZE) for a in areas]
    small_count = sum(1 for a in norm_areas if a < 0.001)  # <0.1% of image
    medium_count = sum(1 for a in norm_areas if 0.001 <= a < 0.01)
    large_count = sum(1 for a in norm_areas if a >= 0.01)
    
    fn_size_analysis[class_id] = {
        'count': len(fn_list),
        'avg_area': avg_area,
        'min_area': min_area,
        'max_area': max_area,
        'norm_avg': np.mean(norm_areas),
        'small': small_count,
        'medium': medium_count,
        'large': large_count
    }
    print(f"  {CLASS_NAMES[class_id]}: {len(fn_list)} FNs, avg_norm_area={np.mean(norm_areas):.5f}, small={small_count}, medium={medium_count}, large={large_count}")

# === ANALYSIS 2: False Positive Patterns ===
print("\n=== FALSE POSITIVE PATTERNS ===")
fp_by_class = defaultdict(list)
for obj in fp_objects:
    fp_by_class[obj['class_id']].append(obj)

fp_score_analysis = {}
for class_id in range(4):
    fp_list = fp_by_class[class_id]
    if not fp_list:
        fp_score_analysis[class_id] = "No FPs"
        continue
    scores = [obj['score'] for obj in fp_list]
    areas = [obj['area'] for obj in fp_list]
    norm_areas = [a / (IMAGE_SIZE * IMAGE_SIZE) for a in areas]
    fp_score_analysis[class_id] = {
        'count': len(fp_list),
        'avg_score': np.mean(scores),
        'min_score': np.min(scores),
        'max_score': np.max(scores),
        'avg_norm_area': np.mean(norm_areas)
    }
    print(f"  {CLASS_NAMES[class_id]}: {len(fp_list)} FPs, avg_score={np.mean(scores):.3f}, avg_norm_area={np.mean(norm_areas):.5f}")

# === ANALYSIS 3: Localization Failures ===
print("\n=== LOCALIZATION FAILURES ===")
if matched_objects:
    ious = [obj['iou'] for obj in matched_objects]
    print(f"  Mean IoU: {np.mean(ious):.3f}")
    print(f"  Median IoU: {np.median(ious):.3f}")
    print(f"  IoU < 0.5: {sum(1 for i in ious if i < 0.5)}")
    print(f"  IoU 0.5-0.7: {sum(1 for i in ious if 0.5 <= i < 0.7)}")
    print(f"  IoU 0.7-0.9: {sum(1 for i in ious if 0.7 <= i < 0.9)}")
    print(f"  IoU >= 0.9: {sum(1 for i in ious if i >= 0.9)}")
    
    # Size deviation
    size_ratios = []
    for obj in matched_objects:
        gt_area = obj['gt_area']
        pred_area = obj['pred_area']
        if gt_area > 0:
            size_ratios.append(pred_area / gt_area)
    print(f"  Size ratio (pred/gt): mean={np.mean(size_ratios):.3f}, std={np.std(size_ratios):.3f}")
    print(f"  Too large (>2x): {sum(1 for r in size_ratios if r > 2)}")
    print(f"  Too small (<0.5x): {sum(1 for r in size_ratios if r < 0.5)}")

# === ANALYSIS 4: Image-level difficulty ===
print("\n=== IMAGE-LEVEL DIFFICULTY ===")
difficult_images = sorted(error_table, key=lambda x: x['fn'], reverse=True)[:15]
print("Top 15 most missed objects:")
for img in difficult_images:
    print(f"  {img['image_id']}: GT={img['gt_count']}, Pred={img['pred_count']}, TP={img['tp']}, FP={img['fp']}, FN={img['fn']}")

# === SAVE ANALYSIS RESULTS ===
analysis_results = {
    'precision': precision,
    'recall': recall,
    'f1': f1,
    'total_tp': total_tp,
    'total_fp': total_fp,
    'total_fn': total_fn,
    'class_stats': {str(k): v for k, v in class_stats.items()},
    'fn_size_analysis': {str(k): v for k, v in fn_size_analysis.items()},
    'fp_score_analysis': {str(k): v for k, v in fp_score_analysis.items()},
    'matched_ious': matched_objects,
    'fn_objects': fn_objects,
    'fp_objects': fp_objects,
    'difficult_images': difficult_images,
    'conf_threshold': CONFIDENCE_THRESHOLD,
    'nms_threshold': NMS_IOU_THRESHOLD
}

# Save for later use
with open(os.path.join(OUTPUT_DIR, 'analysis_results.json'), 'w') as f:
    json.dump(analysis_results, f, default=str)
print(f"\nAnalysis results saved to {OUTPUT_DIR}/analysis_results.json")
