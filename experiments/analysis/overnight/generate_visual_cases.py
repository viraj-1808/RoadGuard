#!/usr/bin/env python3
"""
Generate annotated visual cases for error analysis.
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = r"C:\Users\viraj\Code_files\Github\RoadGuard AI"
PRED_FILE = os.path.join(BASE, "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/test_eval/predictions.json")
LABEL_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/labels/test")
IMAGE_DIR = os.path.join(BASE, "experiments/dataset/yolo_rdd2022_india/images/test")
OUTPUT_DIR = os.path.join(BASE, "experiments/analysis/overnight/visual_cases")

CLASS_NAMES = {0: 'longitudinal_crack', 1: 'transverse_crack', 2: 'alligator_crack', 3: 'pothole'}
PRED_CLASS_MAP = {1: 0, 2: 1, 3: 2, 4: 3}
IMAGE_SIZE = 720

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors for each class
CLASS_COLORS = {
    0: (0, 255, 0),    # green - longitudinal
    1: (0, 0, 255),    # red - transverse
    2: (255, 165, 0),  # orange - alligator
    3: (255, 0, 255),  # magenta - pothole
}

def load_data():
    gt_data = {}
    for filename in os.listdir(LABEL_DIR):
        if not filename.endswith('.txt'):
            continue
        image_id = filename.replace('.txt', '')
        gt_objects = []
        with open(os.path.join(LABEL_DIR, filename), 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    x_c, y_c, w, h = map(float, parts[1:5])
                    x = (x_c - w/2) * IMAGE_SIZE
                    y = (y_c - h/2) * IMAGE_SIZE
                    gt_objects.append({'class_id': class_id, 'bbox': [x, y, w*IMAGE_SIZE, h*IMAGE_SIZE]})
        gt_data[image_id] = gt_objects
    
    with open(PRED_FILE, 'r') as f:
        raw_preds = json.load(f)
    pred_data = {}
    for pred in raw_preds:
        img_id = pred['image_id']
        if img_id not in pred_data:
            pred_data[img_id] = []
        pred_data[img_id].append({
            'class_id': PRED_CLASS_MAP.get(pred['category_id'], pred['category_id'] - 1),
            'bbox': pred['bbox'],
            'score': pred['score']
        })
    return gt_data, pred_data

def draw_annotated_image(image_id, gt_objects, pred_objects, output_name, focus_class=None):
    img_path = os.path.join(IMAGE_DIR, f"{image_id}.jpg")
    if not os.path.exists(img_path):
        return None
    
    img = Image.open(img_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Draw all GT boxes
    for obj in gt_objects:
        x, y, w, h = obj['bbox']
        color = CLASS_COLORS[obj['class_id']]
        draw.rectangle([x, y, x+w, y+h], outline=color, width=2)
        draw.text((x, y-12), f"GT:{CLASS_NAMES[obj['class_id']][:3]}", fill=color)
    
    # Draw predictions
    for obj in pred_objects:
        x, y, w, h = obj['bbox']
        color = CLASS_COLORS[obj['class_id']]
        label = f"P:{obj['score']:.2f}"
        if obj['class_id'] == 1:  # transverse - highlight with red box
            draw.rectangle([x, y, x+w, y+h], outline=(255, 0, 0), width=3)
        draw.rectangle([x, y, x+w, y+h], outline=color, width=1)
        draw.text((x, y+h+2), label, fill=color)
    
    # Add title
    draw.text((10, 10), output_name, fill=(255,255,255), stroke_fill=(0,0,0))
    
    out_path = os.path.join(OUTPUT_DIR, f"{output_name}.jpg")
    img.save(out_path)
    return out_path

# Create contact sheet
def create_contact_sheet(images, output_name, cols=4):
    if not images:
        return None
    
    thumb_size = (180, 180)
    thumbnails = []
    for img_path in images:
        if os.path.exists(img_path):
            img = Image.open(img_path).convert('RGB')
            img.thumbnail(thumb_size)
            thumbnails.append(img)
    
    if not thumbnails:
        return None
    
    rows = (len(thumbnails) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * thumb_size[0], rows * thumb_size[1]), (32, 32, 32))
    
    for i, thumb in enumerate(thumbnails):
        col = i % cols
        row = i // cols
        sheet.paste(thumb, (col * thumb_size[0], row * thumb_size[1]))
    
    out_path = os.path.join(OUTPUT_DIR, output_name)
    sheet.save(out_path)
    return out_path

# Case 1: High-confidence FPs
fp_high_conf = []
with open(os.path.join(BASE, "experiments/analysis/test_error_analysis/error_table.csv"), 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row['fp']) > 0:
            fp_high_conf.append(row['image_id'])

print("Generating Case 1: High-confidence False Positives...")
contact_fp = []
for img_id in fp_high_conf[:8]:
    img_path = draw_annotated_image(img_id, 
        load_data()[0].get(img_id, []),
        load_data()[1].get(img_id, []),
        f"fp_case_{img_id}")
    if img_path:
        contact_fp.append(img_path)

create_contact_sheet(contact_fp, "contact_fp_high_confidence.jpg")

print("Generating Case 2: False Negatives...")
fn_cases = ['India_002793', 'India_001381', 'India_001287', 'India_005781', 'India_003411']
contact_fn = []
for img_id in fn_cases:
    gt_data, pred_data = load_data()
    img_path = draw_annotated_image(img_id,
        gt_data.get(img_id, []),
        pred_data.get(img_id, []),
        f"fn_case_{img_id}")
    if img_path:
        contact_fn.append(img_path)

create_contact_sheet(contact_fn, "contact_fn_samples.jpg")

print("Generating Case 3: Localization Errors (IoU 0.5-0.7)...")
# Find medium IoU matches
gt_data, pred_data = load_data()
localization_cases = []
for img_id in gt_data:
    if not gt_data[img_id] or not pred_data.get(img_id):
        continue
    for gt_obj in gt_data[img_id]:
        for pred_obj in pred_data[img_id]:
            if gt_obj['class_id'] == pred_obj['class_id']:
                # Calculate IoU
                gx, gy, gw, gh = gt_obj['bbox']
                px, py, pw, ph = pred_obj['bbox']
                
                x1_i = max(gx, px)
                y1_i = max(gy, py)
                x2_i = min(gx+gw, px+pw)
                y2_i = min(gy+gh, py+ph)
                
                if x2_i > x1_i and y2_i > y1_i:
                    inter = (x2_i-x1_i)*(y2_i-y1_i)
                    union = gw*gh + pw*ph - inter
                    iou = inter/union if union > 0 else 0
                    
                    if 0.45 <= iou <= 0.7:
                        localization_cases.append((img_id, iou))
                        break
        if len(localization_cases) >= 5:
            break
    if len(localization_cases) >= 5:
        break

contact_loc = []
for img_id, iou in localization_cases[:5]:
    img_path = draw_annotated_image(img_id,
        gt_data.get(img_id, []),
        pred_data.get(img_id, []),
        f"loc_iou{iou:.2f}_{img_id}")
    if img_path:
        contact_loc.append(img_path)

create_contact_sheet(contact_loc, "contact_localization_errors.jpg")

print("Generating Case 4: Small Objects...")
# Find images with small objects
gt_data, pred_data = load_data()
small_object_cases = []
for img_id in gt_data:
    gt_objs = gt_data[img_id]
    if not gt_objs:
        continue
    # Check if any GT is small (normalized area < 0.001)
    for obj in gt_objs:
        norm_area = (obj['bbox'][2] * obj['bbox'][3]) / (IMAGE_SIZE * IMAGE_SIZE)
        if norm_area < 0.001:
            small_object_cases.append(img_id)
            break

contact_small = []
for img_id in small_object_cases[:6]:
    img_path = draw_annotated_image(img_id,
        gt_data.get(img_id, []),
        pred_data.get(img_id, []),
        f"small_obj_{img_id}")
    if img_path:
        contact_small.append(img_path)

create_contact_sheet(contact_small, "contact_small_objects.jpg")

print("Generating Case 5: Medium Difficulty Images...")
# Images with mixed performance
gt_data, pred_data = load_data()
mixed_cases = ['India_005543', 'India_008632', 'India_009553', 'India_007422', 'India_007555']
contact_mixed = []
for img_id in mixed_cases:
    img_path = draw_annotated_image(img_id,
        gt_data.get(img_id, []),
        pred_data.get(img_id, []),
        f"mixed_{img_id}")
    if img_path:
        contact_mixed.append(img_path)

create_contact_sheet(contact_mixed, "contact_mixed_difficulty.jpg")

print("\nAll visual cases generated in:", OUTPUT_DIR)
print("Files created:")
for f in os.listdir(OUTPUT_DIR):
    if f.endswith('.jpg'):
        print(f"  {f}")