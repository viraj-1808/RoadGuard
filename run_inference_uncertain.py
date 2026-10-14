import json
from pathlib import Path
from ultralytics import YOLO

MODEL_PATH = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\runs\detect\experiments\training\yol11s_experiment2\weights\epoch72.pt"
INPUT_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\validation\manual\input")
OUTPUT_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\verified_annotations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UNCERTAIN_IMAGES = [
    "road004.jpg", "road005.jpg", "road012.jpg", "road013.jpg",
    "road016.jpg", "road017.jpg", "road019.jpg", "road020.jpg",
    "road022.jpg", "road023.jpg", "road024.jpg", "road028.jpg",
    "road029.jpg", "road030.jpg", "road031.jpg", "road032.jpg",
    "road033.jpg", "road034.jpg", "road035.jpg", "road036.jpg",
    "road037.jpg", "road038.jpg", "road039.jpg"
]

CLASS_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole"
}

def run_inference():
    model = YOLO(MODEL_PATH)
    results = {}
    
    for img_name in UNCERTAIN_IMAGES:
        img_path = INPUT_DIR / img_name
        if not img_path.exists():
            print(f"WARNING: {img_name} not found")
            continue
        
        print(f"Running inference on {img_name}...")
        result = model.predict(
            source=str(img_path),
            conf=0.05,
            iou=0.7,
            imgsz=720,
            device=0,
            verbose=False
        )[0]
        
        detections = []
        for box in result.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            detections.append({
                "class_id": cls_id,
                "class_name": CLASS_NAMES.get(cls_id, f"unknown_{cls_id}"),
                "confidence": conf,
                "bbox_xyxy": xyxy
            })
        
        results[img_name] = {
            "file": img_name,
            "width": result.orig_shape[1],
            "height": result.orig_shape[0],
            "detections": detections
        }
        print(f"  Found {len(detections)} detections")
    
    output_path = OUTPUT_DIR / "epoch72_inference_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")
    return results

if __name__ == "__main__":
    run_inference()