import json
import os
from collections import defaultdict
import numpy as np

# Load predictions
with open(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\evaluation\exp1_frozen_dataset_a_test\predictions.json') as f:
    pred1 = json.load(f)

with open(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\evaluation\exp2_frozen_dataset_a_test\eval\predictions.json') as f:
    pred2 = json.load(f)

# Load ground truth labels
gt_dir = r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\evaluation\exp1_frozen_dataset_a_test\labels'
gt_files = os.listdir(gt_dir)

gt_boxes = defaultdict(list)
for gt_file in gt_files:
    img_id = gt_file.replace('.txt', '')
    with open(os.path.join(gt_dir, gt_file)) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                cls = int(parts[0])
                x, y, w, h = map(float, parts[1:5])
                gt_boxes[img_id].append({'cls': cls, 'bbox': [x, y, w, h]})

# Convert predictions to normalized YOLO format (x_center, y_center, w, h) / 720
IMG_SIZE = 720

def convert_to_normalized(bbox):
    """Convert from absolute [x, y, w, h] to normalized [x_center, y_center, w, h]"""
    x, y, w, h = bbox
    x_center = (x + w/2) / IMG_SIZE
    y_center = (y + h/2) / IMG_SIZE
    w_norm = w / IMG_SIZE
    h_norm = h / IMG_SIZE
    return [x_center, y_center, w_norm, h_norm]

# Convert predictions
pred_by_img1 = defaultdict(list)
for p in pred1:
    norm_bbox = convert_to_normalized(p['bbox'])
    pred_by_img1[p['image_id']].append({'cls': p['category_id'], 'bbox': norm_bbox, 'score': p['score']})

pred_by_img2 = defaultdict(list)
for p in pred2:
    norm_bbox = convert_to_normalized(p['bbox'])
    pred_by_img2[p['image_id']].append({'cls': p['category_id'], 'bbox': norm_bbox, 'score': p['score']})

# Class names (mapping from data.yaml)
cls_names = {0: 'longitudinal_crack', 1: 'transverse_crack', 2: 'alligator_crack', 3: 'pothole'}

# Simple IoU calculation for normalized boxes
def iou(box1, box2):
    # box format: [x_center, y_center, w, h] normalized
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    x1_min, y1_min = x1 - w1/2, y1 - h1/2
    x1_max, y1_max = x1 + w1/2, y1 + h1/2
    x2_min, y2_min = x2 - w2/2, y2 - h2/2
    x2_max, y2_max = x2 + w2/2, y2 + h2/2
    
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    
    if inter_xmax <= inter_xmin or inter_ymax <= inter_ymin:
        return 0.0
    
    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - inter_area
    return inter_area / union

# Evaluate at conf=0.25, IoU=0.5
conf_thresh = 0.25
iou_thresh = 0.5

for name, preds in [('Exp1', pred_by_img1), ('Exp2', pred_by_img2)]:
    print('\n=== ' + name + ' ===')
    total_tp = defaultdict(int)
    total_fp = defaultdict(int)
    total_fn = defaultdict(int)
    
    for img_id in gt_boxes:
        gt = gt_boxes[img_id]
        pr = [p for p in preds[img_id] if p['score'] >= conf_thresh]
        
        # Match by class
        for cls in range(4):
            gt_cls = [g for g in gt if g['cls'] == cls]
            pr_cls = [p for p in pr if p['cls'] == cls]
            
            matched_gt = set()
            for p in pr_cls:
                best_iou = 0
                best_gt_idx = -1
                for i, g in enumerate(gt_cls):
                    if i in matched_gt:
                        continue
                    iou_val = iou(p['bbox'], g['bbox'])
                    if iou_val > best_iou:
                        best_iou = iou_val
                        best_gt_idx = i
                if best_iou >= iou_thresh:
                    total_tp[cls] += 1
                    matched_gt.add(best_gt_idx)
                else:
                    total_fp[cls] += 1
            
            total_fn[cls] += len(gt_cls) - len(matched_gt)
    
    print('Class | TP | FP | FN | Precision | Recall')
    for cls in range(4):
        tp = total_tp[cls]
        fp = total_fp[cls]
        fn = total_fn[cls]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        print('{:20s} | {:4d} | {:4d} | {:4d} | {:.4f} | {:.4f}'.format(cls_names[cls], tp, fp, fn, prec, rec))
    
    total_tp_all = sum(total_tp.values())
    total_fp_all = sum(total_fp.values())
    total_fn_all = sum(total_fn.values())
    prec_all = total_tp_all / (total_tp_all + total_fp_all) if (total_tp_all + total_fp_all) > 0 else 0
    rec_all = total_tp_all / (total_tp_all + total_fn_all) if (total_tp_all + total_fn_all) > 0 else 0
    print('{:20s} | {:4d} | {:4d} | {:4d} | {:.4f} | {:.4f}'.format('Overall', total_tp_all, total_fp_all, total_fn_all, prec_all, rec_all))

# Also compute mAP@0.5:0.95
print('\n\n=== mAP @ IoU=0.5:0.95 ===')
iou_thresholds = np.arange(0.5, 1.0, 0.05)

for name, preds in [('Exp1', pred_by_img1), ('Exp2', pred_by_img2)]:
    print('\n--- ' + name + ' ---')
    aps = []
    for cls in range(4):
        # Collect all predictions and GT for this class
        all_gt = []
        all_pr = []
        for img_id in gt_boxes:
            gt_cls = [g for g in gt_boxes[img_id] if g['cls'] == cls]
            pr_cls = [p for p in preds[img_id] if p['cls'] == cls]
            all_gt.extend([(img_id, g) for g in gt_cls])
            all_pr.extend([(img_id, p) for p in pr_cls])
        
        if len(all_gt) == 0:
            print('{:20s} | No GT'.format(cls_names[cls]))
            continue
        
        # Sort predictions by confidence
        all_pr.sort(key=lambda x: x[1]['score'], reverse=True)
        
        ap_sum = 0
        for iou_t in iou_thresholds:
            tp = 0
            fp = 0
            matched = set()
            precisions = []
            recalls = []
            
            for img_id, p in all_pr:
                # Find matching GT
                img_gts = [(idx, g) for idx, (gid, g) in enumerate(all_gt) if gid == img_id]
                best_iou = 0
                best_idx = -1
                for idx, g in img_gts:
                    if idx in matched:
                        continue
                    iou_val = iou(p['bbox'], g['bbox'])
                    if iou_val > best_iou:
                        best_iou = iou_val
                        best_idx = idx
                
                if best_iou >= iou_t:
                    tp += 1
                    matched.add(best_idx)
                else:
                    fp += 1
                
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0
                rec = tp / len(all_gt)
                precisions.append(prec)
                recalls.append(rec)
            
            # Compute AP using 11-point interpolation
            ap = 0
            for r in np.arange(0, 1.1, 0.1):
                max_prec = max([p for p, rec in zip(precisions, recalls) if rec >= r], default=0)
                ap += max_prec / 11
            ap_sum += ap
        
        map_cls = ap_sum / len(iou_thresholds)
        aps.append(map_cls)
        print('{:20s} | mAP@0.5:0.95 = {:.4f}'.format(cls_names[cls], map_cls))
    
    print('{:20s} | mAP@0.5:0.95 = {:.4f}'.format('Overall', np.mean(aps)))