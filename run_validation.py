from ultralytics import YOLO
import json
import hashlib
import torch
import ultralytics
from datetime import datetime
from multiprocessing import freeze_support

def main():
    # Load model
    model_path = "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/epoch86.pt"
    model = YOLO(model_path)

    # Get model SHA-256
    with open(model_path, 'rb') as f:
        model_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Run validation
    metrics = model.val(
        data="experiments/dataset/yolo_rdd2022_india/data.yaml",
        imgsz=720,
        batch=16,
        device=0,
        save_json=True,
        project="experiments/results/20261010_phase2_validation",
        name="exp1_epoch86_val",
        exist_ok=False,
        verbose=True
    )

    # Extract metrics
    results = {
        "command": "python run_validation.py",
        "model_path": model_path,
        "model_sha256": model_sha256,
        "ultralytics_version": ultralytics.__version__,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "imgsz": 736,  # Updated by ultralytics
        "batch": 16,
        "device": 0,
        "conf_threshold": 0.001,
        "iou_threshold": 0.6,
        "class_names": metrics.names,
        "class_order": list(metrics.names.values()),
        "per_class": {},
        "confusion_matrix": metrics.confusion_matrix.matrix.tolist() if hasattr(metrics, 'confusion_matrix') and metrics.confusion_matrix is not None else None,
        "timestamp": datetime.now().isoformat()
    }

    # Per-class metrics
    if hasattr(metrics, 'box'):
        box = metrics.box
        for i, name in enumerate(metrics.names.values()):
            results["per_class"][name] = {
                "precision": float(box.p[i]) if i < len(box.p) else None,
                "recall": float(box.r[i]) if i < len(box.r) else None,
                "mAP50": float(box.ap50[i]) if i < len(box.ap50) else None,
                "mAP50-95": float(box.ap[i]) if i < len(box.ap) else None,
            }

    # Overall metrics
    if hasattr(metrics, 'box'):
        box = metrics.box
        results["overall"] = {
            "precision": float(box.mp),
            "recall": float(box.mr),
            "mAP50": float(box.map50),
            "mAP50-95": float(box.map),
            "fitness": float(box.fitness) if hasattr(box, 'fitness') else None
        }

    # Save raw metrics for reference
    with open("experiments/results/20261010_phase2_validation/exp1_epoch86_val/raw_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Validation complete!")
    print(json.dumps(results, indent=2))
    return results

if __name__ == '__main__':
    freeze_support()
    main()