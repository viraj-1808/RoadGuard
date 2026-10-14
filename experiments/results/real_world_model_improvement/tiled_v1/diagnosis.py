#!/usr/bin/env python3
"""
Class-confusion diagnosis on 7 specific images.
"""

import json
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from inference.adapters.yolo_adapter import YOLOAdapter, InferenceResult, Detection


@dataclass
class GTAnnotation:
    class_id: int
    class_name: str
    bbox_xyxy: List[float]
    confidence: float
    source: str


@dataclass
class MatchResult:
    image_name: str
    gt_class_id: int
    gt_class_name: str
    gt_bbox: List[float]
    pred_class_id: int
    pred_class_name: str
    pred_bbox: List[float]
    pred_confidence: float
    iou: float
    match_type: str  # TP, FP, FN


def compute_iou(box1: List[float], box2: List[float]) -> float:
    """Compute IoU between two boxes in xyxy format."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x2 <= x1 or y2 <= y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def load_ground_truth(json_path: str, target_images: List[str]) -> Dict[str, List[GTAnnotation]]:
    """Load ground truth annotations for target images."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    gt_dict = {}
    for img_data in data['images']:
        if img_data['image'] in target_images:
            annotations = []
            for ann in img_data['annotations']:
                annotations.append(GTAnnotation(
                    class_id=ann['class_id'],
                    class_name=ann['class_name'],
                    bbox_xyxy=ann['bbox_xyxy'],
                    confidence=ann['confidence'],
                    source=ann['source']
                ))
            gt_dict[img_data['image']] = annotations
    return gt_dict


def run_inference(adapter: YOLOAdapter, image_paths: List[Path]) -> Dict[str, InferenceResult]:
    """Run inference on all images."""
    results = {}
    for img_path in image_paths:
        result = adapter.predict_image(img_path)
        results[img_path.name] = result
    return results


def match_detections(gt_annotations: List[GTAnnotation], predictions: List[Detection], 
                     iou_threshold: float = 0.5) -> List[MatchResult]:
    """Match GT to predictions with class-aware IoU."""
    matches = []
    gt_matched = [False] * len(gt_annotations)
    pred_matched = [False] * len(predictions)
    
    # First pass: match GT to predictions with same class and IoU >= threshold
    for i, gt in enumerate(gt_annotations):
        best_iou = 0.0
        best_pred_idx = -1
        
        for j, pred in enumerate(predictions):
            if pred_matched[j]:
                continue
            if pred.class_id != gt.class_id:
                continue
            
            iou = compute_iou(gt.bbox_xyxy, list(pred.bbox_xyxy))
            if iou >= iou_threshold and iou > best_iou:
                best_iou = iou
                best_pred_idx = j
        
        if best_pred_idx >= 0:
            pred = predictions[best_pred_idx]
            matches.append(MatchResult(
                image_name="",  # Will be filled later
                gt_class_id=gt.class_id,
                gt_class_name=gt.class_name,
                gt_bbox=gt.bbox_xyxy,
                pred_class_id=pred.class_id,
                pred_class_name=pred.class_name,
                pred_bbox=list(pred.bbox_xyxy),
                pred_confidence=pred.confidence,
                iou=best_iou,
                match_type="TP"
            ))
            gt_matched[i] = True
            pred_matched[best_pred_idx] = True
    
    # Remaining predictions are FPs
    for j, pred in enumerate(predictions):
        if not pred_matched[j]:
            matches.append(MatchResult(
                image_name="",
                gt_class_id=-1,
                gt_class_name="",
                gt_bbox=[],
                pred_class_id=pred.class_id,
                pred_class_name=pred.class_name,
                pred_bbox=list(pred.bbox_xyxy),
                pred_confidence=pred.confidence,
                iou=0.0,
                match_type="FP"
            ))
    
    # Remaining GT are FNs
    for i, gt in enumerate(gt_annotations):
        if not gt_matched[i]:
            matches.append(MatchResult(
                image_name="",
                gt_class_id=gt.class_id,
                gt_class_name=gt.class_name,
                gt_bbox=gt.bbox_xyxy,
                pred_class_id=-1,
                pred_class_name="",
                pred_bbox=[],
                pred_confidence=0.0,
                iou=0.0,
                match_type="FN"
            ))
    
    return matches


def create_annotated_image_gt_vs_pred(image_path: Path, result: InferenceResult, 
                                       gt_annotations: List[GTAnnotation],
                                       output_path: Path) -> bool:
    """Create annotated image showing GT (green) vs predictions (red)."""
    img = cv2.imread(str(image_path))
    if img is None:
        return False
    
    # Draw GT boxes in green
    for gt in gt_annotations:
        x1, y1, x2, y2 = map(int, gt.bbox_xyxy)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
        label = f"GT: {gt.class_name}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(img, (x1, y1 - label_h - 5), (x1 + label_w, y1), (0, 255, 0), -1)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Draw prediction boxes in red
    for det in result.detections:
        x1, y1, x2, y2 = map(int, det.bbox_xyxy)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"PRED: {det.class_name} {det.confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(img, (x1, y1 - label_h - 5), (x1 + label_w, y1), (0, 0, 255), -1)
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.imwrite(str(output_path), img)
    return True


def main():
    # Configuration
    model_path = r"runs\detect\experiments\training\yol11s_dataset_v2_split_v2\weights\epoch72.pt"
    confidence_threshold = 0.05
    iou_threshold = 0.7
    imgsz = 720
    iou_match_threshold = 0.5
    
    target_images = [
        "road001.webp",
        "road002.jpg",
        "road003.jpg",
        "road007.jpg",
        "road018.jpg",
        "road021.jpg",
        "road026.jpg"
    ]
    
    # Paths
    base_dir = Path(__file__).parent.parent.parent.parent.parent
    gt_json_path = base_dir / "experiments" / "results" / "real_world_model_improvement" / "ground_truth_annotations.json"
    input_dir = base_dir / "validation" / "manual" / "input"
    output_dir = Path(__file__).parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load ground truth
    print("Loading ground truth...")
    gt_dict = load_ground_truth(str(gt_json_path), target_images)
    
    # Load model
    print("Loading model...")
    adapter = YOLOAdapter(
        model_path=model_path,
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        imgsz=imgsz,
        device="0"
    )
    
    # Print model info
    model_info = adapter.get_model_info()
    print(f"Model: {model_info.model_name}")
    print(f"Classes: {model_info.class_names}")
    
    # Run inference
    print("\nRunning inference...")
    image_paths = [input_dir / name for name in target_images]
    results = run_inference(adapter, image_paths)
    
    # Process each image
    all_matches = []
    per_image_stats = {}
    
    for img_name in target_images:
        print(f"\n--- {img_name} ---")
        result = results[img_name]
        gt_annotations = gt_dict.get(img_name, [])
        
        print(f"  GT annotations: {len(gt_annotations)}")
        for gt in gt_annotations:
            print(f"    GT: class={gt.class_id}({gt.class_name}), bbox={gt.bbox_xyxy}")
        
        print(f"  Predictions: {len(result.detections)}")
        for det in result.detections:
            print(f"    PRED: class={det.class_id}({det.class_name}), conf={det.confidence:.3f}, bbox={det.bbox_xyxy}")
        
        # Match
        matches = match_detections(gt_annotations, result.detections, iou_match_threshold)
        for m in matches:
            m.image_name = img_name
        all_matches.extend(matches)
        
        # Stats
        tp = sum(1 for m in matches if m.match_type == "TP")
        fp = sum(1 for m in matches if m.match_type == "FP")
        fn = sum(1 for m in matches if m.match_type == "FN")
        per_image_stats[img_name] = {"TP": tp, "FP": fp, "FN": fn}
        print(f"  TP={tp}, FP={fp}, FN={fn}")
        
        # Create annotated image
        annotated_path = output_dir / f"annotated_{img_name}"
        create_annotated_image_gt_vs_pred(image_paths[target_images.index(img_name)], result, gt_annotations, annotated_path)
        print(f"  Annotated saved to: {annotated_path}")
        
        # Save raw predictions
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            if isinstance(obj, tuple):
                return list(obj)
            return obj
        
        pred_json = {
            "image": img_name,
            "image_width": result.image_width,
            "image_height": result.image_height,
            "inference_time_ms": result.inference_time_ms,
            "detections": [
                {
                    "class_id": int(det.class_id),
                    "class_name": det.class_name,
                    "confidence": float(det.confidence),
                    "bbox_xyxy": [float(x) for x in det.bbox_xyxy]
                }
                for det in result.detections
            ]
        }
        pred_path = output_dir / f"predictions_{img_name.replace('.', '_')}.json"
        with open(pred_path, 'w') as f:
            json.dump(pred_json, f, indent=2)
        print(f"  Predictions saved to: {pred_path}")
    
    # Generate CSV
    csv_path = output_dir / "VERIFIED_TP_FP_FN.csv"
    with open(csv_path, 'w') as f:
        f.write("image,match_type,gt_class_id,gt_class_name,pred_class_id,pred_class_name,iou,pred_confidence\n")
        for m in all_matches:
            f.write(f"{m.image_name},{m.match_type},{m.gt_class_id},{m.gt_class_name},{m.pred_class_id},{m.pred_class_name},{m.iou:.4f},{m.pred_confidence:.4f}\n")
    print(f"\nCSV saved to: {csv_path}")
    
    # Generate Markdown report
    md_path = output_dir / "CLASS_CONFUSION_DIAGNOSIS.md"
    with open(md_path, 'w') as f:
        f.write("# Class-Confusion Diagnosis Report\n\n")
        f.write(f"**Model:** {model_info.model_name} (epoch72.pt)\n")
        f.write(f"**Confidence threshold:** {confidence_threshold}\n")
        f.write(f"**IoU threshold (NMS):** {iou_threshold}\n")
        f.write(f"**Image size:** {imgsz}\n")
        f.write(f"**IoU match threshold:** {iou_match_threshold}\n")
        f.write(f"**Class mapping:** {model_info.class_names}\n\n")
        
        f.write("## Per-Image Analysis\n\n")
        
        for img_name in target_images:
            result = results[img_name]
            gt_annotations = gt_dict.get(img_name, [])
            matches = [m for m in all_matches if m.image_name == img_name]
            
            f.write(f"### {img_name}\n\n")
            f.write(f"- **Image dimensions:** {result.image_width}×{result.image_height}\n")
            f.write(f"- **GT annotations:** {len(gt_annotations)}\n")
            f.write(f"- **Predictions:** {len(result.detections)}\n")
            f.write(f"- **Inference time:** {result.inference_time_ms:.1f}ms\n\n")
            
            f.write("#### Ground Truth\n\n")
            for gt in gt_annotations:
                f.write(f"- Class {gt.class_id} ({gt.class_name}): bbox={gt.bbox_xyxy}, conf={gt.confidence:.3f}, source={gt.source}\n")
            
            f.write("\n#### Predictions\n\n")
            for det in result.detections:
                f.write(f"- Class {det.class_id} ({det.class_name}): conf={det.confidence:.3f}, bbox={list(det.bbox_xyxy)}\n")
            
            f.write("\n#### Matching Results\n\n")
            for m in matches:
                if m.match_type == "TP":
                    f.write(f"- **TP**: GT class {m.gt_class_id} ({m.gt_class_name}) <-> Pred class {m.pred_class_id} ({m.pred_class_name}), IoU={m.iou:.4f}, conf={m.pred_confidence:.4f}\n")
                elif m.match_type == "FP":
                    f.write(f"- **FP**: Pred class {m.pred_class_id} ({m.pred_class_name}), bbox={m.pred_bbox}, conf={m.pred_confidence:.4f}\n")
                elif m.match_type == "FN":
                    f.write(f"- **FN**: GT class {m.gt_class_id} ({m.gt_class_name}), bbox={m.gt_bbox}\n")
            
            f.write("\n---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        total_tp = sum(s["TP"] for s in per_image_stats.values())
        total_fp = sum(s["FP"] for s in per_image_stats.values())
        total_fn = sum(s["FN"] for s in per_image_stats.values())
        f.write(f"- **Total TP:** {total_tp}\n")
        f.write(f"- **Total FP:** {total_fp}\n")
        f.write(f"- **Total FN:** {total_fn}\n")
        f.write(f"- **Precision:** {total_tp/(total_tp+total_fp):.4f}" if (total_tp+total_fp) > 0 else "- **Precision:** N/A\n")
        f.write(f"- **Recall:** {total_tp/(total_tp+total_fn):.4f}" if (total_tp+total_fn) > 0 else "- **Recall:** N/A\n")
        
        # Class-wise breakdown
        f.write("\n## Class-wise Breakdown\n\n")
        for class_id in range(4):
            class_name = model_info.class_names.get(class_id, f"class_{class_id}")
            class_matches = [m for m in all_matches if m.gt_class_id == class_id or m.pred_class_id == class_id]
            class_tp = sum(1 for m in class_matches if m.match_type == "TP")
            class_fp = sum(1 for m in class_matches if m.match_type == "FP")
            class_fn = sum(1 for m in class_matches if m.match_type == "FN")
            f.write(f"### {class_name} (class {class_id})\n")
            f.write(f"- TP: {class_tp}, FP: {class_fp}, FN: {class_fn}\n")
            if class_tp + class_fp > 0:
                f.write(f"- Precision: {class_tp/(class_tp+class_fp):.4f}\n")
            if class_tp + class_fn > 0:
                f.write(f"- Recall: {class_tp/(class_tp+class_fn):.4f}\n")
            f.write("\n")
    
    print(f"Markdown report saved to: {md_path}")
    print("\nDone!")


if __name__ == "__main__":
    main()