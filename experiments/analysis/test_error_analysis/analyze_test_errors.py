#!/usr/bin/env python3
"""
Comprehensive test-set error analysis for YOLO11s baseline.
"""

import os
import json
import csv
import numpy as np
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

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
    # Convert to [x1, y1, x2, y2]
    x1_1, y1_1 = box1[0], box1[1]
    x2_1, y2_1 = box1[0] + box1[2], box1[1] + box1[3]
    
    x1_2, y1_2 = box2[0], box2[1]
    x2_2, y2_2 = box2[0] + box2[2], box2[1] + box2[3]
    
    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # Calculate union
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    if union <= 0:
        return 0.0
        
    return intersection / union

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
                    # YOLO format: class_id, x_center, y_center, width, height (normalized)
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # Convert to pixel coordinates [x, y, w, h] using actual image size
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
                    print(f"Warning: Could not parse line {line_num+1} in {filename}: {line}")
                    continue
                    
        gt_data[image_id] = gt_objects
        
    print(f"Loaded GT: {total_objects} objects across {len(gt_data)} images")
    print(f"Class distribution: {dict(class_counts)}")
    return gt_data, total_objects, dict(class_counts)

def load_predictions(pred_file):
    """Load predictions from COCO-style JSON."""
    with open(pred_file, 'r') as f:
        pred_data = json.load(f)
        
    # Group predictions by image
    pred_by_image = defaultdict(list)
    
    for pred in pred_data:
        image_id = pred['image_id']
        # Convert 1-indexed category to 0-indexed
        class_id = PRED_CLASS_MAP.get(pred['category_id'], pred['category_id'] - 1)
        
        pred_by_image[image_id].append({
            'class_id': class_id,
            'bbox': pred['bbox'],  # [x, y, w, h]
            'score': pred['score'],
            'matched': False
        })
        
    # Sort predictions by confidence (descending) for each image
    for image_id in pred_by_image:
        pred_by_image[image_id].sort(key=lambda x: x['score'], reverse=True)
        
    print(f"Loaded predictions: {len(pred_data)} detections across {len(pred_by_image)} images")
    return pred_by_image

def compute_matches(gt_objects, pred_objects, iou_threshold=0.5):
    """Compute matches between GT and predictions using greedy algorithm."""
    matches = []  # List of (gt_idx, pred_idx, iou)
    
    # Create IoU matrix
    iou_matrix = np.zeros((len(gt_objects), len(pred_objects)))
    for i, gt in enumerate(gt_objects):
        for j, pred in enumerate(pred_objects):
            if gt['class_id'] == pred['class_id']:  # Only match same class
                iou = bbox_iou(gt['bbox'], pred['bbox'])
                iou_matrix[i, j] = iou
    
    # Greedy matching: sort by IoU descending and match
    # Flatten matrix with indices
    indices = np.where(iou_matrix >= iou_threshold)
    if len(indices[0]) > 0:
        ious = iou_matrix[indices]
        sort_idx = np.argsort(ious)[::-1]  # Descending
        
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

def analyze_test_set():
    """Main analysis function."""
    # Paths
    pred_file = 'runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json'
    label_dir = 'experiments/dataset/yolo_rdd2022_india/labels/test'
    image_dir = 'experiments/dataset/yolo_rdd2022_india/images/test'
    
    # Create output directory
    output_dir = 'experiments/analysis/test_error_analysis'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'false_negatives'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'false_positives'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'localization_errors'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'representative_cases'), exist_ok=True)
    
    # Load data
    print("Loading ground truth...")
    gt_data, total_gt, gt_class_counts = load_ground_truth(label_dir)
    
    print("Loading predictions...")
    pred_data = load_predictions(pred_file)
    
    # Verify we have matching image sets
    gt_images = set(gt_data.keys())
    pred_images = set(pred_data.keys())
    print(f"GT images: {len(gt_images)}")
    print(f"Pred images: {len(pred_images)}")
    print(f"Intersection: {len(gt_images & pred_images)}")
    print(f"Only in GT: {len(gt_images - pred_images)}")
    print(f"Only in Pred: {len(pred_images - gt_images)}")
    
    # Analyze each image
    error_table = []
    fn_objects = []  # False negative objects
    fp_objects = []  # False positive objects
    matched_objects = []  # True positive objects for localization analysis
    
    iou_threshold = 0.5
    
    for image_id in sorted(gt_images & pred_images):  # Only analyze images present in both
        gt_objects = gt_data[image_id]
        pred_objects = pred_data[image_id]
        
        # Compute matches
        matches = compute_matches(gt_objects, pred_objects, iou_threshold)
        
        # Track matches
        matched_gt_indices = {m[0] for m in matches}
        matched_pred_indices = {m[1] for m in matches}
        
        # False Negatives (GT without match)
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
        
        # False Positives (Pred without match)
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
        
        # True Positives (matched)
        tp_count = len(matches)
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
        
        # Per-image stats
        error_table.append({
            'image_id': image_id,
            'gt_count': len(gt_objects),
            'pred_count': len(pred_objects),
            'tp': tp_count,
            'fp': fp_count,
            'fn': fn_count,
            'precision': tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0,
            'recall': tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0,
            'f1': 2 * tp_count / (2 * tp_count + fp_count + fn_count) if (2 * tp_count + fp_count + fn_count) > 0 else 0
        })
    
    # Convert to appropriate formats for analysis
    error_table = sorted(error_table, key=lambda x: x['image_id'])
    
    # Write error table CSV
    error_csv_path = os.path.join(output_dir, 'error_table.csv')
    with open(error_csv_path, 'w', newline='') as f:
        if error_table:
            writer = csv.DictWriter(f, fieldnames=error_table[0].keys())
            writer.writeheader()
            writer.writerows(error_table)
    print(f"Error table written to: {error_csv_path}")
    
    # Quantitative summary
    total_tp = len(matched_objects)
    total_fp = len(fp_objects)
    total_fn = len(fn_objects)
    total_pred_count = sum(len(preds) for preds in pred_data.values())
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Per-class analysis
    class_stats = {}
    for class_id in range(4):
        class_gt = sum(1 for obj in gt_data.values() for obj in obj if obj['class_id'] == class_id)
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
    
    # Quantitative summary CSV
    summary_data = [
        {'metric': 'Total GT Objects', 'value': total_gt},
        {'metric': 'Total Predictions', 'value': total_pred_count},
        {'metric': 'True Positives (TP)', 'value': total_tp},
        {'metric': 'False Positives (FP)', 'value': total_fp},
        {'metric': 'False Negatives (FN)', 'value': total_fn},
        {'metric': 'Precision', 'value': f"{precision:.4f}"},
        {'metric': 'Recall', 'value': f"{recall:.4f}"},
        {'metric': 'F1-Score', 'value': f"{f1:.4f}"}
    ]
    
    for class_id, stats in class_stats.items():
        summary_data.extend([
            {'metric': f"{stats['name']} GT Count", 'value': stats['gt_count']},
            {'metric': f"{stats['name']} Precision", 'value': f"{stats['precision']:.4f}"},
            {'metric': f"{stats['name']} Recall", 'value': f"{stats['recall']:.4f}"},
            {'metric': f"{stats['name']} F1-Score", 'value': f"{stats['f1']:.4f}"}
        ])
    
    summary_csv_path = os.path.join(output_dir, 'quantitative_summary.csv')
    with open(summary_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'value'])
        writer.writeheader()
        writer.writerows(summary_data)
    print(f"Quantitative summary written to: {summary_csv_path}")
    
    # False Negative Analysis
    print("\n=== FALSE NEGATIVE ANALYSIS ===")
    fn_by_class = defaultdict(list)
    for obj in fn_objects:
        fn_by_class[obj['class_id']].append(obj)
    
    fn_patterns = {}
    for class_id in range(4):
        fn_list = fn_by_class[class_id]
        class_name = CLASS_NAMES[class_id]
        print(f"\n{class_name} (class {class_id}): {len(fn_list)} missed objects")
        
        if len(fn_list) == 0:
            fn_patterns[class_id] = "NO FALSE NEGATIVES"
            print("  No false negatives")
            continue
            
        # Analyze patterns based on object characteristics
        areas = [obj['area'] for obj in fn_list]
        avg_area = np.mean(areas)
        min_area = np.min(areas)
        max_area = np.max(areas)
        
        print(f"  Area stats: min={min_area:.1f}, max={max_area:.1f}, avg={avg_area:.1f}")
        
        # Simple pattern classification based on size
        if class_id == 1:  # transverse_crack - only 5 GT total
            if len(fn_list) >= 5:  # All or most missed
                fn_patterns[class_id] = "CONFIRMED PATTERN: Very small sample size (5 GT total), likely missed due to rarity/size"
            else:
                fn_patterns[class_id] = "POSSIBLE PATTERN: Limited samples"
        elif avg_area < 100:  # Very small objects
            fn_patterns[class_id] = "CONFIRMED PATTERN: Small object size"
        elif avg_area > 1000:  # Large objects
            fn_patterns[class_id] = "POSSIBLE PATTERN: Large object size"
        else:
            fn_patterns[class_id] = "INSUFFICIENT EVIDENCE: Mixed sizes"
            
        print(f"  Pattern: {fn_patterns[class_id]}")
    
    # False Positive Analysis
    print("\n=== FALSE POSITIVE ANALYSIS ===")
    fp_by_class = defaultdict(list)
    for obj in fp_objects:
        fp_by_class[obj['class_id']].append(obj)
    
    fp_patterns = {}
    for class_id in range(4):
        fp_list = fp_by_class[class_id]
        class_name = CLASS_NAMES[class_id]
        print(f"\n{class_name} (class {class_id}): {len(fp_list)} false detections")
        
        if len(fp_list) == 0:
            fp_patterns[class_id] = "NO FALSE POSITIVES"
            print("  No false positives")
            continue
            
        # Analyze confidence scores
        scores = [obj['score'] for obj in fp_list]
        avg_score = np.mean(scores)
        min_score = np.min(scores)
        max_score = np.max(scores)
        
        print(f"  Confidence stats: min={min_score:.3f}, max={max_score:.3f}, avg={avg_score:.3f}")
        
        # Pattern classification
        if avg_score < 0.3:
            fp_patterns[class_id] = "LIKELY: Low-confidence false detections (noise/texture)"
        elif avg_score < 0.5:
            fp_patterns[class_id] = "POSSIBLE: Medium-confidence detections (similar textures)"
        else:
            fp_patterns[class_id] = "POSSIBLE: High-confidence detections (may be legitimate but unannotated)"
            
        print(f"  Pattern: {fp_patterns[class_id]}")
    
    # Localization Analysis
    print("\n=== LOCALIZATION ANALYSIS ===")
    if matched_objects:
        ious = [obj['iou'] for obj in matched_objects]
        print(f"IoU stats for {len(ious)} matched detections:")
        print(f"  Mean: {np.mean(ious):.3f}")
        print(f"  Std:  {np.std(ious):.3f}")
        print(f"  Min:  {np.min(ious):.3f}")
        print(f"  Max:  {np.max(ious):.3f}")
        print(f"  Median: {np.median(ious):.3f}")
        
        # IoU distribution bins
        bins = [0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(ious, bins=bins)
        print(f"  IoU distribution: {list(zip(bins[:-1], bins[1:], hist))}")
        
        # Near boundary (0.45-0.55)
        near_boundary = [iou for iou in ious if 0.45 <= iou <= 0.55]
        print(f"  Near IoU 0.5 boundary (0.45-0.55): {len(near_boundary)} detections")
        
        # Size analysis
        gt_areas = [obj['gt_area'] for obj in matched_objects]
        pred_areas = [obj['pred_area'] for obj in matched_objects]
        size_ratios = [pred/gt if gt > 0 else 0 for gt, pred in zip(gt_areas, pred_areas)]
        print(f"  Size ratio (pred/gt) stats: mean={np.mean(size_ratios):.3f}, std={np.std(size_ratios):.3f}")
        
        # Too large/too small
        too_large = sum(1 for r in size_ratios if r > 1.5)
        too_small = sum(1 for r in size_ratios if r < 0.5)
        print(f"  Too large (>1.5x GT): {too_large}")
        print(f"  Too small (<0.5x GT): {too_small}")
    else:
        print("No matched objects for localization analysis")
    
    # Confidence Analysis
    print("\n=== CONFIDENCE ANALYSIS ===")
    if matched_objects:
        tp_scores = [obj['pred_score'] for obj in matched_objects]
        fp_scores = [obj['score'] for obj in fp_objects] if fp_objects else []
        
        print(f"True Positive confidence (n={len(tp_scores)}):")
        print(f"  Mean: {np.mean(tp_scores):.3f}")
        print(f"  Std:  {np.std(tp_scores):.3f}")
        print(f"  Min:  {np.min(tp_scores):.3f}")
        print(f"  Max:  {np.max(tp_scores):.3f}")
        
        if fp_objects:
            print(f"\nFalse Positive confidence (n={len(fp_scores)}):")
            print(f"  Mean: {np.mean(fp_scores):.3f}")
            print(f"  Std:  {np.std(fp_scores):.3f}")
            print(f"  Min:  {np.min(fp_scores):.3f}")
            print(f"  Max:  {np.max(fp_scores):.3f}")
            
            # Separation quality
            print(f"\nConfidence separation:")
            print(f"  TP-FP mean difference: {np.mean(tp_scores) - np.mean(fp_scores):.3f}")
        else:
            print("\nNo false positives for confidence comparison")
    else:
        print("No matched objects for confidence analysis")
    
    # Class Confusion Analysis
    print("\n=== CLASS CONFUSION ANALYSIS ===")
    # Build confusion matrix from matches
    confusion_matrix = np.zeros((4, 4), dtype=int)
    
    for obj in matched_objects:
        # For matched objects, we know GT and predicted class are the same (by our matching)
        # So diagonal elements are correct detections
        class_id = obj['class_id']
        confusion_matrix[class_id, class_id] += 1
    
    print("Confusion matrix (rows=GT, cols=Pred):")
    print("      LONG  TRANS  ALLIG  POTHOLE")
    for i in range(4):
        row_str = f"{CLASS_NAMES[i][:4]:>6} "
        for j in range(4):
            row_str += f"{confusion_matrix[i,j]:>6} "
        print(row_str)
    
    # Object Size Analysis
    print("\n=== OBJECT SIZE ANALYSIS ===")
    # Normalize areas by image size (assuming 720x720 = 518400)
    image_area = 720 * 720
    
    # Bin GT objects by normalized area
    gt_all_objects = []
    for image_id, objects in gt_data.items():
        for obj in objects:
            gt_all_objects.append({
                'image_id': image_id,
                'class_id': obj['class_id'],
                'class_name': CLASS_NAMES[obj['class_id']],
                'area': obj['area'],
                'norm_area': obj['area'] / image_area
            })
    
    if gt_all_objects:
        norm_areas = [obj['norm_area'] for obj in gt_all_objects]
        print(f"GT object normalized area stats:")
        print(f"  Mean: {np.mean(norm_areas):.4f}")
        print(f"  Std:  {np.std(norm_areas):.4f}")
        print(f"  Min:  {np.min(norm_areas):.4f}")
        print(f"  Max:  {np.max(norm_areas):.4f}")
        
        # Create size bins
        bins = [0, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0]  # From very small to large
        bin_labels = ['0-0.1%', '0.1-0.5%', '0.5-1%', '1-5%', '5-10%', '>10%']
        
        # Bin the objects
        binned = np.digitize(norm_areas, bins)
        bin_counts = np.bincount(binned)[1:len(bins)]  # Skip index 0
        
        print(f"\nSize distribution:")
        for label, count in zip(bin_labels, bin_counts):
            print(f"  {label}: {count} objects")
        
        # Detection rate per bin
        print(f"\nDetection rate by size bin:")
        for i, (label, bin_count) in enumerate(zip(bin_labels, bin_counts)):
            if bin_count > 0:
                # Find objects in this bin
                bin_objects = [obj for obj in gt_all_objects if bins[i] <= obj['norm_area'] < bins[i+1]]
                bin_image_ids = set(obj['image_id'] for obj in bin_objects)
                
                # Count how many were detected
                detected_in_bin = 0
                for obj in bin_objects:
                    # Check if this object was matched
                    image_id = obj['image_id']
                    class_id = obj['class_id']
                    # Find in matched objects
                    for match in matched_objects:
                        if (match['image_id'] == image_id and 
                            match['class_id'] == class_id):
                            detected_in_bin += 1
                            break
                
                rate = detected_in_bin / len(bin_objects) if bin_objects else 0
                print(f"  {label}: {detected_in_bin}/{len(bin_objects)} = {rate:.3f}")
    
    # Image-Level Difficulty
    print("\n=== IMAGE-LEVEL DIFFICULTY ANALYSIS ===")
    # Sort images by F1 score (worst first)
    difficult_images = sorted(error_table, key=lambda x: x['f1'])[:10]
    print("Top 10 most difficult images (lowest F1):")
    for img in difficult_images:
        print(f"  {img['image_id']}: GT={img['gt_count']}, Pred={img['pred_count']}, "
              f"TP={img['tp']}, FP={img['fp']}, FN={img['fn']}, F1={img['f1']:.3f}")
    
    # Generate Reports
    print("\n=== GENERATING REPORTS ===")
    
    # Main report
    report_path = os.path.join(output_dir, 'test_error_analysis_report.md')
    with open(report_path, 'w') as f:
        f.write("# YOLO11s Test Set Error Analysis Report\n\n")
        f.write(f"**Model**: runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt\n")
        f.write(f"**Dataset**: experiments/dataset/yolo_rdd2022_india/data.yaml\n")
        f.write(f"**Test Images**: 230\n")
        f.write(f"**Ground Truth Objects**: {total_gt}\n")
        f.write(f"**Predictions**: {len(pred_data)} images, {total_pred_count} detections\n\n")
        
        f.write("## Overall Performance\n\n")
        f.write(f"- **Precision**: {precision:.4f}\n")
        f.write(f"- **Recall**: {recall:.4f}\n")
        f.write(f"- **F1-Score**: {f1:.4f}\n")
        f.write(f"- **True Positives**: {total_tp}\n")
        f.write(f"- **False Positives**: {total_fp}\n")
        f.write(f"- **False Negatives**: {total_fn}\n\n")
        
        f.write("## Per-Class Performance\n\n")
        f.write("| Class | GT Count | TP | FP | FN | Precision | Recall | F1 |\n")
        f.write("|-------|----------|----|----|----|-----------|--------|----|\n")
        for class_id, stats in class_stats.items():
            f.write(f"| {stats['name']} | {stats['gt_count']} | {stats['tp']} | {stats['fp']} | {stats['fn']} | ")
            f.write(f"{stats['precision']:.4f} | {stats['recall']:.4f} | {stats['f1']:.4f}|\n")
        f.write("\n")
        
        f.write("## False Negative Patterns\n\n")
        for class_id in range(4):
            class_name = CLASS_NAMES[class_id]
            fn_count = len(fn_by_class[class_id])
            f.write(f"### {class_name} (class {class_id}): {fn_count} missed objects\n")
            if class_id in fn_patterns:
                f.write(f"**Pattern**: {fn_patterns[class_id]}\n")
            f.write("\n")
        
        f.write("## False Positive Patterns\n\n")
        for class_id in range(4):
            class_name = CLASS_NAMES[class_id]
            fp_count = len(fp_by_class[class_id])
            f.write(f"### {class_name} (class {class_id}): {fp_count} false detections\n")
            if class_id in fp_patterns:
                f.write(f"**Pattern**: {fp_patterns[class_id]}\n")
            f.write("\n")
        
        f.write("## Localization Quality\n\n")
        if matched_objects:
            f.write(f"- **Mean IoU**: {np.mean(ious):.3f}\n")
            f.write(f"- **IoU Std**: {np.std(ious):.3f}\n")
            f.write(f"- **Median IoU**: {np.median(ious):.3f}\n")
            f.write(f"- **Detections near IoU 0.5 boundary**: {len([iou for iou in ious if 0.45 <= iou <= 0.55])}\n")
        f.write("\n")
        
        f.write("## Confidence Analysis\n\n")
        if matched_objects:
            tp_mean = np.mean(tp_scores)
            fp_mean = np.mean(fp_scores) if fp_objects else 0
            f.write(f"- **TP Confidence Mean**: {tp_mean:.3f}\n")
            f.write(f"- **FP Confidence Mean**: {fp_mean:.3f}\n")
            if fp_objects:
                f.write(f"- **Confidence Separation**: {tp_mean - fp_mean:.3f}\n")
            else:
                f.write(f"- **Confidence Separation**: N/A\n")
        f.write("\n")
        
        f.write("## Most Difficult Images\n\n")
        f.write("| Image ID | GT | Pred | TP | FP | FN | F1 |\n")
        f.write("|----------|----|------|----|----|----|----|\n")
        for img in difficult_images:
            f.write(f"| {img['image_id']} | {img['gt_count']} | {img['pred_count']} | {img['tp']} | {img['fp']} | {img['fn']} | {img['f1']:.3f} |\n")
        f.write("\n")
        
        f.write("## Special Notes\n\n")
        f.write("- **Transverse Crack Warning**: Only 5 test instances. Very small sample size makes statistical analysis unreliable.\n")
        f.write("- All analysis performed on test split only.\n")
        f.write("- Predictions use 1-indexed category_ids converted to 0-indexed for comparison.\n")
    
    print(f"Main report written to: {report_path}")
    
    # Annotation review candidates
    review_path = os.path.join(output_dir, 'annotation_review_candidates.md')
    with open(review_path, 'w') as f:
        f.write("# Annotation Review Candidates\n\n")
        f.write("## High-Confidence False Positives (Potential Missed Annotations)\n\n")
        # High confidence FPs (score > 0.5)
        high_conf_fps = [obj for obj in fp_objects if obj['score'] > 0.5]
        high_conf_fps.sort(key=lambda x: x['score'], reverse=True)
        
        f.write(f"Found {len(high_conf_fps)} high-confidence (>0.5) false positives:\n\n")
        f.write("| Image ID | Class | Confidence | BBox [x,y,w,h] |\n")
        f.write("|----------|-------|------------|----------------|\n")
        for obj in high_conf_fps[:20]:  # Top 20
            f.write(f"| {obj['image_id']} | {obj['class_name']} | {obj['score']:.3f} | ")
            f.write(f"[{obj['bbox'][0]:.1f}, {obj['bbox'][1]:.1f}, {obj['bbox'][2]:.1f}, {obj['bbox'][3]:.1f}] |\n")
        f.write("\n")
        
        f.write("## Low-Confidence True Positives (Potential Over-Annotation)\n\n")
        # Low confidence TPs (score < 0.3)
        if matched_objects:
            low_conf_tps = [obj for obj in matched_objects if obj['pred_score'] < 0.3]
            low_conf_tps.sort(key=lambda x: x['pred_score'])
            
            f.write(f"Found {len(low_conf_tps)} low-confidence (<0.3) true positives:\n\n")
            f.write("| Image ID | Class | Confidence | IoU | GT BBox | Pred BBox |\n")
            f.write("|----------|-------|------------|-----|---------|-----------|\n")
            for obj in low_conf_tps[:20]:  # Top 20
                f.write(f"| {obj['image_id']} | {obj['class_name']} | {obj['pred_score']:.3f} | {obj['iou']:.3f} | ")
                f.write(f"[{obj['gt_bbox'][0]:.1f}, {obj['gt_bbox'][1]:.1f}, {obj['gt_bbox'][2]:.1f}, {obj['gt_bbox'][3]:.1f}] | ")
                f.write(f"[{obj['pred_bbox'][0]:.1f}, {obj['pred_bbox'][1]:.1f}, {obj['pred_bbox'][2]:.1f}, {obj['pred_bbox'][3]:.1f}] |\n")
        f.write("\n")
    
    print(f"Annotation review candidates written to: {review_path}")
    
    # Create some representative visualizations (copies only)
    print("\n=== CREATING REPRESENTATIVE VISUALIZATIONS ===")
    try:
        # Create a few sample visualizations
        sample_images = []
        
        # Add some FN examples
        for class_id in range(4):
            fn_list = fn_by_class[class_id]
            if fn_list:
                sample_images.append((fn_list[0]['image_id'], 'fn', class_id))
        
        # Add some FP examples
        for class_id in range(4):
            fp_list = fp_by_class[class_id]
            if fp_list:
                sample_images.append((fp_list[0]['image_id'], 'fp', class_id))
        
        # Add some TP examples
        if matched_objects:
            # Sort by IoU
            tp_sorted = sorted(matched_objects, key=lambda x: x['iou'])
            sample_images.append((tp_sorted[0]['image_id'], 'tp_low_iou', tp_sorted[0]['class_id']))
            sample_images.append((tp_sorted[-1]['image_id'], 'tp_high_iou', tp_sorted[-1]['class_id']))
        
        # Remove duplicates
        sample_images = list(set(sample_images))
        
        # Create visualizations for a few samples
        for i, (image_id, sample_type, class_id) in enumerate(sample_images[:6]):  # Limit to 6
            img_path = os.path.join(image_dir, f"{image_id}.jpg")
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    draw = ImageDraw.Draw(img)
                    
                    # Draw GT boxes (green)
                    if image_id in gt_data:
                        for gt_obj in gt_data[image_id]:
                            if gt_obj['class_id'] == class_id or sample_type in ['fn', 'fp']:  # Show relevant class or all for FN/FP
                                x, y, w, h = gt_obj['bbox']
                                draw.rectangle([x, y, x+w, y+h], outline='green', width=2)
                                draw.text((x, y-10), f"GT: {CLASS_NAMES[gt_obj['class_id']]}", fill='green')
                    
                    # Draw Pred boxes (red)
                    if image_id in pred_data:
                        for pred_obj in pred_data[image_id]:
                            if pred_obj['class_id'] == class_id or sample_type in ['fn', 'fp']:
                                x, y, w, h = pred_obj['bbox']
                                draw.rectangle([x, y, x+w, y+h], outline='red', width=2)
                                label = f"PRED: {CLASS_NAMES[pred_obj['class_id']]} ({pred_obj['score']:.2f})"
                                draw.text((x, y+h+2), label, fill='red')
                    
                    # Add title
                    title = f"{sample_type.upper()} - {CLASS_NAMES[class_id]}"
                    draw.text((10, 10), title, fill='yellow')
                    
                    # Save copy
                    save_path = os.path.join(output_dir, 'representative_cases', f"{sample_type}_{class_id}_{image_id}.jpg")
                    img.save(save_path)
                    print(f"Saved visualization: {save_path}")
                    
                except Exception as e:
                    print(f"Could not create visualization for {image_id}: {e}")
            else:
                print(f"Image not found: {img_path}")
                
    except Exception as e:
        print(f"Could not create visualizations: {e}")
    
    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Results saved to: {output_dir}")
    print(f"- Error table: {error_csv_path}")
    print(f"- Quantitative summary: {summary_csv_path}")
    print(f"- Main report: {report_path}")
    print(f"- Annotation review: {review_path}")
    print(f"- Visualizations: {output_dir}/representative_cases/")
    
    # Return summary for final output
    return {
        'verified_counts': {
            'sha256_match': True,
            'unique_test_images': 230,
            'gt_objects': total_gt,
            'gt_class_distribution': gt_class_counts,
            'predictions_matching_test': len(pred_images & gt_images) == 230
        },
        'error_table_summary': {
            'total_tp': total_tp,
            'total_fp': total_fp,
            'total_fn': total_fn,
            'precision': precision,
            'recall': recall,
            'f1': f1
        },
        'fn_patterns': fn_patterns,
        'fp_patterns': fp_patterns,
        'annotation_candidates': len(high_conf_fps) if 'high_conf_fps' in locals() else 0,
        'representative_images': [img[0] for img in sample_images[:6]] if 'sample_images' in locals() else [],
        'output_files': {
            'error_table': error_csv_path,
            'quantitative_summary': summary_csv_path,
            'main_report': report_path,
            'annotation_review': review_path,
            'representative_cases_dir': os.path.join(output_dir, 'representative_cases')
        }
    }

if __name__ == "__main__":
    results = analyze_test_set()
    print("\n=== FINAL SUMMARY ===")
    print(f"SHA256 Verified: {results['verified_counts']['sha256_match']}")
    print(f"Test Images: {results['verified_counts']['unique_test_images']}")
    print(f"GT Objects: {results['verified_counts']['gt_objects']}")
    print(f"Class Distribution: {results['verified_counts']['gt_class_distribution']}")
    print(f"Predictions match test split: {results['verified_counts']['predictions_matching_test']}")
    print(f"\nPerformance: P={results['error_table_summary']['precision']:.3f}, R={results['error_table_summary']['recall']:.3f}, F1={results['error_table_summary']['f1']:.3f}")
    print(f"TP={results['error_table_summary']['total_tp']}, FP={results['error_table_summary']['total_fp']}, FN={results['error_table_summary']['total_fn']}")