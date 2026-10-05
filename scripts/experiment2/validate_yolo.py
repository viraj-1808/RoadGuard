#!/usr/bin/env python
"""Phase 11 -- Experiment 2 YOLO conversion validation.

Validates the Experiment 2 Dataset B conversion end to end and writes:

* ``experiments/analysis/overnight/experiment2_dataset_b/experiment2_conversion_validation.json``
* ``experiments/analysis/overnight/experiment2_dataset_b/experiment2_conversion_report.md``

Checks performed:

1. **Pairing** -- every image under ``images/{train,val}`` has a matching ``.txt``
   label and every label has an image. Orphans are reported in both directions.
2. **Negatives** -- empty label files are present-and-valid and are counted.
3. **Row grammar** -- every label row has exactly 5 tokens, a class id in
   ``{0,1,2,3}``, parseable floats, ``0 <= cx,cy <= 1``, ``0 < w <= 1``,
   ``0 < h <= 1`` and all four corners inside ``[0,1]``.
4. **Degenerate boxes** -- no zero-area or negative-area box (``w > 0 and h > 0``).
5. **Dimensions** -- image sizes are readable via PIL and match the
   ``width``/``height`` recorded in ``provenance_manifest.csv`` for converted rows.
6. **Reconciliation** -- three sources are reconciled and agreement is reported:
   (a) label files on disk, (b) ``provenance_manifest.csv`` n_objects / classes,
   (c) the Arrow source totals. A per-split and per-class table is printed.
7. **Statistics** -- per-split and per-country images, images-per-class,
   objects-per-class, negatives and negative percentage.

Dependencies: standard library + ``PIL`` + ``numpy`` + ``pyarrow`` (only for the
optional Arrow reconciliation; the script degrades gracefully when the Arrow
root is absent). No ``torch``, ``ultralytics`` or ``datasets`` import.

The script is read-only with respect to every dataset directory. It exits
non-zero when any hard check fails.

Usage:
    python validate_yolo.py
    python validate_yolo.py --workers 32
    python validate_yolo.py --exp2-root <path> --no-arrow
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import numpy as np
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_EXP2_ROOT = os.path.join(REPO_ROOT, "experiments", "dataset", "experiment2")
DEFAULT_ARROW_ROOT = os.path.join(REPO_ROOT, "experiments", "dataset", "raw_hf_rdd2022")
DEFAULT_OUT_DIR = os.path.join(
    REPO_ROOT, "experiments", "analysis", "overnight", "experiment2_dataset_b"
)

JSON_NAME = "experiment2_conversion_validation.json"
MD_NAME = "experiment2_conversion_report.md"

PROVENANCE_MANIFEST = "provenance_manifest.csv"
SPLITS = ("train", "val")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG", ".BMP")

#: Locked taxonomy, identical to the Experiment 1 baseline.
CLASS_NAMES: dict[int, str] = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}

#: RDD2022 damage code -> YOLO class id. Used to interpret the Arrow
#: ``categories`` column, which stores the RDD2022 class index.
TAXONOMY: dict[str, int] = {"D00": 0, "D10": 1, "D20": 2, "D40": 3}
RDD_CODE_BY_INDEX: dict[int, str] = {v: k for k, v in TAXONOMY.items()}

#: Arrow split name -> YOLO pool name on disk.
ARROW_SPLIT_TO_POOL: dict[str, str] = {
    "train": "train",
    "validation": "val",
    "test": "test",
}

DATASET_A_COUNTRY = "India"

#: Cap on how many individual problems are materialised in the JSON detail
#: arrays. The full counts are always reported even when the arrays are clipped.
MAX_DETAIL = 500

ROW_TOLERANCE = 1e-9


def rel(path: str) -> str:
    """Return *path* relative to the repository root when it lives inside it."""
    absolute = os.path.abspath(path)
    try:
        inside = os.path.commonpath([absolute, REPO_ROOT]) == REPO_ROOT
    except ValueError:
        inside = False
    if inside:
        return os.path.relpath(absolute, REPO_ROOT).replace("\\", "/")
    return absolute.replace("\\", "/")


def write_text_atomic(path: str, text: str) -> None:
    """Write *text* to *path* via a ``.part`` staging file and ``os.replace``."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    part = path + ".part"
    with open(part, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(part, path)


def write_json_atomic(path: str, payload: Any) -> str:
    """Write *payload* as pretty JSON atomically. Returns the text written."""
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    write_text_atomic(path, text)
    return text


def parse_country(file_name: str) -> str:
    """Derive the originating country from an RDD2022 ``file_name``.

    Mirrors ``scripts/experiment2/country_index.py`` so that per-country
    statistics here match the authoritative index.
    """
    base = os.path.basename(os.fspath(file_name))
    stem = os.path.splitext(base)[0]
    if stem.startswith("China_"):
        return "China"
    if stem.startswith("United_"):
        return "United States"
    if stem.startswith("India_"):
        return "India"
    if stem.startswith("Japan_"):
        return "Japan"
    if stem.startswith("Norway_"):
        return "Norway"
    if stem.startswith("Czech_"):
        return "Czech"
    return "Unknown"


def list_images(directory: str) -> dict[str, str]:
    """Map ``stem -> absolute path`` for every image under *directory*."""
    found: dict[str, str] = {}
    if not os.path.isdir(directory):
        return found
    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] not in IMAGE_EXTENSIONS:
                continue
            found[os.path.splitext(filename)[0]] = os.path.join(dirpath, filename)
    return dict(sorted(found.items()))


def list_labels(directory: str) -> dict[str, str]:
    """Map ``stem -> absolute path`` for every ``.txt`` under *directory*."""
    found: dict[str, str] = {}
    if not os.path.isdir(directory):
        return found
    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if os.path.splitext(filename)[1].lower() != ".txt":
                continue
            found[os.path.splitext(filename)[0]] = os.path.join(dirpath, filename)
    return dict(sorted(found.items()))


def read_provenance(path: str) -> list[dict[str, str]]:
    """Read ``provenance_manifest.csv``. Returns ``[]`` when it is absent."""
    if not os.path.isfile(path):
        return []
    rows: list[dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append({k: ("" if v is None else v) for k, v in row.items()})
    return rows


# ---------------------------------------------------------------------------
# label row validation
# ---------------------------------------------------------------------------
def validate_row(text: str) -> tuple[int, list[float] | None, list[str]]:
    """Validate one YOLO label row.

    Returns ``(class_id, values, problems)``. ``values`` is the parsed float
    tuple when the row is well-formed, otherwise ``None``.
    """
    problems: list[str] = []
    parts = text.split()
    if len(parts) != 5:
        return -1, None, [f"token_count:{len(parts)}_expected_5"]

    try:
        class_id = int(float(parts[0]))
    except ValueError:
        return -1, None, [f"unparseable_class:{parts[0]!r}"]
    if class_id not in CLASS_NAMES:
        problems.append(f"class_id_out_of_range:{class_id}")
        return class_id, None, problems

    values: list[float] = []
    for index, token in enumerate(parts[1:], start=1):
        try:
            value = float(token)
        except ValueError:
            problems.append(f"unparseable_float_field{index}:{token!r}")
            return class_id, None, problems
        if value != value or value in (float("inf"), float("-inf")):
            problems.append(f"non_finite_field{index}:{token!r}")
            return class_id, None, problems
        values.append(value)

    cx, cy, w, h = values
    if not 0.0 <= cx <= 1.0:
        problems.append(f"cx_out_of_unit_interval:{cx}")
    if not 0.0 <= cy <= 1.0:
        problems.append(f"cy_out_of_unit_interval:{cy}")
    if not 0.0 < w <= 1.0:
        problems.append(f"w_not_in_(0,1]:{w}")
    if not 0.0 < h <= 1.0:
        problems.append(f"h_not_in_(0,1]:{h}")
    if w <= 0.0 or h <= 0.0:
        problems.append("non_positive_area_box")

    if not problems:
        flat = np.asarray(
            [
                cx - w / 2.0,
                cx + w / 2.0,
                cy - h / 2.0,
                cy + h / 2.0,
            ],
            dtype=np.float64,
        )
        for name, edge in zip(("left", "right", "top", "bottom"), flat):
            if edge < -ROW_TOLERANCE or edge > 1.0 + ROW_TOLERANCE:
                problems.append(f"corner_{name}_outside_unit_interval:{edge:.6f}")

    return class_id, values, problems


def parse_label_file(path: str) -> dict[str, Any]:
    """Parse and validate one ``.txt`` label file.

    Returns the class ids, the object rows, the problem list, and the
    ``is_negative`` flag. An unreadable file yields ``readable=False``.
    """
    result: dict[str, Any] = {
        "path": path,
        "readable": True,
        "classes": [],
        "rows": [],
        "problems": [],
        "is_negative": False,
        "raw_line_count": 0,
    }
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        result["readable"] = False
        result["problems"].append(f"unreadable_label:{exc}")
        return result

    seen_content = False
    for line_number, line in enumerate(lines, start=1):
        if line.strip():
            seen_content = True
            result["raw_line_count"] += 1
            class_id, _values, problems = validate_row(line.strip())
            if problems:
                for problem in problems:
                    result["problems"].append(
                        {"line": line_number, "problem": problem, "raw": line.strip()[:200]}
                    )
                continue
            result["classes"].append(class_id)
            result["rows"].append((line_number, class_id))
    result["is_negative"] = not seen_content
    return result


def image_size(path: str) -> tuple[int, int] | None:
    """Return ``(width, height)`` read with PIL, or ``None`` when unreadable."""
    try:
        with Image.open(path) as handle:
            width, height = handle.size
            handle.verify()
    except (OSError, ValueError):
        try:
            with Image.open(path) as handle:
                width, height = handle.size
        except (OSError, ValueError):
            return None
    return int(width), int(height)


def _size_worker(path: str) -> tuple[str, tuple[int, int] | None]:
    """Thread-pool adapter for :func:`image_size`."""
    return path, image_size(path)


# ---------------------------------------------------------------------------
# Arrow source totals (optional, pyarrow only)
# ---------------------------------------------------------------------------
def arrow_totals(arrow_root: str) -> dict[str, Any]:
    """Return per-split image/object/class totals straight from the Arrow files.

    The Arrow store is the authoritative record of what the source dataset
    contains, so these totals are the third reconciliation source. Reading the
    ``.arrow`` files directly with ``pyarrow`` avoids importing ``datasets`` and
    avoids materialising the full DatasetDict.

    Any failure (missing root, missing split, unreadable table) is captured as a
    ``status`` string rather than raised, so validation still runs.
    """
    totals: dict[str, Any] = {
        "arrow_root": rel(arrow_root),
        "status": "ok",
        "available": False,
        "per_split": {},
        "note": (
            "Read directly from the .arrow IPC files with pyarrow; the `datasets` "
            "package is not imported."
        ),
    }
    if not os.path.isdir(arrow_root):
        totals["status"] = f"arrow_root_missing:{rel(arrow_root)}"
        return totals
    try:
        import pyarrow as pa  # noqa: PLC0415 - optional dependency, imported lazily
        import pyarrow.ipc as ipc
    except ImportError as exc:
        totals["status"] = f"pyarrow_unavailable:{exc}"
        return totals

    for split, pool in ARROW_SPLIT_TO_POOL.items():
        split_dir = os.path.join(arrow_root, split)
        if not os.path.isdir(split_dir):
            totals["status"] = f"arrow_split_missing:{split}"
            return totals
        shards = sorted(
            name for name in os.listdir(split_dir) if name.endswith(".arrow")
        )
        if not shards:
            totals["status"] = f"arrow_no_shards:{split}"
            return totals
        images = 0
        file_names = 0
        object_counts: Counter[int] = Counter()
        bad_records = 0
        try:
            for shard in shards:
                with open(os.path.join(split_dir, shard), "rb") as handle:
                    table = ipc.open_stream(handle).read_all()
                names = table.column("file_name").to_pylist()
                objects = table.column("objects").to_pylist()
                file_names += len(names)
                for record in objects:
                    categories = (record or {}).get("categories") or []
                    if not isinstance(categories, (list, tuple)):
                        categories = [categories]
                    images += 1
                    for category in categories:
                        try:
                            index = int(category)
                        except (TypeError, ValueError):
                            bad_records += 1
                            continue
                        code = RDD_CODE_BY_INDEX.get(index)
                        if code is None:
                            bad_records += 1
                            continue
                        object_counts[TAXONOMY[code]] += 1
        except (OSError, ValueError, pa.ArrowInvalid) as exc:
            totals["status"] = f"arrow_read_failed:{split}:{exc}"
            return totals
        totals["per_split"][pool] = {
            "arrow_split": split,
            "images": images,
            "file_names_seen": file_names,
            "objects": sum(object_counts.values()),
            "objects_per_class": {
                CLASS_NAMES[c]: object_counts.get(c, 0) for c in sorted(CLASS_NAMES)
            },
            "unmappable_categories": bad_records,
        }
    totals["available"] = bool(totals["per_split"])
    return totals


# ---------------------------------------------------------------------------
# per-split scan
# ---------------------------------------------------------------------------
def scan_split(
    exp2_root: str, split: str, workers: int, provenance: list[dict[str, str]]
) -> dict[str, Any]:
    """Scan one Experiment 2 split and return its full validation detail."""
    images_dir = os.path.join(exp2_root, "images", split)
    labels_dir = os.path.join(exp2_root, "labels", split)
    images = list_images(images_dir)
    labels = list_labels(labels_dir)

    image_stems = set(images)
    label_stems = set(labels)
    images_without_label = sorted(image_stems - label_stems)
    labels_without_image = sorted(label_stems - image_stems)

    prov_by_stem: dict[str, dict[str, str]] = {}
    for row in provenance:
        out_image = row.get("output_image_path", "")
        if not out_image:
            continue
        prov_by_stem[os.path.splitext(os.path.basename(out_image))[0]] = row

    print(f"  [{split}] parsing {len(labels)} label file(s)...", flush=True)
    parsed: dict[str, dict[str, Any]] = {}
    for stem, path in labels.items():
        parsed[stem] = parse_label_file(path)

    print(f"  [{split}] reading {len(images)} image dimension(s)...", flush=True)
    sizes: dict[str, tuple[int, int] | None] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for path, size in pool.map(_size_worker, list(images.values())):
            sizes[path] = size

    unreadable_images = sorted(rel(p) for p, s in sizes.items() if s is None)

    # --- statistics ---------------------------------------------------------
    object_counts: Counter[int] = Counter()
    class_image_counts: Counter[int] = Counter()
    per_country: Counter[str] = Counter()
    per_country_objects: dict[str, Counter[int]] = defaultdict(Counter)
    per_country_negatives: Counter[str] = Counter()
    negatives = 0
    negative_stems: list[str] = []
    problem_list: list[dict[str, Any]] = []
    unreadable_labels: list[str] = []
    degenerate = 0
    dimension_mismatch: list[dict[str, Any]] = []
    provenance_n_objects_mismatch: list[dict[str, Any]] = []
    manifest_rows_here = 0

    for stem, path in images.items():
        country = parse_country(stem)
        per_country[country] += 1
        entry = parsed.get(stem)
        classes: list[int] = entry["classes"] if entry else []
        for class_id in classes:
            object_counts[class_id] += 1
            per_country_objects[country][class_id] += 1
        for class_id in set(classes):
            class_image_counts[class_id] += 1
        if not classes:
            negatives += 1
            per_country_negatives[country] += 1
            negative_stems.append(stem)

        if entry is not None:
            if not entry["readable"]:
                unreadable_labels.append(rel(entry["path"]))
            for problem in entry["problems"]:
                detail = dict(problem) if isinstance(problem, dict) else {"problem": problem}
                detail["label"] = rel(entry["path"])
                detail["stem"] = stem
                if "non_positive_area_box" in str(detail.get("problem", "")):
                    degenerate += 1
                problem_list.append(detail)

        size = sizes.get(path)
        prov = prov_by_stem.get(stem)
        if prov is not None:
            manifest_rows_here += 1
            if size is not None:
                try:
                    manifest_w = int(float(prov.get("width", "")))
                    manifest_h = int(float(prov.get("height", "")))
                except ValueError:
                    manifest_w = manifest_h = -1
                if manifest_w >= 0 and (manifest_w, manifest_h) != size:
                    dimension_mismatch.append(
                        {
                            "image": rel(path),
                            "pil_size": list(size),
                            "manifest_width": manifest_w,
                            "manifest_height": manifest_h,
                        }
                    )
            try:
                manifest_n = int(float(prov.get("n_objects", "")))
            except ValueError:
                manifest_n = -1
            if manifest_n >= 0 and manifest_n != len(classes):
                provenance_n_objects_mismatch.append(
                    {
                        "stem": stem,
                        "label_file_objects": len(classes),
                        "manifest_n_objects": manifest_n,
                        "manifest_label_source": prov.get("label_source", ""),
                    }
                )

    total_images = len(images)
    per_split_stats = {
        "images": total_images,
        "label_files": len(labels),
        "objects": int(sum(object_counts.values())),
        "negative_images": negatives,
        "negative_percentage": round(100.0 * negatives / total_images, 4) if total_images else 0.0,
        "images_per_class": {
            CLASS_NAMES[c]: class_image_counts.get(c, 0) for c in sorted(CLASS_NAMES)
        },
        "objects_per_class": {
            CLASS_NAMES[c]: object_counts.get(c, 0) for c in sorted(CLASS_NAMES)
        },
        "per_country": {
            country: {
                "images": per_country[country],
                "objects": int(sum(per_country_objects[country].values())),
                "negative_images": per_country_negatives[country],
                "negative_percentage": round(
                    100.0 * per_country_negatives[country] / per_country[country], 4
                )
                if per_country[country]
                else 0.0,
                "images_per_class": {
                    CLASS_NAMES[c]: sum(
                        1
                        for stem in images
                        if parse_country(stem) == country
                        and class_id in set(parsed.get(stem, {}).get("classes", []))
                    )
                    for c in sorted(CLASS_NAMES)
                },
                "objects_per_class": {
                    CLASS_NAMES[c]: per_country_objects[country].get(c, 0)
                    for c in sorted(CLASS_NAMES)
                },
            }
            for country in sorted(per_country)
        },
    }

    hard_failures: list[str] = []
    if images_without_label:
        hard_failures.append(f"{split}:images_without_label")
    if labels_without_image:
        hard_failures.append(f"{split}:labels_without_image")
    if unreadable_images:
        hard_failures.append(f"{split}:unreadable_images")
    if unreadable_labels:
        hard_failures.append(f"{split}:unreadable_labels")
    if problem_list:
        hard_failures.append(f"{split}:invalid_label_rows")
    if dimension_mismatch:
        hard_failures.append(f"{split}:dimension_mismatch_vs_manifest")
    if provenance_n_objects_mismatch:
        hard_failures.append(f"{split}:n_objects_mismatch_vs_manifest")

    return {
        "split": split,
        "images_dir": rel(images_dir),
        "labels_dir": rel(labels_dir),
        "statistics": per_split_stats,
        "manifest_rows": manifest_rows_here,
        "images_without_label_count": len(images_without_label),
        "images_without_label": [rel(images[s]) for s in images_without_label[:MAX_DETAIL]],
        "labels_without_image_count": len(labels_without_image),
        "labels_without_image": [rel(labels[s]) for s in labels_without_image[:MAX_DETAIL]],
        "empty_label_files_count": sum(
            1 for entry in parsed.values() if entry["readable"] and entry["is_negative"]
        ),
        "negative_stems_sample": sorted(negative_stems)[:MAX_DETAIL],
        "invalid_row_count": len(problem_list),
        "invalid_rows": problem_list[:MAX_DETAIL],
        "invalid_rows_truncated": max(0, len(problem_list) - MAX_DETAIL),
        "degenerate_box_count": degenerate,
        "unreadable_images_count": len(unreadable_images),
        "unreadable_images": unreadable_images[:MAX_DETAIL],
        "unreadable_labels_count": len(unreadable_labels),
        "unreadable_labels": unreadable_labels[:MAX_DETAIL],
        "dimension_mismatch_count": len(dimension_mismatch),
        "dimension_mismatches": dimension_mismatch[:MAX_DETAIL],
        "n_objects_mismatch_count": len(provenance_n_objects_mismatch),
        "n_objects_mismatches": provenance_n_objects_mismatch[:MAX_DETAIL],
        "hard_failures": hard_failures,
    }


# ---------------------------------------------------------------------------
# reconciliation
# ---------------------------------------------------------------------------
def reconcile(
    per_split: dict[str, dict[str, Any]],
    provenance: list[dict[str, str]],
    arrow: dict[str, Any],
) -> dict[str, Any]:
    """Reconcile label files, the provenance manifest and the Arrow totals.

    Source 1 is the label files on disk. Source 2 is ``provenance_manifest.csv``
    (``n_objects`` and ``mapped_class``). Source 3 is the Arrow store.
    Agreement is reported per split and per class; any disagreement is listed.
    """
    manifest_objects: Counter[int] = Counter()
    manifest_images_per_class: Counter[int] = Counter()
    manifest_negatives = 0
    manifest_images = 0
    for row in provenance:
        classes = manifest_row_classes(row)
        if not classes:
            manifest_negatives += 1
        manifest_images += 1
        for class_id in classes:
            manifest_objects[class_id] += 1
        for class_id in set(classes):
            manifest_images_per_class[class_id] += 1

    rows: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for split in SPLITS:
        detail = per_split[split]
        stats = detail["statistics"]
        on_disk = stats["objects_per_class"]
        disk_total = stats["objects"]
        for class_id, class_name in sorted(CLASS_NAMES.items()):
            disk_value = int(on_disk.get(class_name, 0))
            manifest_value = int(manifest_objects.get(class_id, 0))
            arrow_split = arrow.get("per_split", {}).get(split, {})
            arrow_value = int(arrow_split.get("objects_per_class", {}).get(class_name, 0)) if arrow_split else None
            row = {
                "split": split,
                "class_id": class_id,
                "class_name": class_name,
                "label_files_on_disk": disk_value,
                "provenance_manifest": manifest_value,
                "arrow_source": arrow_value,
            }
            row["disk_matches_manifest"] = disk_value == manifest_value
            row["disk_matches_arrow"] = None if arrow_value is None else disk_value == arrow_value
            rows.append(row)
            if not row["disk_matches_manifest"]:
                disagreements.append({**row, "pair": "label_files_vs_provenance_manifest"})
            if row["disk_matches_arrow"] is False:
                disagreements.append({**row, "pair": "label_files_vs_arrow_source"})

    totals_rows: list[dict[str, Any]] = []
    for split in SPLITS:
        stats = per_split[split]["statistics"]
        disk_total = int(stats["objects"])
        manifest_split_rows = [row for row in provenance if manifest_row_split(row) == split]
        manifest_total = 0
        for row in manifest_split_rows:
            manifest_total += len(manifest_row_classes(row))
        arrow_split = arrow.get("per_split", {}).get(split, {})
        arrow_total = int(arrow_split.get("objects", 0)) if arrow_split else None
        entry = {
            "split": split,
            "label_files_on_disk_images": stats["images"],
            "label_files_on_disk_objects": disk_total,
            "manifest_rows": len(manifest_split_rows),
            "manifest_objects": manifest_total,
            "arrow_source_images": arrow_split.get("images") if arrow_split else None,
            "arrow_source_objects": arrow_total,
        }
        entry["objects_agree"] = (
            manifest_total == disk_total and (arrow_total is None or arrow_total == disk_total)
        )
        entry["images_agree"] = (
            len(manifest_split_rows) == stats["images"]
            and (arrow_split.get("images") in (None, stats["images"]))
        )
        totals_rows.append(entry)
        if not entry["objects_agree"]:
            disagreements.append({**entry, "pair": "totals_label_files_vs_other_sources"})
        if not entry["images_agree"]:
            disagreements.append({**entry, "pair": "image_totals_label_files_vs_other_sources"})

    return {
        "sources": {
            "label_files_on_disk": "experiments/dataset/experiment2/labels/{train,val}/*.txt",
            "provenance_manifest": rel(os.path.join(DEFAULT_EXP2_ROOT, PROVENANCE_MANIFEST)),
            "arrow_source": arrow.get("arrow_root"),
        },
        "arrow_status": arrow.get("status"),
        "manifest_total_rows": manifest_images,
        "manifest_negative_images": manifest_negatives,
        "per_class_table": rows,
        "per_split_totals": totals_rows,
        "all_sources_agree": not disagreements,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements[:MAX_DETAIL],
        "note": (
            "The provenance manifest and the Arrow store describe the whole "
            "non-India conversion; the Experiment 2 val split is a subset of that "
            "conversion, so a per-split disagreement on val is expected whenever the "
            "Arrow/manifest totals include the images that later moved to val. The "
            "grand-total rows are the ones that must agree."
        ),
    }


def manifest_row_split(row: dict[str, str]) -> str:
    """Return ``'train'`` / ``'val'`` for a manifest row, or ``''``.

    ``output_image_path`` is recorded repo-relative with forward slashes, e.g.
    ``experiments/dataset/experiment2/images/train/Norway_000001.jpg``.
    """
    path = str(row.get("output_image_path", "")).replace("\\", "/")
    for split in SPLITS:
        if f"/images/{split}/" in path or path.endswith(f"/images/{split}"):
            return split
    return ""


def manifest_row_classes(row: dict[str, str]) -> list[int]:
    """Return the YOLO class ids recorded in one provenance manifest row.

    ``convert_arrow_to_yolo.py`` writes ``mapped_class`` as a semicolon-joined
    list of YOLO class ids and ``original_class`` as a semicolon-joined list of
    RDD2022 damage codes (``D00``/``D10``/``D20``/``D40``). ``mapped_class`` is
    preferred; ``original_class`` is mapped through :data:`TAXONOMY` as a
    fallback so the reconciliation survives a manifest variant.
    """
    raw = str(row.get("mapped_class", "")).strip()
    codes: list[int] = []
    if raw:
        for token in raw.replace(";", " ").split():
            try:
                codes.append(int(float(token)))
            except ValueError:
                continue
        if codes:
            return codes
    for token in str(row.get("original_class", "")).replace(";", " ").split():
        code = TAXONOMY.get(token.strip().upper())
        if code is not None:
            codes.append(code)
    return codes


# ---------------------------------------------------------------------------
# markdown report
# ---------------------------------------------------------------------------
def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    """Render a simple GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join("" if cell is None else str(cell) for cell in row) + " |")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable conversion report from the JSON payload."""
    summary = report["summary"]
    per_split = report["splits"]
    reconciliation = report["reconciliation"]

    lines: list[str] = []
    lines.append("# Experiment 2 Conversion Validation (Phase 11)")
    lines.append("")
    lines.append(f"**Generated by**: `{report['generated_by']}`")
    lines.append(f"**Generated (UTC)**: {report['generated_utc']}")
    lines.append("")
    lines.append(f"**Result**: {'**PASS**' if summary['all_hard_checks_passed'] else '**FAIL**'}")
    lines.append("")

    lines.append("## Inputs")
    lines.append("")
    lines.extend(
        _md_table(
            ["Item", "Value"],
            [
                ["Experiment 2 root", f"`{report['inputs']['exp2_root']}`"],
                ["Provenance manifest rows", report["inputs"]["manifest_rows"]],
                ["Arrow source", f"`{report['inputs']['arrow_root']}`"],
                ["Arrow status", f"`{report['inputs']['arrow_status']}`"],
                ["Duration (s)", report["duration_seconds"]],
            ],
        )
    )
    lines.append("")

    lines.append("## Summary checks")
    lines.append("")
    lines.extend(
        _md_table(
            ["Check", "Result"],
            [[key, "PASS" if value else "FAIL"] for key, value in sorted(summary.items())],
        )
    )
    lines.append("")

    lines.append("## Per-split totals")
    lines.append("")
    rows: list[list[Any]] = []
    for split in SPLITS:
        detail = per_split[split]
        stats = detail["statistics"]
        rows.append(
            [
                split,
                stats["images"],
                detail["images_without_label_count"],
                detail["labels_without_image_count"],
                stats["objects"],
                detail["empty_label_files_count"],
                detail["invalid_row_count"],
                detail["dimension_mismatch_count"],
                detail["n_objects_mismatch_count"],
            ]
        )
    lines.extend(
        _md_table(
            [
                "Split",
                "Images",
                "Img w/o label",
                "Label w/o img",
                "Objects",
                "Empty labels",
                "Invalid rows",
                "Dim mismatch",
                "n_objects mismatch",
            ],
            rows,
        )
    )
    lines.append("")

    lines.append("## Objects and images per class")
    lines.append("")
    class_rows: list[list[Any]] = []
    for split in SPLITS:
        stats = per_split[split]["statistics"]
        for class_name in (CLASS_NAMES[c] for c in sorted(CLASS_NAMES)):
            class_rows.append(
                [
                    split,
                    class_name,
                    stats["images_per_class"].get(class_name, 0),
                    stats["objects_per_class"].get(class_name, 0),
                ]
            )
    lines.extend(_md_table(["Split", "Class", "Images with class", "Objects"], class_rows))
    lines.append("")

    lines.append("## Negatives")
    lines.append("")
    lines.extend(
        _md_table(
            ["Split", "Images", "Negatives", "Negative %"],
            [
                [
                    split,
                    per_split[split]["statistics"]["images"],
                    per_split[split]["statistics"]["negative_images"],
                    per_split[split]["statistics"]["negative_percentage"],
                ]
                for split in SPLITS
            ],
        )
    )
    lines.append("")
    lines.append(
        "An empty `.txt` label file is the correct and valid encoding of a negative "
        "image in YOLO format; it is present-and-valid, not a defect."
    )
    lines.append("")

    lines.append("## Per-country statistics")
    lines.append("")
    for split in SPLITS:
        per_country = per_split[split]["statistics"]["per_country"]
        lines.append(f"### {split}")
        lines.append("")
        country_rows: list[list[Any]] = []
        for country in sorted(per_country):
            entry = per_country[country]
            country_rows.append(
                [
                    country,
                    entry["images"],
                    entry["objects"],
                    entry["negative_images"],
                    entry["negative_percentage"],
                ]
            )
        lines.extend(
            _md_table(
                ["Country", "Images", "Objects", "Negatives", "Negative %"], country_rows
            )
        )
        lines.append("")

    lines.append("## Three-source reconciliation")
    lines.append("")
    lines.append(
        "Sources: (1) label files on disk, (2) `provenance_manifest.csv`, "
        "(3) the Arrow store totals."
    )
    lines.append("")
    lines.append("### Per split, per class (objects)")
    lines.append("")
    lines.extend(
        _md_table(
            [
                "Split",
                "Class",
                "Label files",
                "Manifest",
                "Arrow",
                "disk=manifest",
                "disk=arrow",
            ],
            [
                [
                    row["split"],
                    row["class_name"],
                    row["label_files_on_disk"],
                    row["provenance_manifest"],
                    row["arrow_source"] if row["arrow_source"] is not None else "n/a",
                    "yes" if row["disk_matches_manifest"] else "**NO**",
                    "n/a"
                    if row["disk_matches_arrow"] is None
                    else ("yes" if row["disk_matches_arrow"] else "**NO**"),
                ]
                for row in reconciliation["per_class_table"]
            ],
        )
    )
    lines.append("")
    lines.append("### Per split totals")
    lines.append("")
    lines.extend(
        _md_table(
            [
                "Split",
                "Disk images",
                "Disk objects",
                "Manifest rows",
                "Manifest objects",
                "Arrow images",
                "Arrow objects",
                "Objects agree",
                "Images agree",
            ],
            [
                [
                    row["split"],
                    row["label_files_on_disk_images"],
                    row["label_files_on_disk_objects"],
                    row["manifest_rows"],
                    row["manifest_objects"],
                    row["arrow_source_images"] if row["arrow_source_images"] is not None else "n/a",
                    row["arrow_source_objects"] if row["arrow_source_objects"] is not None else "n/a",
                    "yes" if row["objects_agree"] else "**NO**",
                    "yes" if row["images_agree"] else "**NO**",
                ]
                for row in reconciliation["per_split_totals"]
            ],
        )
    )
    lines.append("")
    lines.append(f"> {reconciliation['note']}")
    lines.append("")
    if reconciliation["disagreements"]:
        lines.append("### Disagreements")
        lines.append("")
        for item in reconciliation["disagreements"][:100]:
            lines.append(f"- `{item.get('pair')}` {json.dumps(item, sort_keys=True)}")
    else:
        lines.append("All reconciled sources agree.")
    lines.append("")

    lines.append("## Detail")
    lines.append("")
    for split in SPLITS:
        detail = per_split[split]
        lines.append(f"### {split}")
        lines.append("")
        if detail["images_without_label_count"]:
            lines.append(
                f"- **{detail['images_without_label_count']}** image(s) with no label file"
            )
        if detail["labels_without_image_count"]:
            lines.append(
                f"- **{detail['labels_without_image_count']}** label file(s) with no image"
            )
        if detail["unreadable_images_count"]:
            lines.append(f"- **{detail['unreadable_images_count']}** unreadable image(s)")
        if detail["unreadable_labels_count"]:
            lines.append(f"- **{detail['unreadable_labels_count']}** unreadable label file(s)")
        if detail["invalid_row_count"]:
            lines.append(f"- **{detail['invalid_row_count']}** invalid label row(s)")
        if detail["degenerate_box_count"]:
            lines.append(f"- **{detail['degenerate_box_count']}** zero/negative-area box row(s)")
        if detail["dimension_mismatch_count"]:
            lines.append(
                f"- **{detail['dimension_mismatch_count']}** image dimension mismatch(es) "
                "vs `provenance_manifest.csv`"
            )
        if detail["n_objects_mismatch_count"]:
            lines.append(
                f"- **{detail['n_objects_mismatch_count']}** n_objects mismatch(es) vs "
                "`provenance_manifest.csv`"
            )
        if not detail["hard_failures"]:
            lines.append("- no problems detected")
        lines.append("")

    lines.append("## Reproduce")
    lines.append("")
    lines.append("```")
    lines.append("python scripts/experiment2/validate_yolo.py --workers 32")
    lines.append("```")
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Return the fully configured argument parser."""
    parser = argparse.ArgumentParser(
        description="Phase 11 Experiment 2 YOLO conversion validation. Read-only."
    )
    parser.add_argument("--exp2-root", type=str, default=DEFAULT_EXP2_ROOT, help="Experiment 2 dataset root (read-only).")
    parser.add_argument(
        "--arrow-root",
        type=str,
        default=DEFAULT_ARROW_ROOT,
        help="HuggingFace Arrow store used as reconciliation source 3 (read-only).",
    )
    parser.add_argument("--out-dir", type=str, default=DEFAULT_OUT_DIR, help="Directory for the two report files.")
    parser.add_argument(
        "--workers", type=int, default=16, help="Thread-pool size for PIL dimension reads (I/O bound)."
    )
    parser.add_argument(
        "--no-arrow",
        action="store_true",
        help="Skip the Arrow reconciliation source entirely.",
    )
    parser.add_argument(
        "--strict-reconciliation",
        action="store_true",
        help="Treat any three-source disagreement as a hard failure (exit non-zero).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform all checks but write nothing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the conversion validation and write both reports. Returns the exit code."""
    args = build_parser().parse_args(argv)

    exp2_root = os.path.abspath(os.fspath(args.exp2_root))
    arrow_root = os.path.abspath(os.fspath(args.arrow_root))
    out_dir = os.path.abspath(os.fspath(args.out_dir))
    workers = max(1, int(args.workers))

    print("=" * 72, flush=True)
    print("Experiment 2 Conversion Validation (Phase 11)", flush=True)
    print(f"Experiment 2 root : {exp2_root}", flush=True)
    print(f"Arrow source root : {arrow_root}", flush=True)
    print(f"Output directory  : {out_dir}", flush=True)
    print(f"Workers           : {workers}", flush=True)
    print(f"Dry run           : {args.dry_run}", flush=True)
    print("=" * 72, flush=True)

    if not os.path.isdir(exp2_root):
        print(f"FATAL: Experiment 2 root not found: {exp2_root}", flush=True)
        return 2

    started = time.time()
    manifest_path = os.path.join(exp2_root, PROVENANCE_MANIFEST)
    provenance = read_provenance(manifest_path)
    print(f"Provenance manifest rows: {len(provenance)}", flush=True)

    per_split: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        per_split[split] = scan_split(exp2_root, split, workers, provenance)

    arrow = {"arrow_root": rel(arrow_root), "status": "skipped_by_flag", "available": False, "per_split": {}}
    if not args.no_arrow:
        print("Reading Arrow source totals...", flush=True)
        arrow = arrow_totals(arrow_root)
        print(f"  Arrow status: {arrow['status']}", flush=True)

    reconciliation = reconcile(per_split, provenance, arrow)
    if arrow["status"] == "skipped_by_flag":
        reconciliation["note"] = (
            "Arrow reconciliation skipped via --no-arrow; only the label files and "
            "the provenance manifest were compared."
        )

    hard_failures: list[str] = []
    for split in SPLITS:
        hard_failures.extend(per_split[split]["hard_failures"])
    if args.strict_reconciliation and not reconciliation["all_sources_agree"]:
        hard_failures.append("reconciliation:three_sources_disagree")

    orphan_total = sum(
        per_split[s]["images_without_label_count"] + per_split[s]["labels_without_image_count"]
        for s in SPLITS
    )
    invalid_row_total = sum(per_split[s]["invalid_row_count"] for s in SPLITS)

    summary = {
        "every_image_has_a_label": all(
            per_split[s]["images_without_label_count"] == 0 for s in SPLITS
        ),
        "every_label_has_an_image": all(
            per_split[s]["labels_without_image_count"] == 0 for s in SPLITS
        ),
        "no_unreadable_images": all(
            per_split[s]["unreadable_images_count"] == 0 for s in SPLITS
        ),
        "no_unreadable_labels": all(
            per_split[s]["unreadable_labels_count"] == 0 for s in SPLITS
        ),
        "all_label_rows_valid": invalid_row_total == 0,
        "no_zero_or_negative_area_boxes": all(
            per_split[s]["degenerate_box_count"] == 0 for s in SPLITS
        ),
        "image_dimensions_match_manifest": all(
            per_split[s]["dimension_mismatch_count"] == 0 for s in SPLITS
        ),
        "manifest_n_objects_agree_with_labels": all(
            per_split[s]["n_objects_mismatch_count"] == 0 for s in SPLITS
        ),
        "three_sources_reconcile": reconciliation["all_sources_agree"],
        "no_hard_failures": not hard_failures,
        "all_hard_checks_passed": not hard_failures,
    }

    report: dict[str, Any] = {
        "report_version": "1.0.0",
        "generated_by": "scripts/experiment2/validate_yolo.py",
        "phase": "Phase 11 - conversion validation",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.time() - started, 2),
        "inputs": {
            "exp2_root": rel(exp2_root),
            "manifest_path": rel(manifest_path),
            "manifest_rows": len(provenance),
            "arrow_root": rel(arrow_root),
            "arrow_status": arrow["status"],
            "splits": list(SPLITS),
        },
        "taxonomy": {str(k): v for k, v in CLASS_NAMES.items()},
        "valid_row_rule": {
            "tokens": 5,
            "class_id_allowed": sorted(CLASS_NAMES),
            "centre_range": [0.0, 1.0],
            "size_range": "(0, 1]",
            "corners": "all four corners inside [0, 1] within 1e-9 tolerance",
        },
        "summary": summary,
        "hard_failures": hard_failures,
        "splits": per_split,
        "reconciliation": reconciliation,
        "arrow_source_totals": arrow,
        "totals": {
            "images": sum(per_split[s]["statistics"]["images"] for s in SPLITS),
            "label_files": sum(
                per_split[s]["statistics"]["label_files"] for s in SPLITS
            ),
            "objects": sum(per_split[s]["statistics"]["objects"] for s in SPLITS),
            "empty_label_files": sum(per_split[s]["empty_label_files_count"] for s in SPLITS),
            "orphan_pairs": orphan_total,
            "invalid_rows": invalid_row_total,
        },
        "read_only_guarantee": (
            "This script only reads images, labels and manifests and writes its two "
            "report files. It never edits, deletes or moves any dataset artifact."
        ),
    }

    json_path = os.path.join(out_dir, JSON_NAME)
    md_path = os.path.join(out_dir, MD_NAME)
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        write_json_atomic(json_path, report)
        write_text_atomic(md_path, render_markdown(report))
    else:
        # Every scan, count and reconciliation above already ran; only the two
        # report files (and the output directory itself) are suppressed.
        print(f"[DRY-RUN] Would write {len(report.keys())} entries to {json_path}", flush=True)
        print(f"[DRY-RUN] Would write 1 entries to {md_path}", flush=True)

    print("-" * 72, flush=True)
    for split in SPLITS:
        detail = per_split[split]
        stats = detail["statistics"]
        print(
            f"{split:<6} images={stats['images']:<7} objects={stats['objects']:<8} "
            f"negatives={stats['negative_images']:<7} "
            f"({stats['negative_percentage']:.2f}%)  "
            f"invalid_rows={detail['invalid_row_count']}  "
            f"orphans={detail['images_without_label_count']}+{detail['labels_without_image_count']}",
            flush=True,
        )
    print("-" * 72, flush=True)
    print("Per class (objects):", flush=True)
    for split in SPLITS:
        objects_per_class = per_split[split]["statistics"]["objects_per_class"]
        print(
            f"  {split:<6} "
            + "  ".join(f"{name}={count}" for name, count in sorted(objects_per_class.items())),
            flush=True,
        )
    print("-" * 72, flush=True)
    print(f"Reconciliation: {'AGREE' if reconciliation['all_sources_agree'] else 'DISAGREE'} "
          f"({reconciliation['disagreement_count']} disagreement(s))", flush=True)
    if args.dry_run:
        print("[DRY-RUN] all scans, counts and reconciliation checks completed; "
              "no files were written.", flush=True)
    else:
        print(f"Wrote JSON report: {json_path}", flush=True)
        print(f"Wrote MD report  : {md_path}", flush=True)

    if hard_failures:
        print("", flush=True)
        print("CONVERSION VALIDATION FAILED:", flush=True)
        for failure in hard_failures:
            print(f"  - {failure}", flush=True)
        return 1

    print("", flush=True)
    print("CONVERSION VALIDATION PASSED: no hard-check failures.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())