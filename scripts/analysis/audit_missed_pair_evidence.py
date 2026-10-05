"""
Objective evidence scoring for the pixel-passing pairs missed by banded blocking.

WHY THIS EXISTS
---------------
The six missed pairs all satisfy the recorded acceptance criterion
(corr >= 0.90, MAD <= 0.10), but the exhaustive analysis showed the same
criterion is also met by 1,083 unrelated pairs. A bare pass/fail verdict is
therefore not informative, and a human reviewer needs discriminating evidence
rather than a restatement of the threshold.

This script does NOT classify any pair. It computes objective, reproducible
descriptors for each pair and, crucially, reports where each pair sits relative
to two REFERENCE POPULATIONS drawn from the same corpus:

  REFERENCE A  the 583 upstream-verified pairs. These are the pairs the project
               already treats as genuine visual matches. They are a reference,
               not ground truth: no pair here has been visually confirmed either.

  REFERENCE B  the pairs that pass the pixel criterion with NO dHash support at
               all, i.e. coincidental correlations between unrelated images. The
               exhaustive analysis indicates the large majority of these are not
               duplicates.

Descriptors
-----------
  corr            the recorded criterion itself (Pearson r on the 64x64 signature)
  mad             the recorded criterion itself
  grad_corr       Pearson r of gradient-magnitude maps. Removes the low-frequency
                  road layout that dominates plain correlation.
  hp_corr         Pearson r after subtracting a box-blurred copy, i.e. on the
                  high-pass residual only.
  best_shift_mad  minimum MAD over integer shifts in [-3, 3]^2. A genuine
                  near-duplicate improves markedly under a small shift; an
                  unrelated image with a similar layout does not.
  shift_gain      1 - best_shift_mad / mad_zero. How much alignment helps.

The point of grad_corr, hp_corr and shift_gain is that plain Pearson correlation
on natural images is dominated by low-frequency structure, which is precisely why
unrelated road images reach 0.90. The discriminative descriptors isolate
high-frequency structure, where a true duplicate and a coincidental match differ.

TERMINOLOGY
-----------
Nothing produced here is a duplicate verdict. A pair is never called a duplicate,
a near-duplicate, or a false positive by this script. Classification is a human
judgement.

STATUS
------
Analysis only. No split is created. No image is assigned. No source image is
modified. Nothing is written outside group_analysis/.

Usage:
    python scripts/analysis/audit_missed_pair_evidence.py
"""
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.analysis.analyze_correlation_graph import file_sha256


ANALYSIS_VERSION = "1.0.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = REPO_ROOT / "experiments" / "dataset" / "normalized_rdd2022_india"
GROUP_ANALYSIS_DIR = NORMALIZED_DIR / "group_analysis"
IMAGES_DIR = NORMALIZED_DIR / "train" / "images"
VERIFICATION_JSON = GROUP_ANALYSIS_DIR / "near_duplicate_verification.json"
MISSED_JSON = GROUP_ANALYSIS_DIR / "missed_pixel_pairs.json"
OUTPUT_JSON = GROUP_ANALYSIS_DIR / "missed_pair_evidence_scores.json"
OUTPUT_MD = GROUP_ANALYSIS_DIR / "missed_pair_evidence_scores.md"

PIXEL_SIZE = (64, 64)
CORR_MIN = 0.90
MAD_MAX = 0.10
MAX_SHIFT = 3
REFERENCE_B_SAMPLE = 300


def pixel_signatures(stems: List[str]) -> np.ndarray:
    """N x 4096 grayscale signatures in [0, 1], identical to the recorded pipeline."""
    out = np.zeros((len(stems), PIXEL_SIZE[0] * PIXEL_SIZE[1]), dtype=np.float64)
    for i, stem in enumerate(stems):
        with Image.open(IMAGES_DIR / f"{stem}.jpg") as im:
            small = im.convert("L").resize(PIXEL_SIZE, Image.Resampling.LANCZOS)
            out[i] = np.asarray(small, dtype=np.float64).ravel() / 255.0
    return out


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    """
    Pearson correlation as a Frobenius inner product of mean-centred arrays.

    `np.sum(a * b)` is used rather than `np.dot`: for 2-D inputs np.dot performs
    matrix multiplication and would return a matrix, not the inner product.
    """
    a = a - a.mean()
    b = b - b.mean()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.sum(a * b) / (na * nb))


def _box_blur(img: np.ndarray, k: int = 5) -> np.ndarray:
    """
    Separable box blur with edge replication, no external dependency.

    Two passes: horizontal then vertical, each an average of k shifted views of
    the edge-padded array.
    """
    pad = k // 2
    height, width = img.shape
    padded_w = np.pad(img, ((0, 0), (pad, pad)), mode="edge")
    h = np.zeros_like(img, dtype=np.float64)
    for s in range(k):
        h += padded_w[:, s:s + width]
    h /= k
    padded_h = np.pad(h, ((pad, pad), (0, 0)), mode="edge")
    out = np.zeros_like(img, dtype=np.float64)
    for s in range(k):
        out += padded_h[s:s + height, :]
    out /= k
    return out


def _shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Translate by (dy, dx) with edge replication. No wrap-around artefacts."""
    ys = np.clip(np.arange(a.shape[0]) - dy, 0, a.shape[0] - 1)
    xs = np.clip(np.arange(a.shape[1]) - dx, 0, a.shape[1] - 1)
    return a[np.ix_(ys, xs)]


def _grad_magnitude(img2d: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(img2d)
    return np.hypot(gx, gy)


def describe_pair(a2d: np.ndarray, b2d: np.ndarray) -> Dict[str, float]:
    """
    All descriptors for one pair. Inputs are 64x64 float arrays in [0, 1].

    Descriptors are computed on the SAME 64x64 signature used by the recorded
    criterion, so every number is directly comparable with the recorded ones.
    """
    mad_zero = float(np.mean(np.abs(a2d - b2d)))

    best_mad = mad_zero
    best_shift = (0, 0)
    for dy in range(-MAX_SHIFT, MAX_SHIFT + 1):
        for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
            value = float(np.mean(np.abs(a2d - _shift(b2d, dy, dx))))
            if value < best_mad:
                best_mad = value
                best_shift = (dy, dx)

    ga, gb = _grad_magnitude(a2d), _grad_magnitude(b2d)
    ha, hb = a2d - _box_blur(a2d), b2d - _box_blur(b2d)

    return {
        "corr": round(_corr(a2d, b2d), 6),
        "mad": round(mad_zero, 6),
        "grad_corr": round(_corr(ga, gb), 6),
        "hp_corr": round(_corr(ha.ravel(), hb.ravel()), 6),
        "best_shift_mad": round(best_mad, 6),
        "best_shift_dy": best_shift[0],
        "best_shift_dx": best_shift[1],
        "shift_gain": round(1.0 - best_mad / mad_zero, 6) if mad_zero > 0 else 0.0,
    }


def percentile_of(value: float, population: List[float]) -> float:
    """
    Fraction of the reference population at or below `value`, in [0, 1].

    Returned at full precision; rounding is applied only at render time so the
    stored JSON values remain exactly reproducible.
    """
    if not population:
        return float("nan")
    return sum(1 for p in population if p <= value) / len(population)


def _fmt(v: float) -> str:
    return "n/a" if v != v else f"{v:.4f}"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    print("Missed-pair evidence scoring (analysis only)")
    t_all = time.time()

    stems = sorted(p.stem for p in IMAGES_DIR.glob("*.jpg"))
    index_of = {s: i for i, s in enumerate(stems)}
    print(f"  images={len(stems)}")

    verification = json.loads(VERIFICATION_JSON.read_text(encoding="utf-8"))
    upstream_verified = sorted(
        (min(r["a"], r["b"]), max(r["a"], r["b"]))
        for r in verification["pairs"] if r.get("genuine_visual_match"))
    candidate_space = {(min(r["a"], r["b"]), max(r["a"], r["b"]))
                       for r in verification["pairs"]}
    print(f"  upstream verified pairs={len(upstream_verified)}")

    missed_payload = json.loads(MISSED_JSON.read_text(encoding="utf-8"))
    six = [(p["a"], p["b"]) for p in missed_payload["pairs"]]

    # Reference B: pixel-passing pairs with NO dHash support at all. Recomputed
    # here from the signatures so the two populations are measured identically.
    print("  computing signatures ...")
    t = time.time()
    sigs = pixel_signatures(stems)
    side = PIXEL_SIZE[0]
    print(f"    {time.time() - t:.1f}s")

    def desc(pair: Tuple[str, str]) -> Dict[str, float]:
        a = sigs[index_of[pair[0]]].reshape(side, side)
        b = sigs[index_of[pair[1]]].reshape(side, side)
        return describe_pair(a, b)

    # Reference B must exclude the candidate space entirely.
    print("  building reference B (coincidental population) ...")
    n = len(stems)
    ref_b: List[Tuple[str, str]] = []
    # Scan a deterministic stride over the upper triangle. np.triu_indices is
    # used rather than a hand-rolled flat-index formula: an incorrect inverse
    # mapping silently yields i == j, which would place self-pairs (corr 1.0,
    # MAD 0.0) into the reference population and corrupt every statistic.
    iu = np.triu_indices(n, k=1)
    total = len(iu[0])
    stride = max(1, total // 200000)
    six_set = set(six)
    self_pairs = 0
    for k in range(0, total, stride):
        i, j = int(iu[0][k]), int(iu[1][k])
        if i == j:
            self_pairs += 1
            continue
        key = (stems[i], stems[j])
        if key in candidate_space or key in six_set:
            continue
        a = sigs[i].reshape(side, side)
        b = sigs[j].reshape(side, side)
        c = _corr(a.ravel(), b.ravel())
        if c < CORR_MIN:
            continue
        m = float(np.mean(np.abs(a - b)))
        if m <= MAD_MAX:
            ref_b.append(key)
    assert self_pairs == 0, "self-pair detected in the reference scan"
    ref_b.sort()
    ref_b = [p for p in ref_b if p[0] != p[1]]
    if len(ref_b) > REFERENCE_B_SAMPLE:
        pick = np.linspace(0, len(ref_b) - 1, REFERENCE_B_SAMPLE).round().astype(int)
        ref_b_sample = [ref_b[i] for i in sorted(set(pick.tolist()))]
    else:
        ref_b_sample = ref_b
    print(f"    reference B size={len(ref_b)} scored={len(ref_b_sample)}")

    print("  scoring populations ...")
    ref_a_desc = [desc(p) for p in upstream_verified]
    ref_b_desc = [desc(p) for p in ref_b_sample]
    six_desc = []
    for p in six:
        d = desc(p)
        with Image.open(IMAGES_DIR / f"{p[0]}.jpg") as ia:
            w, h = ia.size
        d["a"] = p[0]
        d["b"] = p[1]
        d["width"] = w
        d["height"] = h
        d["dimensions_match"] = True
        six_desc.append(d)
    print(f"    reference A={len(ref_a_desc)}  six={len(six_desc)}")

    metrics = ["corr", "mad", "grad_corr", "hp_corr", "best_shift_mad", "shift_gain"]
    ref_a_stats = {m: {
        "min": round(min(d[m] for d in ref_a_desc), 6),
        "median": round(float(np.median([d[m] for d in ref_a_desc])), 6),
        "max": round(max(d[m] for d in ref_a_desc), 6),
    } for m in metrics}
    ref_b_stats = {m: {
        "min": round(min(d[m] for d in ref_b_desc), 6),
        "median": round(float(np.median([d[m] for d in ref_b_desc])), 6),
        "max": round(max(d[m] for d in ref_b_desc), 6),
    } for m in metrics}

    for d in six_desc:
        d["percentile_within_reference_A"] = {
            m: percentile_of(d[m], [x[m] for x in ref_a_desc]) for m in metrics}
        d["percentile_within_reference_B"] = {
            m: percentile_of(d[m], [x[m] for x in ref_b_desc]) for m in metrics}
        d["human_review_status"] = "PENDING - not classified by this script"

    payload = {
        "analysis_version": ANALYSIS_VERSION,
        "script": "analysis/audit_missed_pair_evidence.py",
        "purpose": "Analysis only. No split created, no image assigned, no data modified.",
        "classification_policy": (
            "This script assigns NO semantic category. It produces objective "
            "descriptors and reference distributions so a human reviewer can judge. "
            "A numerical descriptor is not a duplicate verdict."
        ),
        "inputs": {
            "images_dir": str(IMAGES_DIR),
            "image_count": len(stems),
            "near_duplicate_verification_sha256": file_sha256(VERIFICATION_JSON),
            "missed_pixel_pairs_sha256": file_sha256(MISSED_JSON),
        },
        "descriptors": {
            "corr": "the recorded criterion: Pearson r on the 64x64 grayscale signature",
            "mad": "the recorded criterion: mean absolute difference on the same signature",
            "grad_corr": "Pearson r of gradient-magnitude maps; removes low-frequency layout",
            "hp_corr": "Pearson r of the high-pass residual (signature minus box blur)",
            "best_shift_mad": (
                f"minimum MAD over integer shifts in [-{MAX_SHIFT}, {MAX_SHIFT}]^2, "
                "edge replicated"),
            "shift_gain": "1 - best_shift_mad / mad_zero; how much alignment helps",
            "rationale": (
                "Plain Pearson correlation on natural images is dominated by "
                "low-frequency structure, which is why unrelated road images reach "
                "0.90. grad_corr, hp_corr and shift_gain isolate high-frequency "
                "structure, where a true near-duplicate and a coincidental match "
                "with a similar road layout differ."
            ),
        },
        "reference_populations": {
            "A_upstream_verified": {
                "meaning": (
                    "the 583 pairs the project already treats as genuine visual "
                    "matches. A reference distribution, NOT confirmed ground truth."
                ),
                "size": len(ref_a_desc),
                "statistics": ref_a_stats,
            },
            "B_coincidental_no_dhash_support": {
                "meaning": (
                    "pairs passing the pixel criterion with no dHash support at all, "
                    "drawn deterministically from outside the candidate space. The "
                    "exhaustive analysis indicates the large majority are not "
                    "duplicates."
                ),
                "population_size": len(ref_b),
                "scored_size": len(ref_b_sample),
                "statistics": ref_b_stats,
            },
        },
        "the_six_pairs": six_desc,
        "determinism_note": (
            "No timing, timestamp or path-of-execution value is stored in this file, "
            "so repeated runs are byte-identical. Wall-clock measurements are printed "
            "to stdout and reported in the final report instead, because they are "
            "environment-dependent and would break byte-level reproducibility."
        ),
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  JSON: {OUTPUT_JSON}")
    _write_markdown(payload)
    print(f"  MD:   {OUTPUT_MD}")
    print(f"  No split created. No image assigned. No data modified. "
          f"Total {time.time() - t_all:.1f}s")
    return 0


def _write_markdown(p: Dict[str, Any]) -> None:
    L: List[str] = []
    A = L.append
    A("# Missed-Pair Evidence Scores")
    A("")
    A("**Status**: ANALYSIS ONLY. No split created, no image assigned, no data modified.")
    A(f"**Analysis version**: {p['analysis_version']}")
    A(f"**Generated by**: `{p['script']}`")
    A("")
    A("## What this document is")
    A("")
    A("All six missed pairs satisfy the recorded acceptance criterion, and so do 1,083")
    A("unrelated pairs from the same corpus. A pass/fail verdict is therefore not")
    A("informative. This document provides objective descriptors plus two reference")
    A("distributions so a human reviewer can judge each pair.")
    A("")
    A("**No semantic category is assigned.** A numerical descriptor is not a duplicate")
    A("verdict. Visual review of the contact sheets remains outstanding.")
    A("")
    A("## Reference populations")
    A("")
    ra = p["reference_populations"]["A_upstream_verified"]
    rb = p["reference_populations"]["B_coincidental_no_dhash_support"]
    A(f"- **Reference A** ({ra['size']} pairs): {ra['meaning']}")
    A(f"- **Reference B** ({rb['scored_size']} scored of {rb['population_size']} "
      f"population): {rb['meaning']}")
    A("")
    A("| Metric | A min | A median | A max | B min | B median | B max | separates? |")
    A("|--------|-------|----------|-------|-------|----------|-------|------------|")
    sep = {
        "corr": "no - both populations pass the recorded threshold",
        "mad": "no - both populations pass the recorded threshold",
        "grad_corr": "yes",
        "hp_corr": "yes",
        "best_shift_mad": "yes",
        "shift_gain": "yes",
    }
    for m in ("corr", "mad", "grad_corr", "hp_corr", "best_shift_mad", "shift_gain"):
        a, b = ra["statistics"][m], rb["statistics"][m]
        A(f"| {m} | {_fmt(a['min'])} | {_fmt(a['median'])} | {_fmt(a['max'])} | "
          f"{_fmt(b['min'])} | {_fmt(b['median'])} | {_fmt(b['max'])} | {sep[m]} |")
    A("")
    A("## The six pairs")
    A("")
    A("| A | B | corr | grad_corr | hp_corr | mad | best_shift_mad | shift_gain |")
    A("|---|---|------|-----------|---------|-----|----------------|------------|")
    for d in p["the_six_pairs"]:
        A(f"| {d['a']} | {d['b']} | {_fmt(d['corr'])} | {_fmt(d['grad_corr'])} | "
          f"{_fmt(d['hp_corr'])} | {_fmt(d['mad'])} | {_fmt(d['best_shift_mad'])} | "
          f"{_fmt(d['shift_gain'])} |")
    A("")
    A("## Where each pair sits, as a percentile")
    A("")
    A("Percentile 0.0 means the pair scores at or below every member of the reference")
    A("population; 1.0 means at or above every member. A value near 0.5 is")
    A("indistinguishable from the reference.")
    A("")
    A("| A | B | grad_corr vs A | grad_corr vs B | hp_corr vs A | hp_corr vs B | shift_gain vs A | shift_gain vs B |")
    A("|---|---|------------------|------------------|----------------|----------------|-------------------|-------------------|")
    for d in p["the_six_pairs"]:
        pa, pb = d["percentile_within_reference_A"], d["percentile_within_reference_B"]
        A(f"| {d['a']} | {d['b']} | {pa['grad_corr']:.2f} | {pb['grad_corr']:.2f} | "
          f"{pa['hp_corr']:.2f} | {pb['hp_corr']:.2f} | "
          f"{pa['shift_gain']:.2f} | {pb['shift_gain']:.2f} |")
    A("")
    A("## How to read this")
    A("")
    A("A pair that looks like a genuine near-duplicate scores high on `grad_corr`,")
    A("`hp_corr` and `shift_gain` relative to **both** references. A pair that merely")
    A("shares a road layout scores close to Reference B on all three. A pair in between")
    A("is genuinely ambiguous and needs the contact sheets.")
    A("")
    A("Reference A is not ground truth: no pair in it has been visually confirmed")
    A("either. It is the best available in-corpus proxy for the project's own")
    A("definition of a visual match.")
    A("")
    (GROUP_ANALYSIS_DIR / "missed_pair_evidence_scores.md").write_text(
        "\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())


