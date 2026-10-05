import json
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(r".\experiments\dataset\yolo_rdd2022_india")
PRED_PATH = Path(r".\runs\detect\val-5\prediction_boxes.json")

NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}


def iou(box_a, box_b):
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)

    intersection = iw * ih

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)

    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0


predictions = json.loads(PRED_PATH.read_text(encoding="utf-8"))

predictions_by_image = {
    item["image_id"]: item["predictions"]
    for item in predictions
}

stats = {
    cls: {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "tp_conf": [],
        "fp_conf": [],
        "tp_iou": [],
    }
    for cls in NAMES
}

image_stats = defaultdict(
    lambda: {
        "tp": 0,
        "fp": 0,
        "fn": 0,
    }
)


for label_path in sorted((ROOT / "labels" / "val").glob("*.txt")):

    image_id = label_path.stem

    ground_truth = []

    for line in label_path.read_text(encoding="utf-8").splitlines():

        if not line.strip():
            continue

        cls, xc, yc, w, h = map(float, line.split())

        cls = int(cls)

        # YOLO normalized XYWH -> original 720x720 XYXY
        x1 = (xc - w / 2.0) * 720.0
        y1 = (yc - h / 2.0) * 720.0
        x2 = (xc + w / 2.0) * 720.0
        y2 = (yc + h / 2.0) * 720.0

        ground_truth.append(
            {
                "class_id": cls,
                "box": [x1, y1, x2, y2],
            }
        )

    used_gt = set()

    image_predictions = sorted(
        predictions_by_image.get(image_id, []),
        key=lambda p: p["confidence"],
        reverse=True,
    )

    for prediction in image_predictions:

        pred_class = int(prediction["class_id"])
        pred_box = prediction["xyxy"]
        confidence = float(prediction["confidence"])

        best_iou = 0.0
        best_gt_index = None

        for gt_index, gt in enumerate(ground_truth):

            if gt_index in used_gt:
                continue

            if gt["class_id"] != pred_class:
                continue

            overlap = iou(pred_box, gt["box"])

            if overlap > best_iou:
                best_iou = overlap
                best_gt_index = gt_index

        if best_iou >= 0.50:

            used_gt.add(best_gt_index)

            stats[pred_class]["tp"] += 1
            stats[pred_class]["tp_conf"].append(confidence)
            stats[pred_class]["tp_iou"].append(best_iou)

            image_stats[image_id]["tp"] += 1

        else:

            stats[pred_class]["fp"] += 1
            stats[pred_class]["fp_conf"].append(confidence)

            image_stats[image_id]["fp"] += 1

    for gt_index, gt in enumerate(ground_truth):

        if gt_index not in used_gt:

            stats[gt["class_id"]]["fn"] += 1
            image_stats[image_id]["fn"] += 1


print()
print("==============================================")
print("DATASET A VALIDATION ERROR ANALYSIS")
print("conf >= 0.25 | class-aware IoU >= 0.50")
print("==============================================")


for cls, name in NAMES.items():

    s = stats[cls]

    tp = s["tp"]
    fp = s["fp"]
    fn = s["fn"]

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    mean_tp_conf = (
        float(np.mean(s["tp_conf"]))
        if s["tp_conf"]
        else None
    )

    mean_fp_conf = (
        float(np.mean(s["fp_conf"]))
        if s["fp_conf"]
        else None
    )

    mean_iou = (
        float(np.mean(s["tp_iou"]))
        if s["tp_iou"]
        else None
    )

    print()
    print(name)
    print("  TP:", tp)
    print("  FP:", fp)
    print("  FN:", fn)
    print("  Precision:", round(precision, 4))
    print("  Recall:", round(recall, 4))
    print("  F1:", round(f1, 4))
    print(
        "  TP mean confidence:",
        round(mean_tp_conf, 4) if mean_tp_conf is not None else "N/A",
    )
    print(
        "  FP mean confidence:",
        round(mean_fp_conf, 4) if mean_fp_conf is not None else "N/A",
    )
    print(
        "  TP mean IoU:",
        round(mean_iou, 4) if mean_iou is not None else "N/A",
    )


total_tp = sum(s["tp"] for s in stats.values())
total_fp = sum(s["fp"] for s in stats.values())
total_fn = sum(s["fn"] for s in stats.values())

overall_precision = (
    total_tp / (total_tp + total_fp)
    if (total_tp + total_fp)
    else 0.0
)

overall_recall = (
    total_tp / (total_tp + total_fn)
    if (total_tp + total_fn)
    else 0.0
)

overall_f1 = (
    2 * overall_precision * overall_recall
    / (overall_precision + overall_recall)
    if (overall_precision + overall_recall)
    else 0.0
)

print()
print("==============================================")
print("OVERALL")
print("==============================================")
print("TP:", total_tp)
print("FP:", total_fp)
print("FN:", total_fn)
print("Precision:", round(overall_precision, 4))
print("Recall:", round(overall_recall, 4))
print("F1:", round(overall_f1, 4))


print()
print("==============================================")
print("WORST IMAGES")
print("==============================================")

worst_images = sorted(
    image_stats.items(),
    key=lambda item: (
        item[1]["fn"] + item[1]["fp"],
        item[1]["fn"],
    ),
    reverse=True,
)[:15]


for image_id, s in worst_images:

    severity = s["fn"] + s["fp"]

    print(
        image_id,
        "TP=", s["tp"],
        "FP=", s["fp"],
        "FN=", s["fn"],
        "severity=", severity,
    )
