"""Extract ground-truth pothole bounding boxes from annotated images using OpenCV."""
import json
import os
import numpy as np
import cv2

ANNOTATED_DIR = "validation/manual/output/test2"
PREDICTIONS_PATH = "validation/manual/output/test2/predictions.json"
OUTPUT_DIR = "experiments/results/20261010_model_improvement_sprint"


def extract_boxes_from_annotated(image_path):
    """Extract ground-truth bounding boxes from an annotated image using OpenCV.

    Strategy: The annotation tool draws colored bounding boxes (rectangles).
    We detect the dominant saturated color, threshold the image for that color,
    apply morphology to close gaps, and find connected components that are
    approximately rectangular (since they are drawn as rectangle outlines).
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    # Convert to HSV for color detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Find saturated colors (high saturation, moderate value)
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    sat_mask = (s_channel > 80) & (v_channel > 30)  # saturated, not too dark
    
    # Find the most common hue band (in 30-degree increments)
    hue_channel = hsv[:, :, 0]
    hue_bands = (hue_channel[sat_mask] // 30).astype(int)
    if len(hue_bands) == 0:
        return []
    unique_bands, counts = np.unique(hue_bands, return_counts=True)
    top_band = unique_bands[np.argmax(counts)]
    
    # Now create a mask for colors near this hue band
    # Hue is 0-180 in OpenCV
    low_hue = max(0, top_band * 30 - 15)
    high_hue = min(180, top_band * 30 + 15)
    # Handle wrap-around
    if low_hue == 0 and high_hue == 180:
        hue_range_mask = np.ones_like(hue_channel, dtype=bool)
    else:
        hue_range_mask = (hue_channel >= low_hue) & (hue_channel <= high_hue)
    
    color_mask = hue_range_mask & sat_mask
    
    if not color_mask.any():
        return []
    
    # Morphological operations to close gaps in rectangle outlines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    # Dilate to connect line segments
    dilated = cv2.dilate(color_mask.astype(np.uint8), kernel, iterations=2)
    # Close small gaps
    closed = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed.astype(np.uint8))
    
    boxes = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # Filter: bounding box outline components are usually not too small
        # and have a reasonable aspect ratio for a road damage annotation
        if area < 20 or w < 3 or h < 3:
            continue
        # Drawn rectangles have 1-2 pixel thickness, so area << perimeter*bandwidth
        # Let's check if it's roughly a rectangle by looking at the perimeter
        # Actually, just collect all connected components for this color
        # We need to group components that belong to the same rectangle (4 sides)
        pass
    
    # Alternative approach: since boxes are drawn as rectangles (4 line segments),
    # connectedComponents will find the 4 segments separately.
    # Better approach: dilate more to connect the 4 sides of each rectangle.
    kernel_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    connected = cv2.dilate(color_mask.astype(np.uint8), kernel_large, iterations=5)
    connected = cv2.morphologyEx(connected, cv2.MORPH_CLOSE, kernel_large, iterations=5)
    
    num_labels2, labels2, stats2, centroids2 = cv2.connectedComponentsWithStats(connected)
    
    # Filter to find actual bounding boxes
    h_img, w_img = img.shape[:2]
    for i in range(1, num_labels2):
        x, y, w, h, area = stats2[i]
        if area < 100 or w < 5 or h < 5:
            continue
        # Check that it's not the full image
        if w > w_img * 0.95 and h > h_img * 0.95:
            continue
        # Filter by aspect ratio (boxes shouldn't be tiny or huge)
        if w / h > 50 or h / w > 50:
            continue
        # This is a bounding box
        boxes.append({
            "class_id": 3,  # pothole
            "class_name": "pothole",
            "bbox_xyxy": [float(x), float(y), float(x + w), float(y + h)]
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
    
    return ground_truth

if __name__ == "__main__":
    main()