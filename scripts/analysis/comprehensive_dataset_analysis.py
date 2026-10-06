import os
import glob
import csv
import math
from datetime import datetime
from collections import Counter, defaultdict
from PIL import Image
import numpy as np

CLASS_NAMES = ['longitudinal_crack', 'transverse_crack', 'alligator_crack', 'pothole']
CLASS_NAMES_ABBR = ['Lc', 'Tc', 'Ac', 'Ph']

DATA_ROOT = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset"

SUBSETS = [
    {
        "name": "dataset_a_train",
        "dataset": "A",
        "split": "train",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "train"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "train"),
    },
    {
        "name": "dataset_a_val",
        "dataset": "A",
        "split": "val",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "val"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "val"),
    },
    {
        "name": "dataset_a_test",
        "dataset": "A",
        "split": "test",
        "labels_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "labels", "test"),
        "images_dir": os.path.join(DATA_ROOT, "yolo_rdd2022_india", "images", "test"),
    },
    {
        "name": "dataset_b_train",
        "dataset": "B",
        "split": "train",
        "labels_dir": os.path.join(DATA_ROOT, "experiment2", "labels", "train"),
        "images_dir": os.path.join(DATA_ROOT, "experiment2", "images", "train"),
    },
    {
        "name": "dataset_b_val",
        "dataset": "B",
        "split": "val",
        "labels_dir": os.path.join(DATA_ROOT, "experiment2", "labels", "val"),
        "images_dir": os.path.join(DATA_ROOT, "experiment2", "images", "val"),
    },
]

OUTPUT_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\final_training_decision"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def percentile(arr, p):
    if not arr:
        return 0.0
    arr_sorted = sorted(arr)
    k = (len(arr_sorted) - 1) * p / 100.0
    f = int(math.floor(k))
    c = min(f + 1, len(arr_sorted) - 1)
    if f == c:
        return float(arr_sorted[int(k)])
    return float(arr_sorted[f] * (c - k) + arr_sorted[c] * (k - f))


def compute_stats(subset):
    labels_dir = subset["labels_dir"]
    images_dir = subset["images_dir"]

    label_files = sorted(glob.glob(os.path.join(labels_dir, "*.txt")))

    if not label_files:
        return None

    obj_count = 0
    class_dist = Counter()
    aspect_ratios = []
    bbox_widths_norm = []
    bbox_heights_norm = []
    bbox_widths_px = []
    bbox_heights_px = []
    bbox_areas_px = []
    rel_areas = []
    img_dims_counter = Counter()
    missing_images = 0

    size_dist_by_class = {
        cls_id: {
            "very_small": 0,
            "small": 0,
            "medium": 0,
            "large": 0,
        }
        for cls_id in range(len(CLASS_NAMES))
    }

    valid_images = 0

    for lf in label_files:
        fname = os.path.splitext(os.path.basename(lf))[0]
        img_path = os.path.join(images_dir, fname + ".jpg")
        if not os.path.exists(img_path):
            missing_images += 1
            continue

        try:
            img = Image.open(img_path)
            img_w, img_h = img.size
            img_dims_counter[(img_w, img_h)] += 1
            valid_images += 1
            img_area = img_w * img_h
        except Exception:
            missing_images += 1
            continue

        with open(lf, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id = int(parts[0])
                cx, cy, bw_norm, bh_norm = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                class_dist[cls_id] += 1
                obj_count += 1

                bw_px = bw_norm * img_w
                bh_px = bh_norm * img_h
                area_px = bw_px * bh_px
                rel_area = area_px / img_area if img_area > 0 else 0.0

                ar = bw_norm / bh_norm if bh_norm > 0 else 0.0
                aspect_ratios.append(ar)
                bbox_widths_norm.append(bw_norm)
                bbox_heights_norm.append(bh_norm)
                bbox_widths_px.append(bw_px)
                bbox_heights_px.append(bh_px)
                bbox_areas_px.append(area_px)
                rel_areas.append(rel_area)

                if rel_area < 0.001:
                    size_dist_by_class[cls_id]["very_small"] += 1
                elif rel_area < 0.01:
                    size_dist_by_class[cls_id]["small"] += 1
                elif rel_area < 0.1:
                    size_dist_by_class[cls_id]["medium"] += 1
                else:
                    size_dist_by_class[cls_id]["large"] += 1

    summary = {
        "subset": subset["name"],
        "dataset": subset["dataset"],
        "split": subset["split"],
        "image_count": len(label_files),
        "valid_image_count": valid_images,
        "missing_image_count": missing_images,
        "object_count": obj_count,
        "class_distribution": dict(class_dist),
        "unique_image_dims": len(img_dims_counter),
        "most_common_dims": img_dims_counter.most_common(5),
        "aspect_ratios": aspect_ratios,
        "bbox_widths_norm": bbox_widths_norm,
        "bbox_heights_norm": bbox_heights_norm,
        "bbox_widths_px": bbox_widths_px,
        "bbox_heights_px": bbox_heights_px,
        "bbox_areas_px": bbox_areas_px,
        "rel_areas": rel_areas,
        "size_dist_by_class": size_dist_by_class,
    }
    return summary


def fmt(v, decimals=2):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def write_coverage_csv(summaries, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "subset", "dataset", "split", "image_count", "valid_image_count", "missing_image_count",
            "object_count", "class_distribution",
            "unique_image_dims", "most_common_dims",
            "aspect_ratio_min", "aspect_ratio_max", "aspect_ratio_mean", "aspect_ratio_median",
            "bbox_width_norm_min", "bbox_width_norm_max", "bbox_width_norm_mean", "bbox_width_norm_median",
            "bbox_height_norm_min", "bbox_height_norm_max", "bbox_height_norm_mean", "bbox_height_norm_median",
            "bbox_width_px_min", "bbox_width_px_max", "bbox_width_px_mean", "bbox_width_px_median",
            "bbox_height_px_min", "bbox_height_px_max", "bbox_height_px_mean", "bbox_height_px_median",
            "bbox_area_px_min", "bbox_area_px_max", "bbox_area_px_mean", "bbox_area_px_median",
            "rel_area_min", "rel_area_max", "rel_area_mean", "rel_area_median",
        ])
        for s in summaries:
            ar = s["aspect_ratios"]
            bwn = s["bbox_widths_norm"]
            bhn = s["bbox_heights_norm"]
            bwp = s["bbox_widths_px"]
            bhp = s["bbox_heights_px"]
            bap = s["bbox_areas_px"]
            ra = s["rel_areas"]

            def stat(arr):
                if not arr:
                    return ["", "", "", ""]
                return [
                    min(arr), max(arr), np.mean(arr), percentile(arr, 50)
                ]

            ar_min, ar_max, ar_mean, ar_med = stat(ar)
            bwn_min, bwn_max, bwn_mean, bwn_med = stat(bwn)
            bhn_min, bhn_max, bhn_mean, bhn_med = stat(bhn)
            bwp_min, bwp_max, bwp_mean, bwp_med = stat(bwp)
            bhp_min, bhp_max, bhp_mean, bhp_med = stat(bhp)
            bap_min, bap_max, bap_mean, bap_med = stat(bap)
            ra_min, ra_max, ra_mean, ra_med = stat(ra)

            writer.writerow([
                s["subset"], s["dataset"], s["split"],
                s["image_count"], s["valid_image_count"], s["missing_image_count"],
                s["object_count"], str(s["class_distribution"]),
                s["unique_image_dims"], str(s["most_common_dims"]),
                fmt(ar_min), fmt(ar_max), fmt(ar_mean), fmt(ar_med),
                fmt(bwn_min), fmt(bwn_max), fmt(bwn_mean), fmt(bwn_med),
                fmt(bhn_min), fmt(bhn_max), fmt(bhn_mean), fmt(bhn_med),
                fmt(bwp_min), fmt(bwp_max), fmt(bwp_mean), fmt(bwp_med),
                fmt(bhp_min), fmt(bhp_max), fmt(bhp_mean), fmt(bhp_med),
                fmt(bap_min), fmt(bap_max), fmt(bap_mean), fmt(bap_med),
                fmt(ra_min), fmt(ra_max), fmt(ra_mean), fmt(ra_med),
            ])


def write_class_size_csv(summaries, path):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "subset", "dataset", "split", "class_id", "class_name",
            "very_small_count", "small_count", "medium_count", "large_count", "total_count",
            "very_small_pct", "small_pct", "medium_pct", "large_pct",
        ])
        for s in summaries:
            for cls_id in sorted(s["size_dist_by_class"].keys()):
                sd = s["size_dist_by_class"][cls_id]
                total = sd["very_small"] + sd["small"] + sd["medium"] + sd["large"]
                if total == 0:
                    vsp = sp = mp = lp = 0.0
                else:
                    vsp = sd["very_small"] / total * 100
                    sp = sd["small"] / total * 100
                    mp = sd["medium"] / total * 100
                    lp = sd["large"] / total * 100
                writer.writerow([
                    s["subset"], s["dataset"], s["split"], cls_id, CLASS_NAMES[cls_id],
                    sd["very_small"], sd["small"], sd["medium"], sd["large"], total,
                    fmt(vsp), fmt(sp), fmt(mp), fmt(lp),
                ])


def generate_markdown_report(summaries, path):
    lines = []
    lines.append("# RoadGuard AI - Dataset Coverage and Size Analysis Report\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("## Executive Summary\n")
    total_images = sum(s["image_count"] for s in summaries)
    total_objects = sum(s["object_count"] for s in summaries)
    lines.append(f"- **Total subsets analyzed:** {len(summaries)}")
    lines.append(f"- **Total images:** {total_images}")
    lines.append(f"- **Total annotated objects:** {total_objects}")
    lines.append(f"- **Classes:** {', '.join(CLASS_NAMES)}")
    lines.append("")

    lines.append("## Dataset Overview\n")
    lines.append("| Subset | Dataset | Split | Images | Valid | Objects | Unique Dims |")
    lines.append("|--------|---------|-------|--------|-------|---------|-------------|")
    for s in summaries:
        lines.append(
            f"| {s['subset']} | {s['dataset']} | {s['split']} | "
            f"{s['image_count']} | {s['valid_image_count']} | {s['object_count']} | "
            f"{s['unique_image_dims']} |"
        )
    lines.append("")

    lines.append("## Class Distribution per Subset\n")
    lines.append("| Subset | " + " | ".join(CLASS_NAMES_ABBR) + " | Total |")
    lines.append("|--------|" + "|".join(["--------"] * len(CLASS_NAMES_ABBR)) + "|--------|")
    for s in summaries:
        counts = [s["class_distribution"].get(i, 0) for i in range(len(CLASS_NAMES))]
        total = sum(counts)
        pcts = [f"{c/total*100:.1f}%" if total > 0 else "0%" for c in counts]
        line = "| " + s["subset"] + " | " + " | ".join([f"{c} ({p})" for c, p in zip(counts, pcts)]) + f" | {total} |"
        lines.append(line)
    lines.append("")

    lines.append("## Bounding Box Statistics (Normalized Coordinates)\n")
    lines.append("| Subset | W Min | W Max | W Mean | H Min | H Max | H Mean |")
    lines.append("|--------|-------|-------|--------|-------|-------|--------|")
    for s in summaries:
        bw = s["bbox_widths_norm"]
        bh = s["bbox_heights_norm"]
        if bw and bh:
            lines.append(
                f"| {s['subset']} | "
                f"{fmt(min(bw), 4)} | {fmt(max(bw), 4)} | {fmt(np.mean(bw), 4)} | "
                f"{fmt(min(bh), 4)} | {fmt(max(bh), 4)} | {fmt(np.mean(bh), 4)} |"
            )
        else:
            lines.append(f"| {s['subset']} | N/A | N/A | N/A | N/A | N/A | N/A |")
    lines.append("")

    lines.append("## Bounding Box Statistics (Pixel Coordinates)\n")
    lines.append("| Subset | Area Min | Area Max | Area Mean | Rel Area Min | Rel Area Max | Rel Area Mean |")
    lines.append("|--------|----------|----------|-----------|--------------|--------------|---------------|")
    for s in summaries:
        ba = s["bbox_areas_px"]
        ra = s["rel_areas"]
        if ba and ra:
            lines.append(
                f"| {s['subset']} | "
                f"{fmt(min(ba), 1)} | {fmt(max(ba), 1)} | {fmt(np.mean(ba), 1)} | "
                f"{fmt(min(ra), 6)} | {fmt(max(ra), 6)} | {fmt(np.mean(ra), 6)} |"
            )
        else:
            lines.append(f"| {s['subset']} | N/A | N/A | N/A | N/A | N/A | N/A |")
    lines.append("")

    lines.append("## Object Size Distribution by Relative Area\n")
    lines.append("- **Very Small:** < 0.1% of image area")
    lines.append("- **Small:** 0.1% – 1% of image area")
    lines.append("- **Medium:** 1% – 10% of image area")
    lines.append("- **Large:** > 10% of image area\n")

    lines.append("| Subset | Class | Very Small | Small | Medium | Large | Total | Very Small % | Small % | Medium % | Large % |")
    lines.append("|--------|-------|------------|-------|--------|-------|-------|--------------|---------|----------|---------|")
    for s in summaries:
        for cls_id in range(len(CLASS_NAMES)):
            sd = s["size_dist_by_class"][cls_id]
            total = sd["very_small"] + sd["small"] + sd["medium"] + sd["large"]
            if total == 0:
                vsp = sp = mp = lp = 0.0
            else:
                vsp = sd["very_small"] / total * 100
                sp = sd["small"] / total * 100
                mp = sd["medium"] / total * 100
                lp = sd["large"] / total * 100
            lines.append(
                f"| {s['subset']} | {CLASS_NAMES[cls_id]} | "
                f"{sd['very_small']} | {sd['small']} | {sd['medium']} | {sd['large']} | {total} | "
                f"{fmt(vsp)}% | {fmt(sp)}% | {fmt(mp)}% | {fmt(lp)}% |"
            )
    lines.append("")

    lines.append("## Image Dimensions\n")
    lines.append("| Subset | Most Common Dimensions | Count |")
    lines.append("|--------|------------------------|-------|")
    for s in summaries:
        dims_str = ", ".join([f"{d[0][0]}x{d[0][1]} ({d[1]})" for d in s["most_common_dims"]])
        lines.append(f"| {s['subset']} | {dims_str} | {s['unique_image_dims']} unique |")
    lines.append("")

    lines.append("## Key Observations\n")
    for s in summaries:
        lines.append(f"### {s['subset']}")
        lines.append(f"- **Total objects:** {s['object_count']}")
        lines.append(f"- **Images with valid annotations:** {s['valid_image_count']}")
        lines.append(f"- **Missing image files:** {s['missing_image_count']}")

        ra = s["rel_areas"]
        if ra:
            lines.append(f"- **Relative area range:** {fmt(min(ra), 6)} – {fmt(max(ra), 6)}")
            lines.append(f"- **Mean relative area:** {fmt(np.mean(ra), 6)}")

        sd = s["size_dist_by_class"]
        for cls_id in range(len(CLASS_NAMES)):
            total = sum(sd[cls_id].values())
            if total == 0:
                continue
            vs = sd[cls_id]["very_small"]
            sm = sd[cls_id]["small"]
            med = sd[cls_id]["medium"]
            lg = sd[cls_id]["large"]
            lines.append(
                f"- **{CLASS_NAMES[cls_id]}:** very_small={fmt(vs/total*100)}%, "
                f"small={fmt(sm/total*100)}%, medium={fmt(med/total*100)}%, large={fmt(lg/total*100)}%"
            )
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    all_summaries = []

    for subset in SUBSETS:
        print(f"Analyzing {subset['name']}...")
        s = compute_stats(subset)
        if s is None:
            print(f"  No data found for {subset['name']}")
            continue
        all_summaries.append(s)
        print(
            f"  Images: {s['image_count']}, Valid: {s['valid_image_count']}, "
            f"Objects: {s['object_count']}, Classes: {dict(s['class_distribution'])}"
        )

    csv_path1 = os.path.join(OUTPUT_DIR, "dataset_coverage_summary.csv")
    csv_path2 = os.path.join(OUTPUT_DIR, "class_size_distribution.csv")
    md_path = os.path.join(OUTPUT_DIR, "dataset_analysis_report.md")

    write_coverage_csv(all_summaries, csv_path1)
    write_class_size_csv(all_summaries, csv_path2)
    generate_markdown_report(all_summaries, md_path)

    print(f"\nWrote {csv_path1}")
    print(f"Wrote {csv_path2}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
