import json
import csv
from pathlib import Path
import numpy as np

def compute_iou(box1, box2):
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


def match_detections_to_gt(detections, gt_boxes, iou_threshold=0.5):
    """Match detections to GT boxes using greedy IoU matching."""
    if not detections or not gt_boxes:
        return 0, len(detections), len(gt_boxes), []

    iou_matrix = np.zeros((len(detections), len(gt_boxes)))
    for i, det in enumerate(detections):
        for j, gt in enumerate(gt_boxes):
            if det["class_id"] == gt["class_id"]:
                iou_matrix[i, j] = compute_iou(det["bbox_xyxy"], gt["bbox_xyxy"])

    matches = []
    used_dets = set()
    used_gts = set()

    valid_pairs = []
    for i in range(len(detections)):
        for j in range(len(gt_boxes)):
            if iou_matrix[i, j] >= iou_threshold:
                valid_pairs.append((iou_matrix[i, j], i, j))

    valid_pairs.sort(reverse=True)

    for iou, det_idx, gt_idx in valid_pairs:
        if det_idx not in used_dets and gt_idx not in used_gts:
            matches.append((det_idx, gt_idx, iou))
            used_dets.add(det_idx)
            used_gts.add(gt_idx)

    tp = len(matches)
    fp = len(detections) - tp
    fn = len(gt_boxes) - tp

    return tp, fp, fn, matches


def evaluate_image(image_name, gt_boxes, detections, inference_time_ms, tile_count, method_name):
    """Evaluate detections against GT and return metrics."""
    tp, fp, fn, matches = match_detections_to_gt(detections, gt_boxes, 0.5)

    # Best IoU per class
    best_ious = {}
    for gt in gt_boxes:
        cls_name = gt["class_name"]
        best_iou = 0.0
        for det in detections:
            if det["class_id"] == gt["class_id"]:
                iou = compute_iou(det["bbox_xyxy"], gt["bbox_xyxy"])
                if iou > best_iou:
                    best_iou = iou
        best_ious[cls_name] = best_iou

    matched_any = len(matches) > 0

    return {
        "image": image_name,
        "method": method_name,
        "gt_status": "CLEAR",
        "gt_boxes": len(gt_boxes),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": tp / (tp + fp) if (tp + fp) > 0 else 0.0,
        "recall": tp / (tp + fn) if (tp + fn) > 0 else 0.0,
        "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0,
        "best_ious": best_ious,
        "matched_any": matched_any,
        "num_detections": len(detections),
        "inference_time_ms": inference_time_ms,
        "tile_count": tile_count,
        "matches": matches,
    }


def main():
    # Load ground truth
    with open(r"experiments\results\real_world_model_improvement\ground_truth_annotations.json") as f:
        gt_data = json.load(f)

    gt_dict = {}
    for img_info in gt_data["images"]:
        if img_info["image"] in ["road018.jpg", "road021.jpg"]:
            gt_dict[img_info["image"]] = {
                "status": img_info["status"],
                "annotations": [
                    {
                        "class_id": ann["class_id"],
                        "class_name": ann["class_name"],
                        "bbox_xyxy": ann["bbox_xyxy"],
                    }
                    for ann in img_info["annotations"]
                ],
            }

    # Load SAHI predictions
    sahi_dir = Path(r"experiments\results\real_world_model_improvement\tiled_v1")
    sahi_preds = {}
    for img in ["road018.jpg", "road021.jpg"]:
        json_path = sahi_dir / f"{Path(img).stem}_tiled_predictions.json"
        with open(json_path) as f:
            sahi_preds[img] = json.load(f)

    # Load standard predictions
    std_preds = {}
    for img in ["road018.jpg", "road021.jpg"]:
        json_path = sahi_dir / f"{Path(img).stem}_standard_predictions.json"
        with open(json_path) as f:
            std_preds[img] = json.load(f)

    # Evaluate both methods
    results = []
    for img in ["road018.jpg", "road021.jpg"]:
        gt_boxes = gt_dict[img]["annotations"]

        # Standard inference
        std_result = evaluate_image(
            img,
            gt_boxes,
            std_preds[img]["detections"],
            std_preds[img]["inference_time_ms"],
            1,
            "standard",
        )
        results.append(std_result)

        # SAHI inference
        sahi_result = evaluate_image(
            img,
            gt_boxes,
            sahi_preds[img]["detections"],
            sahi_preds[img]["inference_time_ms"],
            sahi_preds[img]["tile_count"],
            "sahi_tiled",
        )
        results.append(sahi_result)

    # Print summary
    print("=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    for r in results:
        print(f"\n{r['image']} - {r['method']}:")
        print(f"  TP={r['tp']}, FP={r['fp']}, FN={r['fn']}")
        print(f"  Precision={r['precision']:.4f}, Recall={r['recall']:.4f}, F1={r['f1']:.4f}")
        print(f"  Time={r['inference_time_ms']:.1f}ms, Tiles={r['tile_count']}")
        print(f"  Matched any: {r['matched_any']}")
        for cls, iou in r["best_ious"].items():
            print(f"  Best IoU ({cls}): {iou:.4f}")

    # Save CSV comparison
    csv_path = sahi_dir / "STANDARD_VS_TILED.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "image", "method", "gt_status", "gt_boxes",
            "tp", "fp", "fn", "precision", "recall", "f1",
            "best_iou_pothole", "best_iou_alligator", "best_iou_longitudinal", "best_iou_transverse",
            "matched_any", "num_detections", "inference_time_ms", "tile_count",
        ])
        for r in results:
            writer.writerow([
                r["image"],
                r["method"],
                r["gt_status"],
                r["gt_boxes"],
                r["tp"],
                r["fp"],
                r["fn"],
                f"{r['precision']:.4f}",
                f"{r['recall']:.4f}",
                f"{r['f1']:.4f}",
                f"{r['best_ious'].get('pothole', 0.0):.4f}",
                f"{r['best_ious'].get('alligator_crack', 0.0):.4f}",
                f"{r['best_ious'].get('longitudinal_crack', 0.0):.4f}",
                f"{r['best_ious'].get('transverse_crack', 0.0):.4f}",
                r["matched_any"],
                r["num_detections"],
                f"{r['inference_time_ms']:.1f}",
                r["tile_count"],
            ])
    print(f"\nCSV saved to: {csv_path}")

    # Save detailed JSON
    json_path = sahi_dir / "TILED_INFERENCE_RESULTS.json"
    with open(json_path, "w") as f:
        json.dump({
            "experiment": "Phase B: SAHI Tiled Inference Comparison",
            "checkpoint": r"runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt",
            "images": ["road018.jpg", "road021.jpg"],
            "inference_config": {
                "standard": {"imgsz": 720, "conf": 0.05, "iou": 0.7, "device": "0"},
                "sahi_tiled": {
                    "slice_height": 640,
                    "slice_width": 640,
                    "overlap_height_ratio": 0.2,
                    "overlap_width_ratio": 0.2,
                    "conf": 0.05,
                    "iou": 0.7,
                    "postprocess": "NMS",
                    "match_metric": "IOU",
                    "match_threshold": 0.5,
                    "device": "0",
                },
            },
            "matching_config": {
                "iou_threshold": 0.5,
                "class_match_required": True,
            },
            "results": results,
        }, f, indent=2)
    print(f"JSON saved to: {json_path}")

    # Generate Markdown report
    md_path = sahi_dir / "TILED_INFERENCE_REPORT.md"
    with open(md_path, "w") as f:
        f.write("# SAHI Tiled Inference vs Standard Inference Comparison\n\n")
        f.write("## Experiment Overview\n\n")
        f.write("- **Checkpoint**: `epoch72.pt` (YOLO11s)\n")
        f.write("- **Images**: road018.jpg (4096x3072), road021.jpg (3072x4096)\n")
        f.write("- **Ground Truth**: Both images labeled as CLEAR with single defect each\n")
        f.write("- **Standard Inference**: imgsz=720 (letterbox to 736x736), conf=0.05, NMS IoU=0.7\n")
        f.write("- **SAHI Tiled Inference**: 640x640 slices, 20% overlap, NMS post-process (IoU=0.5), conf=0.05\n\n")

        f.write("## Per-Image Results\n\n")

        for img in ["road018.jpg", "road021.jpg"]:
            f.write(f"### {img}\n\n")
            gt = gt_dict[img]
            f.write(f"- **GT Status**: {gt['status']}\n")
            f.write(f"- **GT Annotations**: {len(gt['annotations'])} box(es)\n")
            for ann in gt["annotations"]:
                f.write(f"  - Class {ann['class_id']} ({ann['class_name']}): {ann['bbox_xyxy']}\n")
            f.write("\n")

            for method in ["standard", "sahi_tiled"]:
                r = next(x for x in results if x["image"] == img and x["method"] == method)
                f.write(f"#### {method.upper()}\n\n")
                f.write(f"- **Detections**: {r['num_detections']}\n")
                f.write(f"- **TP**: {r['tp']}, **FP**: {r['fp']}, **FN**: {r['fn']}\n")
                f.write(f"- **Precision**: {r['precision']:.4f}, **Recall**: {r['recall']:.4f}, **F1**: {r['f1']:.4f}\n")
                f.write(f"- **Inference Time**: {r['inference_time_ms']:.1f} ms\n")
                f.write(f"- **Tile Count**: {r['tile_count']}\n")
                f.write(f"- **Matched Any GT**: {r['matched_any']}\n")
                for cls, iou in r["best_ious"].items():
                    f.write(f"- **Best IoU ({cls})**: {iou:.4f}\n")
                if r["matches"]:
                    f.write("- **IoU Matches**:\n")
                    for det_idx, gt_idx, iou in r["matches"]:
                        det = (std_preds[img]["detections"] if method == "standard" else sahi_preds[img]["detections"])[det_idx]
                        gt_box = gt_boxes[gt_idx]
                        f.write(f"  - Detection {det_idx} ({det['class_name']} conf={det['confidence']:.4f}) <-> GT {gt_idx} ({gt_box['class_name']}): IoU={iou:.4f}\n")
                f.write("\n")

        f.write("## Summary Comparison\n\n")
        f.write("| Image | Method | TP | FP | FN | Precision | Recall | F1 | Time (ms) | Tiles |\n")
        f.write("|-------|--------|----|----|----|-----------|--------|----|-----------|-------|\n")
        for r in results:
            f.write(f"| {r['image']} | {r['method']} | {r['tp']} | {r['fp']} | {r['fn']} | ")
            f.write(f"{r['precision']:.4f} | {r['recall']:.4f} | {r['f1']:.4f} | ")
            f.write(f"{r['inference_time_ms']:.1f} | {r['tile_count']} |\n")

        f.write("\n## Key Findings\n\n")
        f.write("1. **Standard Inference**: 0 detections on both 4K images (confirmed by audit_v2)\n")
        f.write("2. **SAHI Tiled Inference**: Finds detections but they are **false positives** (wrong location/class)\n")
        f.write("   - road018: 6 detections (3 pothole, 3 transverse_crack) - all far from GT pothole\n")
        f.write("   - road021: 2 detections (1 transverse_crack, 1 pothole) - all far from GT alligator_crack\n")
        f.write("3. **Root Cause**: Model detects artifacts/other patterns, not the annotated defects\n")
        f.write("4. **Qualitative Assessment**: Ground truth may be incomplete or model has domain gap\n")
        f.write("5. **Runtime**: SAHI is ~10-25x slower than standard inference (expected)\n")

    print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()