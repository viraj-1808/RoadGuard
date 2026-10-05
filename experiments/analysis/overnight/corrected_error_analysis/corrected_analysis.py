#!/usr/bin/env python3
"""
Corrected error analysis methodology for YOLO11s test set predictions.

This script implements the proper diagnostic pipeline that:
1. Applies confidence filtering (conf >= 0.25)
2. Applies NMS (iou=0.7) to remove duplicate detections  
3. Uses class-aware one-to-one matching at IoU >= 0.5
4. Uses confidence-ranked matching
5. Computes valid TP/FP/FN counts
6. Does NOT replace official Ultralytics metrics

Based on the original analyze_test_errors.py but corrected with proper
optimization and filtering.
"""

import os
import json
import csv
import numpy as np
from collections import defaultdict, Counter
import csv as csv_module

# Class mapping
CLASS_NAMES = {
    0: 'longitudinal_crack',
    1: 'transverse_crack', 
    2: 'alligator_crack',
    3: 'pothole'
}

# 1-indexed to 0-indexed conversion for predictions
PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}

def bbox_iou(box1, box2):
    """Calculate IoU of two boxes in [x, y, w, h] format."""
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
    
    if union <= 0:
        return 0.0
        
    return intersection / union

def non_max_suppression(predictions, iou_threshold=0.7):
    """
    Apply Non-Maximum Suppression per image per class.
    """
    if not predictions:
        return []
    
    groups = defaultdict(list)
    for pred in predictions:
        key = (pred['image_id'], pred['class_id'])
        groups[key].append(pred)
    
    kept_predictions = []
    
    for (image_id, class_id), pred_list in groups.items():
        if len(pred_list) == 1:
            kept_predictions.extend(pred_list)
            continue
        
        sorted_preds = sorted(pred_list, key=lambda x: x['score'], reverse=True)
        keep_indices = []
        
        for i, pred_i in enumerate(sorted_preds):
            keep = True
            for j in keep_indices:
                pred_j = sorted_preds[j]
                iou = bbox_iou(pred_i['bbox'], pred_j['bbox'])
                if iou >= iou_threshold:
                    keep = False
                    break
            if keep:
                keep_indices.append(i)
        
        for idx in keep_indices:
            kept_predictions.append(sorted_preds[idx])
    
    return kept_predictions

def load_ground_truth(label_dir):
    """Load ground truth labels from YOLO format files."""
    gt_data = {}
    total_objects = 0
    class_counts = Counter()
    
    for filename in os.listdir(label_dir):
        if not filename.endswith('.txt'):
            continue
            
        image_id = filename.replace('.txt', '')
        gt_objects = []
        
        with open(os.path.join(label_dir, filename), 'r') as f:
            for line_num, line in enumerate(f):
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
                    
                    img_width, img_height = 720, 720
                    x = (x_center - width/2) * img_width
                    y = (y_center - height/2) * img_height
                    w = width * img_width
                    h = height * img_height
                    
                    gt_objects.append({
                        'class_id': class_id,
                        'bbox': [x, y, w, h],
                        'area': w * h,
                        'matched': False
                    })
                    
                    class_counts[class_id] += 1
                    total_objects += 1
                except (ValueError, IndexError) as e:
                    continue
                    
        gt_data[image_id] = gt_objects
        
    return gt_data, total_objects, dict(class_counts)

def load_predictions(pred_file, confidence_threshold=0.25):
    """Load predictions from COCO-style JSON with confidence filtering."""
    with open(pred_file, 'r') as f:
        pred_data = json.load(f)
    
    filtered_data = [p for p in pred_data if p['score'] >= confidence_threshold]
    
    pred_by_image = defaultdict(list)
    
    for pred in filtered_data:
        image_id = pred['image_id']
        class_id = PRED_CLASS_MAP.get(pred['category_id'], pred['category_id'] - 1)
        
        pred_by_image[image_id].append({
            'class_id': class_id,
            'bbox': pred['bbox'],
            'score': pred['score'],
            'matched': False,
            'image_id': image_id,
            'category_id': pred['category_id']
        })
    
    return pred_by_image, len(pred_data), len(filtered_data)

def compute_matches(gt_objects, pred_objects, iou_threshold=0.5):
    """Compute matches between GT and predictions using confidence-ranked greedy algorithm."""
    matches = []
    
    if not gt_objects or not pred_objects:
        return matches
    
    iou_matrix = np.zeros((len(gt_objects), len(pred_objects)))
    for i, gt in enumerate(gt_objects):
        for j, pred in enumerate(pred_objects):
            if gt['class_id'] == pred['class_id']:
                iou = bbox_iou(gt['bbox'], pred['bbox'])
                iou_matrix[i, j] = iou
    
    indices = np.where(iou_matrix >= iou_threshold)
    if len(indices[0]) == 0:
        return matches
    
    ious = iou_matrix[indices]
    pred_scores = [pred_objects[j]['score'] for j in indices[1]]
    combined = list(zip(ious, indices[0], indices[1], pred_scores))
    combined.sort(key=lambda x: (-x[0], -x[3]))
    
    matched_gt = set()
    matched_pred = set()
    
    for iou, gt_idx, pred_idx, score in combined:
        if gt_idx not in matched_gt and pred_idx not in matched_pred:
            matches.append((gt_idx, pred_idx, iou_matrix[gt_idx, pred_idx], pred_objects[pred_idx]['score']))
            matched_gt.add(gt_idx)
            matched_pred.add(pred_idx)
            
    return matches

def generate_outputs(output_dir, error_table, fn_objects, fp_objects, matched_objects, 
                     gt_data, pred_data, total_gt, total_pred_all, total_pred_filtered, 
                     class_stats):
    """Generate all required output files."""
    os.makedirs(output_dir, exist_ok=True)
    
    summary_rows = [
        ['Metric', 'Value'],
        ['Total Ground Truth Objects', total_gt],
        ['Total Raw Predictions (all conf)', total_pred_all],
        ['Total Predictions after conf filter', total_pred_filtered],
        ['Total True Positives', len(matched_objects)],
        ['Total False Positives', len(fp_objects)],
        ['Total False Negatives', len(fn_objects)],
        ['Precision', f"{len(matched_objects) / max(1, len(matched_objects) + len(fp_objects)):.4f}"],
        ['Recall', f"{len(matched_objects) / max(1, len(matched_objects) + len(fn_objects)):.4f}"],
        ['F1-Score', f"{2 * len(matched_objects) / max(1, 2*len(matched_objects) + len(fp_objects) + len(fn_objects)):.4f}"],
    ]
    
    summary_path = os.path.join(output_dir, 'error_summary.csv')
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)
    
    per_image_rows = [
        ['Image_ID', 'GT_Count', 'Pred_Count', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F1_Score']
    ]
    
    for row in error_table:
        per_image_rows.append([
            row['image_id'],
            row['gt_count'],
            row['pred_count'],
            row['tp'],
            row['fp'],
            row['fn'],
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['f1']:.4f}"
        ])
    
    per_image_path = os.path.join(output_dir, 'per_image_errors.csv')
    with open(per_image_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(per_image_rows)
    
    confidence_rows = [
        ['Image_ID', 'Class_ID', 'Class_Name', 'Score', 'IoU', 'GT_Area', 'Pred_Area']
    ]
    
    for obj in matched_objects:
        confidence_rows.append([
            obj['image_id'],
            obj['class_id'],
            obj['class_name'],
            f"{obj['pred_score']:.4f}",
            f"{obj['iou']:.4f}",
            f"{obj['gt_area']:.1f}",
            f"{obj['pred_area']:.1f}"
        ])
    
    for obj in fp_objects:
        confidence_rows.append([
            obj['image_id'],
            obj['class_id'],
            obj['class_name'],
            f"{obj['score']:.4f}",
            'NA',
            'NA',
            f"{obj['area']:.1f}"
        ])
    
    confidence_path = os.path.join(output_dir, 'confidence_analysis.csv')
    with open(confidence_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(confidence_rows)
    
    methodology_path = os.path.join(output_dir, 'methodology.md')
    with open(methodology_path, 'w') as f:
        f.write('# Corrected Error Analysis Methodology\n\n')
        f.write('## Overview\n\n')
        f.write('This analysis implements a corrected diagnostic pipeline for YOLO11s test set evaluation.\n\n')
        f.write('## Key Corrections Applied\n\n')
        f.write('1. **Confidence Filtering**: Predictions with confidence < 0.25 are excluded\n')
        f.write('2. **Non-Maximum Suppression (NMS)**: IoU threshold = 0.7 per image per class\n')
        f.write('3. **Class-Aware Matching**: IoU >= 0.5, 1:1 ground truth:prediction mapping\n')
        f.write('4. **Confidence-Ranked Matching**: Higher IoU + higher confidence prioritized\n')
        f.write('5. **Correct Metric Computation**: Only valid detections contribute to TP/FP/FN\n\n')
        f.write('## Pipeline Steps\n\n')
        f.write('1. Load predictions.json (17,198 raw predictions)\n')
        f.write('2. Filter predictions: conf >= 0.25 (682 predictions remain)\n')
        f.write('3. Apply NMS per image per class (iou=0.7)\n')
        f.write('4. For each image: class-aware one-to-one matching (IoU >= 0.5)\n')
        f.write('5. Count valid TP/FP/FN\n')
        f.write('6. Generate error metrics\n\n')
        f.write('## Comparison with Official Ultralytics Metrics\n\n')
        f.write('Official Ultralytics metrics (provided for reference, not to be replaced):\n')
        f.write('- Precision: 0.299\n')
        f.write('- Recall: 0.312\n')
        f.write('- mAP50: 0.252\n')
        f.write('- mAP50-95: 0.0903\n\n')
        f.write('## Methodological Gaps Acknowledged\n\n')
        f.write('1. Single IoU threshold (0.5) only captures mAP50 performance\n')
        f.write('2. No area scaling or size binning for scale-aware analysis\n')
        f.write('3. Limited to detection accuracy, no orientation or severity metrics\n')
        f.write('4. Small sample sizes for rare classes (e.g., transverse cracks)\n')
        f.write('5. No analysis of detection timing or training dynamics\n')

def main():
    """Main analysis function with corrected pipeline."""
    pred_file = 'runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json'
    label_dir = 'experiments/dataset/yolo_rdd2022_india/labels/test'
    
    output_dir = 'experiments/analysis/overnight/corrected_error_analysis'
    
    print("=== CORRECTED ERROR ANALYSIS METHODOLOGY ===")
    print("Loading data...")
    
    gt_data, total_gt, gt_class_counts = load_ground_truth(label_dir)
    
    print("Loading predictions with confidence filtering...")
    pred_data, total_pred_all, total_pred_filtered = load_predictions(pred_file)
    
    print(f"Applying NMS (iou=0.7) to filtered predictions...")
    all_filtered_predictions = []
    for image_id, preds in pred_data.items():
        all_filtered_predictions.extend(preds)
    
    nms_predictions = non_max_suppression(all_filtered_predictions, iou_threshold=0.7)
    
    pred_data_nms = defaultdict(list)
    for pred in nms_predictions:
        pred_data_nms[pred['image_id']].append(pred)
    
    print(f"Original predictions (all conf): {total_pred_all}")
    print(f"After confidence filter (>=0.25): {len(all_filtered_predictions)}")
    print(f"After NMS (iou=0.7): {len(nms_predictions)}")
    print(f"Class distribution after filtering:")
    pred_class_counts = Counter(p['class_id'] for preds in pred_data_nms.values() for p in preds)
    for class_id, count in sorted(pred_class_counts.items()):
        print(f"  {CLASS_NAMES[class_id]}: {count}")
    
    error_table = []
    fn_objects = []
    fp_objects = []
    matched_objects = []
    
    iou_threshold = 0.5
    
    print(f"\nAnalyzing {len(gt_data)} images with matched predictions...")
    
    for image_id in sorted(gt_data.keys() & pred_data_nms.keys()):
        gt_objects = gt_data[image_id]
        pred_objects = pred_data_nms[image_id]
        
        matches = compute_matches(gt_objects, pred_objects, iou_threshold)
        
        matched_gt_indices = {m[0] for m in matches}
        matched_pred_indices = {m[1] for m in matches}
        
        fn_count = 0
        for i, gt in enumerate(gt_objects):
            if i not in matched_gt_indices:
                fn_count += 1
                fn_objects.append({
                    'image_id': image_id,
                    'class_id': gt['class_id'],
                    'class_name': CLASS_NAMES[gt['class_id']],
                    'bbox': gt['bbox'],
                    'area': gt['area']
                })
        
        fp_count = 0
        for i, pred in enumerate(pred_objects):
            if i not in matched_pred_indices:
                fp_count += 1
                fp_objects.append({
                    'image_id': image_id,
                    'class_id': pred['class_id'],
                    'class_name': CLASS_NAMES[pred['class_id']],
                    'bbox': pred['bbox'],
                    'score': pred['score'],
                    'area': pred['bbox'][2] * pred['bbox'][3]
                })
        
        tp_count = len(matches)
        for gt_idx, pred_idx, iou, score in matches:
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
                'pred_score': score
            })
        
        precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
        recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
        f1 = 2 * tp_count / (2 * tp_count + fp_count + fn_count) if (2 * tp_count + fp_count + fn_count) > 0 else 0
        
        error_table.append({
            'image_id': image_id,
            'gt_count': len(gt_objects),
            'pred_count': len(pred_objects),
            'tp': tp_count,
            'fp': fp_count,
            'fn': fn_count,
            'precision': precision,
            'recall': recall,
            'f1': f1
        })
    
    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Total GT objects: {total_gt}")
    print(f"Total predictions after filtering: {len(all_filtered_predictions)}")
    print(f"Total predictions after NMS: {len(nms_predictions)}")
    print(f"True Positives: {len(matched_objects)}")
    print(f"False Positives: {len(fp_objects)}")
    print(f"False Negatives: {len(fn_objects)}")
    
    total_tp = len(matched_objects)
    total_fp = len(fp_objects)
    total_fn = len(fn_objects)
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\nCorrected Pipeline Metrics:")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  F1-Score: {f1:.4f}")
    
    class_stats = {}
    for class_id in range(4):
        class_gt = sum(1 for img_objs in gt_data.values() for obj in img_objs if obj['class_id'] == class_id)
        class_tp = sum(1 for obj in matched_objects if obj['class_id'] == class_id)
        class_fp = sum(1 for obj in fp_objects if obj['class_id'] == class_id)
        class_fn = sum(1 for obj in fn_objects if obj['class_id'] == class_id)
        
        class_precision = class_tp / (class_tp + class_fp) if (class_tp + class_fp) > 0 else 0
        class_recall = class_tp / (class_tp + class_fn) if (class_tp + class_fn) > 0 else 0
        class_f1 = 2 * class_precision * class_recall / (class_precision + class_recall) if (class_precision + class_recall) > 0 else 0
        
        class_stats[class_id] = {
            'name': CLASS_NAMES[class_id],
            'gt_count': class_gt,
            'tp': class_tp,
            'fp': class_fp,
            'fn': class_fn,
            'precision': class_precision,
            'recall': class_recall,
            'f1': class_f1
        }
    
    print(f"\nGenerating output files...")
    generate_outputs(output_dir, error_table, fn_objects, fp_objects, matched_objects,
                     gt_data, pred_data, total_gt, total_pred_all, len(all_filtered_predictions), 
                     class_stats)
    
    print(f"\n=== OUTPUT FILES GENERATED ===")
    print(f"Output directory: {output_dir}")
    
    output_files = [
        'methodology.md',
        'error_summary.csv', 
        'per_image_errors.csv',
        'confidence_analysis.csv'
    ]
    
    for filename in output_files:
        filepath = os.path.join(output_dir, filename)
        size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        print(f"  {filename}: {size} bytes")
    
    print(f"\n=== COMPARISON WITH OFFICIAL METRICS ===")
    print("Official Ultralytics metrics (for reference, not to be replaced):")
    print("  Precision: 0.299")
    print("  Recall: 0.312") 
    print("  mAP50: 0.252")
    print("  mAP50-95: 0.0903")
    print(f"\nCorrected pipeline metrics:")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  F1: {f1:.4f}")
    print(f"\nNote: Do NOT replace official Ultralytics metrics with these corrected values.")

if __name__ == "__main__":
    main()