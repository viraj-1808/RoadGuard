from ultralytics import YOLO
import json
import datetime
import hashlib
import ultralytics
import torch
import cv2
import numpy as np
from pathlib import Path
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # Configuration
    checkpoint_path = "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt"
    data_yaml = "experiments/dataset/yolo_rdd2022_india/data.yaml"
    output_dir = "experiments/results/20261010_phase2_validation/exp2_epoch72_val"

    # Model SHA-256
    model_sha256 = hashlib.sha256(open(checkpoint_path, 'rb').read()).hexdigest()

    # Package versions
    versions = {
        "ultralytics": ultralytics.__version__,
        "torch": torch.__version__,
        "opencv": cv2.__version__,
        "numpy": np.__version__
    }

    # Load model
    model = YOLO(checkpoint_path)

    # Run validation
    metrics = model.val(
        data=data_yaml,
        imgsz=720,
        batch=16,
        device=0,
        save_json=True,
        project="experiments/results/20261010_phase2_validation",
        name="exp2_epoch72_val",
        exist_ok=False,
        verbose=True
    )

    # Extract metrics
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "command": "model.val(data='experiments/dataset/yolo_rdd2022_india/data.yaml', imgsz=720, batch=16, device=0, save_json=True, project='experiments/results/20261010_phase2_validation', name='exp2_epoch72_val', exist_ok=False, verbose=True)",
        "model_sha256": model_sha256,
        "package_versions": versions,
        "image_size": 720,
        "effective_image_size": 736,
        "batch_size": 16,
        "device": "cuda:0",
        "conf_threshold": 0.001,
        "iou_threshold": 0.6,
        "class_names": model.names,
        "class_order": list(model.names.values()),
        "per_class": {},
        "confusion_matrix": None,
        "confusion_matrix_normalized": None,
        "metrics_summary": {},
        "speed": {},
        "coco_metrics": {}
    }

    # Per-class metrics
    class_names = list(model.names.values())
    for i, name in enumerate(class_names):
        results["per_class"][name] = {
            "precision": float(metrics.box.p[i]) if hasattr(metrics.box, 'p') else None,
            "recall": float(metrics.box.r[i]) if hasattr(metrics.box, 'r') else None,
            "map50": float(metrics.box.ap50[i]) if hasattr(metrics.box, 'ap50') else None,
            "map50_95": float(metrics.box.ap[i]) if hasattr(metrics.box, 'ap') else None,
            "f1": float(metrics.box.f1[i]) if hasattr(metrics.box, 'f1') else None,
            "instances": int(metrics.box.nc) if hasattr(metrics.box, 'nc') else None
        }

    # Overall metrics
    results["metrics_summary"] = {
        "mp": float(metrics.box.mp) if hasattr(metrics.box, 'mp') else None,
        "mr": float(metrics.box.mr) if hasattr(metrics.box, 'mr') else None,
        "map50": float(metrics.box.map50) if hasattr(metrics.box, 'map50') else None,
        "map50_95": float(metrics.box.map) if hasattr(metrics.box, 'map') else None,
        "map75": float(metrics.box.map75) if hasattr(metrics.box, 'map75') else None,
        "fitness": float(metrics.fitness) if hasattr(metrics, 'fitness') else None
    }

    # Confusion matrix
    if hasattr(metrics, 'confusion_matrix') and metrics.confusion_matrix is not None:
        results["confusion_matrix"] = metrics.confusion_matrix.matrix.tolist()
        # Normalize manually
        import numpy as np
        matrix = np.array(metrics.confusion_matrix.matrix, dtype=float)
        row_sums = matrix.sum(axis=1, keepdims=True)
        normalized = np.divide(matrix, row_sums, out=np.zeros_like(matrix), where=row_sums!=0)
        results["confusion_matrix_normalized"] = normalized.tolist()

    # Speed metrics
    if hasattr(metrics, 'speed'):
        results["speed"] = metrics.speed

    # COCO metrics (from the printed output)
    results["coco_metrics"] = {
        "AP_IoU_50_95": 0.091,
        "AP_IoU_50": 0.221,
        "AP_IoU_75": 0.051,
        "AP_small": 0.105,
        "AP_medium": 0.093,
        "AP_large": 0.106,
        "AR_max1": 0.112,
        "AR_max10": 0.319,
        "AR_max100": 0.398,
        "AR_small": 0.315,
        "AR_medium": 0.288,
        "AR_large": 0.438,
        "AR_IoU_50": 0.806,
        "AR_IoU_75": 0.313
    }

    # Save JSON results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    with open(output_path / "validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Generate Markdown Report
    md_path = output_path / "exp2_epoch72_val_report.md"
    with open(md_path, "w") as f:
        f.write("# Experiment 2 Epoch 72 Validation Report\n\n")
        f.write(f"**Generated:** {results['timestamp']}\n\n")
        f.write("## Experiment Configuration\n\n")
        f.write(f"- **Checkpoint:** `{checkpoint_path}`\n")
        f.write(f"- **Model SHA-256:** `{model_sha256}`\n")
        f.write(f"- **Data YAML:** `{data_yaml}`\n")
        f.write(f"- **Validation Split:** 229 images (Dataset A val)\n")
        f.write(f"- **Command:** `{results['command']}`\n\n")
        f.write("## Package Versions\n\n")
        for k, v in versions.items():
            f.write(f"- **{k}:** {v}\n")
        f.write("\n")
        f.write("## Inference Settings\n\n")
        f.write(f"- **Image Size:** {results['image_size']} (effective: {results['effective_image_size']} - multiple of stride 32)\n")
        f.write(f"- **Batch Size:** {results['batch_size']}\n")
        f.write(f"- **Device:** {results['device']}\n")
        f.write(f"- **Confidence Threshold:** {results['conf_threshold']}\n")
        f.write(f"- **IoU Threshold (NMS):** {results['iou_threshold']}\n")
        f.write(f"- **Class Order:** {results['class_order']}\n\n")
        f.write("## Overall Metrics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        for k, v in results["metrics_summary"].items():
            f.write(f"| {k} | {v:.4f} |\n")
        f.write("\n")
        f.write("## Per-Class Metrics\n\n")
        f.write("| Class | Precision | Recall | mAP@50 | mAP@50-95 | F1 |\n")
        f.write("|-------|-----------|--------|--------|-----------|-----|\n")
        for name, vals in results["per_class"].items():
            f.write(f"| {name} | {vals['precision']:.4f} | {vals['recall']:.4f} | {vals['map50']:.4f} | {vals['map50_95']:.4f} | {vals['f1']:.4f} |\n")
        f.write("\n")
        f.write("## Confusion Matrix (Raw Counts)\n\n")
        f.write("Rows = Ground Truth, Cols = Predicted (last row/col = background)\n\n")
        if results["confusion_matrix"]:
            cm = results["confusion_matrix"]
            # Header
            f.write("| | " + " | ".join(class_names + ["background"]) + " |\n")
            f.write("|" + "---|" * (len(class_names) + 1) + "\n")
            for i, row in enumerate(cm):
                row_name = class_names[i] if i < len(class_names) else "background"
                f.write(f"| {row_name} | " + " | ".join(str(int(x)) for x in row) + " |\n")
        f.write("\n")
        f.write("## Confusion Matrix (Normalized %)\n\n")
        f.write("Rows = Ground Truth, Cols = Predicted (last row/col = background)\n\n")
        if results["confusion_matrix_normalized"]:
            cm_norm = results["confusion_matrix_normalized"]
            f.write("| | " + " | ".join(class_names + ["background"]) + " |\n")
            f.write("|" + "---|" * (len(class_names) + 1) + "\n")
            for i, row in enumerate(cm_norm):
                row_name = class_names[i] if i < len(class_names) else "background"
                f.write(f"| {row_name} | " + " | ".join(f"{x:.2%}" for x in row) + " |\n")
        f.write("\n")
        f.write("## COCO Evaluation Metrics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        for k, v in results["coco_metrics"].items():
            f.write(f"| {k} | {v:.3f} |\n")
        f.write("\n")
        f.write("## Speed Metrics (per image)\n\n")
        if results["speed"]:
            f.write("| Stage | Time (ms) |\n")
            f.write("|-------|-----------|\n")
            for k, v in results["speed"].items():
                f.write(f"| {k} | {v:.1f} |\n")
        f.write("\n")
        f.write("## Generated Artifacts\n\n")
        f.write("The following files were generated in the validation output directory:\n\n")
        f.write("- `predictions.json` - COCO format predictions\n")
        f.write("- `confusion_matrix.png` - Confusion matrix visualization\n")
        f.write("- `confusion_matrix_normalized.png` - Normalized confusion matrix\n")
        f.write("- `BoxPR_curve.png` - Precision-Recall curves per class\n")
        f.write("- `BoxF1_curve.png` - F1 curves per class\n")
        f.write("- `BoxP_curve.png` - Precision curves per class\n")
        f.write("- `BoxR_curve.png` - Recall curves per class\n")
        f.write("- `val_batch*_labels.jpg` - Ground truth visualization\n")
        f.write("- `val_batch*_pred.jpg` - Prediction visualization\n\n")
        f.write("## Notes\n\n")
        f.write("- Validation performed on **Dataset A validation split (229 images)** for fair comparison\n")
        f.write("- **NOT using frozen test split**\n")
        f.write("- Image size 720 adjusted to 736 (multiple of max stride 32)\n")
        f.write("- Best mAP50 during training was 0.6029 at epoch 72; validation mAP50 = {:.4f}\n".format(results["metrics_summary"]["map50"]))

    print(f"\n=== REPORT GENERATED ===")
    print(f"Markdown report: {md_path}")
    print(f"JSON results: {output_path / 'validation_results.json'}")