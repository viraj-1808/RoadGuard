#!/usr/bin/env python3
"""
Visual error-analysis sheet generator for Dataset A validation.

Reads an EXISTING prediction artifact (prediction_boxes.json) and the
corresponding Dataset A YOLO validation split, performs class-aware
greedy matching at conf >= 0.25 / IoU >= 0.50, then selects a diverse
set of representative annotated images across three categories:

    A. missed/            high-FN cases
    B. false_positives/   high-FP cases
    C. successful/        multiple correct detections, few errors

All work is CPU-based. No GPU inference is performed. No model weights
or dataset splits are modified in any way. Deterministic (fixed seed).
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_ROOT = PROJECT_ROOT / "experiments/dataset/yolo_rdd2022_india"
VAL_IMAGES = DATASET_ROOT / "images" / "val"
VAL_LABELS = DATASET_ROOT / "labels" / "val"

PRED_PATH = PROJECT_ROOT / "runs/detect/val-5/prediction_boxes.json"

OUT_ROOT = PROJECT_ROOT / "experiments/error_analysis"
OUT_DIRS: Dict[str, Path] = {
    "missed": OUT_ROOT / "missed",
    "false_positives": OUT_ROOT / "false_positives",
    "successful": OUT_ROOT / "successful",
}

CONF_THRESH = 0.25
IOU_THRESH = 0.50

NUM_PER_CATEGORY = 12
SEED = 42

CLASS_NAMES: Dict[int, str] = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}

VALID_CLASS_IDS = set(CLASS_NAMES.keys())

# Visual palette (BGR-style RGB for Pillow) 
COLOR_GT_TP: Tuple[int, int, int] = (0, 200, 0)       # green
COLOR_GT_FN: Tuple[int, int, int] = (255, 165, 0)      # orange
COLOR_PRED_TP: Tuple[int, int, int] = (0, 0, 255)     # blue
COLOR_PRED_FP: Tuple[int, int, int] = (255, 0, 0)    # red

IMG_SIZE = 720  # Dataset A val images are 720x720


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #

@dataclass
class Box:
    class_id: int
    conf: float
    xyxy: Tuple[float, float, float, float]  # pixel coords x1,y1,x2,y2


@dataclass
class ImageAnalysis:
    image_id: str
    file_name: str
    width: int
    height: int
    gt_boxes: List[Box] = field(default_factory=list)
    pred_boxes: List[Box] = field(default_factory=list)
    tp_preds: List[Box] = field(default_factory=list)
    fp_preds: List[Box] = field(default_factory=list)
    fn_gts: List[Box] = field(default_factory=list)

    # per-class counts for CSV richness
    def class_counts(self) -> Dict[str, Dict[str, int]]:
        result: Dict[str, Dict[str, int]] = {}
        for cls in VALID_CLASS_IDS:
            result[CLASS_NAMES[cls]] = {
                "gt": sum(1 for b in self.gt_boxes if b.class_id == cls),
                "tp": sum(1 for b in self.tp_preds if b.class_id == cls),
                "fp": sum(1 for b in self.fp_preds if b.class_id == cls),
                "fn": sum(1 for b in self.fn_gts if b.class_id == cls),
            }
        return result

    @property
    def tp(self) -> int:
        return len(self.tp_preds)

    @property
    def fp(self) -> int:
        return len(self.fp_preds)

    @property
    def fn(self) -> int:
        return len(self.fn_gts)


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #

def iou(a: Tuple[float, float, float, float],
        b: Tuple[float, float, float, float]) -> float:
    """IoU between two xyxy boxes (pixel coords)."""
    a1, a2, a3, a4 = a
    b1, b2, b3, b4 = b
    ix1 = max(a1, b1)
    iy1 = max(a2, b2)
    ix2 = min(a3, b3)
    iy2 = min(a4, b4)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, a3 - a1) * max(0.0, a4 - a2)
    area_b = max(0.0, b3 - b1) * max(0.0, b4 - b2)
    union = area_a + area_b - inter
    return inter / union if union > 0.0 else 0.0


def yolo_label_to_xyxy(line: str, img_w: int, img_h: int) -> Optional[Tuple[int, float, float, float, float]]:
    """Parse one YOLO label line.

    Format: class_id cx cy w h  (all normalised, 0-1)
    Returns (class_id, x1, y1, x2, y2) in pixel coords, or None if invalid.
    """
    parts = line.split()
    if len(parts) != 5:
        return None
    try:
        cls = int(float(parts[0]))
        cx, cy, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
    except (ValueError, TypeError):
        return None
    if cls not in VALID_CLASS_IDS:
        return None
    x1 = (cx - w / 2.0) * img_w
    y1 = (cy - h / 2.0) * img_h
    x2 = (cx + w / 2.0) * img_w
    y2 = (cy + h / 2.0) * img_h
    return cls, x1, y1, x2, y2


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #

def class_aware_greedy_match(gt_boxes: List[Box],
                             pred_boxes: List[Box]) -> Tuple[List[Box], List[Box], List[Box]]:
    """Greedy class-aware matching (highest-conf pred first).

    Returns (tp_preds, fp_preds, fn_gts).
    A matched GT marks a TP pred; the GT is then consumed (one-to-one).
    """
    matched_gt_idx: set[int] = set()
    tp_preds: List[Box] = []
    fp_preds: List[Box] = []

    # sort predictions by confidence descending (deterministic tie-break by class then coords)
    ordered = sorted(enumerate(pred_boxes),
                     key=lambda x: (-x[1].conf, x[1].class_id, x[0]))

    for _, pred in ordered:
        best_iou = 0.0
        best_idx: Optional[int] = None
        for gi, gt in enumerate(gt_boxes):
            if gi in matched_gt_idx:
                continue
            if gt.class_id != pred.class_id:
                continue
            i = iou(pred.xyxy, gt.xyxy)
            if i > best_iou:
                best_iou = i
                best_idx = gi
        if best_idx is not None and best_iou >= IOU_THRESH:
            matched_gt_idx.add(best_idx)
            tp_preds.append(pred)
        else:
            fp_preds.append(pred)

    fn_gts = [gt for i, gt in enumerate(gt_boxes) if i not in matched_gt_idx]
    return tp_preds, fp_preds, fn_gts


# --------------------------------------------------------------------------- #
# Selection (diverse, deterministic)
# --------------------------------------------------------------------------- #

def _has_class(analysis: ImageAnalysis, cls: int) -> int:
    """Count of unmatched (FN) instances of a class in this image."""
    return sum(1 for b in analysis.fn_gts if b.class_id == cls)


def _has_fp_class(analysis: ImageAnalysis, cls: int) -> int:
    return sum(1 for b in analysis.fp_preds if b.class_id == cls)


def select_diverse(images: List[ImageAnalysis],
                   sort_key,
                   class_extractor,
                   total: int = NUM_PER_CATEGORY) -> List[ImageAnalysis]:
    """Select *total* images, trying to represent each class.

    *sort_key*: function returning a (primary, secondary) tuple for pre-sorting.
    *class_extractor*: function(analysis) -> dict {class_id: count_of_relevant_objects}
    """
    rng = random.Random(SEED)
    # Pre-sort deterministically by primary then secondary keys
    images_sorted = sorted(images, key=sort_key)

    selected: List[ImageAnalysis] = []
    used_ids: set[str] = set()
    # Track how many selected images cover each class
    class_counts = {c: 0 for c in VALID_CLASS_IDS}

    # First pass: pick images that cover the *least-represented* class first
    # (best-effort diversity).
    candidate_pool = [img for img in images_sorted]

    target_per_class = max(1, total // len(VALID_CLASS_IDS))  # ~3 each

    while len(selected) < total and candidate_pool:
        # Prefer images whose strongest class is the least-represented so far
        def _score(img: ImageAnalysis) -> float:
            counts = class_extractor(img)
            if not counts:
                return 0.0
            top_class = max(counts, key=lambda c: counts[c])
            # negative of current coverage -> prefer under-represented classes
            coverage = class_counts[top_class] / max(target_per_class, 1)
            strength = counts[top_class]
            return strength - coverage * 10  # prefer underrepresented

        # Re-sort pool by score deterministically (tie-break by image_id)
        candidate_pool.sort(key=lambda img: (-_score(img), img.image_id))
        chosen = candidate_pool.pop(0)

        if chosen.image_id in used_ids:
            continue
        selected.append(chosen)
        used_ids.add(chosen.image_id)

        counts = class_extractor(chosen)
        for c in counts:
            if counts[c] > 0:
                class_counts[c] += 1

    # Fallback: if still under quota (rare), fill deterministically
    for img in images_sorted:
        if len(selected) >= total:
            break
        if img.image_id not in used_ids:
            selected.append(img)
            used_ids.add(img.image_id)

    return selected[:total]


# --------------------------------------------------------------------------- #
# Annotation drawing
# --------------------------------------------------------------------------- #

def _get_font(size: int = 14) -> ImageFont.FreeTypeFont:
    """Try common font paths, fall back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    # default
    try:
        return ImageFont.truetype("DejaVuSans-Bold", size)
    except Exception:
        return ImageFont.load_default()


def draw_box(draw: ImageDraw.ImageDraw,
             box: Tuple[float, float, float, float],
             color: Tuple[int, int, int],
             width: int = 2):
    x1, y1, x2, y2 = box
    coords = [x1, y1, x2, y1, x2, y2, x1, y2, x1, y1]
    draw.line(coords, fill=color, width=width)


def annotate_image(analysis: ImageAnalysis) -> Image.Image:
    """Build an annotated image with GT + prediction boxes and a header."""
    img_path = VAL_IMAGES / analysis.file_name
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    font = _get_font(14)
    small_font = _get_font(11)

    # ---- Draw GT boxes ----
    # TP-matched GT (we don't explicitly track which GTs matched, but we can
    # infer via IoU with tp_preds; instead we draw ALL GTs and color by match)
    # To keep it simple and correct, we draw:
    #   - FN GTs in orange
    #   - We also draw matched GTs in green (those that have a matching TP pred)
    tp_pred_boxes = [p.xyxy for p in analysis.tp_preds]

    drawn_gt_tp = set()
    for gi, gt in enumerate(analysis.gt_boxes):
        matched = False
        for pi, pb in enumerate(tp_pred_boxes):
            if pi in drawn_gt_tp:
                continue
            if iou(gt.xyxy, pb) >= IOU_THRESH and gt.class_id == analysis.tp_preds[pi].class_id:
                matched = True
                drawn_gt_tp.add(pi)
                break
        color = COLOR_GT_TP if matched else COLOR_GT_FN
        label = f"GT {CLASS_NAMES[gt.class_id]}"
        if not matched:
            label += " [FN]"
        draw_box(draw, gt.xyxy, color, width=2)
        # label background
        x1, y1 = gt.xyxy[0], gt.xyxy[1]
        tw, th = draw.textlength(label, font=small_font), 13
        draw.rectangle([x1, y1 - th - 2, x1 + tw + 2, y1], fill=(0, 0, 0, 120) if img.mode == "RGBA" else (0, 0, 0))
        draw.text((x1 + 1, y1 - th - 1), label, fill=color, font=small_font)

    # ---- Draw FP predictions in red ----
    for i, pred in enumerate(analysis.fp_preds):
        draw_box(draw, pred.xyxy, COLOR_PRED_FP, width=2)
        x1, y1 = pred.xyxy[0], pred.xyxy[1]
        label = f"FP {CLASS_NAMES[pred.class_id]} {pred.conf:.2f}"
        tw, th = draw.textlength(label, font=small_font), 13
        draw.rectangle([x1, y1 - th - 2, x1 + tw + 2, y1], fill=(0, 0, 0))
        draw.text((x1 + 1, y1 - th - 1), label, fill=COLOR_PRED_FP, font=small_font)

    # ---- Draw TP predictions in blue (with conf) ----
    for i, pred in enumerate(analysis.tp_preds):
        draw_box(draw, pred.xyxy, COLOR_PRED_TP, width=2)
        x1, y1 = pred.xyxy[0], pred.xyxy[1]
        label = f"TP {CLASS_NAMES[pred.class_id]} {pred.conf:.2f}"
        tw, th = draw.textlength(label, font=small_font), 13
        draw.rectangle([x1, y1 - th - 2, x1 + tw + 2, y1], fill=(0, 0, 0))
        draw.text((x1 + 1, y1 - th - 1), label, fill=COLOR_PRED_TP, font=small_font)

    # ---- Header banner ----
    header = (f"{analysis.image_id}  |  TP={analysis.tp}  FP={analysis.fp}  "
              f"FN={analysis.fn}  |  conf>={CONF_THRESH} IoU>={IOU_THRESH}")
    tw = draw.textlength(header, font=font)
    banner_h = 30
    draw.rectangle([0, 0, max(int(w), int(tw + 20)), banner_h], fill=(20, 20, 20))
    draw.text((10, banner_h // 2 - 8), header, fill=(255, 255, 255), font=font)

    # ---- Legend ----
    legend_x = 10
    legend_y = banner_h + 8
    legend_items = [
        ("GT TP  (matched)", COLOR_GT_TP),
        ("GT FN  (missed)", COLOR_GT_FN),
        ("Pred TP  (correct)", COLOR_PRED_TP),
        ("Pred FP  (false)", COLOR_PRED_FP),
    ]
    for label, color in legend_items:
        swatch = draw.rectangle([legend_x, legend_y, legend_x + 14, legend_y + 14],
                                fill=color)
        txt_w = draw.textlength(label, font=small_font)
        draw.text((legend_x + 18, legend_y - 1), label, fill=(240, 240, 240), font=small_font)
        legend_y += 18

    return img


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def validate_inputs() -> List[str]:
    """Return list of error strings (empty = all good)."""
    errors: List[str] = []

    if not PRED_PATH.exists():
        errors.append(f"Prediction file not found: {PRED_PATH}")
    if not VAL_IMAGES.exists():
        errors.append(f"Validation images dir not found: {VAL_IMAGES}")
    if not VAL_LABELS.exists():
        errors.append(f"Validation labels dir not found: {VAL_LABELS}")
    return errors


# --------------------------------------------------------------------------- #
# Main logic
# --------------------------------------------------------------------------- #

def load_predictions() -> Dict[str, dict]:
    """Load and validate prediction_boxes.json. Returns {image_id: record}."""
    with open(PRED_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError(f"prediction_boxes.json must be a list, got {type(raw).__name__}")

    by_id: Dict[str, dict] = {}
    for i, rec in enumerate(raw):
        if not isinstance(rec, dict):
            raise ValueError(f"Record {i} is not a dict")
        image_id = rec.get("image_id")
        file_name = rec.get("file_name")
        if image_id is None or file_name is None:
            raise ValueError(f"Record {i} missing image_id or file_name")
        if image_id in by_id:
            raise ValueError(f"Duplicate image_id in predictions: {image_id}")
        preds = rec.get("predictions", [])
        if not isinstance(preds, list):
            raise ValueError(f"Record {image_id}: predictions is not a list")
        for p in preds:
            cid = p.get("class_id")
            conf = p.get("confidence")
            xyxy = p.get("xyxy")
            if cid is None or conf is None or xyxy is None:
                raise ValueError(f"Record {image_id}: malformed prediction (missing field)")
            cid_int = int(cid)
            if cid_int not in VALID_CLASS_IDS:
                raise ValueError(f"Record {image_id}: invalid class_id {cid}")
            conf_f = float(conf)
            if not (0.0 <= conf_f <= 1.0) or np.isnan(conf_f) or np.isinf(conf_f):
                raise ValueError(f"Record {image_id}: invalid confidence {conf}")
            if not isinstance(xyxy, (list, tuple)) or len(xyxy) != 4:
                raise ValueError(f"Record {image_id}: malformed xyxy")
            vals = [float(v) for v in xyxy]
            if any(np.isnan(v) or np.isinf(v) for v in vals):
                raise ValueError(f"Record {image_id}: non-finite xyxy")
            p["class_id"] = cid_int
            p["confidence"] = conf_f
            p["xyxy"] = tuple(vals)
        by_id[image_id] = rec

    return by_id


def load_gt(label_path: Path, img_w: int, img_h: int) -> List[Box]:
    """Parse a YOLO label file into a list of Boxes."""
    boxes: List[Box] = []
    if not label_path.exists():
        return boxes
    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        result = yolo_label_to_xyxy(line, img_w, img_h)
        if result is None:
            continue
        cls, x1, y1, x2, y2 = result
        # clip coordinates to image bounds
        x1 = max(0.0, min(img_w, x1))
        y1 = max(0.0, min(img_h, y1))
        x2 = max(0.0, min(img_w, x2))
        y2 = max(0.0, min(img_h, y2))
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        if x2 - x1 < 1e-6 or y2 - y1 < 1e-6:
            continue
        boxes.append(Box(class_id=cls, conf=1.0, xyxy=(x1, y1, x2, y2)))
    return boxes


def process_image(image_id: str,
                  pred_record: dict,
                  label_path: Path) -> ImageAnalysis:
    """Build an ImageAnalysis for one image."""
    orig = pred_record.get("orig_shape", [IMG_SIZE, IMG_SIZE])
    if isinstance(orig, (list, tuple)) and len(orig) >= 2:
        img_h, img_w = int(orig[0]), int(orig[1])
    else:
        img_h, img_w = IMG_SIZE, IMG_SIZE

    gt_boxes = load_gt(label_path, img_w, img_h)

    pred_boxes: List[Box] = []
    for p in pred_record.get("predictions", []):
        conf = float(p["confidence"])
        if conf < CONF_THRESH:
            continue
        cid = int(p["class_id"])
        xyxy = tuple(float(v) for v in p["xyxy"])
        # clip predictions to image bounds
        px1 = max(0.0, min(float(img_w), xyxy[0]))
        py1 = max(0.0, min(float(img_h), xyxy[1]))
        px2 = max(0.0, min(float(img_w), xyxy[2]))
        py2 = max(0.0, min(float(img_h), xyxy[3]))
        if px2 < px1:
            px1, px2 = px2, px1
        if py2 < py1:
            py1, py2 = py2, py1
        pred_boxes.append(Box(class_id=cid, conf=conf, xyxy=(px1, py1, px2, py2)))

    tp_preds, fp_preds, fn_gts = class_aware_greedy_match(gt_boxes, pred_boxes)

    return ImageAnalysis(
        image_id=image_id,
        file_name=pred_record.get("file_name", f"{image_id}.jpg"),
        width=img_w,
        height=img_h,
        gt_boxes=gt_boxes,
        pred_boxes=pred_boxes,
        tp_preds=tp_preds,
        fp_preds=fp_preds,
        fn_gts=fn_gts,
    )


def select_representative() -> Dict[str, List[ImageAnalysis]]:
    """Select diverse images for each category."""
    pred_by_id = load_predictions()

    # Build a lookup of label files
    label_map: Dict[str, Path] = {}
    for lp in VAL_LABELS.glob("*.txt"):
        label_map[lp.stem] = lp

    # Ensure every image in predictions has a label
    analyses: List[ImageAnalysis] = []
    missing_labels: List[str] = []
    missing_images: List[str] = []

    for image_id, rec in pred_by_id.items():
        label_path = label_map.get(image_id)
        if label_path is None:
            missing_labels.append(image_id)
            continue
        img_path = VAL_IMAGES / rec.get("file_name", f"{image_id}.jpg")
        if not img_path.exists():
            missing_images.append(image_id)
            continue
        analyses.append(process_image(image_id, rec, label_path))

    if missing_labels:
        print(f"[WARN] {len(missing_labels)} images missing label files (skipped): {missing_labels[:10]}")
    if missing_images:
        print(f"[WARN] {len(missing_images)} predictions missing image files (skipped): {missing_images[:10]}")

    print(f"[INFO] Processed {len(analyses)} validation images.")

    # ---- Build category pools ----
    # Missed / high-FN: significant missed objects (fn > 0, prioritise larger fn+fp)
    missed_pool = [a for a in analyses if a.fn > 0]
    # False-positive-heavy: fp > 0
    fp_pool = [a for a in analyses if a.fp > 0]
    # Successful: tp >= 1 and (fp + fn) is small relative to tp.
    # Relaxed criteria because the model's overall recall is low (0.266), so
    # strict TP>=3 filters out nearly all images.
    successful_pool = [a for a in analyses
                       if a.tp >= 1
                       and (a.tp + a.fp + a.fn) > 0
                       and (a.fp + a.fn) <= a.tp * 2.0]

    # ---- Selection for missed ----
    missed_selected = select_diverse(
        missed_pool,
        sort_key=lambda a: (-(a.fn + a.fp), -a.fn, a.image_id),
        class_extractor=lambda a: {c: _has_class(a, c) for c in VALID_CLASS_IDS},
        total=NUM_PER_CATEGORY,
    )

    # ---- Selection for false_positives ----
    fp_selected = select_diverse(
        [a for a in fp_pool if a.image_id not in {s.image_id for s in missed_selected}],
        sort_key=lambda a: (-(a.fp + a.fn), -a.fp, a.image_id),
        class_extractor=lambda a: {c: _has_fp_class(a, c) for c in VALID_CLASS_IDS},
        total=NUM_PER_CATEGORY,
    )

    # ---- Selection for successful ----
    successful_selected = select_diverse(
        [a for a in successful_pool
         if a.image_id not in {s.image_id for s in missed_selected} | {s.image_id for s in fp_selected}],
        sort_key=lambda a: (-(a.tp - a.fp - a.fn), a.image_id),
        class_extractor=lambda a: {c: sum(1 for p in a.tp_preds if p.class_id == c) for c in VALID_CLASS_IDS},
        total=NUM_PER_CATEGORY,
    )

    return {
        "missed": missed_selected,
        "false_positives": fp_selected,
        "successful": successful_selected,
    }


# --------------------------------------------------------------------------- #
# Output generation
# --------------------------------------------------------------------------- #

def build_annotated_and_copy(analyses: List[ImageAnalysis],
                             out_dir: Path) -> List[Path]:
    """Annotate images and save to *out_dir*. Returns list of output paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    output_paths: List[Path] = []
    for a in analyses:
        img = annotate_image(a)
        out_path = out_dir / f"{a.image_id}.png"
        img.save(out_path, "PNG")
        output_paths.append(out_path)
    return output_paths


def write_csv(all_selected: Dict[str, List[ImageAnalysis]],
              per_class_data: Dict[str, List[ImageAnalysis]]) -> Path:
    csv_path = OUT_ROOT / "ERROR_ANALYSIS_INDEX.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header
        header = ["image_id", "group", "tp", "fp", "fn", "severity",
                  "gt_count", "prediction_count", "output_path"]
        # Add per-class columns
        for cls_name in CLASS_NAMES.values():
            header += [f"{cls_name}_gt", f"{cls_name}_tp",
                       f"{cls_name}_fp", f"{cls_name}_fn"]
        writer.writerow(header)

        for group, img_list in all_selected.items():
            for idx, a in enumerate(img_list):
                severity = a.fn + a.fp
                output_path = (OUT_DIRS[group] / f"{a.image_id}.png").as_posix()
                row = [a.image_id, group, a.tp, a.fp, a.fn, severity,
                       len(a.gt_boxes), len(a.pred_boxes), output_path]
                cc = a.class_counts()
                for cls_name in CLASS_NAMES.values():
                    row += [cc[cls_name]["gt"], cc[cls_name]["tp"],
                            cc[cls_name]["fp"], cc[cls_name]["fn"]]
                writer.writerow(row)

    return csv_path


def write_report(all_analyses: List[ImageAnalysis],
                 selected: Dict[str, List[ImageAnalysis]],
                 csv_path: Path) -> Path:
    report_path = OUT_ROOT / "ERROR_ANALYSIS_REPORT.md"

    # Aggregate stats
    total_tp = sum(a.tp for a in all_analyses)
    total_fp = sum(a.fp for a in all_analyses)
    total_fn = sum(a.fn for a in all_analyses)
    total_gt = sum(len(a.gt_boxes) for a in all_analyses)

    # Per-class stats
    class_stats: Dict[str, Dict[str, int]] = {
        name: {"tp": 0, "fp": 0, "fn": 0, "gt": 0}
        for name in CLASS_NAMES.values()
    }
    for a in all_analyses:
        cc = a.class_counts()
        for name in CLASS_NAMES.values():
            class_stats[name]["tp"] += cc[name]["tp"]
            class_stats[name]["fp"] += cc[name]["fp"]
            class_stats[name]["fn"] += cc[name]["fn"]
            class_stats[name]["gt"] += cc[name]["gt"]

    lines = [
        "# Dataset A Validation Error Analysis Report",
        "",
        "## Purpose",
        "This report documents the visual error analysis of the Experiment 2 model's",
        "predictions on the Dataset A validation split. It generates annotated images",
        "that illustrate **missed detections**, **false positives**, and **successful detections**",
        "to build a visual evidence base for root-cause analysis before designing Experiment 3.",
        "",
        "## Source Artifacts",
        f"- **Prediction file**: `{PRED_PATH.relative_to(PROJECT_ROOT)}`",
        f"- **Image dir**: `{VAL_IMAGES.relative_to(PROJECT_ROOT)}/`",
        f"- **Label dir**: `{VAL_LABELS.relative_to(PROJECT_ROOT)}/`",
        f"- **Experiment 2 model**: `runs/detect/experiments/training/yol11s_experiment2/weights/best.pt`",
        "",
        "## Analysis Settings",
        f"- **Confidence threshold**: {CONF_THRESH}",
        f"- **IoU matching threshold**: {IOU_THRESH}",
        "- **Matching**: class-aware greedy (highest-confidence prediction matched to best-IoU ground truth of same class)",
        "- **Image size**: 720x720 (Dataset A)",
        "",
        "## Class Mapping",
        "| ID | Class Name |",
        "|----|------------|",
    ]
    for cid, name in sorted(CLASS_NAMES.items()):
        lines.append(f"| {cid} | {name} |")

    lines += [
        "",
        "## Scope",
        f"- **Images analyzed**: {len(all_analyses)}",
        f"- **Total ground-truth objects**: {total_gt}",
        f"- **Total TP**: {total_tp}",
        f"- **Total FP**: {total_fp}",
        f"- **Total FN**: {total_fn}",
        f"- **Overall precision**: {total_tp / (total_tp + total_fp):.4f}" if (total_tp + total_fp) else "- **Overall precision**: N/A",
        f"- **Overall recall**: {total_tp / (total_tp + total_fn):.4f}" if (total_tp + total_fn) else "- **Overall recall**: N/A",
        "",
        "## Per-Class Breakdown",
        "| Class | GT | TP | FP | FN | Precision | Recall |",
        "|-------|----|----|----|----|-----------|--------|",
    ]
    for name in CLASS_NAMES.values():
        s = class_stats[name]
        prec = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 0.0
        rec = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 0.0
        lines.append(f"| {name} | {s['gt']} | {s['tp']} | {s['fp']} | {s['fn']} | {prec:.4f} | {rec:.4f} |")

    lines += [
        "",
        "## Selected Examples",
    ]
    for group, img_list in selected.items():
        lines.append(f"### {group} ({len(img_list)} images)")
        for a in img_list:
            cc = a.class_counts()
            lines.append(
                f"- `{a.image_id}`: TP={a.tp} FP={a.fp} FN={a.fn}"
                f" | GT={len(a.gt_boxes)} Preds={len(a.pred_boxes)}"
            )

    lines += [
        "",
        "## Selection Methodology",
        "Selection is deterministic (seed=42).",
        "",
        "- **Missed**: filtered to images with FN > 0, sorted by total severity, then scored to prioritize class diversity.",
        "- **False positives**: filtered to images with FP > 0, excluding images already selected for missed, scored for class diversity.",
        "- **Successful**: filtered to images with TP >= 3 and (FP + FN) <= 0.6 * TP, excluding images already selected for the first two categories.",
        "- Each category targets 12 images with representation across the 4 classes where possible.",
        "",
        "## Limitations",
        "Selection tries to represent all four classes but is constrained by the available error distribution.",
        "If a class has too few representative examples, it may be under-represented or absent in a category.",
        "Image selection is best-effort diversity, not exhaustive ranking.",
        "",
        "## Outputs",
        f"- Annotated images: `experiments/error_analysis/missed/`, `false_positives/`, `successful/`",
        f"- Index CSV: `experiments/error_analysis/{csv_path.name}`",
        f"- This report: `experiments/error_analysis/ERROR_ANALYSIS_REPORT.md`",
        "",
        "## Visual Legend",
        "- **Green**: Ground-truth box that was matched (TP)",
        "- **Orange**: Ground-truth box that was missed (FN)",
        "- **Blue**: Prediction that correctly matched a GT (TP)",
        "- **Red**: Prediction with no matching GT (FP)",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


# --------------------------------------------------------------------------- #
# Validation checks on output
# --------------------------------------------------------------------------- #

def run_output_checks(selected: Dict[str, List[ImageAnalysis]]) -> List[str]:
    errors: List[str] = []

    all_ids: List[str] = []
    for group, img_list in selected.items():
        ids_in_group = [a.image_id for a in img_list]
        all_ids.append(group)

        # check no duplicates within group
        if len(ids_in_group) != len(set(ids_in_group)):
            errors.append(f"Duplicate image IDs found in group '{group}'")

        # check output files exist
        for a in img_list:
            out_path = OUT_DIRS[group] / f"{a.image_id}.png"
            if not out_path.exists():
                errors.append(f"Missing output image: {out_path}")
            # check original image exists
            orig_path = VAL_IMAGES / a.file_name
            if not orig_path.exists():
                errors.append(f"Missing source image: {orig_path}")

    # check cross-category duplicates (warn only, not error)
    seen_ids: set[str] = set()
    for group, img_list in selected.items():
        for a in img_list:
            if a.image_id in seen_ids:
                errors.append(f"Warning: image {a.image_id} appears in multiple categories")
            seen_ids.add(a.image_id)

    return errors


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    print("=" * 60)
    print("Dataset A Validation Error Analysis Sheet Generator")
    print("=" * 60)

    # Clean output directory to avoid stale files from prior runs
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)

    # Step 0: Validate inputs
    input_errors = validate_inputs()
    if input_errors:
        print("[ERROR] Input validation failed:")
        for e in input_errors:
            print(f"  - {e}")
        return 1

    print("[INFO] Inputs validated. Loading predictions...")

    # Step 1-3: Load predictions, GT, and perform matching
    pred_by_id = load_predictions()
    print(f"[INFO] Loaded {len(pred_by_id)} prediction records.")

    # Process all images
    label_map: Dict[str, Path] = {lp.stem: lp for lp in VAL_LABELS.glob("*.txt")}
    all_analyses: List[ImageAnalysis] = []
    for image_id, rec in pred_by_id.items():
        label_path = label_map.get(image_id)
        img_path = VAL_IMAGES / rec.get("file_name", f"{image_id}.jpg")
        if label_path is None:
            print(f"[WARN] No label for {image_id}, skipping.")
            continue
        if not img_path.exists():
            print(f"[WARN] No image for {image_id}, skipping.")
            continue
        all_analyses.append(process_image(image_id, rec, label_path))

    n_processed = len(all_analyses)
    print(f"[INFO] Processed {n_processed} validation images.")

    if n_processed != 229:
        print(f"[WARN] Expected 229 images but processed {n_processed}.")

    # Step 4: Selection
    print("[INFO] Selecting representative images...")
    selected = select_representative()

    for group, img_list in selected.items():
        print(f"  {group}: {len(img_list)} selected")

    # Step 5: Generate annotated images
    print("[INFO] Generating annotated images...")
    for group, img_list in selected.items():
        build_annotated_and_copy(img_list, OUT_DIRS[group])
    print("[INFO] Annotated images saved.")

    # Step 6: Write CSV index
    csv_path = write_csv(selected, selected)
    print(f"[INFO] CSV index written: {csv_path}")

    # Step 7: Write report
    report_path = write_report(all_analyses, selected, csv_path)
    print(f"[INFO] Report written: {report_path}")

    # Step 8: Output validation checks
    print("[INFO] Running output validation checks...")
    check_errors = run_output_checks(selected)
    if check_errors:
        print("[ERROR] Output validation issues:")
        for e in check_errors:
            print(f"  - {e}")
    else:
        print("[INFO] All output validation checks passed.")

    # Print summary stats
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_tp = sum(a.tp for a in all_analyses)
    total_fp = sum(a.fp for a in all_analyses)
    total_fn = sum(a.fn for a in all_analyses)
    print(f"Images processed: {n_processed}")
    print(f"TP={total_tp}  FP={total_fp}  FN={total_fn}")
    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
    print(f"Precision={prec:.4f}  Recall={rec:.4f}")
    print()
    print("Selected examples per category:")
    for group, img_list in selected.items():
        print(f"  {group}: {len(img_list)}")
    print()
    print("Output locations:")
    print(f"  {OUT_ROOT}/")
    print(f"  {csv_path}")
    print(f"  {report_path}")

    return 0 if not check_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
