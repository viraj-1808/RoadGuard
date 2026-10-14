"""Extract ground-truth pothole bounding boxes from annotated images using robust color detection."""
import json
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import cv2

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

# Class-to-color mapping (common annotation colors) - we'll detect dynamically
# The bounding box color is typically the most saturated, non-gray color forming rectangles

def find_box_colors(arr):
    """Find candidate annotation box colors from the image."""
    # Reshape to list of pixels
    pixels = arr.reshape(-1, 3)
    # Convert to HSV to find saturated colors
    hsv_pixels = np.clip((arr.astype(np.float64).reshape(-1, 3) * 1.0 / 255.0), 0, 1)
    # Convert RGB to HSV manually
    hsv = []
    for r, g, b in hsv_pixels:
        mx = max(r, g, b)
        mn = min(r, g, b)
        d = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = ((g - b) / d) % 6
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h = h * 60
        s = mx if mx == 0 else d / mx
        v = mx
        hsv.append((h, s, v))
    hsv = np.array(hsv)
    
    # Saturated colors (saturation > 0.5)
    sat_mask = hsv[:, 1] > 0.5
    sat_pixels = hsv[sat_mask]
    
    if len(sat_pixels) < 50:
        return None
    
    # Round hue to nearest 30 degrees for grouping
    hue_groups = np.round(sat_pixels[:, 0] / 30) * 30
    unique_groups, counts = np.unique(hue_groups, return_counts=True)
    top_group = unique_groups[np.argmax(counts)]
    
    # Find pixels in this hue group with high saturation
    in_group = (np.round(sat_pixels[:, 0] / 30) * 30 == top_group)
    # Map back to RGB
    rgb_in_group = pixels[sat_mask][in_group]
    # Median color
    median_color = np.median(rgb_in_group, axis=0)
    return median_color

def extract_boxes_from_annotated(image_path):
    """Extract ground-truth bounding boxes from an annotated image."""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.array(img)
    
    # Try to find box color
    box_color = find_box_colors(arr)
    if box_color is None:
        return []
    
    r, g, b = box_color
    # Tolerant match (allowing for JPEG compression artifacts)
    tol = 25
    mask = (
        (np.abs(arr[:, :, 0].astype(int) - int(r)) <= tol) &
        (np.abs(arr[:, :, 1].astype(int) - int(g)) <= tol) &
        (np.abs(arr[:, :, 2].astype(int) - int(b)) <= tol)
    )
    
    if not mask.any():
        return []
    
    # Morphological closing to connect fragmented lines
    kernel = np.ones((3, 3), np.uint8)
    # Dilate and erode to fill gaps in the drawn rectangles
    mask_dilated = ndimage.binary_dilation(mask, structure=np.ones((3, 3)), iterations=2).astype(np.uint8)
    mask_closed = ndimage.binary_erosion(mask_dilated, structure=np.ones((3, 3)), iterations=2).astype(np.uint8)
    
    # Find connected components
    labeled, num_features = ndimage.label(mask_closed)
    
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
    
    # Also save for each image the boxes for verification
    return ground_truth

if __name__ == "__main__":
    main()