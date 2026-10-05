"""
Phase 3: rigorous near-duplicate grouping with complete linkage and pixel verification.

Phase 2 used single-linkage (union-find) transitive closure, which chains
A-B-C together when A~B and B~C even if A and C are far apart. That produced a
spurious 1,279-image aHash "group" whose internal max distance was 41 on a
threshold of 5. Single-linkage chaining is the defect this script corrects.

Method:
  1. Recompute all candidate pairs (Hamming distance <= candidate threshold)
  2. Group with COMPLETE linkage: a group is valid only if EVERY member pair
     is within threshold. Diameter is reported for every group.
  3. Verify surviving candidates against actual pixels: normalized grayscale
     correlation and mean-absolute-difference on a downsampled image.
  4. Classify each pair/group as GENUINE VISUAL MATCH vs HASH ARTIFACT.

Outputs:
  - experiments/dataset/normalized_rdd2022_india/group_analysis/near_duplicate_verification.json
  - experiments/dataset/normalized_rdd2022_india/group_analysis/near_duplicate_verification.md

Usage:
    python analysis/verify_near_duplicates.py
"""
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import json
import itertools
import sys

import numpy as np
from PIL import Image
import imagehash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RAW_IMAGES_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\images")
OUT_DIR = Path(r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\normalized_rdd2022_india\group_analysis")

CANDIDATE_THRESHOLD = 10   # permissive: gather any pair worth examining
LINKAGE_THRESHOLD = 5      # strict: every member pair must be within this
PIXEL_SIZE = (64, 64)      # downsample size for pixel verification

# Pixel-level acceptance criteria for "genuine visual match"
PIXEL_CORR_MIN = 0.90      # Pearson correlation of downsampled grayscale
PIXEL_MAD_MAX = 0.10       # mean absolute difference of normalized pixels


def load_hashes(stems: List[str]) -> Dict[str, imagehash.ImageHash]:
    out: Dict[str, imagehash.ImageHash] = {}
    for s in stems:
        with Image.open(RAW_IMAGES_DIR / f"{s}.jpg") as im:
            out[s] = imagehash.dhash(im.convert("RGB"), hash_size=8)
    return out


def candidate_pairs(hashes: Dict[str, imagehash.ImageHash], threshold: int) -> List[Tuple[str, str, int]]:
    """All pairs within `threshold`, found via banded blocking then exact distance."""
    stems = sorted(hashes)
    index = {s: i for i, s in enumerate(stems)}
    BANDS, BAND_BITS = 8, 8
    buckets: Dict[Tuple[int, int], List[int]] = defaultdict(list)

    for s in stems:
        h_int = int("".join("1" if bool(b) else "0" for b in np.asarray(hashes[s].hash).flatten()), 2)
        for b in range(BANDS):
            shift = 63 - (b + 1) * BAND_BITS + 1
            buckets[(b, (h_int >> shift) & ((1 << BAND_BITS) - 1))].append(index[s])

    seen = set()
    pairs: List[Tuple[str, str, int]] = []
    for _, members in buckets.items():
        if len(members) < 2 or len(members) > 400:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                key = (a, b)
                if key in seen:
                    continue
                seen.add(key)
                sa, sb = stems[a], stems[b]
                dist = hashes[sa] - hashes[sb]
                if dist <= threshold:
                    pairs.append((sa, sb, dist))
    return pairs


def complete_linkage_groups(stems: List[str],
                            pairs: List[Tuple[str, str, int]],
                            threshold: int) -> List[Dict[str, Any]]:
    """
    Greedy complete-linkage clustering: a group is valid only if every member
    pair is within `threshold`. Groups are built by repeatedly merging the two
    compatible groups whose merged diameter stays within threshold.
    """
    dist: Dict[Tuple[str, str], int] = {}
    for a, b, d in pairs:
        dist[(a, b)] = d
        dist[(b, a)] = d

    groups: List[List[str]] = [[s] for s in stems]

    def diameter(g: List[str]) -> int:
        worst = 0
        for a, b in itertools.combinations(g, 2):
            d = dist.get((a, b))
            if d is None:
                return 10 ** 9  # unknown pair -> incompatible
            worst = max(worst, d)
        return worst

    changed = True
    while changed:
        changed = False
        # Find compatible groups, smallest first, and merge greedily
        groups = [g for g in groups if g]
        groups.sort(key=len)
        merged = True
        while merged:
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    cand = groups[i] + groups[j]
                    if diameter(cand) <= threshold:
                        groups[i] = cand
                        groups.pop(j)
                        groups.sort(key=len)
                        merged = True
                        changed = True
                        break
                if merged:
                    break

    out = []
    for g in groups:
        if len(g) < 2:
            continue
        ds = [dist[(a, b)] for a, b in itertools.combinations(g, 2)]
        out.append({
            "stems": sorted(g),
            "group_size": len(g),
            "diameter": max(ds),
            "mean_distance": round(sum(ds) / len(ds), 2),
            "min_distance": min(ds),
            "all_pairs_within_threshold": max(ds) <= threshold,
        })
    out.sort(key=lambda g: -g["group_size"])
    return out


def pixel_signature(stem: str) -> np.ndarray:
    """Downsampled normalized grayscale signature for pixel-level comparison."""
    with Image.open(RAW_IMAGES_DIR / f"{stem}.jpg") as im:
        small = im.convert("L").resize(PIXEL_SIZE, Image.Resampling.LANCZOS)
        arr = np.asarray(small, dtype=np.float64) / 255.0
    return arr


def pixel_compare(sig_a: np.ndarray, sig_b: np.ndarray) -> Tuple[float, float]:
    """Return (pearson correlation, mean absolute difference)."""
    a = sig_a.ravel()
    b = sig_b.ravel()
    if a.std() == 0 or b.std() == 0:
        corr = 0.0
    else:
        corr = float(np.corrcoef(a, b)[0, 1])
    mad = float(np.mean(np.abs(a - b)))
    return corr, mad


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stems = sorted(p.stem for p in RAW_IMAGES_DIR.glob("*.jpg"))
    print("Phase 3: complete-linkage near-duplicate verification")
    print(f"  Images: {len(stems):,}")
    print()

    print("[1/4] Computing dHash and candidate pairs (threshold <= %d)..." % CANDIDATE_THRESHOLD)
    hashes = load_hashes(stems)
    pairs = candidate_pairs(hashes, CANDIDATE_THRESHOLD)
    print(f"      {len(pairs):,} candidate pairs within {CANDIDATE_THRESHOLD} bits")
    print()

    print("[2/4] Complete-linkage grouping (every member pair <= %d bits)..." % LINKAGE_THRESHOLD)
    groups = complete_linkage_groups(stems, pairs, LINKAGE_THRESHOLD)
    multi = [g for g in groups if g["group_size"] > 1]
    print(f"      {len(multi)} groups with >=2 members")
    for g in multi[:15]:
        print(f"        size {g['group_size']:>3}  diameter {g['diameter']:>2}  "
              f"mean {g['mean_distance']:>5}  {', '.join(g['stems'][:6])}"
              + (" ..." if g["group_size"] > 6 else ""))
    print()

    print("[3/4] Pixel-level verification of candidate groups...")
    sigs: Dict[str, np.ndarray] = {}
    verified_groups, rejected_groups = [], []
    for g in multi:
        need = set()
        for s in g["stems"]:
            if s not in sigs:
                sigs[s] = pixel_signature(s)
        worst_corr, worst_mad = 1.0, 0.0
        all_ok = True
        for a, b in itertools.combinations(g["stems"], 2):
            corr, mad = pixel_compare(sigs[a], sigs[b])
            worst_corr = min(worst_corr, corr)
            worst_mad = max(worst_mad, mad)
            if corr < PIXEL_CORR_MIN or mad > PIXEL_MAD_MAX:
                all_ok = False
        record = dict(g)
        record["worst_pair_pixel_corr"] = round(worst_corr, 4)
        record["worst_pair_pixel_mad"] = round(worst_mad, 4)
        record["pixel_verified"] = all_ok
        (verified_groups if all_ok else rejected_groups).append(record)
    print(f"      pixel-verified groups: {len(verified_groups)}")
    print(f"      hash-only groups (failed pixel check): {len(rejected_groups)}")
    print()

    print("[4/4] Pair-level summary (every candidate pair, pixel-checked)...")
    pair_records = []
    for a, b, d in pairs:
        for s in (a, b):
            if s not in sigs:
                sigs[s] = pixel_signature(s)
        corr, mad = pixel_compare(sigs[a], sigs[b])
        pair_records.append({
            "a": a, "b": b, "dhash_distance": d,
            "pixel_corr": round(corr, 4), "pixel_mad": round(mad, 4),
            "genuine_visual_match": bool(corr >= PIXEL_CORR_MIN and mad <= PIXEL_MAD_MAX),
        })
    genuine_pairs = [p for p in pair_records if p["genuine_visual_match"]]
    print(f"      candidate pairs: {len(pair_records):,}")
    print(f"      genuine visual matches: {len(genuine_pairs):,}")
    print()

    print("--- Genuine visual match pairs (pixel-verified) ---")
    for p in sorted(genuine_pairs, key=lambda x: x["dhash_distance"])[:40]:
        print(f"  {p['a']} <-> {p['b']}  dhash={p['dhash_distance']:>2}  "
              f"corr={p['pixel_corr']:.3f}  mad={p['pixel_mad']:.3f}")
    if len(genuine_pairs) > 40:
        print(f"  ... and {len(genuine_pairs) - 40} more (see JSON)")
    print()

    payload = {
        "analysis_version": "1.0.0",
        "methodology": {
            "hash": "imagehash dHash 8x8 (64 bit)",
            "candidate_threshold_bits": CANDIDATE_THRESHOLD,
            "linkage": "complete (all member pairs must be within threshold)",
            "linkage_threshold_bits": LINKAGE_THRESHOLD,
            "pixel_verification": {
                "grayscale_downsample": list(PIXEL_SIZE),
                "pearson_corr_min": PIXEL_CORR_MIN,
                "mean_abs_diff_max": PIXEL_MAD_MAX,
            },
            "note": "Single-linkage transitive closure in phase 2 produced chained groups "
                    "whose internal max distance far exceeded the threshold. Complete linkage "
                    "eliminates that artifact.",
        },
        "candidate_pair_count": len(pair_records),
        "complete_linkage_groups": groups,
        "pixel_verified_groups": verified_groups,
        "hash_only_rejected_groups": rejected_groups,
        "genuine_match_pair_count": len(genuine_pairs),
        "pairs": pair_records,
    }
    j = OUT_DIR / "near_duplicate_verification.json"
    j.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"JSON: {j}")

    L = []
    L.append("# RDD2022 India: Near-Duplicate Verification (Complete Linkage)")
    L.append("")
    L.append("## Why this phase exists")
    L.append("")
    L.append("Phase 2 used single-linkage transitive closure. That merges A-B when similar and")
    L.append("B-C when similar, even if A and C are unrelated. It produced an aHash \"group\" of")
    L.append("1,279 images whose internal maximum distance was 41 bits on a threshold of 5. Such")
    L.append("chained groups are artifacts, not real clusters. This phase re-groups with complete")
    L.append("linkage, where **every** member pair must be within threshold, and then verifies each")
    L.append("surviving candidate against actual pixels.")
    L.append("")
    L.append("## Method")
    L.append("")
    L.append("| Parameter | Value |")
    L.append("|-----------|-------|")
    L.append(f"| Hash | dHash 8x8 (64 bit) |")
    L.append(f"| Candidate threshold | <= {CANDIDATE_THRESHOLD} bits (permissive) |")
    L.append(f"| Linkage threshold | <= {LINKAGE_THRESHOLD} bits (strict, complete linkage) |")
    L.append(f"| Pixel check | grayscale {PIXEL_SIZE}, Pearson corr >= {PIXEL_CORR_MIN}, MAD <= {PIXEL_MAD_MAX} |")
    L.append("")
    L.append("## Results")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|--------|-------|")
    L.append(f"| Candidate pairs (<= {CANDIDATE_THRESHOLD} bits) | {len(pair_records):,} |")
    L.append(f"| Genuine visual matches (pixel-verified) | {len(genuine_pairs):,} |")
    L.append(f"| Complete-linkage groups (>=2 members) | {len(multi)} |")
    L.append(f"| Groups passing pixel verification | {len(verified_groups)} |")
    L.append(f"| Groups rejected by pixel check | {len(rejected_groups)} |")
    L.append("")
    if verified_groups:
        L.append("### Pixel-verified groups (GENUINE VISUAL MATCH)")
        L.append("")
        L.append("| Stems | Size | dHash diameter | Worst pixel corr | Worst pixel MAD |")
        L.append("|-------|------|----------------|------------------|----------------|")
        for g in verified_groups:
            L.append(f"| {', '.join(g['stems'])} | {g['group_size']} | {g['diameter']} | "
                     f"{g['worst_pair_pixel_corr']} | {g['worst_pair_pixel_mad']} |")
        L.append("")
    if rejected_groups:
        L.append("### Groups rejected by pixel verification (HASH ARTIFACT)")
        L.append("")
        L.append("| Stems | Size | dHash diameter | Worst pixel corr | Worst pixel MAD |")
        L.append("|-------|------|----------------|------------------|----------------|")
        for g in rejected_groups[:40]:
            stems = ", ".join(g["stems"][:8])
            if len(g["stems"]) > 8:
                stems += f", ... (+{len(g['stems']) - 8})"
            L.append(f"| {stems} | {g['group_size']} | {g['diameter']} | "
                     f"{g['worst_pair_pixel_corr']} | {g['worst_pair_pixel_mad']} |")
        L.append("")
    L.append("## Interpretation")
    L.append("")
    L.append("Even a pixel-verified match proves only that two images look the same. It does NOT")
    L.append("prove they came from the same video, trip, or capture session: a road scene can be")
    L.append("revisited, or two vehicles can record the same location. Treat these as candidate")
    L.append("correlated groups only.")
    (OUT_DIR / "near_duplicate_verification.md").write_text("\n".join(L), encoding="utf-8")
    print(f"MD:   {OUT_DIR / 'near_duplicate_verification.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
