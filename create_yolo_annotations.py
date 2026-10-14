import json
from pathlib import Path

# Load verified annotations
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\verified_annotations\verified_annotations.json") as f:
    verified_annotations = json.load(f)

# Load manifest to get image dimensions
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\annotations\annotation_manifest.json") as f:
    manifest = {item["image_name"]: item for item in json.load(f)}

OUTPUT_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\verified_annotations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Create YOLO format txt files
for va in verified_annotations:
    img_name = va["image"]
    m = manifest.get(img_name, {})
    width = m.get("width", 1)
    height = m.get("height", 1)
    
    # Convert xyxy to YOLO format (normalized x_center, y_center, width, height)
    x1, y1, x2, y2 = va["bbox_xyxy"]
    x_center = (x1 + x2) / 2 / width
    y_center = (y1 + y2) / 2 / height
    w = (x2 - x1) / width
    h = (y2 - y1) / height
    
    # Clamp to [0, 1]
    x_center = max(0, min(1, x_center))
    y_center = max(0, min(1, y_center))
    w = max(0, min(1, w))
    h = max(0, min(1, h))
    
    txt_path = OUTPUT_DIR / f"{img_name.replace('.jpg', '').replace('.webp', '')}.txt"
    with open(txt_path, 'w') as f:
        f.write(f"{va['class_id']} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
    
    print(f"Created {txt_path}: class={va['class_id']}, x={x_center:.4f}, y={y_center:.4f}, w={w:.4f}, h={h:.4f}")

# Also update the ground_truth_annotations.json with verified annotations
# Load existing ground truth
with open(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\results\real_world_model_improvement\annotations\ground_truth_annotations.json") as f:
    gt_annotations = json.load(f)

# Update with verified annotations (change source from model_derived to human_reviewed or model_derived_epoch72)
# Build a lookup for verified annotations by image
verified_by_image = {}
for va in verified_annotations:
    if va["image"] not in verified_by_image:
        verified_by_image[va["image"]] = []
    verified_by_image[va["image"]].append(va)

# Update ground truth annotations
for gt in gt_annotations:
    img_name = gt["image_name"]
    if img_name in verified_by_image:
        # Replace annotations with verified ones
        new_annotations = []
        for va in verified_by_image[img_name]:
            x1, y1, x2, y2 = va["bbox_xyxy"]
            width = gt["width"]
            height = gt["height"]
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
        gt["annotations"] = new_annotations
        gt["status"] = "verified"
    elif gt["status"] == "uncertain":
        # Keep as uncertain but update status
        gt["status"] = "uncertain"

# Save updated ground truth
gt_output_path = OUTPUT_DIR / "ground_truth_annotations_verified.json"
with open(gt_output_path, 'w') as f:
    json.dump(gt_annotations, f, indent=2)
print(f"\nUpdated ground truth saved to {gt_output_path}")

# Also save updated manifest
manifest_output_path = OUTPUT_DIR / "annotation_manifest_verified.json"
with open(manifest_output_path, 'w') as f:
    json.dump(list(gt_annotations), f, indent=2)
print(f"Updated manifest saved to {manifest_output_path}")