#!/usr/bin/env python3
"""
Human Annotation Framework for Manual Validation Images

This script provides an interactive annotation tool for the 39 images in 
validation/manual/input/ using model predictions as reference.

Classes (matching YOLO11s road damage model):
    0: longitudinal_crack
    1: transverse_crack
    2: alligator_crack
    3: pothole

Outputs:
    - YOLO format annotations (.txt files) to experiments/results/real_world_model_improvement/annotations/
    - JSON manifest with image metadata, annotation status, and review flags
"""

import json
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
import argparse
import sys


@dataclass
class BoundingBox:
    """YOLO format bounding box (normalized)"""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float
    confidence: float = 1.0
    source: str = "human"  # "human", "model_derived"

    def to_yolo_string(self) -> str:
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    @staticmethod
    def from_xyxy(xyxy: List[float], img_w: int, img_h: int, class_id: int, confidence: float = 1.0, source: str = "human") -> 'BoundingBox':
        x1, y1, x2, y2 = xyxy
        x_center = ((x1 + x2) / 2) / img_w
        y_center = ((y1 + y2) / 2) / img_h
        width = (x2 - x1) / img_w
        height = (y2 - y1) / img_h
        return BoundingBox(class_id, x_center, y_center, width, height, confidence, source)


@dataclass
class ImageAnnotation:
    """Complete annotation for one image"""
    image_path: str
    image_name: str
    width: int
    height: int
    annotations: List[BoundingBox] = field(default_factory=list)
    status: str = "pending"  # "pending", "annotated", "review_needed", "negative"
    review_flags: List[str] = field(default_factory=list)
    model_predictions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "image_path": self.image_path,
            "image_name": self.image_name,
            "width": self.width,
            "height": self.height,
            "annotations": [asdict(a) for a in self.annotations],
            "status": self.status,
            "review_flags": self.review_flags,
            "model_predictions": self.model_predictions
        }

    def save_yolo(self, output_dir: Path):
        """Save annotations in YOLO format (.txt file)"""
        txt_path = output_dir / f"{Path(self.image_name).stem}.txt"
        with open(txt_path, 'w') as f:
            for ann in self.annotations:
                f.write(ann.to_yolo_string() + "\n")


class AnnotationTool:
    """Interactive annotation tool using OpenCV"""
    
    CLASS_NAMES = {
        0: "longitudinal_crack",
        1: "transverse_crack", 
        2: "alligator_crack",
        3: "pothole"
    }
    
    CLASS_COLORS = {
        0: (0, 255, 0),      # Green
        1: (255, 0, 0),      # Blue
        2: (0, 165, 255),    # Orange
        3: (0, 0, 255),      # Red
    }

    def __init__(self, input_dir: Path, predictions_path: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.predictions_path = Path(predictions_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.images: List[ImageAnnotation] = []
        self.current_idx = 0
        self.drawing = False
        self.current_box = None
        self.selected_class = 3  # Default to pothole
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.load_predictions()
        self.load_images()

    def load_predictions(self):
        with open(self.predictions_path) as f:
            data = json.load(f)
        self.predictions = {img["file"]: img for img in data["images"]}

    def load_images(self):
        image_files = sorted(self.input_dir.glob("road*"))
        for img_file in image_files:
            pred = self.predictions.get(img_file.name, {})
            img = cv2.imread(str(img_file))
            if img is None:
                print(f"Warning: Could not load {img_file}")
                continue
            h, w = img.shape[:2]
            ia = ImageAnnotation(
                image_path=str(img_file),
                image_name=img_file.name,
                width=w,
                height=h,
                model_predictions=pred.get("detections", [])
            )
            self.images.append(ia)

    def xyxy_to_normalized(self, xyxy, img_w, img_h):
        x1, y1, x2, y2 = xyxy
        return [
            ((x1 + x2) / 2) / img_w,
            ((y1 + y2) / 2) / img_h,
            (x2 - x1) / img_w,
            (y2 - y1) / img_h
        ]

    def normalized_to_xyxy(self, norm, img_w, img_h):
        xc, yc, w, h = norm
        x1 = int((xc - w/2) * img_w)
        y1 = int((yc - h/2) * img_h)
        x2 = int((xc + w/2) * img_w)
        y2 = int((yc + h/2) * img_h)
        return [x1, y1, x2, y2]

    def draw_annotations(self, img, annotations, color_map=None, thickness=2):
        """Draw bounding boxes on image"""
        display = img.copy()
        h, w = display.shape[:2]
        
        for ann in annotations:
            if isinstance(ann, BoundingBox):
                xyxy = self.normalized_to_xyxy(
                    [ann.x_center, ann.y_center, ann.width, ann.height], w, h
                )
                cls_id = ann.class_id
                conf = ann.confidence
                src = ann.source
            else:
                xyxy = ann.get("bbox_xyxy", [])
                cls_id = ann.get("class_id", 0)
                conf = ann.get("confidence", 1.0)
                src = "model"
            
            if len(xyxy) != 4:
                continue
                
            x1, y1, x2, y2 = map(int, xyxy)
            color = color_map.get(cls_id, (255, 255, 255)) if color_map else self.CLASS_COLORS.get(cls_id, (255, 255, 255))
            
            cv2.rectangle(display, (x1, y1), (x2, y2), color, thickness)
            label = f"{self.CLASS_NAMES.get(cls_id, cls_id)} {conf:.2f} [{src}]"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(display, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(display, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing boxes"""
        img_ann = self.images[self.current_idx]
        h, w = img_ann.height, img_ann.width
        
        # Convert display coordinates to image coordinates
        img_x = int((x - self.pan_x) / self.zoom)
        img_y = int((y - self.pan_y) / self.zoom)
        img_x = max(0, min(w - 1, img_x))
        img_y = max(0, min(h - 1, img_y))
        
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_box = [img_x, img_y, img_x, img_y]
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.current_box[2] = img_x
            self.current_box[3] = img_y
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            x1, y1, x2, y2 = self.current_box
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                # Ensure proper ordering
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])
                box = BoundingBox.from_xyxy([x1, y1, x2, y2], w, h, self.selected_class)
                img_ann.annotations.append(box)
                print(f"Added {self.CLASS_NAMES[self.selected_class]}: {box.to_yolo_string()}")
            self.current_box = None

    def run_interactive(self):
        """Run interactive annotation loop"""
        cv2.namedWindow("Annotation Tool", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Annotation Tool", self.mouse_callback)
        
        print("\n=== Annotation Tool Controls ===")
        print("  Left-click + drag: Draw bounding box")
        print("  0-3: Select class (0=longitudinal, 1=transverse, 2=alligator, 3=pothole)")
        print("  n: Next image")
        print("  p: Previous image")
        print("  d: Delete last annotation")
        print("  c: Clear all annotations for current image")
        print("  m: Toggle model predictions overlay")
        print("  s: Save annotations")
        print("  q: Quit")
        print("================================\n")
        
        show_model = True
        while True:
            img_ann = self.images[self.current_idx]
            img = cv2.imread(img_ann.image_path)
            
            # Draw model predictions
            if show_model and img_ann.model_predictions:
                model_boxes = []
                for det in img_ann.model_predictions:
                    model_boxes.append({
                        "bbox_xyxy": det["bbox_xyxy"],
                        "class_id": det["class_id"],
                        "confidence": det["confidence"]
                    })
                img = self.draw_annotations(img, model_boxes, 
                    color_map={0: (0, 255, 255), 1: (255, 255, 0), 2: (255, 0, 255), 3: (255, 255, 255)},
                    thickness=1)
            
            # Draw human annotations
            img = self.draw_annotations(img, img_ann.annotations)
            
            # Draw current box being drawn
            if self.drawing and self.current_box:
                x1, y1, x2, y2 = self.current_box
                disp_x1 = int(x1 * self.zoom + self.pan_x)
                disp_y1 = int(y1 * self.zoom + self.pan_y)
                disp_x2 = int(x2 * self.zoom + self.pan_x)
                disp_y2 = int(y2 * self.zoom + self.pan_y)
                color = self.CLASS_COLORS[self.selected_class]
                cv2.rectangle(img, (disp_x1, disp_y1), (disp_x2, disp_y2), color, 2)
            
            # Add status overlay
            status_text = f"[{self.current_idx + 1}/{len(self.images)}] {img_ann.image_name} | Class: {self.CLASS_NAMES[self.selected_class]} ({self.selected_class}) | Status: {img_ann.status} | Annotations: {len(img_ann.annotations)}"
            cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            
            if img_ann.review_flags:
                flags_text = "Flags: " + ", ".join(img_ann.review_flags)
                cv2.putText(img, flags_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            cv2.imshow("Annotation Tool", img)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('n'):
                self.current_idx = min(self.current_idx + 1, len(self.images) - 1)
            elif key == ord('p'):
                self.current_idx = max(self.current_idx - 1, 0)
            elif key in [ord(str(i)) for i in range(4)]:
                self.selected_class = int(chr(key))
                print(f"Selected class: {self.CLASS_NAMES[self.selected_class]}")
            elif key == ord('d'):
                if img_ann.annotations:
                    removed = img_ann.annotations.pop()
                    print(f"Removed: {removed.to_yolo_string()}")
            elif key == ord('c'):
                img_ann.annotations.clear()
                print("Cleared all annotations")
            elif key == ord('m'):
                show_model = not show_model
                print(f"Model predictions: {'ON' if show_model else 'OFF'}")
            elif key == ord('s'):
                self.save_all()
                print("Saved all annotations")
            elif key == ord('r'):
                img_ann.status = "review_needed"
                img_ann.review_flags.append("manual_review_requested")
                print("Marked for review")
            elif key == ord('g'):
                img_ann.status = "annotated"
                print("Marked as annotated")
            elif key == ord('x'):
                img_ann.status = "negative"
                print("Marked as negative (no damage)")
        
        cv2.destroyAllWindows()
        self.save_all()

    def save_all(self):
        """Save all annotations and manifest"""
        manifest = []
        for img_ann in self.images:
            img_ann.save_yolo(self.output_dir)
            manifest.append(img_ann.to_dict())
        
        manifest_path = self.output_dir / "annotation_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Saved manifest to {manifest_path}")

    def load_existing_annotations(self):
        """Load existing YOLO annotations if present"""
        for img_ann in self.images:
            txt_path = self.output_dir / f"{Path(img_ann.image_name).stem}.txt"
            if txt_path.exists():
                with open(txt_path) as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            xc, yc, w, h = map(float, parts[1:5])
                            conf = float(parts[5]) if len(parts) > 5 else 1.0
                            img_ann.annotations.append(BoundingBox(class_id, xc, yc, w, h, conf, "human"))
                print(f"Loaded {len(img_ann.annotations)} existing annotations for {img_ann.image_name}")


def create_preliminary_annotations(input_dir: Path, predictions_path: Path, output_dir: Path, error_analysis_csv: Path = None):
    """
    Create preliminary annotations based on model predictions + error analysis.
    This is the non-interactive path for generating ground truth candidates.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(predictions_path) as f:
        pred_data = json.load(f)
    
    predictions = {img["file"]: img for img in pred_data["images"]}
    
    # Load error analysis if available
    error_info = {}
    if error_analysis_csv and error_analysis_csv.exists():
        import csv
        with open(error_analysis_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                error_info[row["filename"]] = row
    
    CLASS_NAMES = {0: "longitudinal_crack", 1: "transverse_crack", 2: "alligator_crack", 3: "pothole"}
    
    manifest = []
    ground_truth = {
        "experiment_id": "EXP-INF-003",
        "description": "Preliminary ground truth annotations derived from model predictions + error analysis. Source field indicates origin: 'model_derived' (from high-confidence model predictions), 'error_analysis' (from manual error analysis review), or 'human_reviewed' (human-verified).",
        "images": []
    }
    
    image_files = sorted(input_dir.glob("road*"))
    
    for img_file in image_files:
        pred = predictions.get(img_file.name, {})
        img = cv2.imread(str(img_file))
        if img is None:
            continue
        h, w = img.shape[:2]
        
        detections = pred.get("detections", [])
        error_row = error_info.get(img_file.name, {})
        visible_damage = error_row.get("visible_damage", "uncertain")
        visible_class = error_row.get("visible_damage_class", "uncertain")
        notes = error_row.get("notes", "")
        
        # Determine annotation status
        if visible_damage == "yes":
            status = "CLEAR"
        elif visible_damage == "no":
            status = "NEGATIVE"
        else:
            status = "UNCERTAIN"
        
        # Create annotations based on model predictions + error analysis
        annotations = []
        review_flags = []
        
        if status == "CLEAR":
            # Use high-confidence, non-duplicate model predictions
            # Apply NMS-like filtering to remove duplicates
            filtered_dets = filter_duplicate_detections(detections)
            for det in filtered_dets:
                if det["confidence"] >= 0.35:  # Higher threshold per error analysis
                    box = BoundingBox.from_xyxy(
                        det["bbox_xyxy"], w, h, det["class_id"], 
                        det["confidence"], "model_derived"
                    )
                    annotations.append(box)
            if not annotations and visible_class != "uncertain":
                # Error analysis says damage visible but model missed it
                review_flags.append("model_missed_visible_damage")
                status = "UNCERTAIN"
        
        elif status == "UNCERTAIN":
            review_flags.append("needs_human_review")
            if "corner artifact" in notes.lower() or "low confidence" in notes.lower():
                review_flags.append("likely_false_positive")
            if "no detections" in notes.lower() and "high resolution" in notes.lower():
                review_flags.append("high_res_may_miss_defects")
            if "portrait" in notes.lower():
                review_flags.append("portrait_orientation")
        
        elif status == "NEGATIVE":
            review_flags.append("no_visible_damage_per_error_analysis")
        
        # Add specific flags from error analysis
        if "duplicate" in notes.lower() or "overlap" in notes.lower():
            review_flags.append("duplicate_detections_in_predictions")
        if "oversized" in notes.lower() or "over-merging" in notes.lower():
            review_flags.append("oversized_bbox_in_predictions")
        if "missed" in notes.lower():
            review_flags.append("possible_missed_detections")
        
        img_ann = ImageAnnotation(
            image_path=str(img_file),
            image_name=img_file.name,
            width=w,
            height=h,
            annotations=annotations,
            status=status.lower(),
            review_flags=review_flags,
            model_predictions=detections
        )
        
        img_ann.save_yolo(output_dir)
        manifest.append(img_ann.to_dict())
        
        # Add to ground truth JSON
        gt_entry = {
            "image": img_file.name,
            "width": w,
            "height": h,
            "status": status,
            "review_flags": review_flags,
            "annotations": [
                {
                    "class_id": a.class_id,
                    "class_name": CLASS_NAMES[a.class_id],
                    "bbox_xyxy": [
                        (a.x_center - a.width/2) * w,
                        (a.y_center - a.height/2) * h,
                        (a.x_center + a.width/2) * w,
                        (a.y_center + a.height/2) * h
                    ],
                    "bbox_normalized": [a.x_center, a.y_center, a.width, a.height],
                    "confidence": a.confidence,
                    "source": a.source
                }
                for a in annotations
            ]
        }
        ground_truth["images"].append(gt_entry)
    
    # Save manifest
    manifest_path = output_dir / "annotation_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {manifest_path}")
    
    # Save ground truth
    gt_path = output_dir / "ground_truth_annotations.json"
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    print(f"Saved ground truth to {gt_path}")
    
    return manifest, ground_truth


def filter_duplicate_detections(detections, iou_threshold=0.5):
    """Simple NMS to filter duplicate detections"""
    if not detections:
        return []
    
    # Sort by confidence descending
    dets = sorted(detections, key=lambda x: x["confidence"], reverse=True)
    kept = []
    
    for det in dets:
        is_duplicate = False
        for kept_det in kept:
            if det["class_id"] != kept_det["class_id"]:
                continue
            if compute_iou(det["bbox_xyxy"], kept_det["bbox_xyxy"]) > iou_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(det)
    
    return kept


def compute_iou(box1, box2):
    """Compute IoU between two xyxy boxes"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    
    if xi2 <= xi1 or yi2 <= yi1:
        return 0.0
    
    inter = (xi2 - xi1) * (yi2 - yi1)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - inter
    
    return inter / union if union > 0 else 0.0


def create_train_val_holdout_split(ground_truth: Dict, output_dir: Path, train_ratio=0.5, val_ratio=0.25):
    """Split images into train/val/holdout ensuring no near-duplicates in different splits"""
    output_dir = Path(output_dir)
    
    images = ground_truth["images"]
    total = len(images)
    
    # Group by resolution/orientation to avoid near-duplicates in different splits
    groups = {
        "high_res_landscape": [],    # 4096x3072
        "high_res_portrait": [],     # 3072x4096
        "mid_res_landscape": [],     # ~1200x900, 1280x960
        "mid_res_portrait": [],      # 960x1280
        "low_res": [],               # <1000px
    }
    
    for img in images:
        w, h = img["width"], img["height"]
        if max(w, h) >= 3072:
            if w > h:
                groups["high_res_landscape"].append(img)
            else:
                groups["high_res_portrait"].append(img)
        elif max(w, h) >= 960:
            if w > h:
                groups["mid_res_landscape"].append(img)
            else:
                groups["mid_res_portrait"].append(img)
        else:
            groups["low_res"].append(img)
    
    # Shuffle within each group and assign splits
    import random
    random.seed(42)
    
    train, val, holdout = [], [], []
    
    for group_name, group_imgs in groups.items():
        if not group_imgs:
            continue
        random.shuffle(group_imgs)
        n = len(group_imgs)
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio)) if n > 2 else 0
        
        train.extend(group_imgs[:n_train])
        val.extend(group_imgs[n_train:n_train + n_val])
        holdout.extend(group_imgs[n_train + n_val:])
    
    # Ensure minimum counts
    # Rebalance if needed
    split_data = {
        "split_info": {
            "total_images": total,
            "train_count": len(train),
            "val_count": len(val),
            "holdout_count": len(holdout),
            "train_ratio": train_ratio,
            "val_ratio": val_ratio,
            "holdout_ratio": 1 - train_ratio - val_ratio,
            "split_method": "stratified_by_resolution_orientation",
            "random_seed": 42
        },
        "train": [img["image"] for img in train],
        "val": [img["image"] for img in val],
        "holdout": [img["image"] for img in holdout]
    }
    
    split_path = output_dir / "data_split.json"
    with open(split_path, 'w') as f:
        json.dump(split_data, f, indent=2)
    print(f"Saved data split to {split_path}")
    print(f"Train: {len(train)}, Val: {len(val)}, Holdout: {len(holdout)}")
    
    return split_data


def main():
    parser = argparse.ArgumentParser(description="Human Annotation Framework for Road Damage Images")
    parser.add_argument("--input", default="validation/manual/input", help="Input images directory")
    parser.add_argument("--predictions", default="validation/manual/output/test2/predictions.json", help="Model predictions JSON")
    parser.add_argument("--output", default="experiments/results/real_world_model_improvement/annotations", help="Output directory")
    parser.add_argument("--error-analysis", default="experiments/results/20261010_phase3_error_analysis/error_analysis.csv", help="Error analysis CSV")
    parser.add_argument("--interactive", action="store_true", help="Run interactive annotation tool")
    parser.add_argument("--create-preliminary", action="store_true", help="Create preliminary annotations from predictions + error analysis")
    parser.add_argument("--create-split", action="store_true", help="Create train/val/holdout split")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    predictions_path = Path(args.predictions)
    output_dir = Path(args.output)
    error_analysis_path = Path(args.error_analysis) if args.error_analysis else None
    
    if args.interactive:
        tool = AnnotationTool(input_dir, predictions_path, output_dir)
        tool.load_existing_annotations()
        tool.run_interactive()
    
    if args.create_preliminary:
        manifest, ground_truth = create_preliminary_annotations(
            input_dir, predictions_path, output_dir, error_analysis_path
        )
    
    if args.create_split:
        gt_path = output_dir / "ground_truth_annotations.json"
        if gt_path.exists():
            with open(gt_path) as f:
                ground_truth = json.load(f)
        else:
            _, ground_truth = create_preliminary_annotations(
                input_dir, predictions_path, output_dir, error_analysis_path
            )
        create_train_val_holdout_split(ground_truth, output_dir)
    
    if not any([args.interactive, args.create_preliminary, args.create_split]):
        print("No action specified. Use --interactive, --create-preliminary, or --create-split")
        parser.print_help()


if __name__ == "__main__":
    main()