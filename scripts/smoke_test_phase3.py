#!/usr/bin/env python
"""
Smoke test for Phase 3: Run inference on 4 manually identified pothole images
with Exp2 epoch72 checkpoint and evaluate IoU against ground truth annotations.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


def compute_iou(box1: list[float], box2: list[float]) -> float:
    """Compute IoU between two boxes in xyxy format."""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # Intersection
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


def run_inference_on_image(
    model: YOLO,
    image_path: Path,
    conf_threshold: float,
    iou_threshold: float,
    imgsz: int,
    device: str,
) -> list[dict[str, Any]]:
    """Run inference on a single image and return detections for class 3 (pothole)."""
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
                if cls_id == 3 and conf >= conf_threshold:  # class 3 = pothole
                    detections.append({
                        "class_id": int(cls_id),
                        "confidence": float(conf),
                        "bbox_xyxy": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                    })
    return detections


def evaluate_image(
    model: YOLO,
    image_name: str,
    gt_box: list[float],
    conf_threshold: float,
    iou_threshold: float,
    imgsz: int,
    device: str,
    input_dir: Path,
) -> dict[str, Any]:
    """Evaluate a single image against ground truth."""
    image_path = input_dir / image_name
    detections = run_inference_on_image(model, image_path, conf_threshold, iou_threshold, imgsz, device)

    # Find best matching detection for the GT box
    best_iou = 0.0
    best_det = None
    for det in detections:
        iou = compute_iou(det["bbox_xyxy"], gt_box)
        if iou > best_iou:
            best_iou = iou
            best_det = det

    # Determine TP/FP/FN
    tp = 1 if best_iou >= 0.50 else 0
    fp = len(detections) - tp  # All other pothole detections are FP
    fn = 1 - tp  # GT not matched is FN

    return {
        "image": image_name,
        "ground_truth_bbox": gt_box,
        "detections": detections,
        "best_match_iou": best_iou,
        "best_match_detection": best_det,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "matched": tp == 1,
    }


def main():
    # Configuration
    checkpoint_path = Path(r"runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt")
    input_dir = Path(r"validation\manual\input")
    output_dir = Path(r"experiments\results\real_world_model_improvement")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ground truth annotations
    gt_annotations = {
        "road001.webp": [95.39811706542969, 439.5462341308594, 344.9998474121094, 523.6841430664062],
        "road002.jpg": [260.759765625, 150.74246215820312, 413.557373046875, 237.59033203125],
        "road009.jpg": [205.28518676757812, 161.53932189941406, 264.9638366699219, 215.19070434570312],
        "road010.jpg": [169.818359375, 228.73846435546875, 512.373291015625, 439.50830078125],
    }

    # Confidence thresholds to test
    conf_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    iou_threshold = 0.7  # NMS threshold
    imgsz = 720
    device = "0"

    print(f"Loading model: {checkpoint_path}")
    model = YOLO(str(checkpoint_path))
    print(f"Model loaded. Classes: {model.model.names}")

    # Warm up
    dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)
    model.predict(dummy, imgsz=imgsz, device=device, verbose=False)

    all_results = {}

    for conf_thresh in conf_thresholds:
        print(f"\n=== Testing confidence threshold: {conf_thresh} ===")
        threshold_results = {}
        total_tp = total_fp = total_fn = 0
        matched_count = 0

        for image_name, gt_box in gt_annotations.items():
            result = evaluate_image(
                model, image_name, gt_box, conf_thresh, iou_threshold, imgsz, device, input_dir
            )
            threshold_results[image_name] = result
            total_tp += result["tp"]
            total_fp += result["fp"]
            total_fn += result["fn"]
            if result["matched"]:
                matched_count += 1
            status = "MATCHED" if result["matched"] else "MISSED"
            print(f"  {image_name}: IoU={result['best_match_iou']:.4f} [{status}] (TP={result['tp']}, FP={result['fp']}, FN={result['fn']})")
            if result["detections"]:
                for det in result["detections"]:
                    print(f"    Det: conf={det['confidence']:.4f}, bbox={det['bbox_xyxy']}")

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        threshold_results["summary"] = {
            "confidence_threshold": conf_thresh,
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fn": total_fn,
            "matched_images": matched_count,
            "total_images": 4,
            "target_achieved": matched_count >= 3,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        print(f"  Summary: TP={total_tp}, FP={total_fp}, FN={total_fn}, Matched={matched_count}/4, Target={'ACHIEVED' if matched_count >= 3 else 'NOT ACHIEVED'}")
        print(f"  Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")

        all_results[str(conf_thresh)] = threshold_results

    # Find best operating point
    best_conf = max(all_results.keys(), key=lambda k: all_results[k]["summary"]["matched_images"])
    best_result = all_results[best_conf]["summary"]

    # Save JSON results
    json_output = {
        "experiment_id": "EXP-SMOKE-001",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checkpoint": str(checkpoint_path),
        "input_images": list(gt_annotations.keys()),
        "ground_truth": gt_annotations,
        "inference_config": {
            "iou_threshold": iou_threshold,
            "imgsz": imgsz,
            "device": device,
        },
        "confidence_thresholds_tested": conf_thresholds,
        "results_by_threshold": all_results,
        "best_operating_point": {
            "confidence_threshold": float(best_conf),
            "matched_images": best_result["matched_images"],
            "target_achieved": best_result["target_achieved"],
            "precision": best_result["precision"],
            "recall": best_result["recall"],
            "f1": best_result["f1"],
        },
    }

    json_path = output_dir / "smoke_test_results.json"
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2)
    print(f"\nResults saved to: {json_path}")

    # Generate markdown report
    report_lines = [
        "# Smoke Test Report: EXP-SMOKE-001",
        "",
        f"**Timestamp**: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"**Checkpoint**: {checkpoint_path}",
        f"**Images Tested**: {', '.join(gt_annotations.keys())}",
        f"**Target**: 3/4 images matched at IoU >= 0.50",
        "",
        "## Ground Truth Annotations",
        "",
        "| Image | GT BBox (xyxy) |",
        "|-------|----------------|",
    ]

    for img, bbox in gt_annotations.items():
        report_lines.append(f"| {img} | [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}] |")

    report_lines.extend([
        "",
        "## Results by Confidence Threshold",
        "",
        "| Conf | Matched/4 | TP | FP | FN | Precision | Recall | F1 | Target |",
        "|------|-----------|----|----|----|-----------|--------|----|--------|",
    ])

    for conf_str in conf_thresholds:
        conf_key = str(conf_str)
        summary = all_results[conf_key]["summary"]
        target_str = "YES" if summary["target_achieved"] else "NO"
        report_lines.append(
            f"| {conf_str:.2f} | {summary['matched_images']}/4 | "
            f"{summary['total_tp']} | {summary['total_fp']} | {summary['total_fn']} | "
            f"{summary['precision']:.4f} | {summary['recall']:.4f} | {summary['f1']:.4f} | {target_str} |"
        )

    report_lines.extend([
        "",
        "## Per-Image Detail at Best Operating Point",
        "",
        f"**Best Confidence Threshold**: {best_conf}",
        f"**Matched**: {best_result['matched_images']}/4",
        f"**Target Achieved**: {'YES' if best_result['target_achieved'] else 'NO'}",
        "",
        "| Image | Best IoU | Matched | Detections |",
        "|-------|----------|---------|------------|",
    ])

    for image_name in gt_annotations.keys():
        result = all_results[best_conf][image_name]
        det_count = len(result["detections"])
        report_lines.append(
            f"| {image_name} | {result['best_match_iou']:.4f} | "
            f"{'YES' if result['matched'] else 'NO'} | {det_count} |"
        )

    report_lines.extend([
        "",
        "## Detailed Detections at Best Operating Point",
        "",
    ])

    for image_name in gt_annotations.keys():
        result = all_results[best_conf][image_name]
        report_lines.append(f"### {image_name}")
        report_lines.append(f"- Ground Truth BBox: {result['ground_truth_bbox']}")
        report_lines.append(f"- Best Match IoU: {result['best_match_iou']:.4f}")
        report_lines.append(f"- Matched: {'Yes' if result['matched'] else 'No'}")
        if result["detections"]:
            report_lines.append("- Predicted Pothole Detections:")
            for det in result["detections"]:
                report_lines.append(
                    f"  - Conf: {det['confidence']:.4f}, BBox: [{det['bbox_xyxy'][0]:.1f}, {det['bbox_xyxy'][1]:.1f}, {det['bbox_xyxy'][2]:.1f}, {det['bbox_xyxy'][3]:.1f}]"
                )
        else:
            report_lines.append("- No pothole detections")
        report_lines.append("")

    report_lines.extend([
        "## Conclusion",
        "",
        f"The smoke test **{'PASSES' if best_result['target_achieved'] else 'FAILS'}** the 3/4 target at the best operating point (conf={best_conf}).",
        f"At conf={best_conf}: {best_result['matched_images']}/4 images matched at IoU >= 0.50.",
        "",
        "---",
        "*Generated by scripts/smoke_test_phase3.py*",
    ])

    report_path = output_dir / "smoke_test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()