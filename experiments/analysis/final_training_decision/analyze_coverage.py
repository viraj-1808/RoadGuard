import os
import glob
import csv
from collections import Counter
from PIL import Image
import numpy as np

CLASS_NAMES = ['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole']
DATA_ROOT = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset"

# COCO-style size thresholds (pixel area)
# Very small: area < 32^2 = 1024
# Medium: 32^2 <= area < 96^2 = 9216
# Large: area >= 96^2 = 9216

SUBSETS = [
    {
        "name": "dataset_a_train",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "train"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "train"),
        "img_w": 720,
        "img_h": 720,
    },
    {
        "name": "dataset_a_val",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "val"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "val"),
        "img_w": 720,
        "img_h": 720,
    },
    {
        "name": "dataset_a_test",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "test"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "test"),
        "img_w": 720,
        "img_h": 720,
        "frozen": True,
    },
    {
        "name": "dataset_b_train",
        "labels_dir": os.path.join(DATA_ROOT, "experiment2", "labels", "train"),
        "images_dir": os.path.join(DATA_ROOT, "experiment2", "images", "train"),
        "img_w": 512,
        "img_h": 512,
    },
    {
        "name": "dataset_b_val",
        "labels_dir": os.path.join(DATA_ROOT, "experiment2", "labels", "val"),
        "images_dir": os.path.join(DATA_ROOT, "experiment2", "images", "val"),
        "img_w": 512,
        "img_h": 512,
    },
]

OUTPUT_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\final_training_decision"


def compute_stats(subset):
    labels_dir = subset["labels_dir"]
    images_dir = subset["images_dir"]
    img_w = subset["img_w"]
    img_h = subset["img_h"]
    frozen = subset.get("frozen", False)

    label_files = sorted(glob.glob(os.path.join(labels_dir, "*.txt")))

    if not label_files:
        return None

    obj_count = 0
    class_dist = Counter()
    aspect_ratios = []
    bbox_widths = []
    bbox_heights = []
    bbox_areas = []
    rel_areas = []
    size_dist_by_class = {c: {"very_small": 0, "medium": 0, "large": 0} for c in range(len(CLASS_NAMES))}
    img_dim_set = set()

    for lf in label_files:
        fname = os.path.splitext(os.path.basename(lf))[0]
        img_path = os.path.join(images_dir, fname + ".jpg")
        if not os.path.exists(img_path):
            continue
        try:
            img = Image.open(img_path)
            dw, dh = img.size
            img_dim_set.add((dw, dh))
        except Exception:
            continue

        with open(lf, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id = int(parts[0])
                cx, cy, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                class_dist[cls_id] += 1
                obj_count += 1

                # Bbox dimensions in normalized coords
                bbox_widths.append(bw)
                bbox_heights.append(bh)

                # Pixel dimensions
                bw_px = bw * img_w
                bh_px = bh * img_h
                area_px = bw_px * bh_px

                # Relative area (normalized)
                rel_area = bw * bh

                # Aspect ratio
                ar = bw / bh if bh > 0 else 0
                aspect_ratios.append(ar)

                # Bounding-box area
                bbox_areas.append(area_px)
                rel_areas.append(rel_area)

                # Object-size distribution by class (COCO-style pixel area thresholds)
                # very_small: area < 1024, medium: 1024 <= area < 9216, large: area >= 9216
                if area_px < 1024:
                    size_dist_by_class[cls_id]["very_small"] += 1
                elif area_px < 9216:
                    size_dist_by_class[cls_id]["medium"] += 1
                else:
                    size_dist_by_class[cls_id]["large"] += 1

    # Summarize
    total_images = len(label_files)
    # Count actual images with valid labels
    valid_images = len(img_dim_set) if img_dim_set else total_images

    summary = {
        "subset": subset["name"],
        "image_count": total_images,
        "valid_image_count": valid_images,
        "object_count": obj_count,
        "class_distribution": dict(class_dist),
        "image_dimensions": img_dim_set,
        "aspect_ratios": aspect_ratios,
        "bbox_widths_norm": bbox_widths,
        "bbox_heights_norm": bbox_heights,
        "bbox_areas_px": bbox_areas,
        "rel_areas": rel_areas,
        "size_dist_by_class": size_dist_by_class,
    }
    return summary


def percentile(arr, p):
    if not arr:
        return 0
    arr_sorted = sorted(arr)
    k = (len(arr_sorted) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(arr_sorted) - 1)
    if f == c:
        return arr_sorted[int(k)]
    return arr_sorted[f] * (c - k) + arr_sorted[c] * (k - f)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_summaries = []

    for subset in SUBSETS:
        print(f"\nComputing stats for {subset['name']}...")
        s = compute_stats(subset)
        if s is None:
            print(f"  No data found for {subset['name']}")
            continue
        all_summaries.append(s)
        print(f"  Images: {s['image_count']}, Objects: {s['object_count']}, Classes: {dict(s['class_distribution'])}")

    # --- Write dataset_coverage_summary.csv ---
    csv_path1 = os.path.join(OUTPUT_DIR, "dataset_coverage_summary.csv")
    with open(csv_path1, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "subset", "image_count", "valid_image_count", "object_count",
            "class_distribution", "image_dimensions",
            "aspect_ratio_min", "aspect_ratio_max", "aspect_ratio_median",
            "bbox_width_min", "bbox_width_max", "bbox_width_mean",
            "bbox_height_min", "bbox_height_max", "bbox_height_mean",
            "bbox_area_min", "bbox_area_max", "bbox_area_mean",
            "rel_area_min", "rel_area_max", "rel_area_mean",
        ])
        for s in all_summaries:
            cr = s["class_distribution"]
            ad = s["image_dimensions"]
            ar_vals = s["aspect_ratios"]
            bw_vals = s["bbox_widths_norm"]
            bh_vals = s["bbox_heights_norm"]
            ba_vals = s["bbox_areas_px"]
            ra_vals = s["rel_areas"]

            writer.writerow([
                s["subset"],
                s["image_count"],
                s["valid_image_count"],
                s["object_count"],
                str(cr),
                str(ad),
                min(ar_vals) if ar_vals else "",
                max(ar_vals) if ar_vals else "",
                np.median(ar_vals) if ar_vals else "",
                min(bw_vals) if bw_vals else "",
                max(bw_vals) if bw_vals else "",
                np.mean(bw_vals) if bw_vals else "",
                min(bh_vals) if bh_vals else "",
                max(bh_vals) if bh_vals else "",
                np.mean(bh_vals) if bh_vals else "",
                min(ba_vals) if ba_vals else "",
                max(ba_vals) if ba_vals else "",
                np.mean(ba_vals) if ba_vals else "",
                min(ra_vals) if ra_vals else "",
                max(ra_vals) if ra_vals else "",
                np.mean(ra_vals) if ra_vals else "",
            ])

    print(f"\nWrote {csv_path1}")

    # --- Write class_size_distribution.csv ---
    csv_path2 = os.path.join(OUTPUT_DIR, "class_size_distribution.csv")
    with open(csv_path2, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "subset", "class_id", "class_name",
            "very_small_count", "medium_count", "large_count",
            "very_small_rel_percent", "medium_rel_percent", "large_rel_percent",
        ])
        for s in all_summaries:
            for cls_id in sorted(s["size_dist_by_class"].keys()):
                sd = s["size_dist_by_class"][cls_id]
                total_in_class = sd["very_small"] + sd["medium"] + sd["large"]
                if total_in_class == 0:
                    vsp = msp = lsp = 0.0
                else:
                    vsp = sd["very_small"] / total_in_class * 100
                    msp = sd["medium"] / total_in_class * 100
                    lsp = sd["large"] / total_in_class * 100
                writer.writerow([
                s["subset"],
                cls_id,
                    CLASS_NAMES[cls_id],
                    sd["very_small"],
                    sd["medium"],
                    sd["large"],
                    f"{vsp:.2f}",
                    f"{msp:.2f}",
                    f"{lsp:.2f}",
                ])

    print(f"Wrote {csv_path2}")

    # Print summary
    print("\n=== Dataset Coverage Summary ===")
    for s in all_summaries:
        print(f"\n{s['name']}:")
        print(f"  Images: {s['image_count']}, Valid: {s['valid_image_count']}, Objects: {s['object_count']}")
        print(f"  Class distribution: {dict(s['class_distribution'])}")
        print(f"  Image dimensions: {s['image_dimensions']}")
        if s["aspect_ratios"]:
            ar = s["aspect_ratios"]
            print(f"  Aspect ratio: min={min(ar):.4f}, max={max(ar):.4f}, median={np.median(ar):.4f}")
        if s["bbox_areas_px"]:
            ba = s["bbox_areas_px"]
            print(f"  Bbox area (px): min={min(ba)}, max={max(ba)}, mean={np.mean(ba):.1f}")
        if s["rel_areas"]:
            ra = s["rel_areas"]
            print(f"  Relative area: min={min(ra):.6f}, max={max(ra):.6f}, mean={np.mean(ra):.6f}")


if __name__ == "__main__":
    main()