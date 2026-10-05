#!/usr/bin/env python
"""Build the authoritative country index for the HDDRDD2022 dataset.

This script treats the HuggingFace Arrow metadata (loaded via
``datasets.load_from_disk``) as the *complete and authoritative* record of
which images exist and which split they belong to. It does NOT walk the
on-disk image/label shards.

For every record it parses the originating country from the ``file_name``
(see :func:`parse_country` for the filename rules -- note that China filenames
have THREE underscore-delimited parts and must NOT be naively split on the
first underscore), tallies per-split / per-country counts, and writes a sorted
country index JSON. It then verifies the tallies against the expected totals
and exits non-zero on any mismatch.

Usage:
    python country_index.py
    python country_index.py --hf-root <path> --out-dir <path>
    python country_index.py --dry-run
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any

from datasets import DatasetDict, load_from_disk

# Repository root is two levels up from this script (scripts/experiment2/).
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_HF_ROOT = os.path.join(
    REPO_ROOT, "experiments", "dataset", "raw_hf_rdd2022"
)
DEFAULT_OUT_DIR = os.path.join(
    REPO_ROOT, "experiments", "analysis", "overnight", "experiment2_dataset_b"
)

REPO_ID = "dronefreak/RDD2022"

# Verified expected counts. The script VERIFIES actual Arrow-derived counts
# against these at runtime; a mismatch is reported loudly and exits non-zero.
EXPECTED_GRAND_TOTAL = 38_385
EXPECTED_SPLIT_TOTALS = {
    "train": 26_869,
    "validation": 5_758,
    "test": 5_758,
}
EXPECTED_COUNTRY_TOTALS = {
    "Japan": 10_506,
    "Norway": 8_161,
    "India": 7_706,
    "United States": 4_805,
    "China": 4_378,
    "Czech": 2_829,
}

COUNTRIES_IN_ORDER = ["China", "India", "Japan", "Norway", "United States", "Czech"]
SPLITS_IN_ORDER = ["train", "validation", "test"]


def parse_country(file_name: str) -> str:
    """Derive the originating country from an RDD2022 ``file_name``.

    The filename is taken as a basename (any directory component is stripped)
    with or without its ``.jpg`` extension.

    Rules:
      * ``China_Drone_*`` / ``China_MotorBike_*`` / ``China_Satellite_*``
        -> ``China``. China filenames have THREE underscore-delimited parts,
        so a naive ``split('_')[0]`` would be wrong only if it returned
        "China" correctly -- it does -- BUT the rule is called out explicitly
        because several countries map from the first token and China's extra
        tokens must not be mistaken for a different country.
      * ``United_*``      -> ``United States``.
      * ``India_*``       -> ``India``.
      * ``Japan_*``       -> ``Japan``.
      * ``Norway_*``      -> ``Norway``.
      * ``Czech_*``       -> ``Czech``.

    Raises:
        ValueError: if the filename prefix is not recognised.
    """
    file_name = str(file_name)
    base = os.path.basename(file_name)
    stem = os.path.splitext(base)[0]
    if stem.startswith("China_"):
        return "China"
    if stem.startswith("United_"):
        return "United States"
    prefix = stem.split("_", 1)[0]
    mapping = {
        "India": "India",
        "Japan": "Japan",
        "Norway": "Norway",
        "Czech": "Czech",
    }
    if prefix in mapping:
        return mapping[prefix]
    raise ValueError(f"Unrecognised country prefix in filename: {file_name!r}")


def get_git_revision() -> str:
    """Return the current ``git rev-parse HEAD`` of the repo, or ``'unknown'``."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def build_index(hf_root: str) -> dict[str, Any]:
    """Load the DatasetDict from *hf_root* and build the country-index dict.

    The returned dict contains exactly the keys required for
    ``country_index.json``: ``generated_by``, ``source_repo``,
    ``source_revision``, ``totals``, ``per_split_country``, ``entries``.
    """
    ds_dict: DatasetDict = load_from_disk(hf_root)

    entries: list[dict[str, str]] = []
    country_totals: dict[str, int] = {c: 0 for c in COUNTRIES_IN_ORDER}
    per_split_country: dict[str, dict[str, int]] = {
        s: {c: 0 for c in COUNTRIES_IN_ORDER} for s in SPLITS_IN_ORDER
    }
    split_totals: dict[str, int] = {s: 0 for s in SPLITS_IN_ORDER}

    for split in SPLITS_IN_ORDER:
        if split not in ds_dict:
            print(f"WARNING: split '{split}' missing from loaded DatasetDict", flush=True)
            continue
        split_ds = ds_dict[split]
        # Materialise only the file_name column (the Arrow source of truth).
        file_names = split_ds["file_name"]
        for fn in file_names:
            country = parse_country(fn)
            entries.append({"file_name": str(fn), "split": split, "country": country})
            if country not in country_totals:
                country_totals[country] = 0
            country_totals[country] += 1
            if country not in per_split_country[split]:
                per_split_country[split][country] = 0
            per_split_country[split][country] += 1
            split_totals[split] += 1

    # Deterministic ordering by filename.
    entries.sort(key=lambda e: (e["file_name"], e["split"]))

    totals: dict[str, int] = dict(country_totals)
    totals["TOTAL"] = sum(split_totals.values())

    index: dict[str, Any] = {
        "generated_by": "scripts/experiment2/country_index.py",
        "source_repo": REPO_ID,
        "source_revision": get_git_revision(),
        "totals": totals,
        "per_split_country": {
            s: per_split_country[s] for s in SPLITS_IN_ORDER if s in ds_dict
        },
        "entries": entries,
    }
    return index


def print_summary_table(index: dict[str, Any]) -> None:
    """Print a human-readable per-split / per-country count table."""
    totals = index["totals"]
    per_split_country = index["per_split_country"]
    countries = COUNTRIES_IN_ORDER

    header = ["Split"] + countries + ["|Total"]
    rows: list[list[str]] = [header]
    grand_row_vals = {c: 0 for c in countries}
    grand_total = 0
    for split in SPLITS_IN_ORDER:
        row = [split]
        split_total = 0
        for c in countries:
            val = per_split_country.get(split, {}).get(c, 0)
            row.append(str(val))
            grand_row_vals[c] += val
            split_total += val
        row.append(f"|{split_total}")
        rows.append(row)
    grand_row = ["TOTAL"] + [str(grand_row_vals[c]) for c in countries]
    grand_row.append(f"|{totals.get('TOTAL', 0)}")
    rows.append(grand_row)

    # Column widths.
    widths = [max(len(rows[r][i]) for r in range(len(rows))) for i in range(len(header))]
    print("\nPer-split / per-country image counts:", flush=True)
    print("  " + "  ".join(rows[0][i].ljust(widths[i]) for i in range(len(header))), flush=True)
    print("  " + "-" * (sum(widths) + 2 * (len(header) - 1)), flush=True)
    for row in rows[1:]:
        print("  " + "  ".join(row[i].ljust(widths[i]) for i in range(len(header))), flush=True)


def verify_index(index: dict[str, Any]) -> bool:
    """Verify index totals against EXPECTED_* constants. Returns True if all pass."""
    totals = index["totals"]
    per_split_country = index["per_split_country"]
    ok = True

    print("\nVerification against expected totals:", flush=True)

    # Per-country grand totals.
    for country in COUNTRIES_IN_ORDER:
        expected = EXPECTED_COUNTRY_TOTALS[country]
        actual = totals.get(country, 0)
        if actual == expected:
            print(f"  PASS    country '{country}': {actual} (expected {expected})", flush=True)
        else:
            print(
                f"  MISMATCH country '{country}': got {actual}, expected {expected}",
                flush=True,
            )
            ok = False

    # Any unexpected (extra) country present in the data?
    for country in totals:
        if country == "TOTAL":
            continue
        if country not in EXPECTED_COUNTRY_TOTALS:
            print(
                f"  MISMATCH unexpected country '{country}': {totals[country]} "
                f"(not in expected set)",
                flush=True,
            )
            ok = False

    # Per-split totals.
    for split in SPLITS_IN_ORDER:
        expected = EXPECTED_SPLIT_TOTALS[split]
        actual = sum(per_split_country.get(split, {}).values())
        if actual == expected:
            print(f"  PASS    split '{split}': {actual} (expected {expected})", flush=True)
        else:
            print(
                f"  MISMATCH split '{split}': got {actual}, expected {expected}",
                flush=True,
            )
            ok = False

    # Grand total.
    grand = totals.get("TOTAL", 0)
    if grand == EXPECTED_GRAND_TOTAL:
        print(f"  PASS    grand total: {grand} (expected {EXPECTED_GRAND_TOTAL})", flush=True)
    else:
        print(
            f"  MISMATCH grand total: got {grand}, expected {EXPECTED_GRAND_TOTAL}",
            flush=True,
        )
        ok = False

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the authoritative country index from RDD2022 Arrow metadata."
    )
    parser.add_argument(
        "--hf-root",
        type=str,
        default=DEFAULT_HF_ROOT,
        help="Path to the HuggingFace DatasetDict directory (Arrow).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=DEFAULT_OUT_DIR,
        help="Output directory for country_index.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform all checks but write nothing",
    )
    args = parser.parse_args()

    hf_root = os.fspath(args.hf_root)
    out_dir = os.fspath(args.out_dir)

    print("=" * 72, flush=True)
    print("Country Index Builder (HDDRDD2022 Arrow metadata)", flush=True)
    print(f"DatasetDict source: {hf_root}", flush=True)
    print(f"Output directory:   {out_dir}", flush=True)
    print(f"Source repo:        {REPO_ID}", flush=True)
    print(f"Dry run:            {args.dry_run}", flush=True)
    print("=" * 72, flush=True)

    if not os.path.isdir(hf_root):
        print(f"ERROR: hf-root does not exist or is not a directory: {hf_root}", flush=True)
        return 1

    index = build_index(hf_root)

    out_path = os.path.join(out_dir, "country_index.json")
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        # Idempotent: overwriting the same path is safe to re-run.
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
        print(
            f"\nWrote country index: {out_path} "
            f"({len(index['entries'])} entries, source_revision={index['source_revision']})",
            flush=True,
        )
    else:
        print(f"[DRY-RUN] Would write {len(index['entries'])} entries to {out_path}", flush=True)

    print_summary_table(index)
    ok = verify_index(index)

    if ok:
        if args.dry_run:
            print("\n[DRY-RUN] all checks passed; nothing was written.", flush=True)
            return 0
        print("\nALL CHECKS PASSED", flush=True)
        return 0
    print("\n!!! VERIFICATION MISMATCH DETECTED -- exiting non-zero !!!", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
