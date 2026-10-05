from ultralytics import YOLO
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

def run_evaluation():
    model = YOLO(PROJECT_ROOT / 'runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt')
    metrics = model.val(
        data=str(PROJECT_ROOT / 'experiments/dataset/yolo_rdd2022_india/data.yaml'),
        imgsz=720,
        batch=16,
        device=0,
        rect=True,
        save_json=True,
        project=str(PROJECT_ROOT / 'runs/detect/experiments/training/yol11s_dataset_v2_split_v2'),
        name='test_final_eval2',
        exist_ok=True,
        verbose=True
    )

    print("\n=== FULL METRICS OBJECT ===")
    print(f"Type: {type(metrics)}")
    print(f"Dir: {[x for x in dir(metrics) if not x.startswith('_')]}")

    # Print all attributes
    print("\n=== METRICS ATTRIBUTES ===")
    for attr in dir(metrics):
        if not attr.startswith('_'):
            val = getattr(metrics, attr)
            if not callable(val):
                print(f"  {attr}: {val}")

    # Print results_dict
    print("\n=== RESULTS_DICT ===")
    if hasattr(metrics, 'results_dict'):
        for k, v in metrics.results_dict.items():
            print(f"  {k}: {v}")

    # Print box metrics
    print("\n=== BOX METRICS ===")
    if hasattr(metrics, 'box'):
        box = metrics.box
        print(f"  Type: {type(box)}")
        for attr in dir(box):
            if not attr.startswith('_'):
                val = getattr(box, attr)
                if not callable(val):
                    print(f"    {attr}: {val}")

    # Print maps (per-class mAP50-95)
    print("\n=== MAPS (per-class mAP50-95) ===")
    if hasattr(metrics, 'maps'):
        for i, m in enumerate(metrics.maps):
            print(f"  Class {i}: {m}")

    # Print per-class precision/recall/mAP50
    print("\n=== PER-CLASS METRICS ===")
    if hasattr(metrics, 'ap_class_index'):
        print(f"  ap_class_index: {metrics.ap_class_index}")
    if hasattr(metrics, 'ap'):
        print(f"  ap shape: {metrics.ap.shape}")
    if hasattr(metrics, 'precision'):
        print(f"  precision shape: {metrics.precision.shape}")
    if hasattr(metrics, 'recall'):
        print(f"  recall shape: {metrics.recall.shape}")

    # Print names and nt_per_class
    print("\n=== NAMES & COUNTS ===")
    if hasattr(metrics, 'names'):
        print(f"  names: {metrics.names}")
    if hasattr(metrics, 'nt_per_class'):
        print(f"  nt_per_class: {metrics.nt_per_class}")
    if hasattr(metrics, 'nt_per_image'):
        print(f"  nt_per_image: {metrics.nt_per_image}")
    if hasattr(metrics, 'nt_per_class_total'):
        print(f"  nt_per_class_total: {metrics.nt_per_class_total}")
    if hasattr(metrics, 'nt_per_image_total'):
        print(f"  nt_per_image_total: {metrics.nt_per_image_total}")

    # Print fitness
    print("\n=== FITNESS ===")
    if hasattr(metrics, 'fitness'):
        print(f"  fitness: {metrics.fitness}")

    # Print speed
    print("\n=== SPEED ===")
    if hasattr(metrics, 'speed'):
        print(f"  speed: {metrics.speed}")

    # Print save_dir
    print("\n=== SAVE_DIR ===")
    if hasattr(metrics, 'save_dir'):
        print(f"  save_dir: {metrics.save_dir}")

    # Check if confusion matrix exists
    print("\n=== CONFUSION MATRIX ===")
    if hasattr(metrics, 'confusion_matrix'):
        cm = metrics.confusion_matrix
        print(f"  Type: {type(cm)}")
        if hasattr(cm, 'shape'):
            print(f"  Shape: {cm.shape}")
        elif hasattr(cm, '__len__'):
            print(f"  Length: {len(cm)}")

if __name__ == '__main__':
    run_evaluation()