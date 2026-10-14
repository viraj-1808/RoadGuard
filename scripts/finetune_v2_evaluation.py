#!/usr/bin/env python
"""
Fine-tuned v2 Evaluation: Evaluation of yol11s_realworld_finetune_v2/best.pt 
on smoke test + CLEAR holdout images.
Computes IoU metrics at confidence threshold 0.05 for both pothole (class 3) 
and alligator_crack (class 2).
Uses same ground truth and matching logic as audit_v2.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


# Class mapping
CLASS_NAMES = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
TARGET_CLASSES = {2: "alligator_crack", 3: "pothole"}


def compute_iou(box1: list[float], box2: list[float]) -> float:
    """Compute IoU between two boxes in xyxy format."""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

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


def match_detections_to_gt(detections: list[dict], gt_boxes: list[dict], iou_threshold: float = 0.50) -> tuple:
    """
    Match detections to GT boxes using greedy IoU matching.
    Each GT matched at most once. Correct class required.
    Returns: (tp, fp, fn, matches) where matches is list of (det_idx, gt_idx, iou)
    """
    if not detections or not gt_boxes:
        return 0, len(detections), len(gt_boxes), []

    # Compute IoU matrix
    iou_matrix = np.zeros((len(detections), len(gt_boxes)))
    for i, det in enumerate(detections):
        for j, gt in enumerate(gt_boxes):
            if det["class_id"] == gt["class_id"]:
                iou_matrix[i, j] = compute_iou(det["bbox_xyxy"], gt["bbox_xyxy"])

    # Greedy matching: sort by IoU descending
    matches = []
    used_dets = set()
    used_gts = set()

    # Get all valid (iou > threshold) pairs
    valid_pairs = []
    for i in range(len(detections)):
        for j in range(len(gt_boxes)):
            if iou_matrix[i, j] >= iou_threshold:
                valid_pairs.append((iou_matrix[i, j], i, j))

    valid_pairs.sort(reverse=True)  # Highest IoU first

    for iou, det_idx, gt_idx in valid_pairs:
        if det_idx not in used_dets and gt_idx not in used_gts:
            matches.append((det_idx, gt_idx, iou))
            used_dets.add(det_idx)
            used_gts.add(gt_idx)

    tp = len(matches)
    fp = len(detections) - tp
    fn = len(gt_boxes) - tp

    return tp, fp, fn, matches


def run_inference_on_image(
    model: YOLO,
    image_path: Path,
    conf_threshold: float,
    iou_threshold: float,
    imgsz: int,
    device: str,
) -> list[dict[str, Any]]:
    """Run inference on a single image and return detections for target classes."""
    img = cv2.imread(str(image_path))
    if img is None:
        return []

    height, width = img.shape[:2]

    results = model.predict(
        img,
        imgsz=imgsz,
        conf=conf_threshold,
        iou=iou_threshold,
        device=device,
        verbose=False,
    )

    detections = []
    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            cls_ids = result.boxes.cls.cpu().numpy().astype(int)

            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                if cls_id in TARGET_CLASSES and conf >= conf_threshold:
                    detections.append({
                        "class_id": int(cls_id),
                        "class_name": CLASS_NAMES.get(int(cls_id), f"class_{cls_id}"),
                        "confidence": float(conf),
                        "bbox_xyxy": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                    })
    return detections


def draw_annotations(image_path: Path, output_path: Path, detections: list[dict], gt_boxes: list[dict], matches: list):
    """Draw detections and GT boxes on image for visualization."""
    img = cv2.imread(str(image_path))
    if img is None:
        return

    # Draw GT boxes in green
    for gt in gt_boxes:
        x1, y1, x2, y2 = map(int, gt["bbox_xyxy"])
        color = (0, 255, 0)  # Green
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        label = f"GT: {gt['class_name']}"
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Draw detections in red (FP) or blue (TP)
    matched_det_indices = {m[0] for m in matches}
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = map(int, det["bbox_xyxy"])
        if i in matched_det_indices:
            color = (255, 0, 0)  # Blue for TP
            label = f"TP: {det['class_name']} {det['confidence']:.2f}"
        else:
            color = (0, 0, 255)  # Red for FP
            label = f"FP: {det['class_name']} {det['confidence']:.2f}"
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Draw FN (unmatched GT) in yellow
    matched_gt_indices = {m[1] for m in matches}
    for j, gt in enumerate(gt_boxes):
        if j not in matched_gt_indices:
            x1, y1, x2, y2 = map(int, gt["bbox_xyxy"])
            color = (0, 255, 255)  # Yellow for FN
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"FN: {gt['class_name']}"
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imwrite(str(output_path), img)


def main():
    # Configuration - FINE-TUNED CHECKPOINT
    checkpoint_path = Path(r"runs\detect\experiments\training\yol11s_realworld_finetune_v2\weights\best.pt")
    checkpoint_sha256 = "4d5449db73b1e9e3f57ab554b6bf3de7994829cdf275b908653da3b242403a83"
    input_dir = Path(r"validation\manual\input")
    output_dir = Path(r"experiments\results\real_world_model_improvement\finetune_v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir = output_dir / "annotated"
    annotated_dir.mkdir(parents=True, exist_ok=True)

    # Ground truth from smoke_test_report.md (4 images)
    smoke_gt = {
        "road001.webp": [{"class_id": 3, "class_name": "pothole", "bbox_xyxy": [95.39811706542969, 439.5462341308594, 344.9998474121094, 523.6841430664062]}],
        "road002.jpg": [{"class_id": 3, "class_name": "pothole", "bbox_xyxy": [260.759765625, 150.74246215820312, 413.557373046875, 237.59033203125]}],
        "road009.jpg": [{"class_id": 3, "class_name": "pothole", "bbox_xyxy": [205.28518676757812, 161.53932189941406, 264.9638366699219, 215.19070434570312]}],
        "road010.jpg": [{"class_id": 3, "class_name": "pothole", "bbox_xyxy": [169.818359375, 228.73846435546875, 512.373291015625, 439.50830078125]}],
    }

    # Ground truth from ground_truth_annotations.json (5 CLEAR holdout images)
    with open("experiments/results/real_world_model_improvement/ground_truth_annotations.json") as f:
        gt_data = json.load(f)

    holdout_gt = {}
    holdout_images = ["road001.webp", "road002.jpg", "road003.jpg", "road007.jpg", "road026.jpg"]
    for img_info in gt_data["images"]:
        if img_info["image"] in holdout_images:
            anns = []
            for ann in img_info["annotations"]:
                anns.append({
                    "class_id": ann["class_id"],
                    "class_name": ann["class_name"],
                    "bbox_xyxy": ann["bbox_xyxy"],
                })
            holdout_gt[img_info["image"]] = anns

    # Combine all unique images (7 total)
    all_images = {}
    all_images.update(smoke_gt)
    all_images.update(holdout_gt)

    print(f"Total unique images to evaluate: {len(all_images)}")
    for img, anns in all_images.items():
        classes = [a["class_name"] for a in anns]
        print(f"  {img}: {len(anns)} GT boxes ({', '.join(classes)})")

    # Configuration matching audit_v2
    conf_threshold = 0.05
    iou_threshold = 0.7  # NMS threshold
    match_iou_threshold = 0.50  # Matching threshold
    imgsz = 720
    device = "0"

    print(f"\nLoading model: {checkpoint_path}")
    model = YOLO(str(checkpoint_path))
    print(f"Model loaded. Classes: {model.model.names}")

    # Warm up
    dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)
    model.predict(dummy, imgsz=imgsz, device=device, verbose=False)

    # Store all results
    class_totals = {2: {"tp": 0, "fp": 0, "fn": 0}, 3: {"tp": 0, "fp": 0, "fn": 0}}
    total_tp = total_fp = total_fn = 0
    all_per_image_details = []
    threshold_results = {}

    print(f"\n=== Testing confidence threshold: {conf_threshold} ===")

    for image_name, gt_boxes in all_images.items():
        image_path = input_dir / image_name
        detections = run_inference_on_image(model, image_path, conf_threshold, iou_threshold, imgsz, device)

        # Match detections to GT
        tp, fp, fn, matches = match_detections_to_gt(detections, gt_boxes, match_iou_threshold)
        total_tp += tp
        total_fp += fp
        total_fn += fn

        # Per-class breakdown
        for cls_id in TARGET_CLASSES:
            cls_dets = [d for d in detections if d["class_id"] == cls_id]
            cls_gts = [g for g in gt_boxes if g["class_id"] == cls_id]
            cls_tp, cls_fp, cls_fn, cls_matches = match_detections_to_gt(cls_dets, cls_gts, match_iou_threshold)
            class_totals[cls_id]["tp"] += cls_tp
            class_totals[cls_id]["fp"] += cls_fp
            class_totals[cls_id]["fn"] += cls_fn

        # Per-image detail
        best_ious = {}
        for cls_id in TARGET_CLASSES:
            cls_dets = [d for d in detections if d["class_id"] == cls_id]
            cls_gts = [g for g in gt_boxes if g["class_id"] == cls_id]
            best_iou = 0.0
            for det in cls_dets:
                for gt in cls_gts:
                    iou = compute_iou(det["bbox_xyxy"], gt["bbox_xyxy"])
                    if iou > best_iou:
                        best_iou = iou
            best_ious[cls_id] = best_iou

        matched_any = any(m[2] >= match_iou_threshold for m in matches)
        is_smoke = image_name in smoke_gt
        is_holdout = image_name in holdout_gt

        detail = {
            "image": image_name,
            "confidence_threshold": conf_threshold,
            "is_smoke_test": is_smoke,
            "is_holdout": is_holdout,
            "gt_boxes": gt_boxes,
            "detections": detections,
            "matches": matches,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "best_iou_pothole": best_ious.get(3, 0.0),
            "best_iou_alligator": best_ious.get(2, 0.0),
            "matched_any": matched_any,
        }
        all_per_image_details.append(detail)
        threshold_results[image_name] = detail

        status = "MATCHED" if matched_any else "MISSED"
        print(f"  {image_name}: TP={tp}, FP={fp}, FN={fn} [{status}]")
        for det in detections:
            match_status = "TP" if any(m[0] == detections.index(det) for m in matches) else "FP"
            print(f"    {match_status}: {det['class_name']} conf={det['confidence']:.4f} bbox={det['bbox_xyxy']}")

        # Save annotated image
        annotated_path = annotated_dir / f"{Path(image_name).stem}_conf{conf_threshold:.2f}.jpg"
        draw_annotations(image_path, annotated_path, detections, gt_boxes, matches)

    # Compute metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Per-class metrics
    class_metrics = {}
    for cls_id in TARGET_CLASSES:
        ct = class_totals[cls_id]
        p = ct["tp"] / (ct["tp"] + ct["fp"]) if (ct["tp"] + ct["fp"]) > 0 else 0.0
        r = ct["tp"] / (ct["tp"] + ct["fn"]) if (ct["tp"] + ct["fn"]) > 0 else 0.0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        class_metrics[CLASS_NAMES[cls_id]] = {
            "tp": ct["tp"], "fp": ct["fp"], "fn": ct["fn"],
            "precision": p, "recall": r, "f1": f
        }

    # Smoke test specific: 3/4 matched
    smoke_matched = sum(1 for img in smoke_gt if threshold_results[img]["matched_any"])
    smoke_target = smoke_matched >= 3

    # Holdout specific: count matched
    holdout_matched = sum(1 for img in holdout_gt if threshold_results[img]["matched_any"])

    summary = {
        "confidence_threshold": conf_threshold,
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "class_metrics": class_metrics,
        "smoke_test_matched": smoke_matched,
        "smoke_test_total": 4,
        "smoke_target_achieved": smoke_target,
        "holdout_matched": holdout_matched,
        "holdout_total": 5,
    }

    print(f"  Overall: TP={total_tp}, FP={total_fp}, FN={total_fn}, P={precision:.4f}, R={recall:.4f}, F1={f1:.4f}")
    print(f"  Smoke test: {smoke_matched}/4 matched (target: {'YES' if smoke_target else 'NO'})")
    print(f"  Holdout: {holdout_matched}/5 matched")
    for cls_name, cm in class_metrics.items():
        print(f"  {cls_name}: TP={cm['tp']}, FP={cm['fp']}, FN={cm['fn']}, P={cm['precision']:.4f}, R={cm['recall']:.4f}, F1={cm['f1']:.4f}")

    # Prepare FINE_TUNED_METRICS.json
    verified_metrics = {
        "experiment_id": "EXP-FINETUNE-V2-001",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_sha256,
        "images_evaluated": list(all_images.keys()),
        "smoke_test_images": list(smoke_gt.keys()),
        "holdout_images": list(holdout_gt.keys()),
        "inference_config": {
            "iou_threshold_nms": iou_threshold,
            "match_iou_threshold": match_iou_threshold,
            "imgsz": imgsz,
            "device": device,
        },
        "confidence_threshold_tested": conf_threshold,
        "summary": summary,
        "per_image": {},
    }

    # Convert results to serializable format
    for img_name, img_result in threshold_results.items():
        verified_metrics["per_image"][img_name] = {
            "tp": img_result["tp"],
            "fp": img_result["fp"],
            "fn": img_result["fn"],
            "best_iou_pothole": img_result["best_iou_pothole"],
            "best_iou_alligator": img_result["best_iou_alligator"],
            "matched_any": img_result["matched_any"],
            "num_detections": len(img_result["detections"]),
            "num_gt": len(img_result["gt_boxes"]),
            "detections": img_result["detections"],
            "gt_boxes": img_result["gt_boxes"],
            "matches": img_result["matches"],
        }

    # Save FINE_TUNED_METRICS.json
    metrics_path = output_dir / "FINE_TUNED_METRICS.json"
    with open(metrics_path, "w") as f:
        json.dump(verified_metrics, f, indent=2)
    print(f"\nFINE_TUNED_METRICS.json saved to: {metrics_path}")

    # Save ERROR_CASES.csv
    csv_path = output_dir / "ERROR_CASES.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "image", "confidence_threshold", "is_smoke_test", "is_holdout",
            "gt_class", "gt_bbox", "det_class", "det_confidence", "det_bbox",
            "iou", "match_status", "tp", "fp", "fn"
        ])
        for detail in all_per_image_details:
            img_name = detail["image"]
            conf = detail["confidence_threshold"]
            is_smoke = detail["is_smoke_test"]
            is_holdout = detail["is_holdout"]
            
            # Get matched detection indices
            matched_det_indices = {m[0] for m in detail["matches"]}
            matched_gt_indices = {m[1] for m in detail["matches"]}
            
            # Write detections
            for i, det in enumerate(detail["detections"]):
                match_status = "TP" if i in matched_det_indices else "FP"
                # Find IoU with matched GT
                iou = 0.0
                for m in detail["matches"]:
                    if m[0] == i:
                        iou = m[2]
                        break
                writer.writerow([
                    img_name, conf, is_smoke, is_holdout,
                    "", "", det["class_name"], det["confidence"], 
                    str(det["bbox_xyxy"]), iou, match_status,
                    1 if match_status == "TP" else 0,
                    1 if match_status == "FP" else 0, 0
                ])
            
            # Write unmatched GT (FN)
            for j, gt in enumerate(detail["gt_boxes"]):
                if j not in matched_gt_indices:
                    writer.writerow([
                        img_name, conf, is_smoke, is_holdout,
                        gt["class_name"], str(gt["bbox_xyxy"]), "", "", "", 0.0, "FN",
                        0, 0, 1
                    ])
    print(f"ERROR_CASES.csv saved to: {csv_path}")

    # Save COMMANDS.md
    commands_path = output_dir / "COMMANDS.md"
    with open(commands_path, "w") as f:
        f.write("# Fine-tuned v2 Evaluation Commands\n\n")
        f.write(f"## Checkpoint Verification\n")
        f.write(f"```powershell\n")
        f.write(f"Get-FileHash runs/detect/experiments/training/yol11s_realworld_finetune_v2/weights/best.pt -Algorithm SHA256\n")
        f.write(f"```\n\n")
        f.write(f"## Evaluation Command\n")
        f.write(f"```powershell\n")
        f.write(f"python scripts/finetune_v2_evaluation.py\n")
        f.write(f"```\n\n")
        f.write(f"## Model Classes\n")
        f.write(f"```\n")
        f.write(f"{json.dumps(CLASS_NAMES, indent=2)}\n")
        f.write(f"```\n")
    print(f"COMMANDS.md saved to: {commands_path}")

    # Print final summary
    print("\n" + "="*60)
    print("FINE-TUNED V2 EVALUATION SUMMARY")
    print("="*60)
    print(f"Checkpoint SHA-256: {checkpoint_sha256}")
    print(f"Images evaluated: {len(all_images)}")
    print(f"Confidence threshold: {conf_threshold}")
    print(f"Overall F1: {f1:.4f}")
    print(f"Overall Precision: {precision:.4f}")
    print(f"Overall Recall: {recall:.4f}")
    print(f"Smoke test (3/4 target): {smoke_matched}/4 - {'PASSED' if smoke_target else 'FAILED'}")
    print(f"Holdout CLEAR: {holdout_matched}/5 matched")
    print(f"\nPer-class metrics:")
    for cls_name, cm in class_metrics.items():
        print(f"  {cls_name}: TP={cm['tp']}, FP={cm['fp']}, FN={cm['fn']}, P={cm['precision']:.4f}, R={cm['recall']:.4f}, F1={cm['f1']:.4f}")
    print(f"\nOutputs saved to: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()