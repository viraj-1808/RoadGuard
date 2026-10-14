"""Extract ground-truth pothole bounding boxes from annotated images."""
import json
import os
from PIL import Image
import numpy as np

ANNOTATED_DIR = "validation/manual/output/test2"
PREDICTIONS_PATH = "validation/manual/output/test2/predictions.json"
OUTPUT_DIR = "experiments/results/20261010_model_improvement_sprint"

# Class mapping from the predictions file
CLASS_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}

# In the annotated images, the bounding box color is red (255,0,0)
# We need to find connected components of red pixels and extract their bounding boxes

def extract_boxes_from_annotated(image_path):
    """Extract ground-truth bounding boxes from an annotated image."""
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)
    
    # Find red pixels (the bounding box color)
    red_mask = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 0)
    
    if not red_mask.any():
        return []
    
    # Find connected components using simple approach
    # For efficiency, use scipy or manual approach
    from scipy import ndimage
    labeled, num_features = ndimage.label(red_mask)
    
    boxes = []
    for i in range(1, num_features + 1):
        ys, xs = np.where(labeled == i)
        if len(ys) < 5:  # skip tiny noise
            continue
        xmin, xmax = xs.min(), xs.max()
        ymin, ymax = ys.min(), ys.max()
        boxes.append({
            "class_id": 3,  # pothole
            "class_name": "pothole",
            "bbox_xyxy": [float(xmin), float(ymin), float(xmax), float(ymax)]
        })
    
    return boxes

def main():
    with open(PREDICTIONS_PATH) as f:
        predictions = json.load(f)
    
    ground_truth = {}
    for img_data in predictions["images"]:
        file_name = img_data["file"]
        base_name = os.path.splitext(file_name)[0]
        ext = os.path.splitext(file_name)[1]
        annotated_path = os.path.join(ANNOTATED_DIR, f"{base_name}_annotated{ext}")
        
        if not os.path.exists(annotated_path):
            print(f"WARNING: No annotated image for {file_name}")
            ground_truth[file_name] = []
            continue
        
        boxes = extract_boxes_from_annotated(annotated_path)
        ground_truth[file_name] = boxes
        print(f"{file_name}: {len(boxes)} ground-truth pothole boxes")
    
    # Save ground truth
    gt_path = os.path.join(OUTPUT_DIR, "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"\nGround truth saved to {gt_path}")
    
    total_gt = sum(len(v) for v in ground_truth.values())
    print(f"Total ground-truth pothole boxes: {total_gt}")

if __name__ == "__main__":
    main()