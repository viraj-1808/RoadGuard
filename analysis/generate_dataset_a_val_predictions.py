from pathlib import Path
from ultralytics import YOLO
import json

MODEL = r".\runs\detect\experiments\training\yol11s_experiment2\weights\best.pt"
IMAGE_DIR = Path(r".\experiments\dataset\yolo_rdd2022_india\images\val")
OUTPUT = Path(r".\runs\detect\val-5\prediction_boxes.json")

model = YOLO(MODEL)

images = sorted(IMAGE_DIR.glob("*.jpg"))

all_predictions = []

print("Images:", len(images))

for i, image_path in enumerate(images, 1):

    results = model.predict(
        source=str(image_path),
        imgsz=720,
        conf=0.25,
        iou=0.7,
        max_det=300,
        device=0,
        verbose=False,
        save=False,
    )

    result = results[0]

    boxes = result.boxes

    image_predictions = []

    for j in range(len(boxes)):

        xyxy = boxes.xyxy[j].cpu().numpy().tolist()
        cls = int(boxes.cls[j].item())
        conf = float(boxes.conf[j].item())

        image_predictions.append({
            "class_id": cls,
            "confidence": conf,
            "xyxy": xyxy,
        })

    all_predictions.append({
        "image_id": image_path.stem,
        "file_name": image_path.name,
        "orig_shape": list(result.orig_shape),
        "predictions": image_predictions,
    })

    if i % 25 == 0 or i == len(images):
        print(f"Processed {i}/{len(images)}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

OUTPUT.write_text(
    json.dumps(all_predictions, indent=2),
    encoding="utf-8"
)

print()
print("DONE")
print("Output:", OUTPUT)
print("Images:", len(all_predictions))
print(
    "Predictions:",
    sum(len(x["predictions"]) for x in all_predictions)
)
