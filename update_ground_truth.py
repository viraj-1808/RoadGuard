import json
from pathlib import Path

# Load verified annotations
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\verified_annotations\verified_annotations.json") as f:
    verified_annotations = json.load(f)

# Load ground truth annotations
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\annotations\ground_truth_annotations.json") as f:
    gt_data = json.load(f)

OUTPUT_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\verified_annotations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Build lookup for verified annotations by image
verified_by_image = {}
for va in verified_annotations:
    if va["image"] not in verified_by_image:
        verified_by_image[va["image"]] = []
    verified_by_image[va["image"]].append(va)

# Update ground truth annotations
for img_data in gt_data["images"]:
    img_name = img_data["image"]
    if img_name in verified_by_image:
        # Replace annotations with verified ones
        new_annotations = []
        for va in verified_by_image[img_name]:
            x1, y1, x2, y2 = va["bbox_xyxy"]
            width = img_data["width"]
            height = img_data["height"]
            x_center = (x1 + x2) / 2 / width
            y_center = (y1 + y2) / 2 / height
            w = (x2 - x1) / width
            h = (y2 - y1) / height
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            w = max(0, min(1, w))
            h = max(0, min(1, h))
            
            new_annotations.append({
                "class_id": va["class_id"],
                "class_name": va["class_name"],
                "bbox_xyxy": va["bbox_xyxy"],
                "bbox_normalized": [x_center, y_center, w, h],
                "confidence": va.get("confidence"),
                "source": va["source"]
            })
        img_data["annotations"] = new_annotations
        img_data["status"] = "VERIFIED"
        if "review_flags" in img_data:
            img_data["review_flags"] = ["verified"]
    elif img_data["status"] == "UNCERTAIN":
        # Keep as uncertain but could update status
        pass

# Save updated ground truth
gt_output_path = OUTPUT_DIR / "ground_truth_annotations_verified.json"
with open(gt_output_path, 'w') as f:
    json.dump(gt_data, f, indent=2)
print(f"Updated ground truth saved to {gt_output_path}")

# Also create a manifest similar to the original annotation_manifest.json format
# Load original manifest
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\annotations\annotation_manifest.json") as f:
    manifest = json.load(f)

# Update manifest with verified annotations
for m in manifest:
    img_name = m["image_name"]
    if img_name in verified_by_image:
        new_annotations = []
        for va in verified_by_image[img_name]:
            x1, y1, x2, y2 = va["bbox_xyxy"]
            width = m["width"]
            height = m["height"]
            x_center = (x1 + x2) / 2 / width
            y_center = (y1 + y2) / 2 / height
            w = (x2 - x1) / width
            h = (y2 - y1) / height
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            w = max(0, min(1, w))
            h = max(0, min(1, h))
            
            new_annotations.append({
                "class_id": va["class_id"],
                "x_center": x_center,
                "y_center": y_center,
                "width": w,
                "height": h,
                "confidence": va.get("confidence"),
                "source": va["source"]
            })
        m["annotations"] = new_annotations
        m["status"] = "verified"
        m["review_flags"] = ["verified"]

# Save updated manifest
manifest_output_path = OUTPUT_DIR / "annotation_manifest_verified.json"
with open(manifest_output_path, 'w') as f:
    json.dump(manifest, f, indent=2)
print(f"Updated manifest saved to {manifest_output_path}")

print("\nDone!")