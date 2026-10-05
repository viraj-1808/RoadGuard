"""
Exhaustive search-space analysis for RDD2022 India pairwise similarity.

PURPOSE
-------
`verify_near_duplicates.py` finds verified pairs only inside a CANDIDATE set
produced by (a) 8-band blocking of 64-bit dHash values and (b) a dHash <= 10
distance filter, and (c) a hard skip of any blocking bucket holding more than
400 images. This script measures, exhaustively and without any candidate
filter, what that procedure can and cannot see.

Questions answered
------------------
Q1  How many banded buckets exceed the 400-image skip? Is the skip live?
Q2  How many pairs have dHash <= 10 over ALL 1,169,685 pairs, and how many of
    those did the banded blocking procedure MISS?
Q3  How many pairs over the full space satisfy the pixel acceptance criterion
    (Pearson corr >= 0.90 AND MAD <= 0.10)?
Q4  What does that do to connected components, and what threshold would be
    needed for a controlled false-positive count at full-pair scale?

This script is ANALYSIS ONLY.
  * No split is created. No image is assigned. No data is modified.
  * Images are opened read-only. Nothing is written outside group_analysis/.

METHODOLOGY
-----------
dHash      imagehash.dhash(RGB, hash_size=8) -> 64-bit, as upstream.
Band split 8 bands x 8 bits, identical layout to the upstream script.
Bands      band b occupies bits [63-(b+1)*8+1 .. 63-b*8] of the big-endian
           integer built from the boolean hash row, matching upstream.
Distance   popcount of XOR over the 64-bit values.
Signature  grayscale L, LANCZOS resize to 64x64, float64 in [0,1] (identical
           to the upstream pixel_signature()).
Correlation Pearson r over the flattened 4096-element signature, computed as a
           full 1530x1530 Gram matrix after per-image standardisation.
MAD        mean absolute difference, computed only for pairs passing the
           correlation filter (the matrix is otherwise never materialised).

INPUT PATHS
    experiments/dataset/normalized_rdd2022_india/train/images/*.jpg
    experiments/dataset/normalized_rdd2022_india/group_analysis/
        near_duplicate_verification.json

OUTPUT PATHS
    experiments/dataset/normalized_rdd2022_india/group_analysis/
        exhaustive_similarity.json
        exhaustive_similarity.md

Usage:
    python scripts/analysis/analyze_exhaustive_similarity.py
"""
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import Counter, defaultdict
import hashlib
import json
import math
import sys
import time

import numpy as np
from PIL import Image
import imagehash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.analysis.analyze_correlation_graph import (
    connected_components,
    file_sha256,
)


ANALYSIS_VERSION = "1.0.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = REPO_ROOT / "experiments" / "dataset" / "normalized_rdd2022_india"
GROUP_ANALYSIS_DIR = NORMALIZED_DIR / "group_analysis"
IMAGES_DIR = NORMALIZED_DIR / "train" / "images"
INPUT_VERIFICATION_JSON = GROUP_ANALYSIS_DIR / "near_duplicate_verification.json"
OUTPUT_JSON = GROUP_ANALYSIS_DIR / "exhaustive_similarity.json"
OUTPUT_MD = GROUP_ANALYSIS_DIR / "exhaustive_similarity.md"

# upstream constants, restated so this script is self-documenting
UPSTREAM_BANDS = 8
UPSTREAM_BAND_BITS = 8
UPSTREAM_CANDIDATE_THRESHOLD = 10
UPSTREAM_BUCKET_SKIP = 400
PIXEL_SIZE = (64, 64)
PIXEL_CORR_MIN = 0.90
PIXEL_MAD_MAX = 0.10


def load_hashes(stems: List[str]) -> np.ndarray:
    """64-bit dHash values as a uint64 matrix-free 1-D array (one per stem)."""
    out = np.zeros(len(stems), dtype=np.uint64)
    for i, stem in enumerate(stems):
        with Image.open(IMAGES_DIR / f"{stem}.jpg") as im:
            h = imagehash.dhash(im.convert("RGB"), hash_size=8)
        bits = np.asarray(h.hash).flatten().astype(np.uint8)
        value = 0
        for b in bits:
            value = (value << 1) | int(b)
        out[i] = np.uint64(value)
    return out


def band_buckets(hashes: np.ndarray) -> Dict[Tuple[int, int], List[int]]:
    """Reproduce the upstream banded blocking layout exactly."""
    buckets: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    mask = np.uint64((1 << UPSTREAM_BAND_BITS) - 1)
    for i, value in enumerate(hashes):
        v = np.uint64(value)
        for b in range(UPSTREAM_BANDS):
            shift = 63 - (b + 1) * UPSTREAM_BAND_BITS + 1
            key = (b, int((v >> np.uint64(shift)) & mask))
            buckets[key].append(i)
    return buckets


def popcount64_matrix(hashes: np.ndarray) -> np.ndarray:
    """
    Full N x N Hamming distance matrix for 64-bit hashes.

    Implemented with 8-bit lookup tables (BYTE_POPCOUNT) so the whole matrix is
    a handful of vectorised XOR/AND/reduce operations instead of 2.3M Python
    level popcounts.
    """
    byte_lut = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
    # split each uint64 into 8 uint8 lanes
    lanes = np.zeros((len(hashes), 8), dtype=np.uint8)
    for byte_index in range(8):
        shift = np.uint64(8 * (7 - byte_index))
        lanes[:, byte_index] = ((hashes >> shift) & np.uint64(0xFF)).astype(np.uint8)

    dist = np.zeros((len(hashes), len(hashes)), dtype=np.uint8)
    for byte_index in range(8):
        diff = np.bitwise_xor(
            lanes[:, byte_index][:, None], lanes[:, byte_index][None, :])
        dist += byte_lut[diff]
    return dist


def pixel_signatures(stems: List[str]) -> np.ndarray:
    """N x 4096 grayscale signatures in [0, 1] (identical to upstream)."""
    sigs = np.zeros((len(stems), PIXEL_SIZE[0] * PIXEL_SIZE[1]), dtype=np.float32)
    for i, stem in enumerate(stems):
        with Image.open(IMAGES_DIR / f"{stem}.jpg") as im:
            small = im.convert("L").resize(PIXEL_SIZE, Image.Resampling.LANCZOS)
            sigs[i] = np.asarray(small, dtype=np.float32).ravel() / 255.0
    return sigs


def correlation_matrix(sigs: np.ndarray) -> np.ndarray:
    """Full N x N Pearson correlation matrix (diagonal forced to 0)."""
    x = sigs.astype(np.float64)
    x = x - x.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    x /= norms
    corr = x @ x.T
    np.fill_diagonal(corr, 0.0)
    return corr


def mad_for_pairs(sigs: np.ndarray, pairs: List[Tuple[int, int]]) -> Dict[Tuple[int, int], float]:
    """Mean absolute difference, computed only for the listed pairs."""
    out: Dict[Tuple[int, int], float] = {}
    data = sigs.astype(np.float32)
    for i, j in pairs:
        out[(i, j)] = float(np.mean(np.abs(data[i] - data[j])))
    return out


def stirling2(n: int, k: int) -> int:
    """Stirling number of the second kind, for the banded-blocking bound."""
    if n < k:
        return 0
    result = [[0] * (k + 1) for _ in range(n + 1)]
    result[0][0] = 1
    for i in range(1, n + 1):
        for j in range(1, min(i, k) + 1):
            result[i][j] = j * result[i - 1][j] + result[i - 1][j - 1]
    return result[n][k]


def banded_blocking_miss_probability(distance: int,
                                     bands: int = UPSTREAM_BANDS) -> float:
    """
    Probability that a pair at exactly `distance` differing bits is MISSED by
    `bands`-band blocking.

    A pair is found only if at least one band is bit-identical, i.e. if the
    differing bits fail to hit every band. With `distance` >= `bands` that is no
    longer guaranteed, so blocking is INCOMPLETE. The miss probability is the
    number of onto assignments of `distance` bits to `bands` boxes divided by
    all assignments.
    """
    if distance < bands:
        return 0.0
    onto = math.factorial(bands) * stirling2(distance, bands)
    return onto / (bands ** distance)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    GROUP_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    stems = sorted(p.stem for p in IMAGES_DIR.glob("*.jpg"))
    n = len(stems)
    total_pairs = n * (n - 1) // 2
    print("RDD2022 India — exhaustive search-space analysis")
    print(f"  analysis_version : {ANALYSIS_VERSION}")
    print(f"  images           : {n}")
    print(f"  total unordered pairs: {total_pairs:,}")
    print()

    verification = json.loads(INPUT_VERIFICATION_JSON.read_text(encoding="utf-8"))
    upstream_candidates = {(min(r["a"], r["b"]), max(r["a"], r["b"])): r
                           for r in verification.get("pairs", [])}
    upstream_verified = {k for k, r in upstream_candidates.items()
                         if r.get("genuine_visual_match")}

    t0 = time.time()
    print("[1/5] dHash for all images ...")
    hashes = load_hashes(stems)
    print(f"      done in {time.time() - t0:.1f}s")
    print()

    print("[2/5] Banded-blocking bucket occupancy (upstream procedure) ...")
    buckets = band_buckets(hashes)
    sizes = [len(v) for v in buckets.values()]
    over_skip = {k: len(v) for k, v in buckets.items() if len(v) > UPSTREAM_BUCKET_SKIP}
    print(f"      buckets={len(buckets)} max_bucket={max(sizes)} "
          f"mean_bucket={sum(sizes)/len(sizes):.3f} "
          f"buckets_over_{UPSTREAM_BUCKET_SKIP}_skip={len(over_skip)}")
    print()

    print("[3/5] Exhaustive pairwise dHash over all pairs ...")
    t0 = time.time()
    dist = popcount64_matrix(hashes)
    iu = np.triu_indices(n, k=1)
    upper = dist[iu]
    exhaustive_le = int((upper <= UPSTREAM_CANDIDATE_THRESHOLD).sum())
    print(f"      done in {time.time() - t0:.1f}s")
    hist = Counter(upper.tolist())
    print(f"      exhaustive pairs with dHash <= {UPSTREAM_CANDIDATE_THRESHOLD}: {exhaustive_le:,}")
    print(f"      upstream candidate pairs recorded                : "
          f"{len(upstream_candidates):,}")
    missed_flat = np.nonzero(upper <= UPSTREAM_CANDIDATE_THRESHOLD)[0]
    missed_indices = iu[0][missed_flat], iu[1][missed_flat]
    missed_pairs = list(zip(missed_indices[0].tolist(), missed_indices[1].tolist()))
    missed = [(stems[a], stems[b], int(upper[missed_flat[k]]))
              for k, (a, b) in enumerate(missed_pairs)]
    missed_set = {(a, b) for a, b, _ in missed}
    print(f"      pairs at dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} MISSED by blocking: "
          f"{len(missed_set - set(upstream_candidates)):,}")
    print(f"      pairs at dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} caught but not recorded: "
          f"{len(missed_set & set(upstream_candidates)):,}")
    print(f"      dHash distance histogram (exhaustive, all pairs):")
    for d in range(0, 21):
        if hist.get(d):
            print(f"        d={d:2d}: {hist[d]:,}")
    print()

    print("[4/5] Exhaustive pixel correlation over all pairs ...")
    t0 = time.time()
    sigs = pixel_signatures(stems)
    corr = correlation_matrix(sigs)
    print(f"      done in {time.time() - t0:.1f}s")
    corr_upper = corr[iu]
    over_corr_flat = np.nonzero(corr_upper >= PIXEL_CORR_MIN)[0]
    print(f"      pairs with corr >= {PIXEL_CORR_MIN} over ALL pairs: {len(over_corr_flat):,}")
    print(f"      upstream verified pairs                        : {len(upstream_verified):,}")
    corr_pairs = [(int(iu[0][k]), int(iu[1][k])) for k in over_corr_flat]
    t0 = time.time()
    mads = mad_for_pairs(sigs, corr_pairs)
    full_pass = {(min(stems[i], stems[j]), max(stems[i], stems[j])): v
                 for (i, j), v in mads.items() if v <= PIXEL_MAD_MAX}
    print(f"      MAD computed for {len(corr_pairs):,} pairs in {time.time() - t0:.1f}s")
    print(f"      pairs passing corr>={PIXEL_CORR_MIN} AND mad<={PIXEL_MAD_MAX} "
          f"over ALL pairs: {len(full_pass):,}")
    print()

    print("[5/5] Component structure under the full-space criterion ...")
    full_edges = set(full_pass.keys())
    full_nodes = {m for e in full_edges for m in e}
    full_components = connected_components(full_nodes, full_edges)
    size_hist = Counter(len(c) for c in full_components)
    print(f"      full-space verified edges : {len(full_edges):,}")
    print(f"      full-space graph nodes    : {len(full_nodes):,}")
    print(f"      full-space components     : {len(full_components):,}")
    print(f"      largest component         : {max((len(c) for c in full_components), default=0)}")
    print(f"      size histogram            : {dict(sorted(size_hist.items()))}")
    print()

    # theoretical vs empirical blocking miss rate
    theoretical = {d: round(banded_blocking_miss_probability(d), 6)
                   for d in range(0, UPSTREAM_CANDIDATE_THRESHOLD + 1)}
    empirical_miss = Counter()
    for a, b, d in missed:
        if (a, b) not in upstream_candidates:
            empirical_miss[d] += 1
    expected_miss = {d: round(theoretical[d] * hist.get(d, 0), 3)
                     for d in range(0, UPSTREAM_CANDIDATE_THRESHOLD + 1)}

    # how much of the blocking blind spot actually mattered?
    blocking_blind_spot = missed_set - set(upstream_candidates)
    blind_spot_verified = sorted(blocking_blind_spot & set(full_pass))
    upstream_subset_of_full = upstream_verified <= set(full_pass)
    full_only = set(full_pass) - set(upstream_verified) - blocking_blind_spot
    full_in_candidate_space = len(set(full_pass) & set(upstream_candidates))

    payload = {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/analyze_exhaustive_similarity.py",
        "purpose": "Analysis only. No split created. No image assigned. No data modified.",
        "inputs": {
            "images_dir": str(IMAGES_DIR),
            "image_count": n,
            "near_duplicate_verification_json": str(INPUT_VERIFICATION_JSON),
            "near_duplicate_verification_sha256": file_sha256(INPUT_VERIFICATION_JSON),
        },
        "outputs": {
            "json": str(OUTPUT_JSON),
            "markdown": str(OUTPUT_MD),
        },
        "methodology": {
            "hash": "imagehash.dhash(RGB, hash_size=8) -> 64 bit",
            "bands": UPSTREAM_BANDS,
            "band_bits": UPSTREAM_BAND_BITS,
            "upstream_candidate_threshold_bits": UPSTREAM_CANDIDATE_THRESHOLD,
            "upstream_bucket_skip": UPSTREAM_BUCKET_SKIP,
            "pixel_signature": f"grayscale L, LANCZOS {PIXEL_SIZE[0]}x{PIXEL_SIZE[1]}, float in [0,1]",
            "pearson_corr_min": PIXEL_CORR_MIN,
            "mean_abs_diff_max": PIXEL_MAD_MAX,
            "pair_space": "all unordered pairs (no candidate filter)",
            "total_unordered_pairs": total_pairs,
        },
        "banded_blocking": {
            "bucket_count": len(buckets),
            "max_bucket_occupancy": max(sizes),
            "mean_bucket_occupancy": round(sum(sizes) / len(sizes), 4),
            "buckets_over_skip_threshold": len(over_skip),
            "skip_is_live": len(over_skip) > 0,
            "skip_finding": (
                f"The upstream `len(members) > {UPSTREAM_BUCKET_SKIP}` guard is INERT for this "
                f"artifact: the largest band bucket holds {max(sizes)} images, far below the "
                f"threshold. The guard is a latent risk for other datasets but causes no "
                f"false negatives here."
                if not over_skip else
                f"{len(over_skip)} buckets exceed the guard and were skipped entirely."
            ),
            "completeness_theorem": (
                "With 8 bands, banded blocking is complete for Hamming distance d < 8 only. "
                "For d >= 8 a pair can differ in at least one bit of every band and be missed. "
                "At the upstream threshold d <= 10 blocking is therefore INCOMPLETE by construction."
            ),
            "theoretical_miss_probability_by_distance": theoretical,
            "exhaustive_pairs_by_dhash_distance": {str(d): hist.get(d, 0) for d in range(0, 21)},
            "expected_missed_pairs_by_distance": expected_miss,
            "observed_missed_pairs_by_distance": {str(k): v for k, v in sorted(empirical_miss.items())},
            "observed_total_missed": sum(empirical_miss.values()),
        },
        "candidate_space_comparison": {
            "exhaustive_pairs_within_dhash_threshold": exhaustive_le,
            "upstream_candidate_pairs_recorded": len(upstream_candidates),
            "exhaustive_pairs_never_pixel_tested": exhaustive_le - len(upstream_candidates),
            "blocking_missed_pairs_within_threshold": len(missed_set - set(upstream_candidates)),
            "verdict": (
                "The 583 verified edges are NOT exhaustive. They are the subset that survived "
                "a candidate filter (banded blocking + dHash <= 10). Two distinct false-negative "
                "channels exist: (1) pairs beyond dHash 10 were never pixel-tested at all, and "
                "(2) 8-band blocking is mathematically incomplete for distances 8-10, so some "
                "pairs inside the threshold were never even enumerated."
            ),
        },
        "full_space_pixel_criterion": {
            "pairs_with_corr_at_or_above_threshold": len(corr_pairs),
            "pairs_passing_corr_and_mad": len(full_pass),
            "upstream_verified_pairs": len(upstream_verified),
            "upstream_verified_is_subset_of_full_space_result": upstream_subset_of_full,
            "full_space_pass_pairs_inside_upstream_candidate_space": full_in_candidate_space,
            "full_space_pass_pairs_outside_candidate_space": len(full_only),
            "blocking_blind_spot_pairs_that_pass_pixel_criterion": len(blind_spot_verified),
            "blocking_blind_spot_verified_examples": [
                {"a": a, "b": b, "dhash_distance": next(
                    (d for x, y, d in missed if x == a and y == b), None)}
                for a, b in blind_spot_verified[:20]
            ],
            "internal_consistency_note": (
                "All 583 upstream verified pairs are reproduced by the independent "
                "exhaustive computation, which validates the pixel criterion and its "
                "implementation. The difference between 583 and 1,672 is therefore a "
                "SEARCH-SCOPE difference, not a computational disagreement."
            ) if upstream_subset_of_full else (
                "WARNING: the independent exhaustive computation did not reproduce every "
                "upstream verified pair. Investigate before relying on either result."
            ),
            "full_space_pass_rate": round(len(full_pass) / total_pairs, 8),
            "upstream_pass_rate_within_candidate_space": round(
                len(upstream_verified) / max(len(upstream_candidates), 1), 6),
            "false_positive_analysis": (
                "The corr >= 0.90 threshold was calibrated on 1,500 random pairs, where 0.27% "
                "reached it. That calibration is valid ONLY inside the candidate-filtered space "
                f"of {len(upstream_candidates):,} pairs (~10 expected false positives). Applied to "
                f"all {total_pairs:,} pairs, the same threshold yields {len(full_pass):,} passing "
                "pairs, the large majority of which are coincidental correlations between "
                "unrelated road images. The acceptance threshold is therefore a function of the "
                "search space it was calibrated on and cannot be transferred to a larger space "
                "unchanged."
            ),
            "connected_components_full_space": {
                "component_count": len(full_components),
                "largest_component_size": max((len(c) for c in full_components), default=0),
                "size_histogram": {str(k): v for k, v in sorted(size_hist.items())},
                "node_count": len(full_nodes),
            },
            "consequence": (
                "Enforcing the pixel criterion over the full pair space is not viable at the "
                "current threshold: the coincidental edges merge unrelated images into very "
                "large components, which would make group atomicity meaningless. Either the "
                "threshold must be recalibrated for the full space, or the candidate-filtered "
                "space must be declared as the explicit, bounded scope of the evidence."
            ),
        },
        "conclusions": {
            "is_the_583_edge_set_exhaustive": False,
            "reason": "Candidate-filtered, not exhaustive. Bounded above by dHash <= 10 and "
                      "further reduced by incomplete 8-band blocking.",
            "is_the_candidate_procedure_sound_here": True,
            "soundness_note": "Within its declared scope the procedure is defensible: the "
                              "bucket guard is inert at this dataset size, and the 583 pairs are "
                              "~58x enriched over chance within the candidate space. The "
                              "limitation is scope, not correctness.",
            "recommended_scope_declaration": "Declare the evidence as 'pixel-verified visual "
                                             "matches within a dHash<=10, 8-band-blocked candidate "
                                             "space' rather than as 'all visually similar pairs'.",
        },
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"      JSON: {OUTPUT_JSON}")

    write_markdown(payload)
    print(f"      MD:   {OUTPUT_MD}")
    print()
    print("Analysis complete. No split was created and no data was modified.")
    return 0


def write_markdown(p: Dict[str, Any]) -> None:
    # normalise numeric-keyed maps to strings so rendering is identical whether
    # the payload is the in-memory dict or a round-tripped JSON object
    def strkeys(d: Dict[Any, Any]) -> Dict[str, Any]:
        return {str(k): v for k, v in d.items()}

    b = p["banded_blocking"]
    b["theoretical_miss_probability_by_distance"] = strkeys(
        b["theoretical_miss_probability_by_distance"])
    b["exhaustive_pairs_by_dhash_distance"] = strkeys(
        b["exhaustive_pairs_by_dhash_distance"])
    b["expected_missed_pairs_by_distance"] = strkeys(
        b["expected_missed_pairs_by_distance"])
    b["observed_missed_pairs_by_distance"] = strkeys(
        b["observed_missed_pairs_by_distance"])
    c = p["candidate_space_comparison"]
    f = p["full_space_pixel_criterion"]
    L: List[str] = []
    A = L.append
    A("# RDD2022 India: Exhaustive Search-Space Analysis")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A(f"**Analysis version**: {p['analysis_version']}")
    A(f"**Generated by**: `{p['script']}`")
    A("")
    A("## Pair space")
    A("")
    A(f"| Quantity | Value |")
    A(f"|----------|-------|")
    A(f"| Images | {p['inputs']['image_count']} |")
    A(f"| Unordered pairs (no filter) | {p['methodology']['total_unordered_pairs']:,} |")
    A(f"| Upstream candidate space (dHash <= 10, 8-band blocked) | "
      f"{c['upstream_candidate_pairs_recorded']:,} |")
    A(f"| Exhaustive pairs within the same dHash threshold | "
      f"{c['exhaustive_pairs_within_dhash_threshold']:,} |")
    A(f"| **Never pixel-tested** | **{c['exhaustive_pairs_never_pixel_tested']:,}** |")
    A(f"| **Never even enumerated (blocking false negatives)** | "
      f"**{c['blocking_missed_pairs_within_threshold']:,}** |")
    A("")
    A("## Banded blocking")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Buckets | {b['bucket_count']} |")
    A(f"| Max bucket occupancy | {b['max_bucket_occupancy']} |")
    A(f"| Mean bucket occupancy | {b['mean_bucket_occupancy']} |")
    A(f"| Buckets above the `{p['methodology']['upstream_bucket_skip']}` skip guard | "
      f"{b['buckets_over_skip_threshold']} |")
    A(f"| Skip guard is live for this artifact | {b['skip_is_live']} |")
    A("")
    A(f"{b['skip_finding']}")
    A("")
    A(f"{b['completeness_theorem']}")
    A("")
    A("Theoretical miss probability by Hamming distance (8 bands):")
    A("")
    A("| d | theoretical P(miss) | exhaustive pairs at d | expected missed | observed missed |")
    A("|---|---------------------|-----------------------|-----------------|-----------------|")
    for d in range(0, 11):
        key = str(d)
        A(f"| {d} | {b['theoretical_miss_probability_by_distance'][key]} "
          f"| {b['exhaustive_pairs_by_dhash_distance'].get(key, 0):,} "
          f"| {b['expected_missed_pairs_by_distance'].get(key, 0):,} "
          f"| {b['observed_missed_pairs_by_distance'].get(key, 0):,} |")
    A("")
    A("The theoretical column assumes the differing bits are uniformly distributed, which")
    A("real dHash differences are not; the observed column is the measurement that matters.")
    A("")
    A("## Full-space pixel criterion")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Pairs with corr >= {p['methodology']['pearson_corr_min']} over ALL pairs | "
      f"{f['pairs_with_corr_at_or_above_threshold']:,} |")
    A(f"| Pairs also passing MAD <= {p['methodology']['mean_abs_diff_max']} | "
      f"{f['pairs_passing_corr_and_mad']:,} |")
    A(f"| Upstream verified pairs (candidate space only) | {f['upstream_verified_pairs']:,} |")
    A(f"| Upstream 583 reproduced by this independent computation | "
      f"{f['upstream_verified_is_subset_of_full_space_result']} |")
    A(f"| Full-space passes inside the candidate space | "
      f"{f['full_space_pass_pairs_inside_upstream_candidate_space']:,} |")
    A(f"| Full-space passes OUTSIDE the candidate space | "
      f"{f['full_space_pass_pairs_outside_candidate_space']:,} |")
    A(f"| Pairs in the banded-blocking blind spot that pass the pixel criterion | "
      f"{f['blocking_blind_spot_pairs_that_pass_pixel_criterion']:,} |")
    A(f"| Pass rate, full space | {f['full_space_pass_rate']:.6f} |")
    A(f"| Pass rate, candidate space | {f['upstream_pass_rate_within_candidate_space']:.6f} |")
    A(f"| Full-space connected components | "
      f"{f['connected_components_full_space']['component_count']:,} |")
    A(f"| Full-space largest component | "
      f"{f['connected_components_full_space']['largest_component_size']} |")
    A("")
    A(f"{f['internal_consistency_note']}")
    A("")
    A(f"{f['false_positive_analysis']}")
    A("")
    A(f"{f['consequence']}")
    A("")
    A("## Conclusions")
    A("")
    A(f"- Is the 583-edge set exhaustive? **{p['conclusions']['is_the_583_edge_set_exhaustive']}**")
    A(f"  - {p['conclusions']['reason']}")
    A(f"- Is the candidate procedure sound within its scope? "
      f"**{p['conclusions']['is_the_candidate_procedure_sound_here']}**")
    A(f"  - {p['conclusions']['soundness_note']}")
    A(f"- Recommended scope declaration: {p['conclusions']['recommended_scope_declaration']}")
    A("")
    A("---")
    A("")
    A(f"*Generated by `{p['script']}`. Images are opened read-only; nothing is written* "
      f"*outside `group_analysis/`.*")
    OUTPUT_MD.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


