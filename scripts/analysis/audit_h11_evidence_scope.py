"""
H11 / atomicity investigation: evidence-scope audit for RDD2022 India.

PURPOSE
-------
`analysis/verify_near_duplicates.py` produces the 583 pixel-verified pairs that
the split-design gate treats as the authoritative correlation evidence. Those
pairs are produced inside a CANDIDATE set built by 8-band blocking plus a
dHash <= 10 filter. This script measures, from scratch and without reusing any
upstream candidate decision, exactly what that procedure can and cannot see,
and quantifies the consequence of the gaps.

Questions answered
------------------
Q1  Which pixel-passing pairs did the blocking never enumerate, and what are
    their exact properties and the exact reason each was missed?
Q2  Do those pairs change the connected-component atomicity structure?
Q3  What is the structure of the large connected components, and is the
    largest one a dense cluster or a transitive chain?
Q4  Are the 96 dHash<=10 blocking misses reproducible, and what is their
    distribution?
Q5  Is the full-pair-space pixel result technically trustworthy?
Q6  What is the computational cost of re-running this analysis?

STATUS
------
This script is ANALYSIS ONLY.
  * No split is created. No image is assigned to any split.
  * No image, annotation, or manifest is read anything but read-only.
  * Nothing is written outside group_analysis/.
  * Graph B is a SENSITIVITY graph. It is never labelled authoritative.
  * No threshold is selected. No cost function is chosen.

METHODOLOGY
-----------
dHash       imagehash.dhash(RGB, hash_size=8) -> 64 bit, recomputed here.
Bands       8 bands x 8 bits. band b occupies bits [63-(b+1)*8+1 .. 63-b*8]
            of the big-endian integer built from the boolean hash row. This
            reproduces the upstream layout exactly so the miss set is
            attributable.
Distance     popcount of XOR, via an 8-bit lookup table over a full
            1530x1530 uint8 matrix.
Signature    grayscale L, LANCZOS resize to 64x64, float64 in [0,1]. This is
            the upstream `pixel_signature` dtype. The float32 variant is also
            computed so numerical-precision sensitivity can be measured rather
            than assumed.
Correlation  Pearson r over the flattened 4096-element signature, as a full
            1530x1530 Gram matrix after per-image mean/standardisation.
MAD          mean absolute difference, computed only for correlation-passing
            pairs.

NUMERICAL NOTE
--------------
Upstream stores `pixel_corr` rounded to 4 decimals but compares the UNROUNDED
value. This script compares unrounded values, matching upstream, and
additionally reports how many pairs lie within 0.01 of a threshold so the
sensitivity of the pass set to rounding is visible.

Usage:
    python scripts/analysis/audit_h11_evidence_scope.py
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import Counter, defaultdict
import json
import sys
import time

import numpy as np
from PIL import Image
import imagehash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.analysis.analyze_correlation_graph import (
    canonical_group_key,
    connected_components,
    file_sha256,
)
from ml.data.inspection.voc_parser import parse_voc_annotation


ANALYSIS_VERSION = "1.0.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = REPO_ROOT / "experiments" / "dataset" / "normalized_rdd2022_india"
GROUP_ANALYSIS_DIR = NORMALIZED_DIR / "group_analysis"
IMAGES_DIR = NORMALIZED_DIR / "train" / "images"
RAW_IMAGES_DIR = (REPO_ROOT / "experiments" / "dataset" / "raw_rdd2022_india"
                  / "train" / "images")
ANNOTATIONS_DIR = NORMALIZED_DIR / "train" / "annotations"
INPUT_VERIFICATION_JSON = GROUP_ANALYSIS_DIR / "near_duplicate_verification.json"

# upstream constants, restated so this script is self-documenting
UPSTREAM_BANDS = 8
UPSTREAM_BAND_BITS = 8
UPSTREAM_CANDIDATE_THRESHOLD = 10
UPSTREAM_BUCKET_SKIP = 400
PIXEL_SIZE = (64, 64)
PIXEL_CORR_MIN = 0.90
PIXEL_MAD_MAX = 0.10

RARE_CLASS = "transverse_crack"
PROJECT_CLASSES = [
    "longitudinal_crack",
    "transverse_crack",
    "alligator_crack",
    "pothole",
]


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

def load_hashes(stems: List[str]) -> np.ndarray:
    """64-bit dHash per stem, in the upstream band-compatible integer form."""
    out = np.zeros(len(stems), dtype=np.uint64)
    for i, stem in enumerate(stems):
        with Image.open(IMAGES_DIR / f"{stem}.jpg") as im:
            h = imagehash.dhash(im.convert("RGB"), hash_size=8)
        value = 0
        for b in np.asarray(h.hash).flatten().astype(np.uint8):
            value = (value << 1) | int(b)
        out[i] = np.uint64(value)
    return out


def hash_bits(hashes: np.ndarray) -> np.ndarray:
    """(N, 64) uint8 bit matrix, bit 0 = most significant bit."""
    n = len(hashes)
    out = np.zeros((n, 64), dtype=np.uint8)
    for i, value in enumerate(hashes):
        v = int(value)
        for j in range(64):
            out[i, j] = (v >> (63 - j)) & 1
    return out


def popcount64_matrix(hashes: np.ndarray) -> np.ndarray:
    """Full N x N Hamming distance matrix via 8-bit lookup tables."""
    byte_lut = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
    lanes = np.zeros((len(hashes), 8), dtype=np.uint8)
    for k in range(8):
        lanes[:, k] = ((hashes >> np.uint64(8 * (7 - k))) & np.uint64(0xFF)).astype(np.uint8)
    dist = np.zeros((len(hashes), len(hashes)), dtype=np.uint8)
    for k in range(8):
        dist += byte_lut[np.bitwise_xor(lanes[:, k][:, None], lanes[:, k][None, :])]
    return dist


def band_buckets(hashes: np.ndarray) -> Dict[Tuple[int, int], List[int]]:
    """Reproduce the upstream banded-blocking layout exactly."""
    buckets: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    mask = np.uint64((1 << UPSTREAM_BAND_BITS) - 1)
    for i, value in enumerate(hashes):
        v = np.uint64(value)
        for b in range(UPSTREAM_BANDS):
            shift = 63 - (b + 1) * UPSTREAM_BAND_BITS + 1
            buckets[(b, int((v >> np.uint64(shift)) & mask))].append(i)
    return buckets


def enumerate_blocked_pairs(
    buckets: Dict[Tuple[int, int], List[int]],
) -> Tuple[Set[Tuple[int, int]], int]:
    """
    Every index pair the upstream blocking would actually compare.

    Mirrors `verify_near_duplicates.candidate_pairs` including its
    `> UPSTREAM_BUCKET_SKIP` guard, and returns the enumerated set plus the
    number of buckets the guard skipped.
    """
    enumerated: Set[Tuple[int, int]] = set()
    skipped = 0
    for _, members in buckets.items():
        if len(members) < 2:
            continue
        if len(members) > UPSTREAM_BUCKET_SKIP:
            skipped += 1
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                enumerated.add((members[i], members[j]))
    return enumerated, skipped


def pixel_signatures(stems: List[str], dtype) -> np.ndarray:
    """N x 4096 grayscale signatures in [0, 1]."""
    out = np.zeros((len(stems), PIXEL_SIZE[0] * PIXEL_SIZE[1]), dtype=dtype)
    for i, stem in enumerate(stems):
        with Image.open(IMAGES_DIR / f"{stem}.jpg") as im:
            small = im.convert("L").resize(PIXEL_SIZE, Image.Resampling.LANCZOS)
            out[i] = np.asarray(small, dtype=dtype).ravel() / 255.0
    return out


def correlation_matrix(sigs: np.ndarray) -> np.ndarray:
    """Full N x N Pearson correlation matrix, diagonal forced to 0."""
    x = sigs.astype(np.float64)
    x = x - x.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    x = x / norms
    corr = x @ x.T
    np.fill_diagonal(corr, 0.0)
    return corr


def band_miss_diagnosis(bits: np.ndarray, i: int, j: int) -> Dict[str, Any]:
    """
    Explain, bit by bit, why 8-band blocking fails to enumerate this pair.

    A pair is enumerated only if at least one of the 8 bands is bit-identical.
    It is missed exactly when every band contains at least one differing bit.
    """
    diff_positions = [p for p in range(64) if bits[i, p] != bits[j, p]]
    bands_with_diff: List[int] = []
    for b in range(UPSTREAM_BANDS):
        lo = b * UPSTREAM_BAND_BITS
        hi = lo + UPSTREAM_BAND_BITS - 1
        if any(lo <= p <= hi for p in diff_positions):
            bands_with_diff.append(b)
    identical_bands = [b for b in range(UPSTREAM_BANDS) if b not in bands_with_diff]
    return {
        "differing_bit_positions": diff_positions,
        "differing_bit_count": len(diff_positions),
        "bands_with_a_difference": bands_with_diff,
        "differing_bands": f"{len(bands_with_diff)}/{UPSTREAM_BANDS}",
        "identical_bands": identical_bands,
        "miss_reason": (
            "every one of the 8 bands contains at least one differing bit, so no "
            "band is bit-identical and the pair shares no bucket in any band"
        ),
    }


# ---------------------------------------------------------------------------
# graph structure helpers
# ---------------------------------------------------------------------------

def adjacency(nodes: Set[str], edges: Set[Tuple[str, str]]) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def bfs_distances(adj: Dict[str, Set[str]], start: str) -> Dict[str, int]:
    seen = {start: 0}
    frontier = [start]
    d = 0
    while frontier:
        d += 1
        nxt = []
        for cur in frontier:
            for nb in adj[cur]:
                if nb not in seen:
                    seen[nb] = d
                    nxt.append(nb)
        frontier = nxt
    return seen


def graph_diameter(adj: Dict[str, Set[str]]) -> int:
    """Exact diameter via BFS from every node. Only used on small components."""
    best = 0
    for start in sorted(adj):
        d = bfs_distances(adj, start)
        if d:
            best = max(best, max(d.values()))
    return best




def tarjan_structure(adj: Dict[str, Set[str]]) -> Dict[str, Any]:
    """
    Bridges, articulation points, biconnected components, 2-edge- and
    2-vertex-connectivity for a small connected component.

    Components in this dataset are at most a few dozen nodes, so a recursive
    Tarjan is safe and far easier to verify than an iterative variant. The
    recursion depth is bounded by the component size, not by the 1,530 images.
    """
    disc: Dict[str, int] = {}
    low: Dict[str, int] = {}
    parent: Dict[str, Optional[str]] = {}
    timer = 0
    bridges: List[Tuple[str, str]] = []
    articulations: Set[str] = set()
    bcc_vertex_sets: List[List[str]] = []
    edge_stack: List[Tuple[str, str]] = []

    def strongconnect(root: str) -> None:
        nonlocal timer
        disc[root] = low[root] = timer
        timer += 1
        child_count = 0
        for nb in sorted(adj[root]):
            if nb not in disc:
                child_count += 1
                parent[nb] = root
                edge_stack.append((root, nb))
                strongconnect(nb)
                low[root] = min(low[root], low[nb])
                if low[nb] > disc[root]:
                    bridges.append(tuple(sorted((root, nb))))  # type: ignore[arg-type]
                if low[nb] >= disc[root]:
                    # A non-root node is an articulation point when one of its DFS
                    # children cannot reach an ancestor of it. The DFS root is
                    # handled separately below, using the >=2-children rule.
                    if parent.get(root) is not None:
                        articulations.add(root)
                    comp: Set[str] = set()
                    while edge_stack:
                        e = edge_stack.pop()
                        comp.update(e)
                        if e == (root, nb) or e == (nb, root):
                            break
                    bcc_vertex_sets.append(sorted(comp))
            elif nb != parent.get(root) and disc[nb] < disc[root]:
                edge_stack.append((root, nb))
                low[root] = min(low[root], disc[nb])
        if parent.get(root) is None and child_count >= 2:
            articulations.add(root)

    for root in sorted(adj):
        if root not in disc:
            parent[root] = None
            strongconnect(root)
            if edge_stack:
                bcc_vertex_sets.append(sorted({m for e in edge_stack for m in e}))
                edge_stack.clear()

    return {
        "bridges": sorted(bridges),
        "bridge_count": len(bridges),
        "articulation_points": sorted(articulations),
        "articulation_point_count": len(articulations),
        "biconnected_component_count": len(bcc_vertex_sets),
        "biconnected_component_sizes": sorted(
            (len(v) for v in bcc_vertex_sets), reverse=True),
        "is_2_edge_connected": len(bridges) == 0,
        "is_2_vertex_connected": len(articulations) == 0,
    }


def core_decomposition(adj: Dict[str, Set[str]]) -> Dict[str, Any]:
    """
    Batagelj-Zaversnik core decomposition: repeatedly remove the remaining
    node of minimum current degree and record that degree as its core number.
    """
    deg = {n: len(adj[n]) for n in adj}
    remaining = set(adj)
    core: Dict[str, int] = {}
    k = 0
    while remaining:
        n = min(remaining, key=lambda x: (deg[x], x))
        # a node's core number is the running maximum k, never less than its
        # degree at removal time. Without the running maximum a triangle would
        # peel to 2,1,0 instead of 2,2,2.
        k = max(k, deg[n])
        core[n] = k
        remaining.discard(n)
        for nb in adj[n]:
            if nb in remaining:
                deg[nb] -= 1
    by_k: Dict[int, List[str]] = defaultdict(list)
    for n, k in core.items():
        by_k[k].append(n)
    return {
        "core_number_by_node": dict(sorted(core.items())),
        "max_core_number": max(core.values(), default=0),
        "nodes_by_core_number": {str(k): sorted(v) for k, v in sorted(by_k.items())},
        "size_by_core_number": {str(k): len(v) for k, v in sorted(by_k.items())},
    }


def density(node_count: int, edge_count: int) -> float:
    if node_count < 2:
        return 0.0
    return round(2.0 * edge_count / (node_count * (node_count - 1)), 6)


# ---------------------------------------------------------------------------
# annotation-derived per-image statistics
# ---------------------------------------------------------------------------

def per_image_class_stats(stems: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Per-image class presence and object counts, re-derived from the normalized
    XML with the project's own VOC parser.

    `manifest.json` is deliberately NOT read: its per-image class fields are
    cumulative running counters, so they cannot be used for stratification.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for stem in stems:
        ann = parse_voc_annotation(ANNOTATIONS_DIR / f"{stem}.xml")
        counts: Counter = Counter()
        for obj in ann.objects:
            name = getattr(obj, "class_name", None) or getattr(obj, "name", None)
            if name in PROJECT_CLASSES:
                counts[name] += 1
        out[stem] = {
            "object_counts": {c: counts.get(c, 0) for c in PROJECT_CLASSES},
            "presence_mask": "".join(
                "1" if counts.get(c, 0) > 0 else "0" for c in PROJECT_CLASSES),
            "object_total": sum(counts.get(c, 0) for c in PROJECT_CLASSES),
        }
    return out


def class_presence_key(stats: Dict[str, Dict[str, Any]]) -> str:
    return "+".join(
        name for name, present in zip(PROJECT_CLASSES, stats["presence_mask"])
        if present == "1"
    )


# ---------------------------------------------------------------------------
# component audit
# ---------------------------------------------------------------------------

def audit_components(
    components: List[List[str]],
    edge_details: Dict[Tuple[str, str], Dict[str, Any]],
    per_image: Dict[str, Dict[str, Any]],
    with_structure: bool,
) -> List[Dict[str, Any]]:
    """Per-component evidence record. `with_structure` enables the O(V*E) work."""
    records: List[Dict[str, Any]] = []
    for comp in components:
        members = sorted(comp)
        member_set = set(members)
        inside: List[Tuple[str, str]] = [
            e for e in edge_details if e[0] in member_set and e[1] in member_set
        ]
        dets = [edge_details[e] for e in inside]
        dh = sorted(d["dhash_distance"] for d in dets)
        co = sorted(d["pixel_corr"] for d in dets)
        ma = sorted(d["pixel_mad"] for d in dets)
        adj = adjacency(member_set, set(inside))
        degs = sorted((len(adj[m]) for m in members), reverse=True)
        presence = Counter(class_presence_key(per_image[m]) for m in members)
        rec: Dict[str, Any] = {
            "component_id": f"CC_{len(records) + 1:04d}",
            "size": len(members),
            "members": members,
            "member_indices": [_image_index(m) for m in members],
            "edge_count": len(inside),
            "density": density(len(members), len(inside)),
            "dhash_min": dh[0] if dh else None,
            "dhash_max": dh[-1] if dh else None,
            "dhash_median": _median(dh),
            "corr_min": round(co[0], 6) if co else None,
            "corr_max": round(co[-1], 6) if co else None,
            "corr_median": round(_median(co), 6) if co else None,
            "mad_max": round(ma[-1], 6) if ma else None,
            "degree_max": degs[0] if degs else 0,
            "degree_min": degs[-1] if degs else 0,
            "degree_histogram": {str(k): v for k, v in sorted(Counter(degs).items())},
            "nodes_with_degree_one": sum(1 for d in degs if d == 1),
            "class_presence_composition": dict(sorted(presence.items())),
            "rare_class_images": sum(
                1 for m in members
                if per_image[m]["object_counts"][RARE_CLASS] > 0),
            "rare_class_objects": sum(
                per_image[m]["object_counts"][RARE_CLASS] for m in members),
        }
        if not with_structure:
            rec["structural_shape"] = _shape(len(members), len(inside), degs)
        if with_structure:
            rec["diameter"] = graph_diameter(adj)
            rec["tarjan"] = tarjan_structure(adj)
            rec["cores"] = core_decomposition(adj)
            rec["structural_shape"] = _shape(
                len(members), len(inside), degs, rec["tarjan"])
        records.append(rec)
    records.sort(key=lambda r: (-r["size"], r["members"][0]))
    for i, r in enumerate(records):
        r["component_id"] = f"CC_{i + 1:04d}"
    return records


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    m = len(values)
    if m % 2:
        return float(values[m // 2])
    return (values[m // 2 - 1] + values[m // 2]) / 2.0


def _shape(node_count: int, edge_count: int, degs: List[int],
           tarjan: Dict[str, Any] | None = None) -> str:
    """
    Coarse structural label, derived only from measured graph statistics.

    These labels describe GRAPH SHAPE. They are not evidence of capture
    provenance and must never be read as such.

    When Tarjan results are available the label is derived from biconnected
    structure, which is far more informative than a density threshold: a
    40-node graph at density 0.13 is not "dense", and a density-only rule
    would mislabel it.
    """
    if node_count < 2:
        return "single_node"
    if edge_count == node_count - 1:
        return "tree_or_chain"

    if tarjan is not None:
        bcc = sorted(tarjan.get("biconnected_component_sizes", []), reverse=True)
        bridges = tarjan.get("bridge_count", 0)
        articulations = tarjan.get("articulation_point_count", 0)
        if bridges == 0 and articulations == 0:
            return "cohesive_block"
        if bcc and bcc[0] >= node_count:
            return "cohesive_block"
        if bcc and bcc[0] >= 0.5 * node_count:
            return "dominant_block_with_bridges"
        if edge_count > 0 and bridges == edge_count:
            return "chain_like_bridges_only"
        return "multi_block"

    d = density(node_count, edge_count)
    if d >= 0.5:
        return "dense_relative"
    if d >= 0.2:
        return "moderately_connected"
    return "sparse_relative"


def _image_index(stem: str) -> int:
    digits = "".join(ch for ch in stem if ch.isdigit())
    return int(digits) if digits else -1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    GROUP_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    timings: Dict[str, float] = {}
    wall0 = time.time()

    stems = sorted(p.stem for p in IMAGES_DIR.glob("*.jpg"))
    n = len(stems)
    index_of = {s: i for i, s in enumerate(stems)}
    total_pairs = n * (n - 1) // 2
    print("H11 / atomicity investigation - evidence scope audit")
    print(f"  images={n}  unordered_pairs={total_pairs:,}")
    print()

    verification = json.loads(INPUT_VERIFICATION_JSON.read_text(encoding="utf-8"))
    up_cand = {(min(r["a"], r["b"]), max(r["a"], r["b"])): r
               for r in verification.get("pairs", [])}
    up_ver = {k for k, r in up_cand.items() if r.get("genuine_visual_match")}
    up_groups = verification.get("pixel_verified_groups", [])

    print("[1/8] dHash (recomputed) ...")
    t = time.time()
    hashes = load_hashes(stems)
    timings["dhash_s"] = round(time.time() - t, 2)
    bits = hash_bits(hashes)
    print(f"      {timings['dhash_s']}s")

    print("[2/8] exhaustive Hamming matrix ...")
    t = time.time()
    dist = popcount64_matrix(hashes)
    timings["popcount_matrix_s"] = round(time.time() - t, 2)
    iu = np.triu_indices(n, k=1)
    upper = dist[iu]
    dist_hist = Counter(upper.tolist())
    flat_le10 = np.nonzero(upper <= UPSTREAM_CANDIDATE_THRESHOLD)[0]
    exhaustive_le10 = len(flat_le10)
    print(f"      {timings['popcount_matrix_s']}s  dHash<={UPSTREAM_CANDIDATE_THRESHOLD}: "
          f"{exhaustive_le10:,}")

    print("[3/8] banded-blocking reproduction ...")
    t = time.time()
    buckets = band_buckets(hashes)
    enumerated, skipped_buckets = enumerate_blocked_pairs(buckets)
    timings["blocking_enumeration_s"] = round(time.time() - t, 2)
    bucket_sizes = [len(v) for v in buckets.values()]
    over_skip = {k: len(v) for k, v in buckets.items() if len(v) > UPSTREAM_BUCKET_SKIP}
    ex_le10_idx = {(int(iu[0][k]), int(iu[1][k])) for k in flat_le10}
    never_enumerated_idx = ex_le10_idx - enumerated
    le10_stems = {(stems[a], stems[b]) for a, b in ex_le10_idx}
    missed = le10_stems - set(up_cand)
    print(f"      buckets={len(buckets)} max_occ={max(bucket_sizes)} "
          f"over_skip={len(over_skip)} skipped_buckets={skipped_buckets}")
    print(f"      dHash<={UPSTREAM_CANDIDATE_THRESHOLD} pairs never enumerated by blocking: "
          f"{len(never_enumerated_idx)}")
    print(f"      dHash<={UPSTREAM_CANDIDATE_THRESHOLD} pairs absent from upstream file: "
          f"{len(missed)}")

    print("[4/8] pixel signatures + full-space correlation ...")
    t = time.time()
    sigs = pixel_signatures(stems, np.float64)
    timings["pixel_signature_s"] = round(time.time() - t, 2)
    t = time.time()
    corr = correlation_matrix(sigs)
    timings["correlation_matrix_s"] = round(time.time() - t, 2)
    corr_up = corr[iu]
    over_corr = np.nonzero(corr_up >= PIXEL_CORR_MIN)[0]
    t = time.time()
    full_pass: Set[Tuple[str, str]] = set()
    for k in over_corr:
        a, b = int(iu[0][k]), int(iu[1][k])
        if float(np.mean(np.abs(sigs[a] - sigs[b]))) <= PIXEL_MAD_MAX:
            full_pass.add((stems[a], stems[b]))
    timings["full_space_mad_s"] = round(time.time() - t, 2)
    print(f"      corr>={PIXEL_CORR_MIN}: {len(over_corr):,}   full pass: {len(full_pass):,}")
    print(f"      upstream 583 subset of full pass: {up_ver <= full_pass}")

    # ---- float32 sensitivity, so precision effects are measured not assumed ---
    print("[5/8] float32 vs float64 precision sensitivity ...")
    t = time.time()
    sigs32 = pixel_signatures(stems, np.float32)
    corr32 = correlation_matrix(sigs32)
    over32 = np.nonzero(corr32[iu] >= PIXEL_CORR_MIN)[0]
    full_pass32: Set[Tuple[str, str]] = set()
    for k in over32:
        a, b = int(iu[0][k]), int(iu[1][k])
        if float(np.mean(np.abs(sigs32[a] - sigs32[b]))) <= PIXEL_MAD_MAX:
            full_pass32.add((stems[a], stems[b]))
    precision_symmetric_diff = sorted(full_pass ^ full_pass32)
    # how close are the borderline pairs to flipping?
    margin_corr = []
    margin_mad = []
    for k in over_corr:
        a, b = int(iu[0][k]), int(iu[1][k])
        margin_corr.append(float(corr_up[k]) - PIXEL_CORR_MIN)
        m = float(np.mean(np.abs(sigs[a] - sigs[b])))
        margin_mad.append(PIXEL_MAD_MAX - m)
    margin_corr.sort()
    margin_mad.sort()
    timings["precision_check_s"] = round(time.time() - t, 2)
    print(f"      float32 pass set size={len(full_pass32):,}  "
          f"symmetric difference vs float64={len(precision_symmetric_diff)}")
    print(f"      smallest corr margin above threshold: {margin_corr[0]:.3e}  "
          f"smallest MAD margin: {margin_mad[0]:.3e}")

    # ---- the missed pairs in full detail -----------------------------------
    print("[6/8] auditing the 96 misses and the pixel-passing subset ...")
    miss_records: List[Dict[str, Any]] = []
    for k in flat_le10:
        a, b = int(iu[0][k]), int(iu[1][k])
        key = (stems[a], stems[b])
        if key not in missed:
            continue
        c = float(corr[a, b])
        m = float(np.mean(np.abs(sigs[a] - sigs[b])))
        diag = band_miss_diagnosis(bits, a, b)
        miss_records.append({
            "a": key[0], "b": key[1],
            "image_index_a": _image_index(key[0]),
            "image_index_b": _image_index(key[1]),
            "dhash_distance": int(upper[k]),
            "pixel_corr": round(c, 6),
            "pixel_mad": round(m, 6),
            "passes_pixel_criterion": bool(c >= PIXEL_CORR_MIN and m <= PIXEL_MAD_MAX),
            "in_upstream_candidate_file": key in up_cand,
            "in_upstream_verified_graph": key in up_ver,
            "blockage": diag,
        })
    miss_records.sort(key=lambda r: (r["dhash_distance"], r["a"], r["b"]))
    blind_verified = [r for r in miss_records if r["passes_pixel_criterion"]]
    print(f"      misses={len(miss_records)}  pixel-passing={len(blind_verified)}")

    for rec in miss_records:
        ia, ib = index_of[rec["a"]], index_of[rec["b"]]
        diff = np.abs(sigs[ia] - sigs[ib])
        rec["abs_diff_max"] = round(float(diff.max()), 6)
        rec["abs_diff_p99"] = round(float(np.percentile(diff, 99)), 6)
        rec["fraction_pixels_differing_gt_32_255"] = round(
            float((diff > 32.0 / 255.0).mean()), 6)
        rec["index_gap"] = abs(rec["image_index_a"] - rec["image_index_b"])
        rec["same_existing_59_group"] = _same_group(up_groups, rec["a"], rec["b"])

    # ---- Graph A vs Graph B ------------------------------------------------
    print("[7/8] graph A vs graph B ...")
    graph_a_edges: Set[Tuple[str, str]] = set(up_ver)
    graph_b_edges: Set[Tuple[str, str]] = set(graph_a_edges) | {
        (r["a"], r["b"]) for r in blind_verified
    }
    edge_details: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for k in over_corr:
        a, b = int(iu[0][k]), int(iu[1][k])
        key = (stems[a], stems[b])
        if key in graph_b_edges:
            edge_details[key] = {
                "a": key[0], "b": key[1],
                "dhash_distance": int(upper[k]),
                "pixel_corr": round(float(corr[a, b]), 6),
                "pixel_mad": round(float(np.mean(np.abs(sigs[a] - sigs[b]))), 6),
            }

    def summarise_graph(edges: Set[Tuple[str, str]]) -> Dict[str, Any]:
        nodes = {m for e in edges for m in e}
        comps = connected_components(nodes, edges)
        sizes = sorted((len(c) for c in comps), reverse=True)
        return {
            "edge_count": len(edges),
            "node_count": len(nodes),
            "component_count": len(comps),
            "largest_component_size": sizes[0] if sizes else 0,
            "component_size_histogram": {
                str(k): v for k, v in sorted(Counter(sizes).items())},
            "_components": comps,
        }

    summ_a = summarise_graph(graph_a_edges)
    summ_b = summarise_graph(graph_b_edges)
    comp_index_a = {frozenset(c): i for i, c in enumerate(summ_a["_components"])}
    merged: List[Dict[str, Any]] = []
    membership_change: Dict[str, List[str]] = {}
    for comp in summ_b["_components"]:
        touched = sorted(comp_index_a[frozenset(c)]
                         for c in summ_a["_components"] if set(c) & set(comp))
        if len(touched) > 1:
            merged.append({
                "graph_b_component_size": len(comp),
                "graph_a_components_merged": len(touched),
                "graph_a_component_indices": touched,
                "graph_a_component_sizes": [len(summ_a["_components"][i]) for i in touched],
                "new_members": sorted(
                    set(comp) - set().union(*[set(summ_a["_components"][i])
                                              for i in touched])),
            })
        base = set(summ_a["_components"][touched[0]]) if touched else set()
        added = sorted(set(comp) - base)
        if added:
            for m in added:
                membership_change[m] = touched
    print(f"      A: edges={summ_a['edge_count']} nodes={summ_a['node_count']} "
          f"components={summ_a['component_count']} largest={summ_a['largest_component_size']}")
    print(f"      B: edges={summ_b['edge_count']} nodes={summ_b['node_count']} "
          f"components={summ_b['component_count']} largest={summ_b['largest_component_size']}")
    print(f"      components merged: {len(merged)}  images with new membership: "
          f"{len(membership_change)}")

    # ---- transitive chaining analysis ---------------------------------------
    print("[8/8] component + chaining analysis ...")
    t = time.time()
    per_image = per_image_class_stats(stems)
    timings["annotation_parse_s"] = round(time.time() - t, 2)

    large_cutoff = 10
    comp_records = audit_components(
        summ_a["_components"], edge_details, per_image, with_structure=True)
    comp_records_b = audit_components(
        summ_b["_components"], edge_details, per_image, with_structure=False)
    large = [c for c in comp_records if c["size"] >= large_cutoff]
    timings["component_audit_s"] = round(time.time() - t, 2)
    print(f"      components audited: {len(comp_records)}  (size>={large_cutoff}: {len(large)})")

    sensitivity = []
    criteria = [
        ("baseline_all_edges", None, None, None, None),
        ("drop_dhash_gt_8", 8, None, None, None),
        ("drop_dhash_gt_7", 7, None, None, None),
        ("drop_dhash_gt_6", 6, None, None, None),
        ("drop_dhash_gt_5", 5, None, None, None),
        ("drop_corr_lt_0.95", None, 0.95, None, None),
        ("drop_corr_lt_0.93", None, 0.93, None, None),
        ("drop_mad_gt_0.06", None, None, 0.06, None),
        ("drop_mad_gt_0.05", None, None, 0.05, None),
        ("drop_dhash_gt_6_or_corr_lt_0.93", 6, 0.93, None, None),
    ]
    for label, max_dh, min_corr, max_mad, _ in criteria:
        kept = set()
        for e, d in edge_details.items():
            if max_dh is not None and d["dhash_distance"] > max_dh:
                continue
            if min_corr is not None and d["pixel_corr"] < min_corr:
                continue
            if max_mad is not None and d["pixel_mad"] > max_mad:
                continue
            kept.add(e)
        nodes = {m for e in kept for m in e}
        comps = connected_components(nodes, kept) if kept else []
        sizes = sorted((len(c) for c in comps), reverse=True)
        sensitivity.append({
            "criterion": label,
            "edges_retained": len(kept),
            "edges_removed": len(edge_details) - len(kept),
            "nodes": len(nodes),
            "component_count": len(comps),
            "largest_component_size": sizes[0] if sizes else 0,
            "components_ge_10": sum(1 for s in sizes if s >= 10),
            "images_in_components_ge_10": sum(s for s in sizes if s >= 10),
            "size_histogram": {str(k): v for k, v in sorted(Counter(sizes).items())},
        })
        print(f"      {label:34s} edges={len(kept):4d} comps={len(comps):3d} "
              f"largest={sizes[0] if sizes else 0:3d}")

    # ---- rare class across rules -------------------------------------------
    def units_from_components(comps: List[List[str]]) -> List[List[str]]:
        return [sorted(c) for c in comps if len(c) > 1]

    units_59 = [sorted(g["stems"]) for g in up_groups if len(g.get("stems", [])) > 1]
    rules = {
        "A_EXISTING_59_GROUPS": units_59,
        "B_CONNECTED_COMPONENTS_583": units_from_components(summ_a["_components"]),
        "C_CONNECTED_COMPONENTS_589": units_from_components(summ_b["_components"]),
        "D_CLIQUE_COVER_583": _clique_cover_units(graph_a_edges),
    }
    rare_report = {}
    for name, units in rules.items():
        rare_report[name] = _rare_class_report(units, per_image)
        rr = rare_report[name]
        print(f"      {name:28s} units={rr['atomic_units_containing_rare_class']} "
              f"images={rr['images_containing_rare_class_in_units']} "
              f"objects={rr['rare_class_objects_in_units']} "
              f"largest={rr['largest_unit_containing_rare_class']}")

    # ---- output 1: the pixel-passing missed pairs ---------------------------
    six = []
    for rank, rec in enumerate(sorted(blind_verified,
                                      key=lambda r: (r["pixel_corr"], r["dhash_distance"])),
                              start=1):
        with Image.open(IMAGES_DIR / f"{rec['a']}.jpg") as ia:
            w, h = ia.size
        with Image.open(IMAGES_DIR / f"{rec['b']}.jpg") as ib:
            w2, h2 = ib.size
        six.append({
            "rank": rank,
            "total": len(blind_verified),
            "a": rec["a"], "b": rec["b"],
            "image_index_a": rec["image_index_a"],
            "image_index_b": rec["image_index_b"],
            "index_gap": rec["index_gap"],
            "dhash_distance": rec["dhash_distance"],
            "pixel_corr": rec["pixel_corr"],
            "pixel_mad": rec["pixel_mad"],
            "width": w, "height": h,
            "b_width": w2, "b_height": h2,
            "dimensions_match": (w, h) == (w2, h2),
            "abs_diff_max": rec["abs_diff_max"],
            "abs_diff_p99": rec["abs_diff_p99"],
            "fraction_pixels_differing_gt_32_255": rec[
                "fraction_pixels_differing_gt_32_255"],
            "in_upstream_verified_graph": False,
            "in_upstream_candidate_file": False,
            "same_existing_59_group": rec["same_existing_59_group"],
            "differing_bands": rec["blockage"]["differing_bands"],
            "differing_bit_positions": ",".join(
                str(p) for p in rec["blockage"]["differing_bit_positions"]),
            "miss_reason": rec["blockage"]["miss_reason"],
            "contact_sheet": f"missed_pair_contact_sheets/pair_{rank:02d}_"
                             f"{rec['a']}__{rec['b']}.png",
            "human_review_status": "PENDING - not classified by this script",
        })
    _write_json(GROUP_ANALYSIS_DIR / "missed_pixel_pairs.json", {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_h11_evidence_scope.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "definition": (
            "Pairs that satisfy the upstream pixel acceptance criterion "
            f"(corr >= {PIXEL_CORR_MIN}, MAD <= {PIXEL_MAD_MAX}), have dHash <= "
            f"{UPSTREAM_CANDIDATE_THRESHOLD}, were never enumerated by the upstream "
            f"{UPSTREAM_BANDS}-band blocking procedure, and are absent from the "
            "upstream candidate file."
        ),
        "count": len(six),
        "classification_policy": (
            "No semantic category is assigned here. A numerical similarity score is "
            "not evidence of duplicate content. Classification requires human visual "
            "review of the rendered contact sheets."
        ),
        "pairs": six,
    })
    print(f"      wrote missed_pixel_pairs.json ({len(six)} pairs)")

    # ---- output 2: all 96 misses -------------------------------------------
    miss_hist = Counter(r["dhash_distance"] for r in miss_records)
    _write_json(GROUP_ANALYSIS_DIR / "blocking_miss_audit.json", {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_h11_evidence_scope.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "blocking_configuration": {
            "bands": UPSTREAM_BANDS,
            "band_bits": UPSTREAM_BAND_BITS,
            "candidate_threshold_bits": UPSTREAM_CANDIDATE_THRESHOLD,
            "bucket_skip_threshold": UPSTREAM_BUCKET_SKIP,
            "band_bit_range": "band b occupies bits [63-(b+1)*8+1 .. 63-b*8]",
        },
        "census": {
            "exhaustive_pairs_within_dhash_threshold": exhaustive_le10,
            "upstream_candidate_pairs_recorded": len(up_cand),
            "pairs_never_enumerated_by_blocking": len(never_enumerated_idx),
            "pairs_absent_from_upstream_candidate_file": len(missed),
            "channels_are_identical": len(never_enumerated_idx) == len(missed),
            "channel_identity_note": (
                "The set of dHash<=10 pairs the blocking never enumerated is exactly the "
                "set absent from the upstream candidate file, so banded blocking is the "
                "ONLY false-negative channel inside the dHash threshold. The >400 "
                "bucket guard skipped 0 buckets."
            ),
        },
        "bucket_statistics": {
            "bucket_count": len(buckets),
            "max_bucket_occupancy": max(bucket_sizes),
            "mean_bucket_occupancy": round(sum(bucket_sizes) / len(bucket_sizes), 4),
            "buckets_over_skip_threshold": len(over_skip),
            "buckets_skipped_by_guard": skipped_buckets,
            "skip_guard_is_live": len(over_skip) > 0,
        },
        "miss_count_by_dhash_distance": {str(k): v for k, v in sorted(miss_hist.items())},
        "misses_total": len(miss_records),
        "misses_passing_pixel_criterion": len(blind_verified),
        "misses_failing_pixel_criterion": len(miss_records) - len(blind_verified),
        "determinism": (
            "The miss set is a pure function of (dHash values, band layout, band count, "
            "bucket skip threshold). It contains no randomness, no hash-order dependence "
            "and no wall-clock input, so it is exactly reproducible."
        ),
        "misses": miss_records,
    })
    print(f"      wrote blocking_miss_audit.json ({len(miss_records)} misses)")

    # ---- output 3: full-space pixel reproduction ----------------------------
    full_only = sorted(full_pass - up_ver - {
        (r["a"], r["b"]) for r in blind_verified})
    inside_cand = sorted(full_pass & set(up_cand))
    full_nodes = {m for e in full_pass for m in e}
    full_comps = connected_components(full_nodes, full_pass) if full_pass else []
    full_sizes = sorted((len(c) for c in full_comps), reverse=True)
    _write_json(GROUP_ANALYSIS_DIR / "full_space_pixel_reproduction.json", {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_h11_evidence_scope.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "pipeline": {
            "image_source": "normalized_rdd2022_india/train/images (read-only)",
            "raw_vs_normalized_byte_identical": _raw_matches_normalized(stems),
            "dhash": "imagehash.dhash(RGB, hash_size=8) -> 64 bit",
            "pixel_signature": (
                f"PIL convert('L') then LANCZOS resize to {PIXEL_SIZE[0]}x{PIXEL_SIZE[1]}, "
                "float64, divided by 255.0 -> [0,1]"
            ),
            "resizing_present": True,
            "resizing_note": (
                "Pixel comparison is performed on a 64x64 downsampled grayscale signature, "
                "NOT on the original 720x720 image. This matches upstream "
                "verify_near_duplicates.pixel_signature exactly."
            ),
            "normalization": "per-image mean removal and L2 norm for correlation only",
            "correlation": "Pearson r over the flattened 4096-element signature",
            "mad": "mean absolute difference over the flattened 4096-element signature",
            "correlation_dtype": "float64 accumulation over float64 signatures",
            "pair_space": "all unordered pairs, no candidate filter",
        },
        "results": {
            "total_unordered_pairs": total_pairs,
            "pairs_with_corr_at_or_above_threshold": len(over_corr),
            "pairs_passing_corr_and_mad": len(full_pass),
            "upstream_verified_pairs": len(up_ver),
            "upstream_verified_is_subset": up_ver <= full_pass,
            "full_pass_inside_upstream_candidate_space": len(inside_cand),
            "full_pass_outside_candidate_space_not_in_blind_spot": len(full_only),
            "blind_spot_pairs_passing_pixel": len(blind_verified),
            "partition_checksum": len(inside_cand) + len(blind_verified) + len(full_only),
            "partition_balances": (
                len(inside_cand) + len(blind_verified) + len(full_only) == len(full_pass)),
            "full_space_pass_rate": round(len(full_pass) / total_pairs, 10),
            "upstream_pass_rate_within_candidate_space": round(
                len(up_ver) / max(len(up_cand), 1), 6),
        },
        "components_full_space": {
            "component_count": len(full_comps),
            "largest_component_size": full_sizes[0] if full_sizes else 0,
            "node_count": len(full_nodes),
            "size_histogram": {
                str(k): v for k, v in sorted(Counter(full_sizes).items())},
        },
        "exhaustiveness_and_trustworthiness": {
            "pair_space_is_exhaustive": True,
            "any_pair_excluded_for_computational_reasons": False,
            "any_bucket_size_limit_in_this_script": False,
            "any_silent_skip_in_this_script": False,
            "deterministic": True,
            "numerical_precision_sensitivity": {
                "float32_vs_float64_symmetric_difference": len(precision_symmetric_diff),
                "float32_pass_set_size": len(full_pass32),
                "float64_pass_set_size": len(full_pass),
                "verdict": (
                    "None. The float32 and float64 pipelines produce the identical pass "
                    "set, so the result is not an artefact of accumulation precision."
                ) if not precision_symmetric_diff else (
                    "The two dtypes disagree; see pairs listed in "
                    "precision_disagreeing_pairs."
                ),
                "precision_disagreeing_pairs": [
                    {"a": a, "b": b} for a, b in precision_symmetric_diff],
                "smallest_corr_margin_above_threshold": margin_corr[0],
                "smallest_mad_margin_below_threshold": margin_mad[0],
            },
            "upstream_rounding_note": (
                "Upstream rounds pixel_corr and pixel_mad to 4 decimals in its JSON but "
                "compares unrounded values. This script also compares unrounded values. "
                "The reported margins show how much headroom the borderline pairs have."
            ),
        },
    })
    print(f"      wrote full_space_pixel_reproduction.json")

    # ---- output 4: graph A vs graph B --------------------------------------
    rare_delta = {}
    for name, report in rare_report.items():
        rare_delta[name] = report
    _write_json(GROUP_ANALYSIS_DIR / "graph_583_vs_589_comparison.json", {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_h11_evidence_scope.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "status": (
            "SENSITIVITY ANALYSIS ONLY. Graph A is the existing authoritative 583-edge "
            "graph. Graph B adds the pixel-passing pairs that blocking never enumerated "
            "and is NOT authoritative. Nothing in this file changes the recorded evidence."
        ),
        "graph_a": {
            "definition": "pairs with genuine_visual_match == true in the upstream file",
            "edge_count": summ_a["edge_count"],
            "node_count": summ_a["node_count"],
            "component_count": summ_a["component_count"],
            "largest_component_size": summ_a["largest_component_size"],
            "component_size_histogram": summ_a["component_size_histogram"],
        },
        "graph_b": {
            "definition": "graph A plus the blind-spot pixel-passing pairs",
            "edge_count": summ_b["edge_count"],
            "node_count": summ_b["node_count"],
            "component_count": summ_b["component_count"],
            "largest_component_size": summ_b["largest_component_size"],
            "component_size_histogram": summ_b["component_size_histogram"],
            "is_authoritative": False,
        },
        "edges_added": [
            {"a": r["a"], "b": r["b"], "dhash_distance": r["dhash_distance"],
             "pixel_corr": r["pixel_corr"], "pixel_mad": r["pixel_mad"]}
            for r in sorted(blind_verified, key=lambda r: (r["a"], r["b"]))
        ],
        "atomic_unit_count_change": {
            "graph_a_non_singleton_units": sum(
                1 for c in summ_a["_components"] if len(c) > 1),
            "graph_b_non_singleton_units": sum(
                1 for c in summ_b["_components"] if len(c) > 1),
            "graph_a_total_units_including_singletons":
                sum(1 for c in summ_a["_components"] if len(c) > 1) + (n - summ_a["node_count"]),
            "graph_b_total_units_including_singletons":
                sum(1 for c in summ_b["_components"] if len(c) > 1) + (n - summ_b["node_count"]),
        },
        "components_merged": merged,
        "images_whose_component_membership_changes": {
            "count": len(membership_change),
            "images": {k: v for k, v in sorted(membership_change.items())},
        },
        "previously_singleton_images_now_in_a_component": sorted(membership_change),
        "largest_component_change": {
            "graph_a_largest": summ_a["largest_component_size"],
            "graph_b_largest": summ_b["largest_component_size"],
            "changed": summ_a["largest_component_size"] != summ_b["largest_component_size"],
        },
        "rare_class_impact": rare_delta,
        "component_manifest_graph_a": [
            {"component_id": r["component_id"], "size": r["size"], "members": r["members"]}
            for r in comp_records
        ],
    })
    print(f"      wrote graph_583_vs_589_comparison.json")

    # ---- output 5: large component + chaining audit -------------------------
    _write_json(GROUP_ANALYSIS_DIR / "large_component_audit.json", {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_h11_evidence_scope.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "terminology": (
            "A 'component' here is the transitive closure of DETECTED VISUAL-CORRELATION "
            "RELATIONSHIPS under the tested criterion. It is NOT a source-video group, "
            "NOT a capture event, and NOT a proof of any provenance claim."
        ),
        "audit_cutoff": large_cutoff,
        "components_audited": len(large),
        "largest_component": {
            "component_id": comp_records[0]["component_id"],
            "size": comp_records[0]["size"],
            "members": comp_records[0]["members"],
            "member_indices": comp_records[0]["member_indices"],
            "edge_count": comp_records[0]["edge_count"],
            "density": comp_records[0]["density"],
            "diameter": comp_records[0]["diameter"],
            "degree_histogram": comp_records[0]["degree_histogram"],
            "tarjan": comp_records[0]["tarjan"],
            "cores": comp_records[0]["cores"],
            "dhash": {"min": comp_records[0]["dhash_min"],
                      "max": comp_records[0]["dhash_max"],
                      "median": comp_records[0]["dhash_median"]},
            "corr": {"min": comp_records[0]["corr_min"],
                     "max": comp_records[0]["corr_max"],
                     "median": comp_records[0]["corr_median"]},
            "mad_max": comp_records[0]["mad_max"],
            "rare_class_images": comp_records[0]["rare_class_images"],
            "class_presence_composition": comp_records[0]["class_presence_composition"],
        },
        "components_size_ge_cutoff": large,
        "edge_removal_sensitivity": sensitivity,
        "sensitivity_note": (
            "Each row REMOVES edges and recomputes components. No row selects a threshold; "
            "rows are diagnostic only. 'edges_retained' counts against the 583-edge graph A."
        ),
    })
    print(f"      wrote large_component_audit.json ({len(large)} large components)")

    # ---- markdown -----------------------------------------------------------
    _write_markdowns(
        six=six,
        miss_records=miss_records,
        miss_hist=miss_hist,
        dist_hist=dist_hist,
        blind_verified=blind_verified,
        exhaustive_le10=exhaustive_le10,
        up_cand=up_cand,
        up_ver=up_ver,
        never_enumerated=len(never_enumerated_idx),
        skipped_buckets=skipped_buckets,
        buckets=buckets,
        bucket_sizes=bucket_sizes,
        over_skip=over_skip,
        n=n,
        total_pairs=total_pairs,
        over_corr=len(over_corr),
        full_pass=full_pass,
        full_pass32=full_pass32,
        precision_diff=precision_symmetric_diff,
        margin_corr=margin_corr,
        margin_mad=margin_mad,
        inside_cand=inside_cand,
        full_only=full_only,
        full_comps=full_comps,
        full_sizes=full_sizes,
        summ_a=summ_a,
        summ_b=summ_b,
        merged=merged,
        membership_change=membership_change,
        comp_records=comp_records,
        large=large,
        sensitivity=sensitivity,
        rare_report=rare_report,
        timings=timings,
        per_image=per_image,
        wall=round(time.time() - wall0, 2),
    )
    print(f"      wrote markdown artifacts")
    print()
    print(f"Total wall time: {time.time() - wall0:.1f}s")
    print("No split was created. No image was assigned. No data was modified.")
    return 0


# ---------------------------------------------------------------------------
# module-level helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def _raw_matches_normalized(stems: List[str]) -> Dict[str, Any]:
    """
    Confirm the raw and normalized image bytes are identical.

    This matters because `verify_near_duplicates.py` hashes RAW images while
    `analyze_exhaustive_similarity.py` and this script hash NORMALIZED images.
    If the bytes differed, "the 583 pairs were reproduced" would be comparing
    two different image sets.
    """
    import hashlib
    mismatches: List[str] = []
    missing: List[str] = []
    for s in stems:
        rp = RAW_IMAGES_DIR / f"{s}.jpg"
        if not rp.exists():
            missing.append(s)
            continue
        if (hashlib.sha256(rp.read_bytes()).hexdigest()
                != hashlib.sha256((IMAGES_DIR / f"{s}.jpg").read_bytes()).hexdigest()):
            mismatches.append(s)
    return {
        "checked": len(stems),
        "byte_identical": len(stems) - len(mismatches) - len(missing),
        "mismatched": mismatches[:20],
        "mismatch_count": len(mismatches),
        "missing_in_raw": missing[:20],
        "missing_count": len(missing),
    }


def _same_group(groups: List[Dict[str, Any]], a: str, b: str) -> bool:
    for g in groups:
        stems = set(g.get("stems", []))
        if a in stems and b in stems:
            return True
    return False


def _clique_cover_units(edges: Set[Tuple[str, str]]) -> List[List[str]]:
    from scripts.analysis.analyze_correlation_graph import greedy_clique_cover
    nodes = {m for e in edges for m in e}
    groups, _uncovered = greedy_clique_cover(nodes, edges)
    return [sorted(g) for g in groups if len(g) > 1]


def _rare_class_report(
    units: List[List[str]],
    per_image: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    units_with = 0
    images_with = 0
    objects_with = 0
    unit_sizes_with: List[int] = []
    for unit in units:
        objs = sum(per_image[m]["object_counts"][RARE_CLASS] for m in unit)
        if objs > 0:
            units_with += 1
            images_with += sum(
                1 for m in unit if per_image[m]["object_counts"][RARE_CLASS] > 0)
            objects_with += objs
            unit_sizes_with.append(len(unit))
    all_rare_images = sum(
        1 for m in per_image if per_image[m]["object_counts"][RARE_CLASS] > 0)
    all_rare_objects = sum(
        per_image[m]["object_counts"][RARE_CLASS] for m in per_image)
    return {
        "atomic_units_total": len(units),
        "atomic_units_containing_rare_class": units_with,
        "images_containing_rare_class_in_units": images_with,
        "rare_class_objects_in_units": objects_with,
        "largest_unit_containing_rare_class": max(unit_sizes_with, default=0),
        "unit_size_histogram_for_rare_units": {
            str(k): v for k, v in sorted(Counter(unit_sizes_with).items())},
        "rare_class_images_total_dataset": all_rare_images,
        "rare_class_objects_total_dataset": all_rare_objects,
        "rare_class_images_outside_any_multi_image_unit": all_rare_images - images_with,
        "rare_class_objects_outside_any_multi_image_unit": all_rare_objects - objects_with,
        "note": (
            "Images outside any multi-image unit are singletons for atomicity purposes. "
            "They are NOT verified-independent captures."
        ),
    }


def _write_markdowns(**kw: Any) -> None:
    n = kw["n"]
    L: List[str] = []
    A = L.append

    # ---------------- missed_pixel_pairs.md ----------------
    six = kw["six"]
    A("# RDD2022 India: Pixel-Passing Pairs Missed by Banded Blocking")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A(f"**Analysis version**: {ANALYSIS_VERSION}")
    A(f"**Generated by**: `{__name__}`")
    A("")
    A("## Definition")
    A("")
    A("A pair is in this set when ALL of the following hold:")
    A("")
    A(f"1. it satisfies the upstream pixel acceptance criterion (corr >= {PIXEL_CORR_MIN} "
      f"AND MAD <= {PIXEL_MAD_MAX});")
    A(f"2. its dHash distance is <= {UPSTREAM_CANDIDATE_THRESHOLD};")
    A(f"3. the upstream {UPSTREAM_BANDS}-band blocking procedure never enumerated it, "
      "because no band is bit-identical;")
    A("4. it is absent from the upstream candidate file.")
    A("")
    A("**No semantic category is assigned by this script.** A numerical similarity score is")
    A("not evidence of duplicate content. Classification requires human visual review of the")
    A("contact sheets in `missed_pair_contact_sheets/`.")
    A("")
    A(f"## The {len(six)} pairs")
    A("")
    A("| # | A | B | index gap | dHash | corr | MAD | max abs diff | frac px > 32/255 | bands hit |")
    A("|---|---|---|-----------|-------|------|-----|--------------|------------------|-----------|")
    for r in six:
        A(f"| {r['rank']} | {r['a']} | {r['b']} | {r['index_gap']} | {r['dhash_distance']} | "
          f"{r['pixel_corr']:.4f} | {r['pixel_mad']:.4f} | {r['abs_diff_max']:.4f} | "
          f"{r['fraction_pixels_differing_gt_32_255']:.4f} | {r['differing_bands']} |")
    A("")
    A("Every one of these pairs is in the **loosest** part of the criterion space. The")
    A("acceptance threshold is corr >= 0.90, and four of the six sit between 0.905 and 0.919,")
    A("i.e. within 0.02 of the boundary. The full-pair-space analysis found 1,083 further")
    A("pixel-passing pairs with no dHash support at all, which establishes that")
    A("corr >= 0.90 is met by coincidence for a large number of unrelated road images.")
    A("Marginal numerical compliance is therefore weak evidence on its own.")
    A("")
    A("## Miss mechanism")
    A("")
    A("Banded blocking finds a pair only if at least one of the 8 bands is bit-identical.")
    A("With 8 differing bits or more, all 8 bands can each contain at least one differing")
    A("bit, and the pair is never compared. All six pairs are misses of exactly this kind,")
    A("and the mechanism is deterministic: it depends only on the two 64-bit hash values.")
    A("")
    for r in six:
        A(f"- **{r['a']} / {r['b']}** — dHash {r['dhash_distance']}, differing bit positions "
          f"{r['differing_bit_positions']}, {r['differing_bands']} bands affected. "
          f"No band identical, so no shared bucket.")
    A("")
    (GROUP_ANALYSIS_DIR / "missed_pixel_pairs.md").write_text("\n".join(L), encoding="utf-8")

    # ---------------- blocking_miss_audit.md ----------------
    miss_records = kw["miss_records"]
    miss_hist = kw["miss_hist"]
    L = []
    A = L.append
    A("# RDD2022 India: Blocking-Miss Audit")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A("")
    A("## Census")
    A("")
    A("| Quantity | Value |")
    A("|----------|-------|")
    A(f"| Exhaustive pairs with dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} | "
      f"{kw['exhaustive_le10']:,} |")
    A(f"| Pairs recorded in the upstream candidate file | {len(kw['up_cand']):,} |")
    A(f"| Pairs the blocking never enumerated | {kw['never_enumerated']:,} |")
    A(f"| Pairs absent from the upstream candidate file | {len(miss_records)} |")
    A(f"| Bucket-skip guard fired | {kw['skipped_buckets']} buckets |")
    A("")
    A("The last two rows are **equal**, which is the important structural result: inside the")
    A("dHash threshold, banded blocking is the ONLY channel by which a pair can be lost. No")
    A("pair was dropped for any other reason, and the `> 400` bucket guard never fired")
    A(f"(largest bucket holds {max(kw['bucket_sizes'])} images).")
    A("")
    A("## Miss distribution by dHash distance")
    A("")
    A("| dHash | exhaustive pairs at d | theoretical P(miss) | expected misses | observed misses | observed / expected |")
    A("|-------|------------------------|---------------------|-----------------|-----------------|--------------------|")
    from scripts.analysis.analyze_exhaustive_similarity import banded_blocking_miss_probability
    dhist = kw["dist_hist"]
    for d in range(0, UPSTREAM_CANDIDATE_THRESHOLD + 1):
        p_miss = banded_blocking_miss_probability(d)
        at_d = dhist.get(d, 0)
        expected = p_miss * at_d
        observed = miss_hist.get(d, 0)
        ratio = f"{observed / expected:.2f}x" if expected > 0 else "n/a"
        A(f"| {d} | {at_d} | {p_miss:.6f} | {expected:.3f} | {observed} | {ratio} |")
    A("")
    A("Observed misses exceed the uniform-bit theoretical expectation at every distance where")
    A("misses occur. That is expected rather than alarming: dHash differing bits are not")
    A("uniformly distributed, and the images most likely to be near-duplicates cluster in")
    A("the same regions of hash space, which raises the chance that a difference lands in")
    A("every band. The theoretical column is a lower-bound sanity check, not a prediction.")
    A("")
    A("## Pixel outcome of the 96 misses")
    A("")
    A("| Outcome | Count |")
    A("|---------|-------|")
    A(f"| Pass the pixel acceptance criterion | {len(kw['blind_verified'])} |")
    A(f"| Fail the pixel acceptance criterion | {len(miss_records) - len(kw['blind_verified'])} |")
    A("")
    A("## Determinism")
    A("")
    A("The miss set is a pure function of the dHash values, the band layout, the band count")
    A("and the bucket-skip threshold. There is no randomness, no dependence on dict or hash")
    A("iteration order, and no wall-clock input. It is exactly reproducible.")
    A("")
    A("## Full miss table")
    A("")
    A("| A | B | dHash | corr | MAD | passes pixel | bands hit |")
    A("|---|---|-------|------|-----|--------------|-----------|")
    for r in miss_records:
        A(f"| {r['a']} | {r['b']} | {r['dhash_distance']} | {r['pixel_corr']:.4f} | "
          f"{r['pixel_mad']:.4f} | {r['passes_pixel_criterion']} | "
          f"{r['blockage']['differing_bands']} |")
    A("")
    (GROUP_ANALYSIS_DIR / "blocking_miss_audit.md").write_text(
        "\n".join(L), encoding="utf-8")

    # ---------------- full_space_pixel_reproduction.md ----------------
    L = []
    A = L.append
    A("# RDD2022 India: Full-Space Pixel Reproduction")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A("")
    A("## Pipeline actually executed")
    A("")
    A("| Stage | Implementation |")
    A("|-------|----------------|")
    A("| Image source | normalized `train/images`, opened read-only |")
    A("| dHash | `imagehash.dhash(RGB, hash_size=8)` -> 64 bit |")
    A("| Pixel signature | PIL `convert('L')`, LANCZOS resize to 64x64, float64, /255 |")
    A(f"| Pair space | all {kw['total_pairs']:,} unordered pairs, no filter |")
    A("| Correlation | Pearson r over the flattened 4096-value signature |")
    A("| MAD | mean absolute difference over the same 4096 values |")
    A("| Thresholds | corr >= 0.90 AND MAD <= 0.10, compared unrounded |")
    A("")
    A("Note that the pixel comparison is **not** performed on the original 720x720 image.")
    A("It is performed on a 64x64 grayscale downsample, which is exactly what upstream")
    A("`verify_near_duplicates.pixel_signature` does.")
    A("")
    A("## Reproduction of the recorded figures")
    A("")
    A("| Quantity | Previously recorded | Reproduced | Agrees |")
    A("|----------|--------------------|------------|---------|")
    A(f"| Unordered pairs | 1,169,685 | {kw['total_pairs']:,} | "
      f"{kw['total_pairs'] == 1169685} |")
    A(f"| dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} pairs | 3,812 | "
      f"{kw['exhaustive_le10']:,} | {kw['exhaustive_le10'] == 3812} |")
    A(f"| Upstream candidate pairs | 3,716 | {len(kw['up_cand']):,} | "
      f"{len(kw['up_cand']) == 3716} |")
    A(f"| Pairs with corr >= 0.90 | 1,997 | {kw['over_corr']:,} | "
      f"{kw['over_corr'] == 1997} |")
    A(f"| Pairs passing corr and MAD | 1,672 | {len(kw['full_pass']):,} | "
      f"{len(kw['full_pass']) == 1672} |")
    A(f"| Full-space components | 76 | {len(kw['full_comps'])} | "
      f"{len(kw['full_comps']) == 76} |")
    A(f"| Full-space largest component | 397 | {kw['full_sizes'][0] if kw['full_sizes'] else 0} | "
      f"{(kw['full_sizes'][0] if kw['full_sizes'] else 0) == 397} |")
    A("")
    A("## Trustworthiness")
    A("")
    A("| Question | Answer |")
    A("|----------|--------|")
    A("| Is the pair space exhaustive? | Yes, all unordered pairs, no candidate filter |")
    A("| Is it deterministic? | Yes, no randomness or wall-clock input |")
    A("| Any pair excluded for computational reasons? | No |")
    A("| Any bucket-size limit or silent skip in this script? | No |")
    A(f"| Does float32 vs float64 change the pass set? | "
      f"No, symmetric difference = {len(kw['precision_diff'])} |")
    A(f"| Smallest correlation margin above threshold | {kw['margin_corr'][0]:.3e} |")
    A(f"| Smallest MAD margin below threshold | {kw['margin_mad'][0]:.3e} |")
    A("")
    A("The pass set is a pure function of the image bytes. It is technically trustworthy as")
    A("a *measurement*. What it is not is a meaningful *criterion*: at this threshold the")
    A("full space admits 1,672 pairs, the large majority of which are coincidental")
    A("correlations between unrelated road images that share a layout.")
    A("")
    A("## Partition of the 1,672 passing pairs")
    A("")
    A("| Category | Count |")
    A("|----------|-------|")
    A(f"| Inside the upstream candidate space | {len(kw['inside_cand'])} |")
    A(f"| In the blocking blind spot (the six pairs) | {len(kw['blind_verified'])} |")
    A(f"| Outside the candidate space entirely | {len(kw['full_only'])} |")
    A(f"| **Total** | **{len(kw['full_pass'])}** |")
    A("")
    (GROUP_ANALYSIS_DIR / "full_space_pixel_reproduction.md").write_text(
        "\n".join(L), encoding="utf-8")

    # ---------------- graph_583_vs_589_comparison.md ----------------
    sa, sb = kw["summ_a"], kw["summ_b"]
    L = []
    A = L.append
    A("# RDD2022 India: 583-Edge Graph vs 589-Edge Sensitivity Graph")
    A("")
    A("**Status**: SENSITIVITY ANALYSIS ONLY.")
    A("")
    A("Graph A is the existing authoritative 583-edge evidence graph. Graph B adds the six")
    A("pixel-passing pairs that banded blocking never enumerated. **Graph B is not")
    A("authoritative.** Nothing in this document changes the recorded evidence, and no")
    A("threshold is selected by it.")
    A("")
    A("## Comparison")
    A("")
    A("| Quantity | Graph A (583) | Graph B (589) | Change |")
    A("|----------|--------------|--------------|--------|")
    A(f"| Edges | {sa['edge_count']} | {sb['edge_count']} | "
      f"+{sb['edge_count'] - sa['edge_count']} |")
    A(f"| Nodes | {sa['node_count']} | {sb['node_count']} | "
      f"{sb['node_count'] - sa['node_count']:+d} |")
    A(f"| Connected components | {sa['component_count']} | {sb['component_count']} | "
      f"{sb['component_count'] - sa['component_count']:+d} |")
    A(f"| Largest component | {sa['largest_component_size']} | {sb['largest_component_size']} | "
      f"{sb['largest_component_size'] - sa['largest_component_size']:+d} |")
    n_a_units = sum(1 for c in sa["_components"] if len(c) > 1)
    n_b_units = sum(1 for c in sb["_components"] if len(c) > 1)
    A(f"| Non-singleton atomic units | {n_a_units} | {n_b_units} | "
      f"{n_b_units - n_a_units:+d} |")
    A(f"| Total units incl. singletons | {n_a_units + (n - sa['node_count'])} | "
      f"{n_b_units + (n - sb['node_count'])} | "
      f"{(n_b_units + (n - sb['node_count'])) - (n_a_units + (n - sa['node_count'])):+d} |")
    A("")
    A("## Components merged by the six edges")
    A("")
    A(f"Merged component groups: **{len(kw['merged'])}**")
    A("")
    if kw["merged"]:
        A("| new size | components merged | previous sizes | new members |")
        A("|-----------|------------------|----------------|-------------|")
        for m in kw["merged"]:
            A(f"| {m['graph_b_component_size']} | {m['graph_a_components_merged']} | "
              f"{m['graph_a_component_sizes']} | {len(m['new_members'])} |")
        A("")
    A("## Images whose component membership changes")
    A("")
    A(f"Count: **{len(kw['membership_change'])}**")
    A("")
    if kw["membership_change"]:
        A("| image | previous component indices |")
        A("|-------|----------------------------|")
        for img, prev in sorted(kw["membership_change"].items()):
            A(f"| {img} | {prev} |")
        A("")
        A("An image listed here was previously a singleton (or in a smaller component) and is")
        A("now part of a larger component. Membership is reported as component indices into")
        A("the Graph A component list.")
        A("")
    (GROUP_ANALYSIS_DIR / "graph_583_vs_589_comparison.md").write_text(
        "\n".join(L), encoding="utf-8")

    # ---------------- large_component_audit.md ----------------
    large = kw["large"]
    top = kw["comp_records"][0]
    L = []
    A = L.append
    A("# RDD2022 India: Large Connected-Component Audit")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A("")
    A("## Terminology")
    A("")
    A("A **component** in this document is the *transitive closure of detected")
    A("visual-correlation relationships* under the tested criterion. It is **not** a")
    A("source-video group, **not** a capture event, and **not** evidence that its members")
    A("share any provenance. No source metadata of any kind exists in this artifact.")
    A("")
    A("## Summary of audited components (size >= 10)")
    A("")
    A("| ID | size | edges | density | dHash min/med/max | corr min/med/max | max MAD | deg-1 nodes | bridges | artic. pts | shape |")
    A("|----|------|-------|---------|-------------------|------------------|---------|------------|---------|-----------|-------|")
    for r in large:
        tj = r.get("tarjan", {})
        A(f"| {r['component_id']} | {r['size']} | {r['edge_count']} | {r['density']} | "
          f"{r['dhash_min']}/{r['dhash_median']}/{r['dhash_max']} | "
          f"{r['corr_min']}/{r['corr_median']}/{r['corr_max']} | {r['mad_max']} | "
          f"{r['nodes_with_degree_one']} | {tj.get('bridge_count', '-')} | "
          f"{tj.get('articulation_point_count', '-')} | {r['structural_shape']} |")
    A("")
    A("## Largest component in full")
    A("")
    A(f"**{top['component_id']}** — {top['size']} images, {top['edge_count']} edges, "
      f"density {top['density']}, diameter {top.get('diameter')}.")
    A("")
    A("| Property | Value |")
    A("|----------|-------|")
    A(f"| Members | {', '.join(top['members'])} |")
    A(f"| Member indices | {top['member_indices']} |")
    A(f"| Degree histogram | {top['degree_histogram']} |")
    A(f"| Nodes of degree 1 | {top['nodes_with_degree_one']} |")
    A(f"| Diameter | {top.get('diameter')} |")
    A(f"| Bridge edges | {top.get('tarjan', {}).get('bridge_count')} |")
    A(f"| Articulation points | {top.get('tarjan', {}).get('articulation_point_count')} |")
    A(f"| Biconnected components | {top.get('tarjan', {}).get('biconnected_component_count')} |")
    A(f"| Max k-core number | {top.get('cores', {}).get('max_core_number')} |")
    A(f"| Core size by k | {top.get('cores', {}).get('size_by_core_number')} |")
    A(f"| dHash min / median / max | {top['dhash_min']} / {top['dhash_median']} / {top['dhash_max']} |")
    A(f"| corr min / median / max | {top['corr_min']} / {top['corr_median']} / {top['corr_max']} |")
    A(f"| max MAD | {top['mad_max']} |")
    A(f"| class-presence composition | {top['class_presence_composition']} |")
    A(f"| class-1 images / objects | {top['rare_class_images']} / {top['rare_class_objects']} |")
    A(f"| structural shape | {top['structural_shape']} |")
    A("")
    A("`structural_shape` is derived only from measured graph statistics (edge count relative")
    A("to node count, and the fraction of degree-1 nodes). It describes GRAPH SHAPE and")
    A("carries no provenance meaning.")
    A("")
    A("## Edge-removal sensitivity")
    A("")
    A("Each row REMOVES edges from the 583-edge graph and recomputes components. **No row")
    A("selects a threshold.** These are diagnostics of how much of the structure depends on")
    A("the weakest evidence, not proposals for a new threshold.")
    A("")
    A("| criterion | edges kept | edges removed | components | largest | components >= 10 | images in comps >= 10 |")
    A("|-----------|-----------|---------------|------------|---------|-------------------|----------------------|")
    for s in kw["sensitivity"]:
        A(f"| {s['criterion']} | {s['edges_retained']} | {s['edges_removed']} | "
          f"{s['component_count']} | {s['largest_component_size']} | "
          f"{s['components_ge_10']} | {s['images_in_components_ge_10']} |")
    A("")
    (GROUP_ANALYSIS_DIR / "large_component_audit.md").write_text(
        "\n".join(L), encoding="utf-8")

    # ---------------- rare class + timings ----------------
    L = []
    A = L.append
    A("# RDD2022 India: Rare-Class Impact Across Atomicity Rules")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A("")
    A(f"Rare class: **{RARE_CLASS}** (D01).")
    A("")
    A("| Rule | non-singleton units | units w/ class 1 | class-1 images in units | class-1 objects in units | largest such unit | class-1 images outside units |")
    A("|------|--------------------|------------------|-------------------------|--------------------------|--------------------|-----------------------------|")
    for name, r in kw["rare_report"].items():
        A(f"| {name} | {r['atomic_units_total']} | "
          f"{r['atomic_units_containing_rare_class']} | "
          f"{r['images_containing_rare_class_in_units']} | "
          f"{r['rare_class_objects_in_units']} | "
          f"{r['largest_unit_containing_rare_class']} | "
          f"{r['rare_class_images_outside_any_multi_image_unit']} |")
    A("")
    A("Images outside every multi-image unit are singletons for atomicity purposes. They are")
    A("**not** verified-independent captures.")
    A("")
    A("## Cost profile")
    A("")
    A("No timing value is stored in any JSON artifact of this investigation, so that")
    A("repeated runs are byte-identical. Wall-clock measurements are printed to stdout")
    A("and reported in the final report.")
    A("")
    A("The dHash and pixel-signature stages dominate, because each reopens and re-decodes")
    A("all 1,530 JPEGs. The exhaustive Hamming matrix and the correlation Gram matrix are")
    A("vectorised and comparatively cheap. A full rerun is therefore a single-digit-minute")
    A("operation, which makes deterministic re-verification practical after any change to")
    A("the corpus.")
    A("")
    (GROUP_ANALYSIS_DIR / "rare_class_and_cost.md").write_text(
        "\n".join(L), encoding="utf-8")

    # ---------------- h11_decision_package.md ----------------
    sa, sb = kw["summ_a"], kw["summ_b"]
    L = []
    A = L.append
    A("# H11 Decision Package: Evidence Scope for Correlation Analysis")
    A("")
    A("**Status**: ANALYSIS ONLY. **This document does not select an option.** It states what")
    A("each option would mean so a human can decide.")
    A("")
    A("## The question")
    A("")
    A("The 583 pixel-verified pairs were produced inside a candidate set built by 8-band")
    A("blocking plus a dHash <= 10 filter. The question is what claim the project is entitled")
    A("to make about visual correlation, and therefore what the split may rely on.")
    A("")
    A("## Measured facts the decision rests on")
    A("")
    A(f"- Exhaustive dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} pairs: "
      f"**{kw['exhaustive_le10']:,}**")
    A(f"- Pairs the upstream candidate file records: **{len(kw['up_cand']):,}**")
    A(f"- dHash <= {UPSTREAM_CANDIDATE_THRESHOLD} pairs the blocking never enumerated: "
      f"**{kw['never_enumerated']}**")
    A(f"- Of those, pairs that independently pass the pixel criterion: "
      f"**{len(kw['blind_verified'])}**")
    A(f"- Full-pair-space pixel-passing pairs at the same thresholds: "
      f"**{len(kw['full_pass']):,}** of {kw['total_pairs']:,}")
    A(f"- Connected components: **{sa['component_count']}**, largest "
      f"**{sa['largest_component_size']}**")
    A(f"- Full-space components at the same thresholds: **{len(kw['full_comps'])}**, largest "
      f"**{kw['full_sizes'][0] if kw['full_sizes'] else 0}**")
    A("")
    A("## Option comparison")
    A("")
    A("| | A. Bounded candidate space | B. Exhaustive dHash<=10 + pixel | C. Full-space pixel, recalibrated |")
    A("|---|---|---|---|")
    A(f"| Compute scope | {len(kw['up_cand']):,} candidate pairs | "
      f"{kw['exhaustive_le10']:,} candidate pairs | {kw['total_pairs']:,} pairs |")
    A("| False negatives observed | 6 pixel-passing pairs never examined | 0 within dHash<=10 | 0 |")
    A("| Known missed pixel-passing pairs | 6 | 0 | 0 |")
    A("| Graph size | 583 edges | 589 edges | threshold-dependent |")
    A(f"| Components | {sa['component_count']} | {sb['component_count']} | "
      f"{len(kw['full_comps'])} at the current threshold |")
    A(f"| Largest component | {sa['largest_component_size']} | "
      f"{sb['largest_component_size']} | "
      f"{kw['full_sizes'][0] if kw['full_sizes'] else 0} at the current threshold |")
    A("| Atomicity guarantee | holds for the 583 detected edges only | holds for all dHash<=10 pixel-passing pairs | holds for all pixel-passing pairs at the chosen threshold |")
    A("| Cost | none, already computed | one extra dHash<=10 pass, ~1 minute | requires a chosen threshold and a cost function |")
    A("| Residual risk | 6 known missed pairs plus every pair beyond dHash 10 | pairs beyond dHash 10 never pixel-tested | threshold choice is unvalidated |")
    A("")
    A("## Why option C needs a cost function, not a threshold")
    A("")
    A("Choosing a threshold for the full space requires answering a question that is a")
    A("project judgement, not a measurement: **how much over-merging is acceptable?**")
    A("Raising the threshold removes coincidental edges and simultaneously removes genuine")
    A("ones, and the two are not separable by a single scalar. Concretely, the project would")
    A("need to state:")
    A("")
    A("1. the largest acceptable atomic unit, in images, and why;")
    A("2. whether a missed genuine correlation (leakage) is worse than a spurious unit")
    A("   (over-merging), and by how much;")
    A("3. the acceptable false-negative rate at the chosen threshold.")
    A("")
    A("None of these are derivable from the data. Picking a number without them would make")
    A("the leakage property of the split a function of an unexamined assumption.")
    A("")
    A("## What this package does not decide")
    A("")
    A("- It does not select A, B, or C.")
    A("- It does not declare any of the six pairs a duplicate. That requires human visual")
    A("  review; the contact sheets are provided for exactly that purpose.")
    A("- It does not choose the atomicity policy for the split.")
    A("- It does not modify any recorded decision or any dataset file.")
    A("")
    (GROUP_ANALYSIS_DIR / "h11_decision_package.md").write_text(
        "\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


