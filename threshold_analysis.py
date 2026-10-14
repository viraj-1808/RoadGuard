import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Paths
PRED1_PATH = r"runs\detect\experiments\results\20261010_phase2_validation\exp1_epoch86_val-3\predictions.json"
PRED2_PATH = r"runs\detect\experiments\results\20261010_phase2_validation\exp2_epoch72_val-3\predictions.json"
GT_DIR = r"experiments\dataset\yolo_rdd2022_india\labels\val"
OUTPUT_DIR = r"experiments\results\20261010_phase5_threshold"

THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.25]
IOU_THRESH = 0.5
NMS_IOU = 0.6

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_ground_truth(gt_dir):
    """Load ground truth labels in YOLO format."""
    gt_by_image = defaultdict(list)
    for txt_file in Path(gt_dir).glob("*.txt"):
        image_id = txt_file.stem
        with open(txt_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                    gt_by_image[image_id].append({
                        'class': cls,
                        'bbox': [x_center, y_center, w, h]  # normalized YOLO format
                    })
    return gt_by_image

def load_predictions(pred_path):
    """Load predictions in COCO format."""
    with open(pred_path, 'r') as f:
        preds = json.load(f)
    preds_by_image = defaultdict(list)
    for p in preds:
        image_id = p['image_id']
        preds_by_image[image_id].append({
            'class': p['category_id'],
            'bbox': p['bbox'],  # [x, y, w, h] in absolute pixels
            'score': p['score']
        })
    return preds_by_image

def yolo_to_xyxy(bbox, img_w, img_h):
    """Convert YOLO normalized bbox to absolute xyxy."""
    x_center, y_center, w, h = bbox
    x1 = (x_center - w/2) * img_w
    y1 = (y_center - h/2) * img_h
    x2 = (x_center + w/2) * img_w
    y2 = (y_center + h/2) * img_h
    return [x1, y1, x2, y2]

def xywh_to_xyxy(bbox):
    """Convert COCO xywh to xyxy."""
    x, y, w, h = bbox
    return [x, y, x + w, y + h]

def compute_iou(box1, box2):
    """Compute IoU between two boxes in xyxy format."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x2 <= x1 or y2 <= y1:
        return 0.0
    
    inter = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    
    return inter / union if union > 0 else 0.0

def nms(boxes, scores, iou_threshold):
    """Non-maximum suppression."""
    if len(boxes) == 0:
        return []
    
    boxes = np.array(boxes)
    scores = np.array(scores)
    order = scores.argsort()[::-1]
    keep = []
    
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        
        area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
        area_rest = (boxes[order[1:], 2] - boxes[order[1:], 0]) * (boxes[order[1:], 3] - boxes[order[1:], 1])
        iou = inter / (area_i + area_rest - inter + 1e-10)
        
        order = order[1:][iou <= iou_threshold]
    
    return keep

def evaluate_at_threshold(preds_by_image, gt_by_image, threshold, img_w=1280, img_h=720):
    """Evaluate predictions at a given confidence threshold."""
    # Class metrics: TP, FP, FN per class
    metrics = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    # Get all classes present
    all_classes = set()
    for preds in preds_by_image.values():
        for p in preds:
            all_classes.add(p['class'])
    for gts in gt_by_image.values():
        for g in gts:
            all_classes.add(g['class'])
    
    for image_id in set(list(preds_by_image.keys()) + list(gt_by_image.keys())):
        preds = preds_by_image.get(image_id, [])
        gts = gt_by_image.get(image_id, [])
        
        # Filter predictions by threshold
        filtered_preds = [p for p in preds if p['score'] >= threshold]
        
        # Group by class
        preds_by_class = defaultdict(list)
        for p in filtered_preds:
            bbox_xyxy = xywh_to_xyxy(p['bbox'])
            preds_by_class[p['class']].append({
                'bbox': bbox_xyxy,
                'score': p['score']
            })
        
        gts_by_class = defaultdict(list)
        for g in gts:
            bbox_xyxy = yolo_to_xyxy(g['bbox'], img_w, img_h)
            gts_by_class[g['class']].append({
                'bbox': bbox_xyxy,
                'matched': False
            })
        
        # For each class, apply NMS and match
        for cls in all_classes:
            cls_preds = preds_by_class.get(cls, [])
            cls_gts = gts_by_class.get(cls, [])
            
            if not cls_preds and not cls_gts:
                continue
            
            # Apply NMS per class
            if cls_preds:
                boxes = np.array([p['bbox'] for p in cls_preds])
                scores = np.array([p['score'] for p in cls_preds])
                keep_idx = nms(boxes, scores, NMS_IOU)
                cls_preds = [cls_preds[i] for i in keep_idx]
            
            # Match predictions to GTs
            for pred in cls_preds:
                best_iou = 0
                best_gt_idx = -1
                for gi, gt in enumerate(cls_gts):
                    if not gt['matched']:
                        iou = compute_iou(pred['bbox'], gt['bbox'])
                        if iou > best_iou:
                            best_iou = iou
                            best_gt_idx = gi
                
                if best_iou >= IOU_THRESH and best_gt_idx >= 0:
                    cls_gts[best_gt_idx]['matched'] = True
                    metrics[cls]['tp'] += 1
                else:
                    metrics[cls]['fp'] += 1
            
            # Count unmatched GTs as FN
            for gt in cls_gts:
                if not gt['matched']:
                    metrics[cls]['fn'] += 1
    
    # Compute P, R, F1 per class
    results = []
    for cls in sorted(all_classes):
        tp = metrics[cls]['tp']
        fp = metrics[cls]['fp']
        fn = metrics[cls]['fn']
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results.append({
            'class': cls,
            'P': precision,
            'R': recall,
            'F1': f1,
            'FP': fp,
            'TP': tp,
            'FN': fn
        })
    
    return results

def main():
    print("Loading ground truth...")
    gt_by_image = load_ground_truth(GT_DIR)
    print(f"Loaded GT for {len(gt_by_image)} images")
    
    print("Loading predictions (exp1_epoch86)...")
    preds1 = load_predictions(PRED1_PATH)
    print(f"Loaded predictions for {len(preds1)} images")
    
    print("Loading predictions (exp2_epoch72)...")
    preds2 = load_predictions(PRED2_PATH)
    print(f"Loaded predictions for {len(preds2)} images")
    
    all_results = []
    
    for model_name, preds in [("exp1_epoch86", preds1), ("exp2_epoch72", preds2)]:
        print(f"\nEvaluating {model_name}...")
        for thresh in THRESHOLDS:
            print(f"  Threshold {thresh}...")
            results = evaluate_at_threshold(preds, gt_by_image, thresh)
            for r in results:
                r['model'] = model_name
                r['threshold'] = thresh
                all_results.append(r)
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    df = df[['model', 'threshold', 'class', 'P', 'R', 'F1', 'FP', 'TP', 'FN']]
    
    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, "THRESHOLD_COMPARISON.csv")
    df.to_csv(csv_path, index=False, float_format='%.4f')
    print(f"\nSaved CSV to {csv_path}")
    
    # Create markdown analysis focusing on pothole (class 3)
    md_path = os.path.join(OUTPUT_DIR, "THRESHOLD_ANALYSIS.md")
    with open(md_path, 'w') as f:
        f.write("# Threshold Analysis for Pothole Detection (Class 3)\n\n")
        f.write(f"Models: exp1_epoch86, exp2_epoch72\n")
        f.write(f"IoU threshold for matching: {IOU_THRESH}\n")
        f.write(f"NMS IoU: {NMS_IOU}\n")
        f.write(f"Confidence thresholds tested: {THRESHOLDS}\n\n")
        
        for model_name in ["exp1_epoch86", "exp2_epoch72"]:
            model_df = df[(df['model'] == model_name) & (df['class'] == 3)]
            f.write(f"## {model_name}\n\n")
            f.write("| Threshold | Precision | Recall | F1 | FP | TP | FN |\n")
            f.write("|-----------|-----------|--------|-----|----|----|----|\n")
            best_f1 = 0
            best_thresh = None
            for _, row in model_df.iterrows():
                f.write(f"| {row['threshold']:.2f} | {row['P']:.4f} | {row['R']:.4f} | {row['F1']:.4f} | {int(row['FP'])} | {int(row['TP'])} | {int(row['FN'])} |\n")
                if row['F1'] > best_f1:
                    best_f1 = row['F1']
                    best_thresh = row['threshold']
            f.write(f"\n**Best threshold for pothole F1: {best_thresh:.2f} (F1 = {best_f1:.4f})**\n\n")
        
        # Overall comparison
        f.write("## Summary: Best Pothole F1 by Model\n\n")
        f.write("| Model | Best Threshold | Best F1 | Precision | Recall |\n")
        f.write("|-------|----------------|---------|-----------|--------|\n")
        for model_name in ["exp1_epoch86", "exp2_epoch72"]:
            model_df = df[(df['model'] == model_name) & (df['class'] == 3)]
            best_row = model_df.loc[model_df['F1'].idxmax()]
            f.write(f"| {model_name} | {best_row['threshold']:.2f} | {best_row['F1']:.4f} | {best_row['P']:.4f} | {best_row['R']:.4f} |\n")
    
    print(f"Saved analysis to {md_path}")
    print("\nDone!")

if __name__ == "__main__":
    main()