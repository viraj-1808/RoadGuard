#!/usr/bin/env python3
"""
Visual Error Analysis - Agent C (READ-ONLY analysis mode).
Analyzes representative test cases to identify visual patterns in errors.
Generates annotated images and contact sheets.
"""

import os
import json
import csv
import numpy as np
from collections import defaultdict, Counter
from PIL import Image, ImageDraw, ImageFont
import shutil

BASE = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
PRED_FILE = os.path.join(BASE, "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json")
LABEL_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/labels/test")
IMAGE_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/images/test")
OUTPUT_DIR = os.path.join(BASE, "experiments/analysis/overnight")
VIS_DIR = os.path.join(OUTPUT_DIR, "visual_cases")
REPORT_FILE = os.path.join(OUTPUT_DIR, "visual_error_analysis.md")

CLASS_NAMES = {0: 'longitudinal_crack', 1: 'transverse_crack', 2: 'alligator_crack', 3: 'pothole'}
PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}
CONFIDENCE_THRESHOLD = 0.25
NMS_IOU_THRESHOLD = 0.5
IMAGE_SIZE = 720

os.makedirs(VIS_DIR, exist_ok=True)

CLASS_COLORS = {
    0: (0, 255, 0),    # green - longitudinal
    1: (0, 0, 255),    # red - transverse
    2: (255, 165, 0),  # orange - alligator
    3: (255, 0, 255),  # magenta - pothole
}

def load_ground_truth(label_dir):
    gt_data = {}
    class_counts = Counter()
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
                        'norm_area': (w * h) / (IMAGE_SIZE * IMAGE_SIZE),
                        'x_center': x_center,
                        'y_center': y_center,
                        'width': width,
                        'height': height,
                        'matched': False
                    })
                    class_counts[class_id] += 1
                except (ValueError, IndexError):
                    continue
        gt_data[image_id] = gt_objects
    return gt_data, dict(class_counts)

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

def box_center_x(bbox):
    return bbox[0] + bbox[2] / 2

def box_center_y(bbox):
    return bbox[1] + bbox[3] / 2

def box_area(bbox):
    return bbox[2] * bbox[3]

def box_width(bbox):
    return bbox[2]

def box_height(bbox):
    return bbox[3]

def is_edge_object(bbox, margin=0.05):
    x, y, w, h = bbox
    return (x < margin * IMAGE_SIZE or y < margin * IMAGE_SIZE or
            x + w > (1 - margin) * IMAGE_SIZE or y + h > (1 - margin) * IMAGE_SIZE)

print("Loading data...")
gt_data, gt_class_counts = load_ground_truth(LABEL_DIR)
raw_pred_data = load_predictions(PRED_FILE)

print("Filtering predictions...")
filtered_pred_data = {}
for image_id, preds in raw_pred_data.items():
    filtered = [p for p in preds if p['score'] >= CONFIDENCE_THRESHOLD]
    if not filtered:
        continue
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

print("Computing matches...")
fn_objects = []
fp_objects = []
matched_objects = []
error_table = []

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
            fn_obj = dict(gt)
            fn_obj['image_id'] = image_id
            fn_obj['class_name'] = CLASS_NAMES[gt['class_id']]
            fn_obj['edge'] = is_edge_object(gt['bbox'])
            fn_objects.append(fn_obj)
    for i, pred in enumerate(pred_objects):
        if i not in matched_pred_indices:
            fp_obj = dict(pred)
            fp_obj['image_id'] = image_id
            fp_obj['class_name'] = CLASS_NAMES[pred['class_id']]
            fp_obj['area'] = box_area(pred['bbox'])
            fp_obj['norm_area'] = fp_obj['area'] / (IMAGE_SIZE * IMAGE_SIZE)
            fp_objects.append(fp_obj)
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
            'pred_area': box_area(pred_obj['bbox']),
            'pred_score': pred_obj['score'],
            'size_ratio': box_area(pred_obj['bbox']) / gt_obj['area'] if gt_obj['area'] > 0 else 0,
            'center_offset': np.sqrt((box_center_x(gt_obj['bbox']) - box_center_x(pred_obj['bbox']))**2 +
                                     (box_center_y(gt_obj['bbox']) - box_center_y(pred_obj['bbox']))**2)
        })
    
    error_table.append({
        'image_id': image_id,
        'gt_count': len(gt_objects),
        'pred_count': len(pred_objects),
        'tp': tp_count,
        'fp': fp_count,
        'fn': fn_count,
    })

print(f"P={len(matched_objects)/(len(matched_objects)+len(fp_objects)):.3f}, R={len(matched_objects)/(len(matched_objects)+len(fn_objects)):.3f}")
print(f"TP={len(matched_objects)}, FP={len(fp_objects)}, FN={len(fn_objects)}")

# Per-class stats
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

# === DETAILED VISUAL ANALYSIS ===

print("\n=== FALSE NEGATIVE ANALYSIS ===")
fn_by_class = defaultdict(list)
for obj in fn_objects:
    fn_by_class[obj['class_id']].append(obj)

fn_analysis = {}
for class_id in range(4):
    fn_list = fn_by_class[class_id]
    if not fn_list:
        fn_analysis[class_id] = "No FNs"
        continue
    
    areas = [obj['area'] for obj in fn_list]
    norm_areas = [obj['norm_area'] for obj in fn_list]
    
    # Size categories
    tiny = sum(1 for a in norm_areas if a < 0.0005)
    small = sum(1 for a in norm_areas if 0.0005 <= a < 0.005)
    medium = sum(1 for a in norm_areas if 0.005 <= a < 0.02)
    large = sum(1 for a in norm_areas if a >= 0.02)
    
    # Position analysis
    edge_count = sum(1 for obj in fn_list if obj['edge'])
    center_count = sum(1 for obj in fn_list if not obj['edge'])
    
    # Aspect ratio analysis
    aspect_ratios = [max(box_width(obj['bbox']), box_height(obj['bbox'])) / 
                     min(box_width(obj['bbox']), box_height(obj['bbox'])) 
                     for obj in fn_list if min(box_width(obj['bbox']), box_height(obj['bbox'])) > 0]
    
    fn_analysis[class_id] = {
        'count': len(fn_list),
        'avg_norm_area': np.mean(norm_areas),
        'tiny': tiny, 'small': small, 'medium': medium, 'large': large,
        'edge': edge_count, 'center': center_count,
        'avg_aspect_ratio': np.mean(aspect_ratios) if aspect_ratios else 0,
        'areas': sorted(norm_areas),
        'image_ids': [obj['image_id'] for obj in fn_list]
    }
    print(f"  {CLASS_NAMES[class_id]}: {len(fn_list)} FNs")
    print(f"    Size: tiny={tiny}, small={small}, medium={medium}, large={large}")
    print(f"    Position: edge={edge_count}, center={center_count}")
    print(f"    Avg norm area={np.mean(norm_areas):.5f}, avg aspect ratio={np.mean(aspect_ratios):.2f}" if aspect_ratios else "")

print("\n=== FALSE POSITIVE ANALYSIS ===")
fp_by_class = defaultdict(list)
for obj in fp_objects:
    fp_by_class[obj['class_id']].append(obj)

fp_analysis = {}
for class_id in range(4):
    fp_list = fp_by_class[class_id]
    if not fp_list:
        fp_analysis[class_id] = "No FPs"
        continue
    
    scores = [obj['score'] for obj in fp_list]
    norm_areas = [obj['norm_area'] for obj in fp_list]
    
    # Score distribution
    very_low = sum(1 for s in scores if s < 0.3)
    low = sum(1 for s in scores if 0.3 <= s < 0.5)
    medium = sum(1 for s in scores if 0.5 <= s < 0.7)
    high = sum(1 for s in scores if s >= 0.7)
    
    fp_analysis[class_id] = {
        'count': len(fp_list),
        'avg_score': np.mean(scores),
        'very_low': very_low, 'low': low, 'medium': medium, 'high': high,
        'avg_norm_area': np.mean(norm_areas),
        'scores': sorted(scores),
        'norm_areas': sorted(norm_areas),
        'image_ids': list(set(obj['image_id'] for obj in fp_list))
    }
    print(f"  {CLASS_NAMES[class_id]}: {len(fp_list)} FPs, avg_score={np.mean(scores):.3f}")
    print(f"    Score: very_low={very_low}, low={low}, medium={medium}, high={high}")

print("\n=== LOCALIZATION ANALYSIS ===")
if matched_objects:
    ious = [obj['iou'] for obj in matched_objects]
    size_ratios = [obj['size_ratio'] for obj in matched_objects]
    center_offsets = [obj['center_offset'] for obj in matched_objects]
    
    print(f"  Mean IoU: {np.mean(ious):.3f}")
    print(f"  IoU < 0.5: {sum(1 for i in ious if i < 0.5)}")
    print(f"  IoU 0.5-0.7: {sum(1 for i in ious if 0.5 <= i < 0.7)}")
    print(f"  IoU 0.7-0.9: {sum(1 for i in ious if 0.7 <= i < 0.9)}")
    print(f"  IoU >= 0.9: {sum(1 for i in ious if i >= 0.9)}")
    print(f"  Size ratio mean: {np.mean(size_ratios):.3f}")
    print(f"  Center offset mean: {np.mean(center_offsets):.1f} pixels")
    
    # Per-class localization
    for class_id in range(4):
        class_matches = [obj for obj in matched_objects if obj['class_id'] == class_id]
        if class_matches:
            class_ious = [obj['iou'] for obj in class_matches]
            class_offsets = [obj['center_offset'] for obj in class_matches]
            print(f"  {CLASS_NAMES[class_id]}: mean IoU={np.mean(class_ious):.3f}, mean offset={np.mean(class_offsets):.1f}px")

print("\n=== SMALL vs LARGE OBJECT ANALYSIS ===")
for class_id in range(4):
    gt_list = [obj for objs in gt_data.values() for obj in objs if obj['class_id'] == class_id]
    if not gt_list:
        continue
    areas = [obj['norm_area'] for obj in gt_list]
    print(f"  {CLASS_NAMES[class_id]}: avg_norm_area={np.mean(areas):.5f}, min={np.min(areas):.5f}, max={np.max(areas):.5f}")

# Save all analysis data
analysis_data = {
    'precision': len(matched_objects)/(len(matched_objects)+len(fp_objects)) if (len(matched_objects)+len(fp_objects)) > 0 else 0,
    'recall': len(matched_objects)/(len(matched_objects)+len(fn_objects)) if (len(matched_objects)+len(fn_objects)) > 0 else 0,
    'total_tp': len(matched_objects),
    'total_fp': len(fp_objects),
    'total_fn': len(fn_objects),
    'class_stats': {str(k): v for k, v in class_stats.items()},
    'fn_analysis': {str(k): v for k, v in fn_analysis.items()},
    'fp_analysis': {str(k): v for k, v in fp_analysis.items()},
    'matched_objects': matched_objects,
    'fn_objects': fn_objects,
    'fp_objects': fp_objects,
    'error_table': error_table,
    'gt_class_counts': dict(gt_class_counts),
}

with open(os.path.join(OUTPUT_DIR, 'analysis_results.json'), 'w') as f:
    json.dump(analysis_data, f, default=str)
print(f"\nAnalysis results saved to {OUTPUT_DIR}/analysis_results.json")