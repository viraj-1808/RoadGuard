#!/usr/bin/env python
"""Build the Experiment 2 train/val split and emit ``data.yaml``.

Composition (this is the Experiment 2 data ablation):

* **TRAIN** = Dataset A ``train`` ONLY (1,071 frozen India images, copied
  read-only) **PLUS** the non-India Dataset B ``train`` pool.
  Dataset A ``val`` and Dataset A ``test`` are EXCLUDED; the script hard-fails
  if any of their filenames reach the train pool.
* **VAL** = a deterministic hold-out carved ONLY out of the non-India Dataset B
  train pool, using ``--seed`` (default 42) and stratified by country so each of
  the 5 non-India countries is represented proportionally. Stratification is
  applied jointly on ``(country, is_negative)``, which preserves the
  negative-image ratio inside every country instead of only overall.
* **TEST** is NOT created. The frozen 230-image India test set stays in place and
  is referenced from ``data.yaml`` as an external path.

After the split, the chosen val files are moved from ``images/train`` to
``images/val`` (copied and committed with ``os.replace``, then removed from
train). The move is fully idempotent and self-healing: a re-run reconciles the
filesystem to the selected split even after an interrupted previous run.

Invariants, each a hard failure with a non-zero exit:

* no filename appears in both train and val;
* no image sha256 appears in both train and val;
* no Dataset A val/test filename enters the train pool.

Writes (in this order, and only after every invariant has passed):

* ``<exp2-root>/split_manifest.json`` -- counts, seed, algorithm, self sha256.
* ``<out-dir>/val_holdout_manifest.json`` -- the exact val image list + sha256.
* ``<exp2-root>/data.yaml`` -- LAST.

Reproducibility:
    The val selection is order-independent by construction. Every candidate
    collection is sorted with an explicit, total key before sampling, and the
    per-stratum RNG is seeded from a SHA-256 derived *integer*, not from a
    string. ``--verify-determinism`` proves both properties on the real pool and
    exits non-zero if either fails.

Usage:
    python build_splits.py
    python build_splits.py --dry-run
    python build_splits.py --val-frac 0.11 --seed 42
    python build_splits.py --verify-determinism
"""
import argparse
import csv
import glob
import hashlib
import json
import math
import os
import random
import shutil
import sys
from collections import Counter
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_DATASET_A = os.path.join(REPO_ROOT, "experiments", "dataset", "yolo_rdd2022_india")
DEFAULT_EXP2_ROOT = os.path.join(REPO_ROOT, "experiments", "dataset", "experiment2")
DEFAULT_OUT_DIR = os.path.join(
    REPO_ROOT, "experiments", "analysis", "overnight", "experiment2_dataset_b"
)

#: Frozen external test set, written verbatim into ``data.yaml``.
FROZEN_TEST_PATH = "experiments/dataset/yolo_rdd2022_india/images/test"
DATA_YAML_PATH = "experiments/dataset/experiment2"
TRAIN_YAML_KEY = "images/train"
VAL_YAML_KEY = "images/val"

PROVENANCE_MANIFEST = "provenance_manifest.csv"
SPLIT_MANIFEST_NAME = "split_manifest.json"
DATA_YAML_NAME = "data.yaml"
VAL_HOLDOUT_NAME = "val_holdout_manifest.json"

#: Locked taxonomy, identical to the Experiment 1 baseline.
CLASS_NAMES: dict[int, str] = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",
}

#: Dataset A is India-only; it is reported under this country key.
DATASET_A_COUNTRY = "India"

#: Dataset A split sizes, used as a read-only sanity assertion when non-zero.
EXPECTED_DATASET_A_TRAIN = 1071
EXPECTED_DATASET_A_VAL = 229
EXPECTED_DATASET_A_TEST = 230

ALGORITHM_DESCRIPTION = (
    "Deterministic country-stratified hold-out. The Dataset B non-India train pool is "
    "partitioned into strata keyed by (country, is_negative). A val budget of "
    "round(val_frac * len(pool)) is distributed across strata proportionally to "
    "stratum size using the largest-remainder method (ties broken by stratum key). "
    "Within each stratum the members are sorted by (country, file_name) and sampled "
    "without replacement with random.Random(derive_stratum_seed(seed, country, "
    "is_negative)). The per-stratum seed is derived from the global seed and the "
    "stratum identity, so the selection is independent of stratum iteration order. "
    "The seed is an integer derived from "
    "int(sha256(f'{seed}|{country}|{int(is_negative)}').hexdigest()[:16], 16) because "
    "seeding random.Random from a str/bytes is an implementation detail of CPython "
    "and is not part of its documented compatibility contract, whereas an explicit "
    "integer seed is. Every candidate list is sorted by an explicit total key before "
    "sampling, so the selection does not depend on the order in which the filesystem "
    "enumeration happened to return the files; the same seed therefore reproduces the "
    "same hold-out on any machine, any filesystem, and any rerun. "
    "Stratifying jointly on (country, is_negative) guarantees that both the country mix "
    "and the negative-image ratio of the pool are preserved in the hold-out."
)

#: Deterministic total ordering key for a pool member. Used to make every
#: candidate collection order-independent before sampling.
def pool_order_key(item: dict[str, Any]) -> tuple[str, int, str]:
    """Return the total, locale-independent sort key of one pool member."""
    return (
        str(item["country"]).lower(),
        1 if item["is_negative"] else 0,
        str(item["stem"]).lower(),
    )

#: Fixed seed for the adversarial shuffle used by ``--verify-determinism``. It is a
#: constant so that the verification itself is reproducible.
DETERMINISM_PROBE_SEED = 0x5D57



def sha256_file(path: str) -> str:
    """Return the hex sha256 digest of the file at *path*."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_atomic(path: str, text: str) -> None:
    """Write *text* to *path* via a ``.part`` staging file and ``os.replace``."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    part_path = path + ".part"
    with open(part_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(part_path, path)


def write_json_atomic(path: str, payload: Any) -> str:
    """Write *payload* as pretty JSON atomically. Returns the text written."""
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    write_text_atomic(path, text)
    return text


def copy_file_atomic(src: str, dst: str) -> None:
    """Copy *src* to *dst* via a ``.part`` staging file and ``os.replace``."""
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    part_path = dst + ".part"
    shutil.copyfile(src, part_path)
    os.replace(part_path, dst)


def list_images(directory: str) -> dict[str, str]:
    """Map ``stem -> absolute path`` for every image under *directory* (recursive).

    The filesystem enumeration is sorted explicitly (``glob``/``rglob``/``iterdir``
    return entries in whatever order the filesystem hands back, which differs
    between machines, drives and even between runs on some network filesystems).
    Callers that sample from the result therefore get a stable, reproducible
    ordering rather than an incidental one.
    """
    found: dict[str, str] = {}
    if not os.path.isdir(directory):
        return found
    candidates = sorted(
        glob.glob(os.path.join(directory, "**", "*"), recursive=True),
        key=lambda p: str(p).lower(),
    )
    for path in candidates:
        if not os.path.isfile(path):
            continue
        if os.path.splitext(path)[1].lower() not in (".jpg", ".jpeg", ".png", ".bmp"):
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem in found:
            raise ValueError(f"duplicate image stem {stem!r} under {directory}: {found[stem]} and {path}")
        found[stem] = path
    return {stem: found[stem] for stem in sorted(found, key=lambda s: s.lower())}



def read_label_classes(label_path: str) -> list[int]:
    """Return the class ids in a YOLO label file (``[]`` for a negative)."""
    if not os.path.isfile(label_path):
        return []
    classes: list[int] = []
    with open(label_path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != 5:
                continue
            try:
                classes.append(int(float(parts[0])))
            except ValueError:
                continue
    return classes


def read_provenance(path: str) -> list[dict[str, str]]:
    """Read ``provenance_manifest.csv`` written by ``convert_arrow_to_yolo.py``."""
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"provenance manifest not found: {path}\n"
            "Run scripts/experiment2/convert_arrow_to_yolo.py first."
        )
    rows: list[dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("source_image_id"):
                rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return rows


def allocate_largest_remainder(sizes: dict[Any, int], total: int) -> dict[Any, int]:
    """Distribute *total* across strata proportionally to their sizes.

    Uses the largest-remainder (Hare-Niemeyer) method with deterministic
    tie-breaking on the stratum key, and never allocates more than a stratum
    holds.
    """
    if not sizes:
        return {}
    total = max(0, min(total, sum(sizes.values())))
    if total == 0:
        return {key: 0 for key in sizes}

    quotas = {key: (total * size) / sum(sizes.values()) for key, size in sizes.items()}
    base = {key: int(math.floor(quota)) for key, quota in quotas.items()}
    for key in base:
        base[key] = min(base[key], sizes[key])

    order = sorted(sizes, key=lambda key: (-(quotas[key] - math.floor(quotas[key])), str(key)))
    assigned = sum(base.values())
    index = 0
    while assigned < total and index < len(order) * 4:
        key = order[index % len(order)]
        if base[key] < sizes[key]:
            base[key] += 1
            assigned += 1
        index += 1
    return base


def derive_stratum_seed(seed: int, country: str, is_negative: Any) -> int:
    """Return the deterministic integer seed for one ``(country, is_negative)`` stratum.

    ``random.Random`` accepts ``str``/``bytes`` seeds, but that conversion is an
    implementation detail of CPython (it hashes the object with a version-tagged
    algorithm) and is explicitly *not* part of the documented compatibility
    contract for the ``random`` module. Relying on it makes the split an implicit
    dependency on interpreter internals. Hashing the stratum identity ourselves
    and feeding ``random`` a plain ``int`` is documented behaviour and therefore
    stable across interpreters, versions and platforms.
    """
    identity = f"{seed}|{country}|{int(is_negative)}"
    return int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16)


def stable_sort_pool(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a new pool list in the canonical, filesystem-order-independent order."""
    return sorted(pool, key=pool_order_key)


def stratified_val_selection(
    pool: list[dict[str, Any]], val_frac: float, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Select the val hold-out from *pool*, stratified by ``(country, is_negative)``.

    The selection is deliberately independent of the order in which *pool* (or any
    directory it was discovered from) is ordered: the pool and every stratum are
    re-sorted here with an explicit total key before any sampling happens, and each
    stratum draws from its own integer-seeded RNG.

    Returns ``(selected, selection_stats)``.
    """
    ordered_pool = stable_sort_pool(pool)

    strata: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for item in ordered_pool:
        key = (item["country"], 1 if item["is_negative"] else 0)
        strata.setdefault(key, []).append(item)
    for key in strata:
        # Defensive: the pool is already canonical-ordered, so this only guarantees
        # the property locally even if a caller mutates ``ordered_pool`` in future.
        strata[key] = sorted(strata[key], key=pool_order_key)

    total = int(round(val_frac * len(ordered_pool)))
    if total > 0 and len(ordered_pool) > 0:
        total = max(1, min(total, len(ordered_pool)))

    sizes = {key: len(members) for key, members in strata.items()}
    quota = allocate_largest_remainder(sizes, total)

    selected: list[dict[str, Any]] = []
    stratum_stats: dict[str, Any] = {}
    for key in sorted(strata, key=lambda k: (k[0], k[1])):
        country, is_negative = key
        members = strata[key]
        k = quota[key]
        rng = random.Random(derive_stratum_seed(seed, country, is_negative))
        picked = rng.sample(members, k) if k > 0 else []
        selected.extend(picked)
        stratum_stats[f"{country}|{'negative' if is_negative else 'positive'}"] = {
            "pool": len(members),
            "selected": k,
            "frac": (k / len(members)) if members else 0.0,
        }

    selected.sort(key=pool_order_key)
    stats = {
        "requested_total": total,
        "strata": stratum_stats,
        "pool_negatives": sum(1 for item in ordered_pool if item["is_negative"]),
        "selected_negatives": sum(1 for item in selected if item["is_negative"]),
    }
    return selected, stats


def selection_fingerprint(selected: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    """Return a canonical byte string identifying one selection and its allocation."""
    return json.dumps(
        {
            "stems": sorted(str(item["stem"]) for item in selected),
            "requested_total": stats["requested_total"],
            "strata": {key: stats["strata"][key] for key in sorted(stats["strata"])},
            "selected_negatives": stats["selected_negatives"],
        },
        sort_keys=True,
        ensure_ascii=False,
    )


def verify_determinism(pool: list[dict[str, Any]], val_frac: float, seed: int) -> list[str]:
    """Return a list of determinism failures; empty means the selection is deterministic.

    Two properties are checked, both of which used to be broken:

    1. **Repeatability** -- the selection is computed twice in-process from the same
       input and the two results must be byte-identical.
    2. **Order independence** -- the selection is recomputed from a deliberately
       shuffled copy of the pool (simulating a filesystem enumeration that returns
       entries in a different order) and must produce the identical result.
    """
    failures: list[str] = []

    first, first_stats = stratified_val_selection(pool, val_frac, seed)
    fingerprint_a = selection_fingerprint(first, first_stats)

    second, second_stats = stratified_val_selection(pool, val_frac, seed)
    fingerprint_b = selection_fingerprint(second, second_stats)
    if fingerprint_a != fingerprint_b:
        failures.append(
            "repeatability: two in-process selections with the same seed differ "
            f"({len(first)} vs {len(second)} images)"
        )

    shuffled = list(pool)
    random.Random(DETERMINISM_PROBE_SEED).shuffle(shuffled)
    if [item["stem"] for item in shuffled] == [item["stem"] for item in pool]:
        shuffled = list(reversed(shuffled))
    third, third_stats = stratified_val_selection(shuffled, val_frac, seed)
    fingerprint_c = selection_fingerprint(third, third_stats)
    if fingerprint_a != fingerprint_c:
        only_a = sorted({str(i["stem"]) for i in first} - {str(i["stem"]) for i in third})
        only_c = sorted({str(i["stem"]) for i in third} - {str(i["stem"]) for i in first})
        failures.append(
            "order_independence: selection differs when the input pool is presented in a "
            f"different order; only_in_baseline={only_a[:5]} only_in_shuffled={only_c[:5]}"
        )

    return failures



def discover_pool(exp2_root: str, provenance_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Build the Dataset B train pool from the provenance manifest.

    Each item records the stem, its country, its current on-disk location
    (``train`` or ``val`` -- a previous run may already have moved it), the
    label-derived class set, and whether the image is a negative.
    """
    images_dirs = {split: os.path.join(exp2_root, "images", split) for split in ("train", "val")}
    labels_dirs = {split: os.path.join(exp2_root, "labels", split) for split in ("train", "val")}

    pool: list[dict[str, Any]] = []
    for row in provenance_rows:
        if row.get("source_split") != "train":
            continue
        stem = os.path.splitext(os.path.basename(row["source_image_id"]))[0]
        extension = os.path.splitext(row.get("output_image_path", ""))[1] or ".jpg"

        location = ""
        image_path = ""
        for split in ("train", "val"):
            candidate = os.path.join(images_dirs[split], stem + extension)
            if os.path.isfile(candidate):
                location = split
                image_path = candidate
                break
        if not location:
            raise FileNotFoundError(
                f"Dataset B pool image missing from both train and val: {stem}{extension}"
            )

        label_path = os.path.join(labels_dirs[location], stem + ".txt")
        if not os.path.isfile(label_path):
            # An interrupted previous run can leave an image and its label in
            # different pools. A negative is an existing but EMPTY label file --
            # an absent label is an integrity error, never a negative.
            for other in ("train", "val"):
                candidate = os.path.join(labels_dirs[other], stem + ".txt")
                if other != location and os.path.isfile(candidate):
                    print(
                        f"WARNING: label for {stem} was in labels/{other} while its image is in "
                        f"images/{location}; the run will reconcile it.",
                        flush=True,
                    )
                    label_path = candidate
                    break
            else:
                raise FileNotFoundError(
                    f"label file missing for pool image {stem}{extension} in both "
                    "labels/train and labels/val; refusing to treat it as a negative. "
                    "Re-run convert_arrow_to_yolo.py."
                )
        classes = read_label_classes(label_path)
        pool.append(
            {
                "stem": stem,
                "extension": extension,
                "country": row.get("source_country") or "Unknown",
                "location": location,
                "image_path": image_path,
                "label_path": label_path,
                "classes": sorted(set(classes)),
                "n_objects": len(classes),
                "is_negative": len(classes) == 0,
                "sha256": sha256_file(image_path),
            }
        )
    pool.sort(key=pool_order_key)
    return pool


def sync_pool_pair(
    exp2_root: str, stem: str, extension: str, desired: str, dry_run: bool
) -> list[str]:
    """Reconcile one pool image + its label into the *desired* split directory.

    Self-healing and idempotent: it removes a stale copy from the other pool,
    and copies-then-commits-then-removes when the file is currently in the other
    pool. This is what makes an interrupted previous run recoverable.

    Returns a list of action strings; any ``MISSING:`` action is a hard failure.
    """
    other = "val" if desired == "train" else "train"
    images_dirs = {s: os.path.join(exp2_root, "images", s) for s in ("train", "val")}
    labels_dirs = {s: os.path.join(exp2_root, "labels", s) for s in ("train", "val")}

    actions: list[str] = []
    for name, dirs in ((stem + extension, images_dirs), (stem + ".txt", labels_dirs)):
        in_desired = os.path.isfile(os.path.join(dirs[desired], name))
        in_other = os.path.isfile(os.path.join(dirs[other], name))
        if in_desired and in_other:
            if not dry_run:
                os.remove(os.path.join(dirs[other], name))
            actions.append(f"dedup:{name}:{other}->{desired}")
        elif in_desired:
            actions.append(f"ok:{name}:{desired}")
        elif in_other:
            if not dry_run:
                copy_file_atomic(os.path.join(dirs[other], name), os.path.join(dirs[desired], name))
                os.remove(os.path.join(dirs[other], name))
            actions.append(f"move:{name}:{other}->{desired}")
        else:
            actions.append(f"MISSING:{name}")
    return actions


def copy_dataset_a_train(dataset_a: str, exp2_root: str, dry_run: bool) -> dict[str, Any]:
    """Copy the Dataset A train images + labels into the Experiment 2 train pool.

    Dataset A is treated as strictly read-only. A name collision with a Dataset B
    image is a hard failure unless the sha256 matches exactly.
    """
    images_dir = os.path.join(exp2_root, "images", "train")
    labels_dir = os.path.join(exp2_root, "labels", "train")

    source_images = list_images(os.path.join(dataset_a, "images", "train"))
    copied = 0
    already = 0
    objects = 0
    negatives = 0
    sha_by_stem: dict[str, str] = {}
    classes_by_stem: dict[str, list[int]] = {}

    for stem in sorted(source_images, key=lambda s: s.lower()):
        src_image = source_images[stem]
        extension = os.path.splitext(src_image)[1]
        src_label = os.path.join(dataset_a, "labels", "train", stem + ".txt")
        dst_image = os.path.join(images_dir, stem + extension)
        dst_label = os.path.join(labels_dir, stem + ".txt")

        digest = sha256_file(src_image)
        sha_by_stem[stem] = digest
        classes = read_label_classes(src_label)
        classes_by_stem[stem] = classes
        objects += len(classes)
        if not classes:
            negatives += 1

        if os.path.isfile(dst_image):
            if sha256_file(dst_image) != digest:
                raise ValueError(
                    f"Dataset A/B name collision with differing content in the train pool: {stem}"
                )
            already += 1
        else:
            if not dry_run:
                copy_file_atomic(src_image, dst_image)
                if os.path.isfile(src_label):
                    copy_file_atomic(src_label, dst_label)
            copied += 1

    return {
        "copied": copied,
        "already_present": already,
        "total": len(source_images),
        "objects": objects,
        "negatives": negatives,
        "sha_by_stem": sha_by_stem,
        "classes_by_stem": classes_by_stem,
    }


def scan_split(exp2_root: str, split: str) -> list[dict[str, Any]]:
    """Read the actual on-disk state of one split: stems, sha256, label classes."""
    items: list[dict[str, Any]] = []
    images_dir = os.path.join(exp2_root, "images", split)
    labels_dir = os.path.join(exp2_root, "labels", split)
    for stem, path in sorted(list_images(images_dir).items()):
        classes = read_label_classes(os.path.join(labels_dir, stem + ".txt"))
        items.append(
            {
                "stem": stem,
                "sha256": sha256_file(path),
                "classes": classes,
                "n_objects": len(classes),
                "is_negative": len(classes) == 0,
            }
        )
    return items


def summarize_split(items: list[dict[str, Any]], country_of_stem: dict[str, str]) -> dict[str, Any]:
    """Aggregate per-split counts: images, objects, class images, negatives, countries."""
    object_counts: Counter[int] = Counter()
    class_image_counts: Counter[int] = Counter()
    per_country: Counter[str] = Counter()
    negatives = 0
    for item in items:
        if item["is_negative"]:
            negatives += 1
        per_country[country_of_stem.get(item["stem"], "Unknown")] += 1
        for class_id in set(item["classes"]):
            class_image_counts[class_id] += 1
        for class_id in item["classes"]:
            object_counts[class_id] += 1
    return {
        "images": len(items),
        "objects": sum(object_counts.values()),
        "negative_images": negatives,
        "objects_per_class": {
            CLASS_NAMES[c]: object_counts.get(c, 0) for c in sorted(CLASS_NAMES)
        },
        "images_per_class": {
            CLASS_NAMES[c]: class_image_counts.get(c, 0) for c in sorted(CLASS_NAMES)
        },
        "per_country": {country: per_country[country] for country in sorted(per_country)},
    }


def render_data_yaml() -> str:
    """Render the Experiment 2 ``data.yaml``.

    ``test`` is the frozen 230-image India test set from Dataset A. It is
    external to ``path`` and resolved from the repository root; Experiment 2
    never creates or modifies a test split.
    """
    lines = [
        "# Experiment 2 dataset configuration (A train + non-India Dataset B).",
        "# `test` is the FROZEN 230-image India test set from Dataset A. It lives",
        "# outside `path` above and is referenced as a repository-root-relative",
        "# path; Experiment 2 does not create or modify a test split.",
        f"path: {DATA_YAML_PATH}",
        f"train: {TRAIN_YAML_KEY}",
        f"val: {VAL_YAML_KEY}",
        f"test: {FROZEN_TEST_PATH}",
        f"nc: {len(CLASS_NAMES)}",
        "names:",
    ]
    lines.extend(f"- {CLASS_NAMES[class_id]}" for class_id in sorted(CLASS_NAMES))
    return "\n".join(lines) + "\n"


def build_split_manifest(
    seed: int,
    val_frac: float,
    train_summary: dict[str, Any],
    val_summary: dict[str, Any],
    dataset_a_summary: dict[str, Any],
    selection_stats: dict[str, Any],
    val_frac_requested: float,
) -> dict[str, Any]:
    """Assemble ``split_manifest.json`` including its own sha256.

    The self hash is computed over the canonical serialisation
    (``json.dumps(..., sort_keys=True, indent=2)``) of the manifest with the
    ``manifest_sha256`` and ``manifest_sha256_note`` keys omitted, so it is
    stable and independently reproducible.
    """
    body: dict[str, Any] = {
        "manifest_version": "1.0.0",
        "generated_by": "scripts/experiment2/build_splits.py",
        "seed": seed,
        "val_frac": val_frac,
        "val_frac_as_requested": val_frac_requested,
        "algorithm": ALGORITHM_DESCRIPTION,
        "test_policy": (
            "No test split is created. The frozen 230-image India test set from Dataset A "
            f"is referenced unchanged at '{FROZEN_TEST_PATH}'."
        ),
        "train_composition": {
            "dataset_a_train_images": dataset_a_summary["total"],
            "dataset_b_train_pool_images": selection_stats.get("pool_size"),
            "dataset_b_images_moved_to_val": val_summary["images"],
            "train_images_total": train_summary["images"],
        },
        "splits": {"train": train_summary, "val": val_summary},
        "val_selection": selection_stats,
    }
    canonical = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False)
    body["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    body["manifest_sha256_note"] = (
        "sha256 of json.dumps(this_manifest, indent=2, sort_keys=True, ensure_ascii=False) "
        "with the 'manifest_sha256' and 'manifest_sha256_note' keys omitted"
    )
    return body


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the Experiment 2 train/val split and emit data.yaml."
    )
    parser.add_argument(
        "--dataset-a", type=str, default=DEFAULT_DATASET_A, help="Frozen Dataset A root (read-only)."
    )
    parser.add_argument(
        "--exp2-root", type=str, default=DEFAULT_EXP2_ROOT, help="Converted Experiment 2 dataset root."
    )
    parser.add_argument(
        "--out-dir", type=str, default=DEFAULT_OUT_DIR, help="Directory for the val hold-out record."
    )
    parser.add_argument(
        "--val-frac", type=float, default=0.11, help="Fraction of the Dataset B train pool to hold out for val."
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed for the deterministic stratified hold-out.")
    parser.add_argument(
        "--expected-a-train",
        type=int,
        default=EXPECTED_DATASET_A_TRAIN,
        help="Asserted Dataset A train size (0 disables the check).",
    )
    parser.add_argument(
        "--expected-a-val",
        type=int,
        default=EXPECTED_DATASET_A_VAL,
        help="Asserted Dataset A val size (0 disables the check).",
    )
    parser.add_argument(
        "--expected-a-test",
        type=int,
        default=EXPECTED_DATASET_A_TEST,
        help="Asserted Dataset A test size (0 disables the check).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute and report without writing anything.")
    parser.add_argument(
        "--verify-determinism",
        action="store_true",
        help=(
            "Assert the val selection is reproducible: run it twice in-process and "
            "assert the results are byte-identical, then re-run it from a deliberately "
            "shuffled pool and assert the selection is unchanged. Exits non-zero on "
            "any mismatch."
        ),
    )
    args = parser.parse_args()

    dataset_a = os.path.abspath(os.fspath(args.dataset_a))
    exp2_root = os.path.abspath(os.fspath(args.exp2_root))
    out_dir = os.path.abspath(os.fspath(args.out_dir))

    print("=" * 72, flush=True)
    print("Experiment 2 Split Builder", flush=True)
    print(f"Dataset A (read-only): {dataset_a}", flush=True)
    print(f"Experiment 2 root   : {exp2_root}", flush=True)
    print(f"Output directory    : {out_dir}", flush=True)
    print(f"val_frac            : {args.val_frac}", flush=True)
    print(f"seed                : {args.seed}", flush=True)
    print(f"Dry run             : {args.dry_run}", flush=True)
    print(f"Verify determinism  : {args.verify_determinism}", flush=True)
    print("=" * 72, flush=True)

    if not 0.0 < args.val_frac < 1.0:
        print(f"FATAL: --val-frac must be in (0, 1), got {args.val_frac}", flush=True)
        return 1
    if not os.path.isdir(dataset_a):
        print(f"FATAL: Dataset A not found: {dataset_a}", flush=True)
        return 1
    if not os.path.isdir(exp2_root):
        print(f"FATAL: Experiment 2 root not found: {exp2_root}", flush=True)
        return 1

    # --- Dataset A inventory (read-only) ------------------------------------
    a_train = list_images(os.path.join(dataset_a, "images", "train"))
    a_val = list_images(os.path.join(dataset_a, "images", "val"))
    a_test = list_images(os.path.join(dataset_a, "images", "test"))
    print(f"Dataset A inventory : train={len(a_train)} val={len(a_val)} test={len(a_test)}", flush=True)
    expectations = (
        ("train", len(a_train), args.expected_a_train),
        ("val", len(a_val), args.expected_a_val),
        ("test", len(a_test), args.expected_a_test),
    )
    for split_name, observed, expected in expectations:
        if expected and observed != expected:
            print(
                f"FATAL: Dataset A {split_name} has {observed} images, expected {expected}",
                flush=True,
            )
            return 1

    # --- Dataset B pool -----------------------------------------------------
    try:
        provenance_rows = read_provenance(os.path.join(exp2_root, PROVENANCE_MANIFEST))
        pool = discover_pool(exp2_root, provenance_rows)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FATAL: {exc}", flush=True)
        return 1
    if not pool:
        print("FATAL: Dataset B train pool is empty; nothing to split.", flush=True)
        return 1
    countries = sorted({item["country"] for item in pool})
    pool_negatives = sum(1 for item in pool if item["is_negative"])
    print(
        f"Dataset B train pool: {len(pool)} images, {len(countries)} countries {countries}, "
        f"{pool_negatives} negatives ({100.0 * pool_negatives / len(pool):.2f}%)",
        flush=True,
    )
    if "India" in countries:
        print(
            "FATAL: an India image reached the Dataset B train pool; the India exclusion "
            "is broken. Re-run exclude_india.py and convert_arrow_to_yolo.py.",
            flush=True,
        )
        return 1

    # --- HARD ASSERT: no Dataset A val/test contamination --------------------
    already_val = [s for s in pool if s["location"] == "val"]
    if already_val:
        print(
            f"NOTE: {len(already_val)} pool images were already in val/ by a previous run "
            "(will be reconciled).",
            flush=True,
        )

    # --- Select the val hold-out --------------------------------------------
    if args.verify_determinism:
        print("Verifying selection determinism...", flush=True)
        determinism_failures = verify_determinism(pool, args.val_frac, args.seed)
        if determinism_failures:
            print("\n" + "!" * 72, flush=True)
            for failure in determinism_failures:
                print(f"DETERMINISM VERIFICATION FAILED: {failure}", flush=True)
            print("!" * 72 + "\n", flush=True)
            return 1
        print(
            "Determinism verified: two in-process selections are byte-identical and a "
            "selection from a shuffled pool is identical to the baseline.",
            flush=True,
        )

    selected, selection_stats = stratified_val_selection(pool, args.val_frac, args.seed)
    selection_stats["pool_size"] = len(pool)
    selection_stats["pool_per_country"] = dict(sorted(Counter(i["country"] for i in pool).items()))
    selection_stats["val_per_country"] = dict(
        sorted(Counter(i["country"] for i in selected).items())
    )
    val_stems = {item["stem"] for item in selected}
    print(f"Val hold-out selected: {len(selected)} images", flush=True)
    for key in sorted(selection_stats["strata"]):
        stratum = selection_stats["strata"][key]
        print(
            f"    {key:<28} {stratum['selected']:>5} / {stratum['pool']:>5}  "
            f"({100.0 * stratum['frac']:.2f}%)",
            flush=True,
        )

    # --- Reconcile the filesystem -------------------------------------------
    for split in ("train", "val"):
        os.makedirs(os.path.join(exp2_root, "images", split), exist_ok=True)
        os.makedirs(os.path.join(exp2_root, "labels", split), exist_ok=True)
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)

    missing_actions: list[str] = []
    moved = 0
    for item in pool:
        desired = "val" if item["stem"] in val_stems else "train"
        actions = sync_pool_pair(exp2_root, item["stem"], item["extension"], desired, args.dry_run)
        for action in actions:
            if action.startswith("MISSING:"):
                missing_actions.append(f"{item['stem']} {action}")
            elif action.startswith("move:") or action.startswith("dedup:"):
                moved += 1
    if missing_actions:
        print(f"FATAL: {len(missing_actions)} pool files are missing from both pools:", flush=True)
        for line in missing_actions[:10]:
            print(f"    {line}", flush=True)
        return 1
    print(f"Pool file moves/dedups required: {moved}", flush=True)

    # --- Copy Dataset A train (read-only source) ----------------------------
    try:
        dataset_a_summary = copy_dataset_a_train(dataset_a, exp2_root, args.dry_run)
    except ValueError as exc:
        print(f"FATAL: {exc}", flush=True)
        return 1
    print(
        f"Dataset A train copied: {dataset_a_summary['copied']} "
        f"(already present: {dataset_a_summary['already_present']})",
        flush=True,
    )

    # --- Verify the final split state ---------------------------------------
    country_of_stem: dict[str, str] = {item["stem"]: item["country"] for item in pool}
    for stem in dataset_a_summary["sha_by_stem"]:
        country_of_stem[stem] = DATASET_A_COUNTRY

    if args.dry_run:
        # Nothing was moved, so the on-disk state cannot be the post-split state.
        # Verify the projection the run would produce instead.
        print("DRY RUN: verifying the projected post-split state (nothing was moved).", flush=True)
        train_items = [
            {
                "stem": item["stem"],
                "sha256": item["sha256"],
                "classes": item["classes"],
                "n_objects": item["n_objects"],
                "is_negative": item["is_negative"],
            }
            for item in pool
            if item["stem"] not in val_stems
        ]
        train_items.extend(
            {
                "stem": stem,
                "sha256": dataset_a_summary["sha_by_stem"][stem],
                "classes": dataset_a_summary["classes_by_stem"][stem],
                "n_objects": len(dataset_a_summary["classes_by_stem"][stem]),
                "is_negative": not dataset_a_summary["classes_by_stem"][stem],
            }
            for stem in sorted(dataset_a_summary["sha_by_stem"])
        )
        val_items = [
            {
                "stem": item["stem"],
                "sha256": item["sha256"],
                "classes": item["classes"],
                "n_objects": item["n_objects"],
                "is_negative": item["is_negative"],
            }
            for item in selected
        ]
    else:
        train_items = scan_split(exp2_root, "train")
        val_items = scan_split(exp2_root, "val")

    train_stems = {item["stem"] for item in train_items}
    val_stem_set = {item["stem"] for item in val_items}
    violations: list[str] = []
    name_overlap = sorted(train_stems & val_stem_set)
    if name_overlap:
        violations.append(
            f"{len(name_overlap)} filename(s) present in BOTH train and val: {name_overlap[:5]}"
        )
    train_shas = Counter(item["sha256"] for item in train_items)
    val_shas = Counter(item["sha256"] for item in val_items)
    sha_overlap = sorted(s for s in set(train_shas) & set(val_shas))
    if sha_overlap:
        violations.append(
            f"{len(sha_overlap)} image sha256(s) present in BOTH train and val: {sha_overlap[:5]}"
        )
    contamination = sorted((set(a_val) | set(a_test)) & train_stems)
    if contamination:
        violations.append(
            f"{len(contamination)} Dataset A val/test filename(s) reached the train pool: "
            f"{contamination[:5]}"
        )
    pool_in_val = sorted({item["stem"] for item in pool} & val_stem_set)
    if len(pool_in_val) != len(val_stem_set):
        violations.append(
            f"val contains {len(val_stem_set)} images but only {len(pool_in_val)} are Dataset B "
            "pool members; val must come exclusively from the Dataset B train pool"
        )

    if violations:
        print("\n" + "!" * 72, flush=True)
        for violation in violations:
            print(f"INVARIANT VIOLATED: {violation}", flush=True)
        print("!" * 72 + "\n", flush=True)
        return 1
    print("HARD FAIL checks passed: no train/val name overlap, no sha256 overlap, "
          "no Dataset A val/test contamination.", flush=True)

    # --- Summaries ----------------------------------------------------------
    train_summary = summarize_split(train_items, country_of_stem)
    val_summary = summarize_split(val_items, country_of_stem)
    train_neg_pct = 100.0 * train_summary["negative_images"] / max(1, train_summary["images"])
    val_neg_pct = 100.0 * val_summary["negative_images"] / max(1, val_summary["images"])

    print("\n" + "=" * 72, flush=True)
    print("SPLIT SUMMARY", flush=True)
    print("=" * 72, flush=True)
    print(f"  train images : {train_summary['images']}  objects: {train_summary['objects']}"
          f"  negatives: {train_summary['negative_images']} ({train_neg_pct:.2f}%)", flush=True)
    print(f"  val   images : {val_summary['images']}  objects: {val_summary['objects']}"
          f"  negatives: {val_summary['negative_images']} ({val_neg_pct:.2f}%)", flush=True)
    print(f"  test         : NOT CREATED - frozen external set at {FROZEN_TEST_PATH}", flush=True)
    for split_name, summary in (("train", train_summary), ("val", val_summary)):
        print(f"\n  {split_name} objects per class:", flush=True)
        for class_name, count in summary["objects_per_class"].items():
            print(f"    {class_name:<22} {count:>8}", flush=True)
        print(f"  {split_name} images per class (>=1 object):", flush=True)
        for class_name, count in summary["images_per_class"].items():
            print(f"    {class_name:<22} {count:>8}", flush=True)
        print(f"  {split_name} images per country:", flush=True)
        for country, count in summary["per_country"].items():
            print(f"    {country:<22} {count:>8}", flush=True)
    print("=" * 72, flush=True)

    if args.dry_run:
        print("\nDRY RUN: nothing written, data.yaml not emitted.", flush=True)
        print("ALL CHECKS PASSED (dry run)", flush=True)
        return 0

    # --- Write the split manifest, then the val record, then data.yaml LAST --
    manifest = build_split_manifest(
        seed=args.seed,
        val_frac=args.val_frac,
        train_summary=train_summary,
        val_summary=val_summary,
        dataset_a_summary=dataset_a_summary,
        selection_stats=selection_stats,
        val_frac_requested=args.val_frac,
    )
    manifest_path = os.path.join(exp2_root, SPLIT_MANIFEST_NAME)
    write_json_atomic(manifest_path, manifest)
    print(f"\nWrote split manifest: {manifest_path}", flush=True)
    print(f"  manifest_sha256: {manifest['manifest_sha256']}", flush=True)

    val_record = {
        "generated_by": "scripts/experiment2/build_splits.py",
        "seed": args.seed,
        "val_frac": args.val_frac,
        "algorithm": ALGORITHM_DESCRIPTION,
        "val_images": [
            {
                "file_name": item["stem"],
                "country": country_of_stem.get(item["stem"], "Unknown"),
                "n_objects": item["n_objects"],
                "is_negative": item["is_negative"],
                "sha256": item["sha256"],
            }
            for item in val_items
        ],
    }
    val_record_path = os.path.join(out_dir, VAL_HOLDOUT_NAME)
    write_json_atomic(val_record_path, val_record)
    print(f"Wrote val hold-out record: {val_record_path}", flush=True)

    data_yaml_path = os.path.join(exp2_root, DATA_YAML_NAME)
    write_text_atomic(data_yaml_path, render_data_yaml())
    print(f"Wrote data.yaml:          {data_yaml_path}", flush=True)

    print("\nALL CHECKS PASSED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
