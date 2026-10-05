import os
import json
import csv
import numpy as np
from collections import defaultdict, Counter

BASE_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
PREDICTIONS_PATH = os.path.join(BASE_DIR, "runs", "detect", "experiments", "training", "yol11s_dataset_v2_split_v2", "test_eval", "predictions.json")
LABEL_DIR = os.path.join(BASE_DIR, "experiments", "dataset", "yolo_rdd2022_india", "labels", "test")
OUTPUT_DIR = os.path.join(BASE_DIR, "experiments", "analysis", "overnight", "corrected_error_analysis")

CLASS_NAMES = {
    0: 'longitudinal_crack',
    1: 'transverse_crack',
    2: 'alligator_crack',
    3: 'pothole'
}

PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}

IMG_W, IMG_H = 720, 720

def load_predictions():
    with open(PREDICTIONS_PATH, 'r') as f:
        preds = json.load(f)
    by_image = defaultdict(list)
    for p in preds:
        img_id = p['image_id']
        class_id = PRED_CLASS_MAP.get(p['category_id'], p['category_id'] - 1)
        by_image[img_id].append({
            'class_id': class_id,
            'bbox': p['bbox'],
            'score': p['score']
        })
    return by_image

def load_ground_truth():
    gt_data = {}
    for fname in sorted(os.listdir(LABEL_DIR)):
        if not fname.endswith('.txt'):
            continue
        img_id = fname.replace('.txt', '')
        objs = []
        with open(os.path.join(LABEL_DIR, fname), 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                class_id = int(parts[0])
                xc, yc, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                x_px = (xc - w / 2) * IMG_W
                y_px = (yc - h / 2) * IMG_H
                w_px = w * IMG_W
                h_px = h * IMG_H
                objs.append({
                    'class_id': class_id,
                    'bbox': [x_px, y_px, w_px, h_px],
                    'area': w_px * h_px,
                    'matched': False
                })
        gt_data[img_id] = objs
    return gt_data

def bbox_iou(box1, box2):
    x1_1, y1_1 = box1[0], box1[1]
    x2_1, y2_1 = box1[0] + box1[2], box1[1] + box1[3]
    x1_2, y1_2 = box2[0], box2[1]
    x2_2, y2_2 = box2[0] + box2[2], box2[1] + box2[3]
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    intersection = inter_w * inter_h
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    if union <= 0:
        return 0.0
    return intersection / union

def nms_predictions(pred_objects, iou_threshold=0.7, conf_threshold=0.001):
    filtered = [p for p in pred_objects if p['score'] >= conf_threshold]
    filtered.sort(key=lambda x: x['score'], reverse=True)
    keep = []
    for pred in filtered:
        suppress = False
        for kept in keep:
            if pred['class_id'] == kept['class_id']:
                iou = bbox_iou(pred['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    suppress = True
                    break
        if not suppress:
            keep.append(pred)
    return keep

def confidence_ranked_match(gt_objects, pred_objects, iou_threshold=0.5):
    gt_matched = [False] * len(gt_objects)
    pred_matched = [False] * len(pred_objects)
    matches = []
    for pi, pred in enumerate(pred_objects):
        best_iou = 0
        best_gt_idx = -1
        for gi, gt in enumerate(gt_objects):
            if gt_matched[gi]:
                continue
            if pred['class_id'] != gt['class_id']:
                continue
            iou = bbox_iou(pred['bbox'], gt['bbox'])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gi
        if best_gt_idx >= 0 and best_iou >= iou_threshold:
            matches.append((best_gt_idx, pi, best_iou))
            gt_matched[best_gt_idx] = True
            pred_matched[pi] = True
    return matches, gt_matched, pred_matched

def compute_metrics(gt_data, pred_by_image, conf_threshold=0.25):
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_preds_after_nms = 0
    total_preds_after_filter = 0
    per_image = []
    class_tp = Counter()
    class_fp = Counter()
    class_fn = Counter()
    class_gt = Counter()

    for img_id in sorted(gt_data.keys()):
        gt_objs = gt_data[img_id]
        pred_objs = pred_by_image.get(img_id, [])
        for gt in gt_objs:
            class_gt[gt['class_id']] += 1

        nms_preds = nms_predictions(pred_objs, iou_threshold=0.7, conf_threshold=0.001)
        total_preds_after_nms += len(nms_preds)
        filtered_preds = [p for p in nms_preds if p['score'] >= conf_threshold]
        total_preds_after_filter += len(filtered_preds)
        matches, gt_matched, pred_matched = confidence_ranked_match(gt_objs, filtered_preds, iou_threshold=0.5)
        tp = len(matches)
        fp = sum(1 for m in pred_matched if not m)
        fn = sum(1 for m in gt_matched if not m)
        total_tp += tp
        total_fp += fp
        total_fn += fn
        for m in matches:
            class_tp[gt_objs[m[0]]['class_id']] += 1
        for i, m in enumerate(pred_matched):
            if not m:
                class_fp[filtered_preds[i]['class_id']] += 1
        for i, m in enumerate(gt_matched):
            if not m:
                class_fn[gt_objs[i]['class_id']] += 1
        per_image.append({
            'image_id': img_id,
            'gt_count': len(gt_objs),
            'pred_count_after_nms': len(nms_preds),
            'pred_count_after_filter': len(filtered_preds),
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': tp / (tp + fp) if (tp + fp) > 0 else 0.0,
            'recall': tp / (tp + fn) if (tp + fn) > 0 else 0.0,
            'f1': 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0
        })

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    class_stats = {}
    for cid in range(4):
        gt_c = class_gt[cid]
        tp_c = class_tp[cid]
        fp_c = class_fp[cid]
        fn_c = class_fn[cid]
        prec_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) > 0 else 0.0
        rec_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) > 0 else 0.0
        f1_c = 2 * prec_c * rec_c / (prec_c + rec_c) if (prec_c + rec_c) > 0 else 0.0
        class_stats[cid] = {
            'name': CLASS_NAMES[cid],
            'gt_count': gt_c,
            'tp': tp_c,
            'fp': fp_c,
            'fn': fn_c,
            'precision': prec_c,
            'recall': rec_c,
            'f1': f1_c
        }

    return {
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'total_preds_after_nms': total_preds_after_nms,
        'total_preds_after_filter': total_preds_after_filter,
        'per_image': per_image,
        'class_stats': class_stats
    }

def build_confidence_analysis(gt_data, pred_by_image, thresholds):
    rows = []
    for conf in thresholds:
        m = compute_metrics(gt_data, pred_by_image, conf_threshold=conf)
        rows.append({
            'confidence_threshold': conf,
            'tp': m['total_tp'],
            'fp': m['total_fp'],
            'fn': m['total_fn'],
            'precision': m['precision'],
            'recall': m['recall'],
            'f1': m['f1'],
            'preds_after_filter': m['total_preds_after_filter']
        })
    return rows

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading predictions...")
    pred_by_image = load_predictions()
    print(f"Loaded predictions for {len(pred_by_image)} images")

    print("Loading ground truth...")
    gt_data = load_ground_truth()
    total_gt = sum(len(v) for v in gt_data.values())
    print(f"Loaded {total_gt} GT objects across {len(gt_data)} images")

    # --- Confidence analysis ---
    conf_thresholds = [0.001, 0.01, 0.05, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    print(f"\nRunning confidence analysis at {len(conf_thresholds)} thresholds...")
    conf_rows = build_confidence_analysis(gt_data, pred_by_image, conf_thresholds)
    conf_csv_path = os.path.join(OUTPUT_DIR, "confidence_analysis.csv")
    with open(conf_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['confidence_threshold', 'tp', 'fp', 'fn', 'precision', 'recall', 'f1', 'preds_after_filter'])
        writer.writeheader()
        writer.writerows(conf_rows)
    print(f"Confidence analysis written to {conf_csv_path}")

    # --- Main analysis at 0.25 confidence threshold ---
    print("\nComputing metrics at conf=0.25...")
    main_metrics = compute_metrics(gt_data, pred_by_image, conf_threshold=0.25)

    # --- Write error_summary.csv ---
    summary_path = os.path.join(OUTPUT_DIR, "error_summary.csv")
    with open(summary_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'value'])
        writer.writeheader()
        rows = [
            {'metric': 'Total GT Objects', 'value': total_gt},
            {'metric': 'Total Predictions (raw)', 'value': sum(len(v) for v in pred_by_image.values())},
            {'metric': 'Predictions after NMS', 'value': main_metrics['total_preds_after_nms']},
            {'metric': 'Predictions after conf_filter (0.25)', 'value': main_metrics['total_preds_after_filter']},
            {'metric': 'True Positives', 'value': main_metrics['total_tp']},
            {'metric': 'False Positives', 'value': main_metrics['total_fp']},
            {'metric': 'False Negatives', 'value': main_metrics['total_fn']},
            {'metric': 'Precision', 'value': f"{main_metrics['precision']:.4f}"},
            {'metric': 'Recall', 'value': f"{main_metrics['recall']:.4f}"},
            {'metric': 'F1-Score', 'value': f"{main_metrics['f1']:.4f}"},
            {'metric': 'Official Precision', 'value': '0.299'},
            {'metric': 'Official Recall', 'value': '0.312'},
            {'metric': 'Methodology Note 1', 'value': 'This pipeline applies NMS (iou=0.7), confidence filtering, and confidence-ranked one-to-one matching at IoU>=0.5.'},
            {'metric': 'Methodology Note 2', 'value': 'Official Ultralytics metrics are computed over a range of confidence thresholds using the full PR curve.'}
        ]
        writer.writerows(rows)
    print(f"Error summary written to {summary_path}")

    # --- Write per_image_errors.csv ---
    per_img_path = os.path.join(OUTPUT_DIR, "per_image_errors.csv")
    with open(per_img_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['image_id', 'gt_count', 'pred_count_after_nms', 'pred_count_after_filter', 'tp', 'fp', 'fn', 'precision', 'recall', 'f1'])
        writer.writeheader()
        writer.writerows(main_metrics['per_image'])
    print(f"Per-image errors written to {per_img_path}")

    # --- Print summary ---
    print("\n" + "=" * 70)
    print("CORRECTED DIAGNOSTIC PIPELINE RESULTS")
    print("=" * 70)
    print(f"Total GT Objects:       {total_gt}")
    total_raw = sum(len(v) for v in pred_by_image.values())
    print(f"Total Raw Predictions:  {total_raw}")
    print(f"Predictions after NMS:  {main_metrics['total_preds_after_nms']}")
    print(f"Predictions after conf_filter: {main_metrics['total_preds_after_filter']}")
    print(f"\nCorrected Metrics (conf=0.25, NMS iou=0.7):")
    print(f"  Precision: {main_metrics['precision']:.4f}")
    print(f"  Recall:    {main_metrics['recall']:.4f}")
    print(f"  F1-Score:  {main_metrics['f1']:.4f}")
    print(f"  TP={main_metrics['total_tp']}, FP={main_metrics['total_fp']}, FN={main_metrics['total_fn']}")
    print(f"\nOfficial Ultralytics Metrics:")
    print(f"  Precision: 0.299")
    print(f"  Recall:    0.312")
    print(f"  mAP50:     0.252")
    print(f"  mAP50-95:  0.0903")
    print(f"\nPer-Class Corrected Metrics:")
    for cid in range(4):
        cs = main_metrics['class_stats'][cid]
        print(f"  {cs['name']}: P={cs['precision']:.3f} R={cs['recall']:.3f} F1={cs['f1']:.3f} (GT={cs['gt_count']} TP={cs['tp']} FP={cs['fp']} FN={cs['fn']})")