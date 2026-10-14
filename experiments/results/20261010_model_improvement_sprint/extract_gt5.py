"""Extract ground-truth pothole bounding boxes from annotated images using Hough-like detection."""
import json
import os
import numpy as np
import cv2

ANNOTATED_DIR = "validation/manual/output/test2"
PREDICTIONS_PATH = "validation/manual/output/test2/predictions.json"
OUTPUT_DIR = "experiments/results/20261010_model_improvement_sprint"


def extract_boxes_from_annotated(image_path):
    """Extract ground-truth bounding boxes from an annotated image.

    Strategy:
    1. Find the dominant saturated color in the image
    2. Create a binary mask for that color
    3. Use morphological operations to close gaps in rectangle outlines
    4. Find connected components and filter by size/shape
    """
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    h_orig, w_orig = img.shape[:2]
    
    # Scale down if needed for processing
    scale = 1.0
    if max(w_orig, h_orig) > 1000:
        scale = 1000 / max(w_orig, h_orig)
        new_w = int(w_orig * scale)
        new_h = int(h_orig * scale)
        img = cv2.resize(img, (new_w, new_h))
    
    h, w = img.shape[:2]
    
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Find saturated pixels
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    sat_mask = (s_channel > 60) & (v_channel > 30) & (v_channel < 250)
    
    if not sat_mask.any():
        return []
    
    # Find dominant hue band
    hue_channel = hsv[:, :, 0]
    hue_bands = (hue_channel[sat_mask] // 30).astype(int)
    if len(hue_bands) == 0:
        return []
    unique_bands, counts = np.unique(hue_bands, return_counts=True)
    top_band = unique_bands[np.argmax(counts)]
    
    # Create mask for this hue band
    low_hue = max(0, top_band * 30 - 15)
    high_hue = min(180, top_band * 30 + 15)
    hue_range_mask = (hue_channel >= low_hue) & (hue_channel <= high_hue)
    color_mask = hue_range_mask & sat_mask
    
    if not color_mask.any():
        return []
    
    # Morphological closing to connect line segments
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(color_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=3)
    
    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        
        # Filter by size
        if area < 50 or bw < 10 or bh < 10:
            continue
        if bw > w * 0.95 and bh > h * 0.95:
            continue
        if bw / bh > 20 or bh / bw > 20:
            continue
        
        # Check if it's roughly rectangular
        # A rectangle outline has area ~ perimeter * thickness
        # But after morphological closing, it becomes a filled shape
        # So we check the aspect ratio and area
        aspect = bw / bh
        if aspect < 0.1 or aspect > 10:
            continue
        
        # Scale back to original coordinates
        x1 = x / scale
        y1 = y / scale
        x2 = (x + bw) / scale
        y2 = (y + bh) / scale
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, w_orig))
        y1 = max(0, min(y1, h_orig))
        x2 = max(0, min(x2, w_orig))
        y2 = max(0, min(y2, h_orig))
        
        boxes.append({
            "class_id": 3,
            "class_name": "pothole",
            "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)]
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