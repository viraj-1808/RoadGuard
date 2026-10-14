#!/usr/bin/env python
"""
Comprehensive holdout evaluation for RoadGuard AI.
Evaluates both original (epoch72) and fine-tuned models on holdout set at multiple thresholds.
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
CLASS_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}

POTHOLE_CLASS_ID = 3

# Thresholds to test
CONF_THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
IOU_THRESHOLD_NMS = 0.7
IOU_THRESHOLD_MATCH = 0.50
IMGSZ = 720
DEVICE = "0"


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


def run_inference_on_image(
    model: YOLO,
    image_path: Path,
    conf_threshold: float,
    iou_threshold: float,
    imgsz: int,
    device: str,
) -> list[dict[str, Any]]:
    """Run inference on a single image and return all detections."""
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
                if conf >= conf_threshold:
                    detections.append({
                        "class_id": int(cls_id),
                        "class_name": CLASS_NAMES.get(int(cls_id), f"class_{int(cls_id)}"),
                        "confidence": float(conf),
                        "bbox_xyxy": [float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                    })
    return detections


def match_detections_to_gt(
    detections: list[dict[str, Any]],
    gt_annotations: list[dict[str, Any]],
    iou_threshold: float = 0.50,
) -> dict[str, Any]:
    """Match detections to ground truth annotations using IoU."""
    matched_gt = set()
    matched_det = set()

    # For each GT, find best matching detection
    for gt_idx, gt in enumerate(gt_annotations):
        gt_box = gt["bbox_xyxy"]
        gt_class = gt["class_id"]
        best_iou = 0.0
        best_det_idx = -1

        for det_idx, det in enumerate(detections):
            if det_idx in matched_det:
                continue
            if det["class_id"] != gt_class:
                continue
            iou = compute_iou(det["bbox_xyxy"], gt_box)
            if iou > best_iou and iou >= iou_threshold:
                best_iou = iou
                best_det_idx = det_idx

        if best_det_idx >= 0:
            matched_gt.add(gt_idx)
            matched_det.add(best_det_idx)

    # Count TP, FP, FN per class
    tp_per_class = {}
    fp_per_class = {}
    fn_per_class = {}

    # Initialize all classes
    for class_id in CLASS_NAMES:
        tp_per_class[class_id] = 0
        fp_per_class[class_id] = 0
        fn_per_class[class_id] = 0

    # TP: matched detections
    for det_idx in matched_det:
        cls = detections[det_idx]["class_id"]
        tp_per_class[cls] += 1

    # FP: unmatched detections
    for det_idx, det in enumerate(detections):
        if det_idx not in matched_det:
            fp_per_class[det["class_id"]] += 1

    # FN: unmatched GT
    for gt_idx, gt in enumerate(gt_annotations):
        if gt_idx not in matched_gt:
            fn_per_class[gt["class_id"]] += 1

    return {
        "tp_per_class": tp_per_class,
        "fp_per_class": fp_per_class,
        "fn_per_class": fn_per_class,
        "matched_gt_indices": matched_gt,
        "matched_det_indices": matched_det,
    }


def compute_metrics(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Compute precision, recall, F1."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def evaluate_model_on_holdout(
    model: YOLO,
    model_name: str,
    holdout_images: list[str],
    gt_data: dict[str, Any],
    input_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Evaluate a model on the holdout set at all confidence thresholds."""

    print(f"\n{'='*60}")
    print(f"Evaluating {model_name}")
    print(f"{'='*60}")

    all_results = {}

    for conf_thresh in CONF_THRESHOLDS:
        print(f"\n  Confidence threshold: {conf_thresh}")

        # Aggregate metrics
        total_tp = {c: 0 for c in CLASS_NAMES}
        total_fp = {c: 0 for c in CLASS_NAMES}
        total_fn = {c: 0 for c in CLASS_NAMES}
        image_results = {}
        correct_images = 0

        for image_name in holdout_images:
            image_path = input_dir / image_name

            # Get GT for this image
            gt_entry = None
            for img in gt_data["images"]:
                if img["image"] == image_name:
                    gt_entry = img
                    break

            if gt_entry is None:
                print(f"    {image_name}: No GT entry found")
                continue

            gt_annotations = gt_entry.get("annotations", [])
            gt_status = gt_entry.get("status", "UNCERTAIN")

            # Run inference
            detections = run_inference_on_image(
                model, image_path, conf_thresh, IOU_THRESHOLD_NMS, IMGSZ, DEVICE
            )

            # Match to GT
            match_result = match_detections_to_gt(detections, gt_annotations, IOU_THRESHOLD_MATCH)

            # Update totals
            for cls in CLASS_NAMES:
                total_tp[cls] += match_result["tp_per_class"][cls]
                total_fp[cls] += match_result["fp_per_class"][cls]
                total_fn[cls] += match_result["fn_per_class"][cls]

            # Image-level correctness: all GT matched AND no FP
            all_gt_matched = len(match_result["matched_gt_indices"]) == len(gt_annotations)
            no_fp = sum(match_result["fp_per_class"].values()) == 0
            image_correct = all_gt_matched and no_fp

            if image_correct:
                correct_images += 1

            # Pothole-specific
            pothole_tp = match_result["tp_per_class"][POTHOLE_CLASS_ID]
            pothole_fp = match_result["fp_per_class"][POTHOLE_CLASS_ID]
            pothole_fn = match_result["fn_per_class"][POTHOLE_CLASS_ID]

            image_results[image_name] = {
                "status": gt_status,
                "gt_annotations": gt_annotations,
                "detections": detections,
                "tp_per_class": match_result["tp_per_class"],
                "fp_per_class": match_result["fp_per_class"],
                "fn_per_class": match_result["fn_per_class"],
                "pothole_tp": pothole_tp,
                "pothole_fp": pothole_fp,
                "pothole_fn": pothole_fn,
                "image_correct": image_correct,
                "all_gt_matched": all_gt_matched,
                "no_fp": no_fp,
            }

            if gt_status == "CLEAR":
                print(f"    {image_name}: TP={sum(match_result['tp_per_class'].values())}, "
                      f"FP={sum(match_result['fp_per_class'].values())}, "
                      f"FN={sum(match_result['fn_per_class'].values())}, "
                      f"Correct={image_correct}")

        # Compute per-class metrics
        per_class_metrics = {}
        for cls in CLASS_NAMES:
            tp = total_tp[cls]
            fp = total_fp[cls]
            fn = total_fn[cls]
            p, r, f1 = compute_metrics(tp, fp, fn)
            per_class_metrics[cls] = {
                "class_name": CLASS_NAMES[cls],
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": p,
                "recall": r,
                "f1": f1,
            }

        # Overall metrics (macro average)
        valid_classes = [c for c in CLASS_NAMES if (total_tp[c] + total_fp[c] + total_fn[c]) > 0]
        if valid_classes:
            macro_p = np.mean([per_class_metrics[c]["precision"] for c in valid_classes])
            macro_r = np.mean([per_class_metrics[c]["recall"] for c in valid_classes])
            macro_f1 = np.mean([per_class_metrics[c]["f1"] for c in valid_classes])
        else:
            macro_p = macro_r = macro_f1 = 0.0

        # Overall micro metrics
        total_tp_all = sum(total_tp.values())
        total_fp_all = sum(total_fp.values())
        total_fn_all = sum(total_fn.values())
        micro_p, micro_r, micro_f1 = compute_metrics(total_tp_all, total_fp_all, total_fn_all)

        # Pothole-specific
        pothole_tp_total = total_tp[POTHOLE_CLASS_ID]
        pothole_fp_total = total_fp[POTHOLE_CLASS_ID]
        pothole_fn_total = total_fn[POTHOLE_CLASS_ID]
        pothole_p, pothole_r, pothole_f1 = compute_metrics(pothole_tp_total, pothole_fp_total, pothole_fn_total)

        all_results[conf_thresh] = {
            "confidence_threshold": conf_thresh,
            "per_class": per_class_metrics,
            "macro": {"precision": macro_p, "recall": macro_r, "f1": macro_f1},
            "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f1},
            "pothole": {
                "tp": pothole_tp_total,
                "fp": pothole_fp_total,
                "fn": pothole_fn_total,
                "precision": pothole_p,
                "recall": pothole_r,
                "f1": pothole_f1,
            },
            "total_images": len(holdout_images),
            "correct_images": correct_images,
            "image_accuracy": correct_images / len(holdout_images) if holdout_images else 0.0,
            "image_details": image_results,
        }

        print(f"    Micro P={micro_p:.4f}, R={micro_r:.4f}, F1={micro_f1:.4f}")
        print(f"    Pothole P={pothole_p:.4f}, R={pothole_r:.4f}, F1={pothole_f1:.4f}")
        print(f"    Image Accuracy: {correct_images}/{len(holdout_images)} = {correct_images/len(holdout_images):.4f}")

    return all_results


def save_threshold_comparison_csv(
    original_results: dict,
    finetuned_results: dict,
    output_path: Path,
):
    """Save threshold comparison CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        header = [
            "Model", "Confidence_Threshold",
            # Per-class metrics
            "Longitudinal_Crack_TP", "Longitudinal_Crack_FP", "Longitudinal_Crack_FN",
            "Longitudinal_Crack_Precision", "Longitudinal_Crack_Recall", "Longitudinal_Crack_F1",
            "Transverse_Crack_TP", "Transverse_Crack_FP", "Transverse_Crack_FN",
            "Transverse_Crack_Precision", "Transverse_Crack_Recall", "Transverse_Crack_F1",
            "Alligator_Crack_TP", "Alligator_Crack_FP", "Alligator_Crack_FN",
            "Alligator_Crack_Precision", "Alligator_Crack_Recall", "Alligator_Crack_F1",
            "Pothole_TP", "Pothole_FP", "Pothole_FN",
            "Pothole_Precision", "Pothole_Recall", "Pothole_F1",
            # Macro/Micro
            "Macro_Precision", "Macro_Recall", "Macro_F1",
            "Micro_Precision", "Micro_Recall", "Micro_F1",
            # Image-level
            "Correct_Images", "Total_Images", "Image_Accuracy",
        ]
        writer.writerow(header)

        for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
            for conf in CONF_THRESHOLDS:
                r = results[conf]
                row = [
                    model_name, conf,
                    # Longitudinal crack (0)
                    r["per_class"][0]["tp"], r["per_class"][0]["fp"], r["per_class"][0]["fn"],
                    r["per_class"][0]["precision"], r["per_class"][0]["recall"], r["per_class"][0]["f1"],
                    # Transverse crack (1)
                    r["per_class"][1]["tp"], r["per_class"][1]["fp"], r["per_class"][1]["fn"],
                    r["per_class"][1]["precision"], r["per_class"][1]["recall"], r["per_class"][1]["f1"],
                    # Alligator crack (2)
                    r["per_class"][2]["tp"], r["per_class"][2]["fp"], r["per_class"][2]["fn"],
                    r["per_class"][2]["precision"], r["per_class"][2]["recall"], r["per_class"][2]["f1"],
                    # Pothole (3)
                    r["per_class"][3]["tp"], r["per_class"][3]["fp"], r["per_class"][3]["fn"],
                    r["per_class"][3]["precision"], r["per_class"][3]["recall"], r["per_class"][3]["f1"],
                    # Macro/Micro
                    r["macro"]["precision"], r["macro"]["recall"], r["macro"]["f1"],
                    r["micro"]["precision"], r["micro"]["recall"], r["micro"]["f1"],
                    # Image-level
                    r["correct_images"], r["total_images"], r["image_accuracy"],
                ]
                writer.writerow(row)

    print(f"Threshold comparison CSV saved to: {output_path}")


def generate_markdown_report(
    original_results: dict,
    finetuned_results: dict,
    holdout_images: list[str],
    gt_data: dict,
    output_path: Path,
):
    """Generate comprehensive markdown report."""

    lines = [
        "# Holdout Set Evaluation Report",
        "",
        f"**Generated**: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"**Holdout Images**: {len(holdout_images)}",
        f"**CLEAR Status Images**: {sum(1 for img in gt_data['images'] if img['image'] in holdout_images and img['status'] == 'CLEAR')}",
        f"**UNCERTAIN Status Images**: {sum(1 for img in gt_data['images'] if img['image'] in holdout_images and img['status'] == 'UNCERTAIN')}",
        "",
        "## Holdout Set Composition",
        "",
        "| Image | Status | Annotations | Classes |",
        "|-------|--------|-------------|---------|",
    ]

    for img in gt_data["images"]:
        if img["image"] in holdout_images:
            classes = ", ".join([f"{a['class_name']}({a['class_id']})" for a in img["annotations"]]) or "None"
            lines.append(f"| {img['image']} | {img['status']} | {len(img['annotations'])} | {classes} |")

    lines.extend([
        "",
        "## Threshold Comparison: Original (Epoch72) vs Fine-Tuned",
        "",
        "### Overall Micro Metrics",
        "",
        "| Model | Conf | Micro_P | Micro_R | Micro_F1 | Pothole_P | Pothole_R | Pothole_F1 | Img_Acc |",
        "|-------|------|---------|---------|----------|-----------|-----------|------------|---------|",
    ])

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        for conf in CONF_THRESHOLDS:
            r = results[conf]
            lines.append(
                f"| {model_name} | {conf:.2f} | "
                f"{r['micro']['precision']:.4f} | {r['micro']['recall']:.4f} | {r['micro']['f1']:.4f} | "
                f"{r['pothole']['precision']:.4f} | {r['pothole']['recall']:.4f} | {r['pothole']['f1']:.4f} | "
                f"{r['image_accuracy']:.4f} |"
            )

    lines.extend([
        "",
        "### Per-Class Metrics at Each Threshold",
        "",
    ])

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        lines.append(f"#### {model_name}")
        lines.append("")
        lines.append("| Conf | Class | TP | FP | FN | Precision | Recall | F1 |")
        lines.append("|------|-------|----|----|----|-----------|--------|----|")
        for conf in CONF_THRESHOLDS:
            r = results[conf]
            for cls in CLASS_NAMES:
                pc = r["per_class"][cls]
                lines.append(
                    f"| {conf:.2f} | {CLASS_NAMES[cls]} | {pc['tp']} | {pc['fp']} | {pc['fn']} | "
                    f"{pc['precision']:.4f} | {pc['recall']:.4f} | {pc['f1']:.4f} |"
                )
        lines.append("")

    lines.extend([
        "### Image-Level Correctness",
        "",
        "| Model | Conf | Correct/Total | Accuracy | CLEAR Correct | CLEAR Total |",
        "|-------|------|---------------|----------|---------------|-------------|",
    ])

    clear_images = [img["image"] for img in gt_data["images"] if img["image"] in holdout_images and img["status"] == "CLEAR"]

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        for conf in CONF_THRESHOLDS:
            r = results[conf]
            clear_correct = sum(1 for img in clear_images if r["image_details"][img]["image_correct"])
            lines.append(
                f"| {model_name} | {conf:.2f} | {r['correct_images']}/{r['total_images']} | "
                f"{r['image_accuracy']:.4f} | {clear_correct}/{len(clear_images)} | {len(clear_images)} |"
            )

    lines.extend([
        "",
        "### Pothole-Specific Performance",
        "",
        "| Model | Conf | TP | FP | FN | Precision | Recall | F1 |",
        "|-------|------|----|----|----|-----------|--------|----|",
    ])

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        for conf in CONF_THRESHOLDS:
            r = results[conf]
            p = r["pothole"]
            lines.append(
                f"| {model_name} | {conf:.2f} | {p['tp']} | {p['fp']} | {p['fn']} | "
                f"{p['precision']:.4f} | {p['recall']:.4f} | {p['f1']:.4f} |"
            )

    # Best operating points
    lines.extend([
        "",
        "## Best Operating Points",
        "",
    ])

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        best_conf = max(results.keys(), key=lambda k: results[k]["micro"]["f1"])
        best = results[best_conf]
        lines.append(f"### {model_name}")
        lines.append(f"- **Best Confidence Threshold**: {best_conf}")
        lines.append(f"- **Micro F1**: {best['micro']['f1']:.4f}")
        lines.append(f"- **Pothole F1**: {best['pothole']['f1']:.4f}")
        lines.append(f"- **Image Accuracy**: {best['image_accuracy']:.4f} ({best['correct_images']}/{best['total_images']})")
        lines.append("")

    # Extrapolation to 100 images
    lines.extend([
        "## Extrapolation to 100-Image Target",
        "",
        "Only 39 images total available (14 in holdout, 5 with CLEAR annotations).",
        "The 75/100 target requires evaluation on a larger, fully-annotated test set.",
        "",
        "**Current Holdout Results (5 CLEAR images):**",
        "",
    ])

    for model_name, results in [("Original_Epoch72", original_results), ("FineTuned", finetuned_results)]:
        best_conf = max(results.keys(), key=lambda k: results[k]["micro"]["f1"])
        best = results[best_conf]
        clear_correct = sum(1 for img in clear_images if best["image_details"][img]["image_correct"])
        lines.append(f"- **{model_name}** (conf={best_conf}): {clear_correct}/{len(clear_images)} CLEAR images correct")
        lines.append(f"  - Extrapolated to 100 CLEAR images: ~{int(clear_correct / len(clear_images) * 100) if clear_images else 0}/100")
        lines.append("")

    lines.extend([
        "### Gap Analysis",
        "",
        "- **Available CLEAR annotations**: 5/14 holdout images (36%)",
        "- **Total dataset**: 39 images (vs 100 target)",
        "- **UNCERTAIN images**: 9/14 holdout images have no ground truth",
        "- **Recommendation**: Human annotation of UNCERTAIN images needed for reliable 100-image evaluation",
        "",
        "---",
        "*Generated by holdout_evaluation.py*",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Markdown report saved to: {output_path}")


def main():
    # Paths
    project_root = Path(__file__).resolve().parent
    original_model_path = project_root / "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt"
    finetuned_model_path = project_root / "runs/detect/experiments/training/yol11s_microtrial_w2_pf2/weights/last.pt"
    gt_path = project_root / "experiments/results/real_world_model_improvement/ground_truth_annotations.json"
    split_path = project_root / "experiments/results/real_world_model_improvement/data_split.json"
    input_dir = project_root / "validation/manual/input"
    output_dir = project_root / "experiments/results/real_world_model_improvement"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load ground truth and split
    with open(gt_path) as f:
        gt_data = json.load(f)
    with open(split_path) as f:
        split_data = json.load(f)

    holdout_images = split_data["holdout"]

    print(f"Holdout images: {holdout_images}")
    print(f"Original model: {original_model_path}")
    print(f"Fine-tuned model: {finetuned_model_path}")

    # Load models
    print("\nLoading original model (epoch72)...")
    original_model = YOLO(str(original_model_path))
    print(f"Classes: {original_model.model.names}")

    print("\nLoading fine-tuned model (microtrial)...")
    finetuned_model = YOLO(str(finetuned_model_path))
    print(f"Classes: {finetuned_model.model.names}")

    # Warm up
    dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
    original_model.predict(dummy, imgsz=IMGSZ, device=DEVICE, verbose=False)
    finetuned_model.predict(dummy, imgsz=IMGSZ, device=DEVICE, verbose=False)

    # Evaluate both models
    original_results = evaluate_model_on_holdout(
        original_model, "Original_Epoch72", holdout_images, gt_data, input_dir, output_dir
    )

    finetuned_results = evaluate_model_on_holdout(
        finetuned_model, "FineTuned", holdout_images, gt_data, input_dir, output_dir
    )

    # Save results
    csv_path = output_dir / "THRESHOLD_COMPARISON.csv"
    save_threshold_comparison_csv(original_results, finetuned_results, csv_path)

    md_path = output_dir / "HOLDOUT_EVALUATION.md"
    generate_markdown_report(original_results, finetuned_results, holdout_images, gt_data, md_path)

    # Also save detailed JSON
    json_path = output_dir / "holdout_evaluation_detailed.json"
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "holdout_images": holdout_images,
            "confidence_thresholds": CONF_THRESHOLDS,
            "iou_threshold_match": IOU_THRESHOLD_MATCH,
            "original_model": str(original_model_path),
            "finetuned_model": str(finetuned_model_path),
            "original_results": original_results,
            "finetuned_results": finetuned_results,
        }, f, indent=2, default=str)
    print(f"Detailed JSON saved to: {json_path}")

    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()