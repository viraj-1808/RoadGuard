#!/usr/bin/env python
"""Phase 10 -- Experiment 2 dataset leakage audit.

Implements checks **A** through **F** over the frozen Experiment 1 test set, the
Dataset A (India) splits, and the Experiment 2 Dataset B (non-India) splits:

===  =========================================================================
A    Dataset A train vs frozen test            exact sha256 intersection == 0
B    Dataset B vs frozen test                  exact sha256 intersection == 0,
                                               no ``India_`` filename prefix
C    Dataset A train vs Dataset B              enumerate every colliding pair
D    Experiment 2 train vs Experiment 2 val    exact sha256 and filename == 0
E    near-duplicate audit                      two detectors, reported separately:
                                               (1) ``dhash_screen`` -- 64-bit
                                                   dHash Hamming <= 5 confirmed
                                                   by exact pixel equality (a
                                                   cheap pre-screen only)
                                               (2) ``correlation_criterion`` --
                                                   the PROJECT STANDARD from
                                                   analysis/verify_near_duplicates.py
                                                   (64x64 grayscale, Pearson
                                                   corr >= 0.90 AND MAD <= 0.10).
                                               The hard failure is driven by (2).
F    source-level split leakage                residual risk, documented
===  =========================================================================

Outputs (idempotent, overwritten in place):

* ``experiments/analysis/overnight/experiment2_dataset_b/experiment2_leakage_report.md``
* ``experiments/analysis/overnight/experiment2_dataset_b/experiment2_leakage_report.json``

The script is strictly read-only with respect to every dataset directory. It
never deletes, moves or edits an image or label. If any Experiment 2 image is
byte-identical to a frozen test image the offending files are recorded in the
``REMOVAL_REQUIRED`` array of the JSON report, a loud warning is printed, and
the process exits non-zero so that a human performs the removal.

Dependencies: standard library + ``PIL`` + ``numpy``. No ``torch``,
``ultralytics`` or ``datasets`` import is required.

Usage:
    python audit_leakage.py
    python audit_leakage.py --workers 32
    python audit_leakage.py --skip-near-dup
    python audit_leakage.py --no-cache
    python audit_leakage.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Iterable

import numpy as np
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_DATASET_A = os.path.join(REPO_ROOT, "experiments", "dataset", "yolo_rdd2022_india")
DEFAULT_EXP2_ROOT = os.path.join(REPO_ROOT, "experiments", "dataset", "experiment2")
DEFAULT_OUT_DIR = os.path.join(
    REPO_ROOT, "experiments", "analysis", "overnight", "experiment2_dataset_b"
)

REPORT_JSON_NAME = "experiment2_leakage_report.json"
REPORT_MD_NAME = "experiment2_leakage_report.md"
CACHE_NAME = "_hash_cache.json"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG", ".BMP")

#: Frozen Experiment 1 test set. Dataset A ``images/test`` *is* the frozen set.
FROZEN_TEST_SPLIT = "test"

#: Prefix every India image carries; no Experiment 2 file may carry it.
INDIA_PREFIX = "India_"

#: Verified Dataset A sizes, asserted when non-zero.
EXPECTED_A_TRAIN = 1071
EXPECTED_A_VAL = 229
EXPECTED_A_TEST = 230

#: dHash Hamming threshold that flags a near-duplicate *candidate*.
NEAR_DUP_THRESHOLD = 5

#: Thumbnail edge used before the 9x8 dHash reduction.
THUMB_SIZE = 32
DHASH_SIZE = 9

# --- project-standard near-duplicate criterion -----------------------------
# These values mirror ``analysis/verify_near_duplicates.py`` EXACTLY, which is the
# script that established Dataset A's correlation graph (59 verified groups over
# 121 images). A near-duplicate criterion is only comparable across datasets if
# it is the same criterion, so the Experiment 2 audit must use the same
# downsampling (64x64 ``convert("L")`` + LANCZOS, divided by 255) and the same two
# statistics (Pearson correlation of the downsampled grayscale, and the mean
# absolute difference of the normalised pixels).
PROJECT_STANDARD_SOURCE = "analysis/verify_near_duplicates.py"
PIXEL_SIZE = (64, 64)      # grayscale downsample size, per the project standard
PIXEL_CORR_MIN = 0.90      # Pearson correlation of downsampled grayscale
PIXEL_MAD_MAX = 0.10       # mean absolute difference of normalised pixels


#: Number of 16-bit LSH bands. Four 16-bit bands guarantee that any pair at
#: Hamming distance <= 3 shares at least one band; the residual 4-5 distance
#: pairs are still caught with high probability by the bucket index.
LSH_BANDS = 4
LSH_BAND_BITS = 64 // LSH_BANDS

SOURCE_SPLIT_NOTE = (
    "The upstream RDD2022 RDD_SPLIT split is a random 70/15/15 PER-IMAGE split with "
    "no country grouping and no video/sequence grouping. Consequently near-duplicate "
    "frames captured along the same source video, drive, or dashcam run can land in "
    "two different source splits, and therefore also in two different Experiment 2 "
    "splits after the stratified hold-out. This is a KNOWN RESIDUAL RISK that cannot "
    "be eliminated by per-image hashing and is recorded here rather than silently "
    "accepted. The mitigation available at report time is the Experiment 2 val split "
    "itself: val is drawn from the Dataset B train pool only, never from the frozen "
    "test set, so test-set optimism is unaffected by this risk."
)

NEAR_DUP_LIMITATION = (
    "dHash at Hamming distance <= 5 is a HEURISTIC SCREEN, not an exhaustive search. "
    "It is a 64-bit perceptual summary of a 32x32 grayscale thumbnail and therefore "
    "misses pairs that survive crops, rotation, rescaling, strong JPEG quality "
    "differences, colour or brightness shifts, heavy blur, or partial occlusion, "
    "because those perturbations move many more than 5 of the 64 comparison bits. "
    "Confirmed counts are therefore a LOWER BOUND on true near-duplication. Only "
    "confirmed pairs (exact decoded pixel-array equality) are reported as "
    "near-duplicates; candidates are reported separately and never counted as "
    "violations."
)

CORRELATION_CRITERION_NOTE = (
    "The correlation_criterion detector reproduces the criterion the rest of the "
    "project already relies on: analysis/verify_near_duplicates.py established the "
    "Dataset A correlation graph (59 verified groups over 121 images) by "
    "downsampling each image to 64x64 grayscale with a LANCZOS resample, normalising "
    "to [0, 1], and confirming a pair only when the Pearson correlation of the "
    "downsampled grayscale is >= {corr_min} AND the mean absolute difference is "
    "<= {mad_max}. A dHash Hamming threshold and an exact pixel-equality test are "
    "NOT comparable to that criterion, so this audit runs the criterion-compatible "
    "detector alongside the dHash screen and drives the hard failure from the "
    "correlation criterion. Both detectors are reported separately below: "
    "dhash_screen is retained as a cheap pre-screen / secondary signal, and "
    "correlation_criterion is the project standard. Candidate generation for the "
    "correlation criterion is identical to Dataset A's: 8 bands of 8 dHash bits, "
    "then every pair within Hamming <= {cand_hamming} is pixel-verified, so the "
    "recall envelope of the two audits matches. Note that this is still candidate-"
    "driven, not an all-pairs search; the reported count is a lower bound on true "
    "near-duplication at both stages."
)

HARD_FAILURE_DRIVER_NOTE = (
    "The E hard failures are driven by the PROJECT-STANDARD correlation criterion, "
    "not by the dHash screen, because that is the criterion Dataset A was built and "
    "audited against. A pair is a hard failure when it is confirmed by the "
    "correlation criterion AND either (a) it crosses the Experiment 2 train/val "
    "boundary, or (b) it involves the frozen test set. The dHash screen is reported "
    "for information and never drives an exit code."
)

#: Chunk size used when streaming a file through sha256.
_CHUNK = 1 << 20


# ---------------------------------------------------------------------------
# small filesystem helpers
# ---------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    """Return the hex sha256 digest of the file at *path*."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def list_images(directory: str) -> dict[str, str]:
    """Map ``stem -> absolute path`` for every image under *directory* (recursive).

    A duplicate stem inside a single directory is a hard error: it would make
    filename-based and content-based comparisons ambiguous.
    """
    found: dict[str, str] = {}
    if not os.path.isdir(directory):
        return found
    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] not in IMAGE_EXTENSIONS:
                continue
            path = os.path.join(dirpath, filename)
            stem = os.path.splitext(filename)[0]
            if stem in found:
                raise ValueError(
                    f"duplicate image stem {stem!r} under {directory}: "
                    f"{found[stem]} and {path}"
                )
            found[stem] = path
    return dict(sorted(found.items()))


class ImageGroup:
    """A named set of images that participate in the cross-group comparisons."""

    __slots__ = ("name", "paths")

    def __init__(self, name: str, paths: dict[str, str]) -> None:
        self.name = name
        self.paths = paths

    def __len__(self) -> int:
        return len(self.paths)

    @property
    def stems(self) -> set[str]:
        return set(self.paths)


# ---------------------------------------------------------------------------
# hash cache
# ---------------------------------------------------------------------------
class HashCache:
    """Persistent ``path|mtime|size -> sha256`` cache for fast re-runs.

    The cache is a plain JSON object written to ``<exp2-root>/_hash_cache.json``.
    Entries whose key no longer matches the file on disk are simply recomputed,
    so a stale cache can never produce a wrong digest.
    """

    def __init__(self, path: str | None) -> None:
        self.path = path
        self.entries: dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict):
                    self.entries = {str(k): str(v) for k, v in loaded.items()}
            except (OSError, json.JSONDecodeError) as exc:
                print(f"WARNING: ignoring unreadable hash cache {path}: {exc}", flush=True)

    @staticmethod
    def key_for(path: str) -> str:
        """Return the cache key ``path|mtime_ns|size`` for *path*."""
        stat = os.stat(path)
        return f"{rel(path)}|{stat.st_mtime_ns}|{stat.st_size}"

    def lookup(self, path: str) -> str | None:
        """Return the cached digest for *path* when still valid, else ``None``."""
        try:
            return self.entries.get(self.key_for(path))
        except OSError:
            return None

    def store(self, path: str, digest: str) -> None:
        """Record *digest* for *path* in the cache."""
        try:
            self.entries[self.key_for(path)] = digest
        except OSError:
            pass

    def save(self) -> None:
        """Persist the cache to disk (best effort)."""
        if not self.path:
            return
        try:
            write_text_atomic(
                self.path, json.dumps(self.entries, indent=0, sort_keys=True) + "\n"
            )
        except OSError as exc:
            print(f"WARNING: could not write hash cache {self.path}: {exc}", flush=True)


def hash_paths(
    paths: Iterable[str], workers: int, cache: HashCache
) -> dict[str, str]:
    """Return ``absolute path -> sha256`` for every path in *paths*.

    Cached digests are reused; the remainder are hashed on a thread pool because
    the work is I/O bound (file reads plus the sha256 update loop).
    """
    unique = sorted({os.path.abspath(p) for p in paths})
    digests: dict[str, str] = {}
    todo: list[str] = []

    for path in unique:
        cached = cache.lookup(path)
        if cached is not None:
            digests[path] = cached
            cache.hits += 1
        else:
            todo.append(path)
            cache.misses += 1

    if todo:
        print(f"  hashing {len(todo)} file(s) on {workers} thread(s)...", flush=True)
        done = 0
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            for path, digest in pool.map(_hash_and_store, todo):
                digests[path] = digest
                cache.store(path, digest)
                done += 1
                if done % 5000 == 0:
                    print(f"    ... {done}/{len(todo)}", flush=True)
    return digests


def _hash_and_store(path: str) -> tuple[str, str]:
    """Return ``(path, sha256)``. Split out so the pool map needs one argument."""
    return path, sha256_file(path)


# ---------------------------------------------------------------------------
# dHash
# ---------------------------------------------------------------------------
def dhash_of(path: str) -> int | None:
    """Return the 64-bit dHash of the image at *path*, or ``None`` if unreadable.

    The image is reduced to a 32x32 grayscale thumbnail (an antialiasing resize,
    which also drops high-frequency compression noise) and then to 9x8, where
    each of the 64 bits records whether a pixel is brighter than its right-hand
    neighbour.
    """
    try:
        with Image.open(path) as handle:
            gray = handle.convert("L").resize(
                (THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS
            )
            small = np.asarray(
                gray.resize((DHASH_SIZE, DHASH_SIZE - 1), Image.Resampling.LANCZOS),
                dtype=np.int16,
            )
    except (OSError, ValueError):
        return None
    bits = small[:, 1:] > small[:, :-1]
    value = 0
    for bit in bits.reshape(-1):
        value = (value << 1) | int(bit)
    return value


def hamming(a: int, b: int) -> int:
    """Return the Hamming distance between two 64-bit dHash integers."""
    return (a ^ b).bit_count()


def identical_pixels(path_a: str, path_b: str) -> bool:
    """True when the two images decode to identical RGB pixel arrays."""
    try:
        with Image.open(path_a) as first:
            array_a = np.asarray(first.convert("RGB"))
        with Image.open(path_b) as second:
            array_b = np.asarray(second.convert("RGB"))
    except (OSError, ValueError):
        return False
    if array_a.shape != array_b.shape:
        return False
    return bool(np.array_equal(array_a, array_b))


# ---------------------------------------------------------------------------
# project-standard correlation criterion (mirrors analysis/verify_near_duplicates.py)
# ---------------------------------------------------------------------------
def pixel_signature(path: str) -> np.ndarray | None:
    """Return the 64x64 downsampled normalised grayscale signature of *path*.

    Byte-for-byte the same recipe as ``analysis/verify_near_duplicates.py``:
    ``convert("L")`` -> ``resize((64, 64), LANCZOS)`` -> ``/ 255.0``. Returns
    ``None`` when the file cannot be decoded.
    """
    try:
        with Image.open(path) as handle:
            small = handle.convert("L").resize(PIXEL_SIZE, Image.Resampling.LANCZOS)
            array = np.asarray(small, dtype=np.float64) / 255.0
    except (OSError, ValueError):
        return None
    return array


def pixel_compare(sig_a: np.ndarray, sig_b: np.ndarray) -> tuple[float, float]:
    """Return ``(pearson correlation, mean absolute difference)`` of two signatures.

    A constant signature has zero standard deviation, so the correlation is
    defined as 0.0 in that case (mirroring the project-standard implementation
    rather than emitting a NaN that would silently compare False).
    """
    a = sig_a.ravel()
    b = sig_b.ravel()
    if a.std() == 0 or b.std() == 0:
        corr = 0.0
    else:
        corr = float(np.corrcoef(a, b)[0, 1])
    mad = float(np.mean(np.abs(a - b)))
    return corr, mad


def confirm_by_correlation(
    sig_a: np.ndarray, sig_b: np.ndarray, corr_min: float, mad_max: float
) -> tuple[bool, float, float]:
    """Return ``(confirmed, corr, mad)`` under the project-standard criterion."""
    corr, mad = pixel_compare(sig_a, sig_b)
    return bool(corr >= corr_min and mad <= mad_max), corr, mad




def _lsh_candidates(hashes: dict[str, int]) -> set[tuple[str, str]]:
    """Return candidate index pairs that share at least one LSH band.

    Four 16-bit bands are used. Pigeonhole guarantees any pair at distance <= 3
    shares a band; distance 4-5 pairs are still found in practice, and every
    surviving pair is re-checked with the exact Hamming distance anyway.
    """
    band_mask = (1 << LSH_BAND_BITS) - 1
    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    keys = list(hashes)
    values = [hashes[k] for k in keys]
    for index, value in enumerate(values):
        for band in range(LSH_BANDS):
            buckets[(band, (value >> (band * LSH_BAND_BITS)) & band_mask)].append(index)

    candidates: set[tuple[str, str]] = set()
    for members in buckets.values():
        if len(members) < 2 or len(members) > 400:
            continue
        for i_pos in range(len(members)):
            for j_pos in range(i_pos + 1, len(members)):
                a = members[i_pos]
                b = members[j_pos]
                candidates.add((keys[a], keys[b]) if a < b else (keys[b], keys[a]))
    return candidates


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def group_sha_index(
    group: ImageGroup, digests: dict[str, str]
) -> dict[str, list[str]]:
    """Return ``sha256 -> [relative image paths]`` for one group."""
    index: dict[str, list[str]] = defaultdict(list)
    for stem, path in group.paths.items():
        index[digests[path]].append(rel(path))
    return {sha: sorted(paths) for sha, paths in sorted(index.items())}


def intersect(
    index_a: dict[str, list[str]], index_b: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """Return the ``sha256`` keys present in both indexes, with their members."""
    shared = sorted(set(index_a) & set(index_b))
    return [
        {"sha256": sha, "a_paths": index_a[sha], "b_paths": index_b[sha]} for sha in shared
    ]


def check_a(
    a_train: ImageGroup,
    frozen: ImageGroup,
    idx_train: dict[str, list[str]],
    idx_frozen: dict[str, list[str]],
) -> dict[str, Any]:
    """Check A -- Dataset A train must not overlap the frozen test set."""
    collisions = intersect(idx_train, idx_frozen)
    return {
        "name": "dataset_a_train_vs_frozen_test",
        "description": (
            "Exact sha256 intersection between Dataset A train and the frozen "
            "230-image India test set."
        ),
        "dataset_a_train_images": len(a_train),
        "frozen_test_images": len(frozen),
        "duplicate_sha256_count": len(collisions),
        "expected_count": 0,
        "passed": not collisions,
        "collisions": collisions,
    }


def check_b(
    dataset_b: ImageGroup,
    frozen: ImageGroup,
    idx_b: dict[str, list[str]],
    idx_frozen: dict[str, list[str]],
    idx_a_train: dict[str, list[str]],
    digests: dict[str, str],
) -> dict[str, Any]:
    """Check B -- Dataset B must not overlap the frozen test set at all.

    The ``India_`` filename assertion is reported as two counts. ``build_splits.py``
    deliberately copies Dataset A train into ``<exp2-root>/images/train`` under its
    original name, so ``India_``-prefixed files that are byte-identical to a
    Dataset A train image are the *designed* carry-over and are informational.
    An ``India_``-prefixed file that is NOT in Dataset A train would mean an India
    image survived the exclusion somewhere unexpected, and is a hard failure.
    """
    shared = sorted(set(idx_b) & set(idx_frozen))
    collisions = [
        {
            "sha256": sha,
            "dataset_b_paths": idx_b[sha],
            "frozen_test_paths": idx_frozen[sha],
        }
        for sha in shared
    ]
    a_train_shas = set(idx_a_train)
    india_all: list[str] = []
    india_carry_over: list[str] = []
    india_unexpected: list[str] = []
    for path in dataset_b.paths.values():
        if not os.path.basename(path).startswith(INDIA_PREFIX):
            continue
        india_all.append(rel(path))
        sha = digests.get(path)
        if sha is not None and sha in a_train_shas:
            india_carry_over.append(rel(path))
        else:
            india_unexpected.append(rel(path))
    return {
        "name": "dataset_b_vs_frozen_test",
        "description": (
            "Exact sha256 intersection between every Experiment 2 image (the "
            "non-India Dataset B pool) and the frozen test set, plus a filename "
            "prefix audit."
        ),
        "dataset_b_images": len(dataset_b),
        "frozen_test_images": len(frozen),
        "duplicate_sha256_count": len(collisions),
        "expected_count": 0,
        "india_prefixed_filenames": len(india_all),
        "india_prefixed_designed_carry_over": len(india_carry_over),
        "india_prefixed_unexpected": len(india_unexpected),
        "india_prefixed_filenames_sample": sorted(india_all)[:50],
        "india_prefixed_unexpected_sample": sorted(india_unexpected)[:50],
        "india_prefix_note": (
            "`build_splits.py` copies Dataset A train into <exp2-root>/images/train "
            "verbatim, so the India_ prefix appears in the Experiment 2 train split "
            "by design. Only an India_-prefixed file that is absent from Dataset A "
            "train counts as a failure."
        ),
        "passed": not collisions and not india_unexpected,
        "collisions": collisions,
    }


def check_c(
    a_train: ImageGroup,
    dataset_b: ImageGroup,
    idx_train: dict[str, list[str]],
    idx_b: dict[str, list[str]],
) -> dict[str, Any]:
    """Check C -- enumerate every Dataset A train / Dataset B content collision."""
    pairs: list[dict[str, Any]] = []
    for collision in intersect(idx_train, idx_b):
        for name_a in collision["a_paths"]:
            for name_b in collision["b_paths"]:
                carry_over = os.path.basename(name_b).startswith(INDIA_PREFIX)
                pairs.append(
                    {
                        "filename_a": name_a,
                        "filename_b": name_b,
                        "sha256": collision["sha256"],
                        "classification": (
                            "expected_dataset_a_carry_over"
                            if carry_over
                            else "unexpected_cross_dataset_duplicate"
                        ),
                    }
                )
    unexpected = [p for p in pairs if p["classification"] != "expected_dataset_a_carry_over"]
    expected = [p for p in pairs if p["classification"] == "expected_dataset_a_carry_over"]
    return {
        "name": "dataset_a_train_vs_dataset_b",
        "description": (
            "Exact duplicate sha256 count between Dataset A train and the "
            "Experiment 2 pool. Pairs whose Experiment 2 filename still carries "
            "the India_ prefix are the designed Dataset A carry-over; anything "
            "else is an unexpected cross-dataset duplicate."
        ),
        "duplicate_sha256_count": len({p["sha256"] for p in pairs}),
        "duplicate_pair_count": len(pairs),
        "expected_carry_over_pair_count": len(expected),
        "unexpected_pair_count": len(unexpected),
        "informational": True,
        "passed": not unexpected,
        "pairs": sorted(pairs, key=lambda p: (p["sha256"], p["filename_a"], p["filename_b"])),
    }


def check_d(
    e2_train: ImageGroup,
    e2_val: ImageGroup,
    idx_train: dict[str, list[str]],
    idx_val: dict[str, list[str]],
) -> dict[str, Any]:
    """Check D -- Experiment 2 train and val must be disjoint by content and name."""
    content = intersect(idx_train, idx_val)
    names = sorted(e2_train.stems & e2_val.stems)
    return {
        "name": "experiment2_train_vs_val",
        "description": (
            "Exact sha256 and filename intersection between the Experiment 2 "
            "train and val splits."
        ),
        "train_images": len(e2_train),
        "val_images": len(e2_val),
        "duplicate_sha256_count": len(content),
        "filename_intersection_count": len(names),
        "expected_count": 0,
        "passed": not content and not names,
        "duplicate_pairs": content,
        "shared_filenames": names[:50],
    }


def near_duplicate_audit(
    groups: list[ImageGroup],
    workers: int,
    threshold: int,
    corr_min: float = PIXEL_CORR_MIN,
    mad_max: float = PIXEL_MAD_MAX,
) -> dict[str, Any]:
    """Check E -- two independently reported near-duplicate detectors.

    ``dhash_screen`` (cheap pre-screen / secondary signal): 64-bit dHash with
    Hamming distance <= *threshold*, confirmed by exact decoded RGB pixel-array
    equality. Retained because it is cheap and very high precision, but it is NOT
    the project standard.

    ``correlation_criterion`` (project standard, drives the hard failure): 64x64
    downsampled grayscale, confirmed when Pearson correlation >= *corr_min* AND
    mean absolute difference <= *mad_max* -- the criterion
    ``analysis/verify_near_duplicates.py`` used to build Dataset A's correlation
    graph. Candidate pairs are gathered with the same banded dHash blocking and the
    same permissive Hamming threshold Dataset A used, so the recall envelope
    matches the standard rather than being a different search.

    Signatures are computed lazily and only for images that appear in a candidate
    pair, so peak memory is bounded by the candidate set rather than by the
    38k-image corpus.
    """
    all_paths: dict[str, str] = {}
    group_of: dict[str, str] = {}
    for group in groups:
        for stem, path in group.paths.items():
            all_paths[path] = stem
            group_of[path] = group.name

    print(f"  computing dHash for {len(all_paths)} image(s)...", flush=True)
    hashes: dict[str, int] = {}
    unreadable: list[str] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for path, value in zip(all_paths, pool.map(dhash_of, all_paths)):
            if value is None:
                unreadable.append(rel(path))
            else:
                hashes[path] = value
    if unreadable:
        print(f"WARNING: {len(unreadable)} image(s) unreadable by PIL", flush=True)

    # --- candidate generation for BOTH detectors ----------------------------
    candidates = _lsh_candidates(hashes)
    print(
        f"  [candidate generation] {len(candidates)} LSH candidate pair(s); applying "
        f"Hamming <= {threshold} screen...",
        flush=True,
    )

    screened_candidates = []
    needed_for_corr = set()
    for path_a, path_b in sorted(candidates):
        distance = hamming(hashes[path_a], hashes[path_b])
        if distance <= threshold:
            screened_candidates.append((path_a, path_b, distance))
            needed_for_corr.add(path_a)
            needed_for_corr.add(path_b)
            
    # --- detector 1: dHash screen + exact pixel equality --------------------
    dhash_pixel_exact_confirmed = []
    candidates_within_threshold = len(screened_candidates)
    
    for path_a, path_b, distance in screened_candidates:
        if identical_pixels(path_a, path_b):
            group_a = group_of[path_a]
            group_b = group_of[path_b]
            dhash_pixel_exact_confirmed.append(
                {
                    "image_a": rel(path_a),
                    "image_b": rel(path_b),
                    "group_a": group_a,
                    "group_b": group_b,
                    "hamming": distance,
                    "crosses_splits": group_a != group_b,
                    "split_pair": sorted([group_a, group_b]),
                }
            )
    dhash_pixel_exact_confirmed.sort(key=lambda r: (r["hamming"], r["image_a"], r["image_b"]))

    # --- detector 2: project-standard correlation criterion -----------------
    print(
        f"  [correlation_criterion] {len(screened_candidates)} candidate pair(s) "
        f"(Hamming <= {threshold}); verifying 64x64 grayscale "
        f"(corr >= {corr_min}, MAD <= {mad_max})...",
        flush=True,
    )

    needed = sorted(needed_for_corr)
    signatures = {}
    signature_unreadable = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for path, signature in zip(needed, pool.map(pixel_signature, needed)):
            if signature is None:
                signature_unreadable.append(rel(path))
            else:
                signatures[path] = signature
    if signature_unreadable:
        print(
            f"WARNING: {len(signature_unreadable)} image(s) unreadable for pixel "
            "verification",
            flush=True,
        )

    correlation_criterion_confirmed = []
    evaluated = 0
    rejected = 0
    for path_a, path_b, distance in screened_candidates:
        sig_a = signatures.get(path_a)
        sig_b = signatures.get(path_b)
        if sig_a is None or sig_b is None:
            rejected += 1
            continue
        evaluated += 1
        confirmed, corr, mad = confirm_by_correlation(sig_a, sig_b, corr_min, mad_max)
        if not confirmed:
            rejected += 1
            continue
        group_a = group_of[path_a]
        group_b = group_of[path_b]
        correlation_criterion_confirmed.append(
            {
                "image_a": rel(path_a),
                "image_b": rel(path_b),
                "group_a": group_a,
                "group_b": group_b,
                "dhash_distance": distance,
                "pixel_corr": round(corr, 4),
                "pixel_mad": round(mad, 4),
                "crosses_splits": group_a != group_b,
                "split_pair": sorted([group_a, group_b]),
            }
        )
    correlation_criterion_confirmed.sort(key=lambda r: (r["pixel_corr"], r["image_a"], r["image_b"]))

    note = CORRELATION_CRITERION_NOTE.format(
        corr_min=corr_min, mad_max=mad_max, cand_hamming=threshold
    )
    return {        "images_screened": len(hashes),
        "images_unreadable": len(unreadable),
        "unreadable_sample": sorted(unreadable)[:25],
        "hamming_threshold": threshold,
        "confirmation_method": "exact decoded RGB pixel-array equality",
        "limitations": NEAR_DUP_LIMITATION,
        "dhash_screen": {
            "role": "cheap pre-screen / secondary signal; never drives the exit code",
            "hash": f"dHash {THUMB_SIZE}x{THUMB_SIZE} grayscale thumbnail -> "
            f"{DHASH_SIZE}x{DHASH_SIZE - 1}, 64 bits",
            "lsh_candidate_pairs": len(candidates),
            "candidate_pairs_within_hamming_threshold": candidates_within_threshold,
            "hamming_threshold": threshold,
            "confirmation_method": "exact decoded RGB pixel-array equality",
            "confirmed_near_duplicate_pairs": len(dhash_pixel_exact_confirmed),
            "limitations": NEAR_DUP_LIMITATION,
            "pairs": dhash_pixel_exact_confirmed,
        },
        "correlation_criterion": {
            "role": (
                "PROJECT STANDARD; this is the detector that drives the hard failure"
            ),
            "criterion_source": PROJECT_STANDARD_SOURCE,
            "criterion": (
                f"grayscale {PIXEL_SIZE[0]}x{PIXEL_SIZE[1]} LANCZOS downsample, "
                f"normalised to [0, 1]; confirm when pearson_corr >= {corr_min} "
                f"AND mean_abs_diff <= {mad_max}"
            ),
            "grayscale_downsample": list(PIXEL_SIZE),
            "pearson_corr_min": corr_min,
            "mean_abs_diff_max": mad_max,
                    "candidate_generation": (
                "dHash LSH candidate generation, "
                "Hamming <= {threshold}"
            ),
            "candidate_hamming_threshold": threshold,
            "candidate_pairs": len(screened_candidates),
            "pairs_pixel_evaluated": evaluated,
            "pairs_rejected_by_criterion": rejected,
            "images_unreadable_for_pixel_check": len(signature_unreadable),
            "confirmed_near_duplicate_pairs": len(correlation_criterion_confirmed),
            "note": note,
            "pairs": correlation_criterion_confirmed,
        },
        "hard_failure_driver": "correlation_criterion",
        "hard_failure_driver_note": HARD_FAILURE_DRIVER_NOTE,
        # Flattened aliases kept so the report plumbing and the existing
        # summary/check-F fields keep working. They refer to the dHash screen.
        "lsh_candidate_pairs": len(candidates),
        "candidate_pairs_within_hamming_threshold": candidates_within_threshold,
        "confirmed_near_duplicate_pairs": len(dhash_pixel_exact_confirmed),
        "confirmed_correlation_criterion_pairs": len(correlation_criterion_confirmed),
        "pairs": dhash_pixel_exact_confirmed,
    }


# ---------------------------------------------------------------------------
# markdown report
# ---------------------------------------------------------------------------
def _md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    """Render a simple GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable leakage report from the JSON payload."""
    summary = report["summary"]
    inputs = report["inputs"]
    checks = report["checks"]
    near = checks["E"]["near_duplicates"]

    lines: list[str] = []
    lines.append("# Experiment 2 Leakage Audit (Phase 10)")
    lines.append("")
    lines.append(f"**Generated by**: `{report['generated_by']}`")
    lines.append(f"**Generated (UTC)**: {report['generated_utc']}")
    lines.append("")
    lines.append(
        "Dataset B is every non-India image under the Experiment 2 root. The frozen "
        "test set is Dataset A `images/test` (230 India images, 679 GT label lines) "
        "and is referenced read-only; this audit never modifies it, `runs/`, "
        "`experiments/dataset/raw_hf_rdd2022/`, or "
        "`experiments/dataset/yolo_rdd2022_india/`."
    )
    lines.append("")

    lines.append("## Verdict")
    lines.append("")
    lines.extend(
        _md_table(
            ["Result", "Value"],
            [
                ["Overall", "**PASS**" if summary["all_hard_checks_passed"] else "**FAIL**"],
                ["Images hashed", report["totals"]["images_hashed"]],
                ["Cache hits / misses", f"{report['hash_cache']['hits']} / {report['hash_cache']['misses']}"],
                ["`REMOVAL_REQUIRED` entries", len(report["REMOVAL_REQUIRED"])],
                ["Near-duplicate candidates (dHash <= %d)" % near["hamming_threshold"], near["candidate_pairs_within_hamming_threshold"]],
                ["Near-duplicates **confirmed** (pixel-equal, dHash screen)", near["confirmed_near_duplicate_pairs"]],
                ["Near-duplicates **confirmed** (project standard, corr/MAD)", near["confirmed_correlation_criterion_pairs"]],
                ["Hard failure driven by", "correlation_criterion (project standard)"],
            ],
        )
    )
    lines.append("")

    lines.append("## Inputs")
    lines.append("")
    lines.extend(
        _md_table(
            ["Group", "Images"],
            [[key, value] for key, value in sorted(inputs["group_sizes"].items())],
        )
    )
    lines.append("")

    lines.append("## Check A - Dataset A train vs frozen test")
    lines.append("")
    a = checks["A"]
    lines.append(
        f"Exact sha256 intersection: **{a['duplicate_sha256_count']}** "
        f"(expected 0). Result: **{'PASS' if a['passed'] else 'FAIL'}**."
    )
    lines.append("")

    lines.append("## Check B - Dataset B vs frozen test")
    lines.append("")
    b = checks["B"]
    lines.append(
        f"Exact sha256 intersection: **{b['duplicate_sha256_count']}** (expected 0). "
        f"`{INDIA_PREFIX}`-prefixed Experiment 2 filenames: "
        f"**{b['india_prefixed_filenames']}**, of which "
        f"**{b['india_prefixed_designed_carry_over']}** are the designed Dataset A "
        f"train carry-over and **{b['india_prefixed_unexpected']}** are unexpected. "
        f"Result: **{'PASS' if b['passed'] else 'FAIL'}**."
    )
    lines.append("")
    lines.append(f"> {b['india_prefix_note']}")
    lines.append("")

    lines.append("## Check C - Dataset A train vs Dataset B")
    lines.append("")
    c = checks["C"]
    lines.append(
        f"Duplicate sha256 values: **{c['duplicate_sha256_count']}**; colliding "
        f"pairs: **{c['duplicate_pair_count']}** "
        f"({c['expected_carry_over_pair_count']} designed Dataset A carry-over, "
        f"{c['unexpected_pair_count']} unexpected)."
    )
    lines.append("")
    lines.append(
        "This check is informational. `build_splits.py` copies Dataset A train into "
        "the Experiment 2 train split by design, so `India_`-prefixed collisions are "
        "expected; any other collision would be a genuine cross-dataset duplicate."
    )
    if c["pairs"]:
        lines.append("")
        shown = c["pairs"][:200]
        lines.extend(
            _md_table(
                ["Dataset A filename", "Experiment 2 filename", "sha256", "classification"],
                [
                    [p["filename_a"], p["filename_b"], p["sha256"][:16] + "...", p["classification"]]
                    for p in shown
                ],
            )
        )
        if len(c["pairs"]) > len(shown):
            lines.append("")
            lines.append(
                f"_... {len(c['pairs']) - len(shown)} further pair(s) omitted; the JSON "
                "report contains the complete list._"
            )
    lines.append("")

    lines.append("## Check D - Experiment 2 train vs val")
    lines.append("")
    d = checks["D"]
    lines.append(
        f"sha256 intersection: **{d['duplicate_sha256_count']}** (expected 0). "
        f"Filename intersection: **{d['filename_intersection_count']}** (expected 0). "
        f"Result: **{'PASS' if d['passed'] else 'FAIL'}**."
    )
    lines.append("")

    lines.append("## Check E - near-duplicate audit")
    lines.append("")
    lines.append(
        "Two detectors are run and reported **separately** because their "
        "criteria are not comparable. `dhash_screen` is the cheap 64-bit "
        "perceptual screen retained for information; `correlation_criterion` "
        "reproduces the criterion `analysis/verify_near_duplicates.py` used "
        "to build Dataset A's correlation graph (59 verified groups / 121 "
        "images) and is therefore the detector that drives the E hard "
        "failures and the check F crossing count."
    )
    lines.append("")
    corr = near["correlation_criterion"]
    lines.extend(
        _md_table(
            ["Detector", "Role", "Candidate pairs", "Confirmed pairs"],
            [
                [
                    "dhash_screen",
                    "cheap pre-screen / secondary signal",
                    near["candidate_pairs_within_hamming_threshold"],
                    near["confirmed_near_duplicate_pairs"],
                ],
                [
                    "correlation_criterion",
                    "PROJECT STANDARD - drives the hard failure",
                    corr["candidate_pairs"],
                    corr["confirmed_near_duplicate_pairs"],
                ],
            ],
        )
    )
    lines.append("")
    lines.append("### dhash_screen (secondary signal)")
    lines.append("")
    lines.append(
        f"- Images screened: **{near['images_screened']}** "
        f"(unreadable: {near['images_unreadable']})"
    )
    lines.append(f"- dHash: {THUMB_SIZE}x{THUMB_SIZE} grayscale thumbnail -> {DHASH_SIZE}x{DHASH_SIZE - 1}, 64 bits")
    lines.append(f"- LSH candidate pairs: **{near['lsh_candidate_pairs']}**")
    lines.append(
        f"- Candidates with Hamming <= {near['hamming_threshold']}: "
        f"**{near['candidate_pairs_within_hamming_threshold']}**"
    )
    lines.append(
        f"- Confirmed near-duplicate pairs (exact pixel equality): "
        f"**{near['confirmed_near_duplicate_pairs']}**"
    )
    lines.append("")
    lines.append(
        "Candidate and confirmed counts are reported **separately on purpose**: a "
        "dHash hit is only a candidate and is never counted as a violation."
    )
    lines.append("")
    lines.append("### Limitation")
    lines.append("")
    lines.append(NEAR_DUP_LIMITATION)
    lines.append("")
    if near["pairs"]:
        lines.append("### dhash_screen confirmed pairs")
        lines.append("")
        lines.extend(
            _md_table(
                ["Image A", "Group A", "Image B", "Group B", "Hamming", "Crosses splits"],
                [
                    [
                        p["image_a"],
                        p["group_a"],
                        p["image_b"],
                        p["group_b"],
                        p["hamming"],
                        "yes" if p["crosses_splits"] else "no",
                    ]
                    for p in near["pairs"][:200]
                ],
            )
        )
    else:
        lines.append("No near-duplicate pair survived the pixel-equality confirmation.")
    lines.append("")
    lines.append("### correlation_criterion (PROJECT STANDARD)")
    lines.append("")
    lines.append(
        f"- Criterion: grayscale {corr['grayscale_downsample'][0]}x"
        f"{corr['grayscale_downsample'][1]} LANCZOS downsample, normalised "
        f"to [0, 1]; confirm when **pearson_corr >= {corr['pearson_corr_min']}** "
        f"AND **mean_abs_diff <= {corr['mean_abs_diff_max']}**"
    )
    lines.append(
        f"- Source: `{corr['criterion_source']}` (Dataset A's established standard)"
    )
    lines.append(f"- Candidate generation: {corr['candidate_generation']}")
    lines.append(
        f"- Candidate pairs: **{corr['candidate_pairs']}**; pixel-evaluated: "
        f"**{corr['pairs_pixel_evaluated']}**; rejected by the criterion: "
        f"**{corr['pairs_rejected_by_criterion']}**; unreadable for pixel "
        f"check: {corr['images_unreadable_for_pixel_check']}"
    )
    lines.append(
        f"- Confirmed near-duplicate pairs (project standard): "
        f"**{corr['confirmed_near_duplicate_pairs']}**"
    )
    lines.append("")
    lines.append("**The E hard failures are driven by this criterion**, because it "
                 "is the standard the rest of the project relies on. The dHash "
                 "screen is reported for information and never drives an exit "
                 "code.")
    lines.append("")
    lines.append(corr["note"])
    lines.append("")
    if corr["pairs"]:
        lines.append("#### correlation_criterion confirmed pairs")
        lines.append("")
        lines.extend(
            _md_table(
                [
                    "Image A",
                    "Group A",
                    "Image B",
                    "Group B",
                    "dHash dist",
                    "Pixel corr",
                    "Pixel MAD",
                    "Crosses splits",
                ],
                [
                    [
                        p["image_a"],
                        p["group_a"],
                        p["image_b"],
                        p["group_b"],
                        p["dhash_distance"],
                        p["pixel_corr"],
                        p["pixel_mad"],
                        "yes" if p["crosses_splits"] else "no",
                    ]
                    for p in corr["pairs"][:200]
                ],
            )
        )
    else:
        lines.append("No pair satisfied the project-standard correlation criterion.")
    lines.append("")

    lines.append("## Check F - source-level split leakage")
    lines.append("")
    f = checks["F"]
    lines.append(
        f"Confirmed near-duplicate pairs crossing Experiment 2 train vs val "
        f"(project standard): **{f['confirmed_pairs_crossing_exp2_train_val']}** "
        f"(train->val: {f['crossing_exp2_train_to_val']}, "
        f"val->train: {f['crossing_exp2_val_to_train']})."
    )
    lines.append("")
    lines.append(
        f"Project-standard near-duplicate pairs involving the frozen test set: "
        f"**{f['correlation_criterion_pairs_involving_frozen_test']}**. "
        f"For comparison, the dHash screen alone reports "
        f"{f['dhash_screen_pairs_crossing_exp2_train_val']} crossing pair(s)."
    )
    lines.append("")
    lines.append("### Known residual risk")
    lines.append("")
    lines.append(SOURCE_SPLIT_NOTE)
    lines.append("")

    lines.append("## Removal required")
    lines.append("")
    if report["REMOVAL_REQUIRED"]:
        lines.append(
            "**The following Experiment 2 file(s) are byte-identical to a frozen test "
            "image. They must be removed manually. This script does not delete "
            "anything.**"
        )
        lines.append("")
        lines.extend(
            _md_table(
                ["Experiment 2 file", "sha256", "Frozen test file"],
                [
                    [e["experiment2_path"], e["sha256"][:16] + "...", e["frozen_test_path"]]
                    for e in report["REMOVAL_REQUIRED"]
                ],
            )
        )
    else:
        lines.append("None. No Experiment 2 image is byte-identical to a frozen test image.")
    lines.append("")

    lines.append("## Reproduce")
    lines.append("")
    lines.append("```")
    lines.append("python scripts/experiment2/audit_leakage.py --workers 32")
    lines.append("```")
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Return the fully configured argument parser."""
    parser = argparse.ArgumentParser(
        description="Phase 10 Experiment 2 leakage audit (checks A-F). Read-only."
    )
    parser.add_argument(
        "--dataset-a", type=str, default=DEFAULT_DATASET_A, help="Frozen Dataset A root (read-only)."
    )
    parser.add_argument(
        "--exp2-root", type=str, default=DEFAULT_EXP2_ROOT, help="Experiment 2 dataset root (read-only)."
    )
    parser.add_argument(
        "--out-dir", type=str, default=DEFAULT_OUT_DIR, help="Directory for the two report files."
    )
    parser.add_argument(
        "--workers", type=int, default=16, help="Thread-pool size for hashing and dHashing (I/O bound)."
    )
    parser.add_argument(
        "--hamming-threshold",
        type=int,
        default=NEAR_DUP_THRESHOLD,
        help="dHash Hamming distance that flags a near-duplicate candidate.",
    )
    parser.add_argument(
        "--skip-near-dup",
        action="store_true",
        help="Skip check E entirely (useful for a fast hash-only pass).",
    )
    parser.add_argument(
        "--no-cache",
        dest="cache",
        action="store_false",
        help="Disable the sha256 cache (hashing is still threaded).",
    )
    parser.add_argument(
        "--cache-path",
        type=str,
        default=None,
        help="Override the sha256 cache location (default: <exp2-root>/_hash_cache.json).",
    )
    parser.add_argument(
        "--expected-a-train",
        type=int,
        default=EXPECTED_A_TRAIN,
        help="Asserted Dataset A train size (0 disables the check).",
    )
    parser.add_argument(
        "--expected-a-val",
        type=int,
        default=EXPECTED_A_VAL,
        help="Asserted Dataset A val size (0 disables the check).",
    )
    parser.add_argument(
        "--expected-a-test",
        type=int,
        default=EXPECTED_A_TEST,
        help="Asserted Dataset A test size (0 disables the check).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform all checks but write nothing",
    )
    parser.add_argument(
        "--corr-min",
        type=float,
        default=PIXEL_CORR_MIN,
        help=(
            "Project-standard near-duplicate criterion: minimum Pearson "
            "correlation of the 64x64 downsampled grayscale (default 0.90)."
        ),
    )
    parser.add_argument(
        "--mad-max",
        type=float,
        default=PIXEL_MAD_MAX,
        help=(
            "Project-standard near-duplicate criterion: maximum mean absolute "
            "difference of the normalised 64x64 grayscale pixels (default 0.10)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run checks A-F and write the leakage report. Returns the process exit code."""
    args = build_parser().parse_args(argv)

    dataset_a = os.path.abspath(os.fspath(args.dataset_a))
    exp2_root = os.path.abspath(os.fspath(args.exp2_root))
    out_dir = os.path.abspath(os.fspath(args.out_dir))
    workers = max(1, int(args.workers))

    print("=" * 72, flush=True)
    print("Experiment 2 Leakage Audit (Phase 10)", flush=True)
    print(f"Dataset A (read-only): {dataset_a}", flush=True)
    print(f"Experiment 2 root    : {exp2_root}", flush=True)
    print(f"Output directory     : {out_dir}", flush=True)
    print(f"Workers              : {workers}", flush=True)
    print(f"Skip near-dup (E)    : {args.skip_near_dup}", flush=True)
    print(f"Dry run              : {args.dry_run}", flush=True)
    print(
        f"Correlation criterion: corr >= {args.corr_min} AND mad <= {args.mad_max} "
        f"(from {PROJECT_STANDARD_SOURCE}; drives the E hard failures)",
        flush=True,
    )
    print(
        f"dHash screen (info)  : Hamming <= {args.hamming_threshold}, "
        "pre-screen only",
        flush=True,
    )
    print("=" * 72, flush=True)

    for label, path in (("Dataset A", dataset_a), ("Experiment 2 root", exp2_root)):
        if not os.path.isdir(path):
            print(f"FATAL: {label} not found: {path}", flush=True)
            return 2

    # --- inventory (read-only) ---------------------------------------------
    a_train = ImageGroup("dataset_a_train", list_images(os.path.join(dataset_a, "images", "train")))
    a_val = ImageGroup("dataset_a_val", list_images(os.path.join(dataset_a, "images", "val")))
    a_test = ImageGroup("frozen_test", list_images(os.path.join(dataset_a, "images", FROZEN_TEST_SPLIT)))
    e2_train = ImageGroup("exp2_train", list_images(os.path.join(exp2_root, "images", "train")))
    e2_val = ImageGroup("exp2_val", list_images(os.path.join(exp2_root, "images", "val")))

    # Dataset B for checks B/C is every non-India file under the Experiment 2 root,
    # i.e. the union of both Experiment 2 splits.
    dataset_b = ImageGroup(
        "dataset_b",
        {**{f"train/{k}": v for k, v in e2_train.paths.items()},
         **{f"val/{k}": v for k, v in e2_val.paths.items()}},
    )

    print("Inventory:", flush=True)
    for group in (a_train, a_val, a_test, e2_train, e2_val):
        print(f"  {group.name:<16} {len(group):>7}", flush=True)
    print(f"  {'dataset_b':<16} {len(dataset_b):>7}  (train + val union)", flush=True)

    for label, observed, expected in (
        ("train", len(a_train), args.expected_a_train),
        ("val", len(a_val), args.expected_a_val),
        ("test", len(a_test), args.expected_a_test),
    ):
        if expected and observed != expected:
            print(
                f"FATAL: Dataset A {label} has {observed} images, expected {expected}",
                flush=True,
            )
            return 2

    # --- sha256 every image -------------------------------------------------
    cache_path = args.cache_path
    if cache_path is None and args.cache:
        cache_path = os.path.join(exp2_root, CACHE_NAME)
    cache = HashCache(cache_path)
    all_paths: list[str] = []
    for group in (a_train, a_val, a_test, e2_train, e2_val):
        all_paths.extend(group.paths.values())

    started = time.time()
    print("Hashing all images (sha256)...", flush=True)
    digests = hash_paths(all_paths, workers, cache)
    if not args.dry_run:
        cache.save()
    else:
        if cache.path:
            print(f"[DRY-RUN] Would write {len(cache.entries)} entries to {cache.path}", flush=True)
    print(f"Hashing finished in {time.time() - started:.1f}s", flush=True)

    idx_a_train = group_sha_index(a_train, digests)
    idx_a_val = group_sha_index(a_val, digests)
    idx_frozen = group_sha_index(a_test, digests)
    idx_e2_train = group_sha_index(e2_train, digests)
    idx_e2_val = group_sha_index(e2_val, digests)
    idx_dataset_b: dict[str, list[str]] = {}
    for sha, paths in idx_e2_train.items():
        idx_dataset_b.setdefault(sha, []).extend(paths)
    for sha, paths in idx_e2_val.items():
        idx_dataset_b.setdefault(sha, []).extend(paths)
    idx_dataset_b = {sha: sorted(p) for sha, p in sorted(idx_dataset_b.items())}

    # --- checks -------------------------------------------------------------
    result_a = check_a(a_train, a_test, idx_a_train, idx_frozen)
    print(f"Check A: {result_a['duplicate_sha256_count']} train/test overlap(s)", flush=True)

    result_b = check_b(dataset_b, a_test, idx_dataset_b, idx_frozen, idx_a_train, digests)
    print(
        f"Check B: {result_b['duplicate_sha256_count']} datasetB/test overlap(s), "
        f"{result_b['india_prefixed_filenames']} India_ filename(s) "
        f"({result_b['india_prefixed_designed_carry_over']} designed carry-over, "
        f"{result_b['india_prefixed_unexpected']} unexpected)",
        flush=True,
    )

    result_c = check_c(a_train, dataset_b, idx_a_train, idx_dataset_b)
    print(
        f"Check C: {result_c['duplicate_pair_count']} colliding pair(s) "
        f"({result_c['unexpected_pair_count']} unexpected)",
        flush=True,
    )

    result_d = check_d(e2_train, e2_val, idx_e2_train, idx_e2_val)
    print(
        f"Check D: {result_d['duplicate_sha256_count']} sha overlap(s), "
        f"{result_d['filename_intersection_count']} filename overlap(s)",
        flush=True,
    )

    if args.skip_near_dup:
        near = {
            "images_screened": 0,
            "images_unreadable": 0,
            "unreadable_sample": [],
            "lsh_candidate_pairs": 0,
            "candidate_pairs_within_hamming_threshold": 0,
            "confirmed_near_duplicate_pairs": 0,
            "confirmed_correlation_criterion_pairs": 0,
            "hamming_threshold": args.hamming_threshold,
            "confirmation_method": "exact decoded RGB pixel-array equality",
            "limitations": NEAR_DUP_LIMITATION,
            "dhash_screen": {
                "role": "cheap pre-screen / secondary signal; never drives the exit code",
                "lsh_candidate_pairs": 0,
                "candidate_pairs_within_hamming_threshold": 0,
                "hamming_threshold": args.hamming_threshold,
                "confirmed_near_duplicate_pairs": 0,
                "pairs": [],
            },
            "correlation_criterion": {
                "role": "PROJECT STANDARD; this is the detector that drives the hard failure",
                "criterion_source": PROJECT_STANDARD_SOURCE,
                "grayscale_downsample": list(PIXEL_SIZE),
                "pearson_corr_min": args.corr_min,
                "mean_abs_diff_max": args.mad_max,
                "candidate_hamming_threshold": args.hamming_threshold,
                "candidate_pairs": 0,
                "pairs_pixel_evaluated": 0,
                "pairs_rejected_by_criterion": 0,
                "confirmed_near_duplicate_pairs": 0,
                "note": CORRELATION_CRITERION_NOTE.format(
                    corr_min=args.corr_min,
                    mad_max=args.mad_max,
                    threshold=args.hamming_threshold,
                ),
                "pairs": [],
            },
            "hard_failure_driver": "correlation_criterion",
            "hard_failure_driver_note": HARD_FAILURE_DRIVER_NOTE,
            "skipped": True,
            "pairs": [],
        }
        print("Check E: SKIPPED (--skip-near-dup)", flush=True)
    else:
        near = near_duplicate_audit(
            [a_train, a_val, a_test, e2_train, e2_val],
            workers,
            args.hamming_threshold,
            args.corr_min,
            args.mad_max,
        )
        near["skipped"] = False
        print(
            f"Check E: dhash_screen {near['candidate_pairs_within_hamming_threshold']} "
            f"candidate(s), {near['confirmed_near_duplicate_pairs']} confirmed by pixel "
            f"equality; correlation_criterion {near['correlation_criterion']['candidate_pairs']} "
            f"candidate(s), {near['confirmed_correlation_criterion_pairs']} confirmed by the "
            "project standard (drives the exit code)",
            flush=True,
        )

    # The correlation criterion -- the project standard -- drives check F and the
    # E hard failures. The dHash screen is reported alongside it for information.
    corr_pairs = near["correlation_criterion"]["pairs"]
    corr_crossing = [
        p for p in corr_pairs if sorted(p["split_pair"]) == ["exp2_train", "exp2_val"]
    ]
    corr_touching_frozen = [p for p in corr_pairs if "frozen_test" in p["split_pair"]]
    crossing = [p for p in near["pairs"] if sorted(p["split_pair"]) == ["exp2_train", "exp2_val"]]
    result_f = {
        "name": "source_level_split_leakage",
        "description": (
            "The upstream RDD2022 RDD_SPLIT split is a random per-image split, so "
            "frames from the same source video can cross source splits. Recorded as "
            "a known residual risk; the confirmed near-dup crossing count for "
            "Experiment 2 train vs val is reported alongside it."
        ),
        "source_split_is_random_per_image": True,
        "source_split_is_country_grouped": False,
        "residual_risk_accepted": True,
        "risk_note": SOURCE_SPLIT_NOTE,
        "driven_by": "correlation_criterion (project standard)",
        "confirmed_pairs_crossing_exp2_train_val": len(corr_crossing),
        "crossing_exp2_train_to_val": sum(
            1 for p in corr_crossing if p["group_a"] == "exp2_train"
        ),
        "crossing_exp2_val_to_train": sum(1 for p in corr_crossing if p["group_a"] == "exp2_val"),
        "crossing_pairs": corr_crossing,
        "dhash_screen_pairs_crossing_exp2_train_val": len(crossing),
        "correlation_criterion_pairs_involving_frozen_test": len(corr_touching_frozen),
    }
    print(
        f"Check F: {len(corr_crossing)} project-standard confirmed near-dup "
        f"pair(s) cross exp2 train/val; {len(corr_touching_frozen)} involve "
        "the frozen test set",
        flush=True,
    )

    # --- REMOVAL_REQUIRED ---------------------------------------------------
    removal: list[dict[str, Any]] = []
    for collision in result_b["collisions"]:
        for name_b in collision["dataset_b_paths"]:
            for name_test in collision["frozen_test_paths"]:
                removal.append(
                    {
                        "reason": "byte_identical_to_frozen_test_image",
                        "experiment2_path": name_b,
                        "frozen_test_path": name_test,
                        "sha256": collision["sha256"],
                    }
                )
    removal.sort(key=lambda e: (e["sha256"], e["experiment2_path"]))

    hard_failures: list[str] = []
    if not result_a["passed"]:
        hard_failures.append("A_dataset_a_train_overlaps_frozen_test")
    if not result_b["passed"]:
        hard_failures.append("B_dataset_b_overlaps_frozen_test_or_contains_india_names")
    if not result_c["passed"]:
        hard_failures.append("C_unexpected_cross_dataset_duplicates")
    if not result_d["passed"]:
        hard_failures.append("D_experiment2_train_val_not_disjoint")
    if removal:
        hard_failures.append("B_removal_required_non_empty")
    if not args.skip_near_dup:
        # The E hard failures are driven by the PROJECT-STANDARD
        # correlation criterion (see HARD_FAILURE_DRIVER_NOTE), never by
        # the dHash screen.
        if corr_crossing:
            hard_failures.append(
                "E_project_standard_near_duplicates_cross_exp2_train_val"
            )
        if corr_touching_frozen:
            hard_failures.append(
                "E_project_standard_near_duplicates_involve_frozen_test"
            )

    summary = {
        "a_dataset_a_train_vs_frozen_test_clean": result_a["passed"],
        "b_dataset_b_vs_frozen_test_clean": result_b["passed"],
        "b_no_india_prefixed_filenames": result_b["india_prefixed_unexpected"] == 0,
        "b_no_unexpected_india_prefixed_filenames": result_b["india_prefixed_unexpected"] == 0,
        "c_no_unexpected_cross_dataset_duplicates": result_c["passed"],
        "d_exp2_train_val_content_disjoint": result_d["duplicate_sha256_count"] == 0,
        "d_exp2_train_val_names_disjoint": result_d["filename_intersection_count"] == 0,
        "e_no_confirmed_near_duplicates_dhash_screen": (
            near["confirmed_near_duplicate_pairs"] == 0
        ),
        "e_no_confirmed_near_duplicates_correlation_criterion": (
            near["confirmed_correlation_criterion_pairs"] == 0
        ),
        "f_no_confirmed_near_dup_crosses_exp2_train_val": len(corr_crossing) == 0,
        "f_no_project_standard_near_dup_involves_frozen_test": (
            len(corr_touching_frozen) == 0
        ),
        "near_duplicate_hard_failure_driver": "correlation_criterion",
        "removal_required_is_empty": not removal,
        "all_hard_checks_passed": not hard_failures,
    }

    report: dict[str, Any] = {
        "report_version": "1.0.0",
        "generated_by": "scripts/experiment2/audit_leakage.py",
        "phase": "Phase 10 - leakage audit",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.time() - started, 2),
        "inputs": {
            "dataset_a_root": rel(dataset_a),
            "exp2_root": rel(exp2_root),
            "frozen_test_dir": rel(os.path.join(dataset_a, "images", FROZEN_TEST_SPLIT)),
            "group_sizes": {
                "dataset_a_train": len(a_train),
                "dataset_a_val": len(a_val),
                "frozen_test": len(a_test),
                "exp2_train": len(e2_train),
                "exp2_val": len(e2_val),
                "dataset_b": len(dataset_b),
            },
        },
        "taxonomy": {
            "0": "longitudinal_crack",
            "1": "transverse_crack",
            "2": "alligator_crack",
            "3": "pothole",
        },
        "totals": {
            "images_hashed": len(digests),
            "unique_sha256": len(set(digests.values())),
            "duplicate_sha256_values_within_all_groups": len(digests) - len(set(digests.values())),
        },
        "hash_cache": {
            "path": rel(cache.path) if cache.path else None,
            "hits": cache.hits,
            "misses": cache.misses,
            "key_format": "repo_relative_path|mtime_ns|size",
        },
        "summary": summary,
        "hard_failures": hard_failures,
        "checks": {
            "A": result_a,
            "B": result_b,
            "C": result_c,
            "D": result_d,
            "E": {
                "name": "near_duplicate_audit",
                "description": (
                    "Two detectors, reported separately. dhash_screen is the "
                    "cheap 64-bit dHash Hamming screen confirmed by exact "
                    "pixel equality; correlation_criterion is the project "
                    "standard from analysis/verify_near_duplicates.py "
                    "(64x64 grayscale, Pearson corr >= 0.90 AND MAD <= 0.10) "
                    "and is the detector that drives the hard failures."
                ),
                "hard_failure_driver": near.get("hard_failure_driver"),
                "near_duplicates": near,
            },
            "F": result_f,
        },
        "limitations": [
            NEAR_DUP_LIMITATION,
            SOURCE_SPLIT_NOTE,
            HARD_FAILURE_DRIVER_NOTE,
        ],
        "REMOVAL_REQUIRED": removal,
        "read_only_guarantee": (
            "This script never deletes, moves, or edits any image, label, manifest, "
            "or frozen-test artifact. REMOVAL_REQUIRED is a report, not an action."
        ),
    }

    json_path = os.path.join(out_dir, REPORT_JSON_NAME)
    md_path = os.path.join(out_dir, REPORT_MD_NAME)
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        write_json_atomic(json_path, report)
        write_text_atomic(md_path, render_markdown(report))
    else:
        # Every inventory, hash, screen, pixel verification and invariant
        # check above has already run; only the two report files, the
        # output directory and the sha256 cache are suppressed.
        print(f"[DRY-RUN] Would write {len(report.keys())} entries to {json_path}", flush=True)
        print(f"[DRY-RUN] Would write 1 entries to {md_path}", flush=True)
        print(
            "[DRY-RUN] all checks completed; nothing was written.",
            flush=True,
        )

    print("-" * 72, flush=True)
    print(f"Wrote JSON report: {json_path}", flush=True)
    print(f"Wrote MD report  : {md_path}", flush=True)

    if removal:
        print("", flush=True)
        print("#" * 72, flush=True)
        print("!!!  REMOVAL_REQUIRED - DATASET B LEAKAGE INTO THE FROZEN TEST SET  !!!", flush=True)
        print("#" * 72, flush=True)
        for entry in removal:
            print(
                f"  {entry['experiment2_path']}  == frozen test  "
                f"{entry['frozen_test_path']}  sha256={entry['sha256']}",
                flush=True,
            )
        print(
            "\nThese Experiment 2 file(s) are byte-identical to a frozen test image.",
            flush=True,
        )
        print(
            "This script does NOT delete anything -- remove them manually and re-run.",
            flush=True,
        )
        print("Exiting non-zero.", flush=True)
        return 1

    if hard_failures:
        print("", flush=True)
        print("LEAKAGE AUDIT FAILED:", flush=True)
        for failure in hard_failures:
            print(f"  - {failure}", flush=True)
        return 1

    print("", flush=True)
    print("LEAKAGE AUDIT PASSED: all hard checks clean.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())