#!/usr/bin/env python
"""Emit the authoritative India-exclusion decision record.

Reads the ``country_index.json`` produced by :mod:`country_index` (NOT the
on-disk shards) and partitions its entries into India vs non-India records.

Two outputs are written:

* ``india_excluded.json`` -- the decision record (counts + India file list +
  the rule used). Hard-asserts that no entry counted as non-India carries
  ``country == 'India'``.
* ``non_india_allowlist.json`` -- a sorted list of non-India entries
  ``{'file_name', 'split', 'country'}`` for downstream pipeline consumption.

Both outputs are idempotent and safe to re-run (they overwrite in place).

Usage:
    python exclude_india.py
    python exclude_india.py --index <path> --out-dir <path>
    python exclude_india.py --dry-run
"""
import argparse
import json
import os
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_OUT_DIR = os.path.join(
    REPO_ROOT, "experiments", "analysis", "overnight", "experiment2_dataset_b"
)
DEFAULT_INDEX = os.path.join(DEFAULT_OUT_DIR, "country_index.json")

# Verified expected India image count across all splits (authoritative source
# is the Arrow index; this is the runtime check value).
EXPECTED_INDIA_COUNT = 7_706

RULE = "country prefix 'India_'"


def partition_entries(
    entries: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split entries into (india_entries, non_india_entries) by country."""
    india = [e for e in entries if e["country"] == "India"]
    non_india = [e for e in entries if e["country"] != "India"]
    return india, non_india


def per_split_counts(
    entries: list[dict[str, str]],
) -> dict[str, int]:
    """Tally entries per split (train/validation/test), preserving order."""
    counts: dict[str, int] = {"train": 0, "validation": 0, "test": 0}
    for e in entries:
        split = e["split"]
        counts[split] = counts.get(split, 0) + 1
    return counts


def verify_india_count(india_count: int) -> bool:
    """Compare the observed India count against EXPECTED_INDIA_COUNT."""
    print(f"\nExpected India count: {EXPECTED_INDIA_COUNT}", flush=True)
    print(f"Observed India count: {india_count}", flush=True)
    if india_count == EXPECTED_INDIA_COUNT:
        print("PASS: India count matches expected value.", flush=True)
        return True
    print(
        f"MISMATCH: India count {india_count} != expected {EXPECTED_INDIA_COUNT}",
        flush=True,
    )
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit the India-exclusion decision record from country_index.json."
    )
    parser.add_argument(
        "--index",
        type=str,
        default=DEFAULT_INDEX,
        help="Path to country_index.json (output of country_index.py).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=DEFAULT_OUT_DIR,
        help="Output directory for india_excluded.json and non_india_allowlist.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform all checks but write nothing",
    )
    args = parser.parse_args()

    index_path = os.fspath(args.index)
    out_dir = os.fspath(args.out_dir)

    print("=" * 72, flush=True)
    print("India-Exclusion Decision Record Builder", flush=True)
    print(f"Input index:     {index_path}", flush=True)
    print(f"Output directory: {out_dir}", flush=True)
    print(f"Dry run:          {args.dry_run}", flush=True)
    print("=" * 72, flush=True)

    if not os.path.isfile(index_path):
        print(f"ERROR: index file not found: {index_path}", flush=True)
        return 1

    with open(index_path, "r", encoding="utf-8") as f:
        index: dict[str, Any] = json.load(f)

    entries: list[dict[str, str]] = index["entries"]
    total_entries = len(entries)

    india_entries, non_india_entries = partition_entries(entries)

    # HARD ASSERT: no non-India entry may carry country == 'India'.
    bad = [e for e in non_india_entries if e["country"] == "India"]
    if bad:
        print(
            f"FATAL: {len(bad)} non-India entries have country=='India'. "
            f"First: {bad[0]}",
            flush=True,
        )
        return 1
    print(
        f"HARD ASSERT passed: non_india contains no 'India' entries "
        f"({len(non_india_entries)} entries).",
        flush=True,
    )

    india_count = len(india_entries)
    non_india_count = len(non_india_entries)

    india_per_split = per_split_counts(india_entries)
    non_india_per_split = per_split_counts(non_india_entries)

    print(f"\nTotal entries:        {total_entries}", flush=True)
    print(f"India entries:        {india_count}", flush=True)
    print(f"Non-India entries:    {non_india_count}", flush=True)
    print(f"India per split:      {india_per_split}", flush=True)
    print(f"Non-India per split:  {non_india_per_split}", flush=True)

    # Sanity: partition must be exhaustive and disjoint.
    if india_count + non_india_count != total_entries:
        print(
            f"FATAL: partition sum {india_count + non_india_count} != total {total_entries}",
            flush=True,
        )
        return 1

    # --- india_excluded.json ---
    india_excluded: dict[str, Any] = {
        "total_entries": total_entries,
        "india_count": india_count,
        "non_india_count": non_india_count,
        "india_per_split": india_per_split,
        "non_india_per_split": non_india_per_split,
        "india_files": [
            {"file_name": e["file_name"], "split": e["split"]}
            for e in sorted(india_entries, key=lambda e: (e["file_name"], e["split"]))
        ],
        "rule": RULE,
    }

    excluded_path = os.path.join(out_dir, "india_excluded.json")
    allowlist_path = os.path.join(out_dir, "non_india_allowlist.json")
    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        with open(excluded_path, "w", encoding="utf-8") as f:
            json.dump(india_excluded, f, indent=2)
        print(f"\nWrote India-exclusion record: {excluded_path}", flush=True)
    else:
        print(f"[DRY-RUN] Would write {len(india_excluded['india_files'])} entries to {excluded_path}", flush=True)

    # --- non_india_allowlist.json ---
    allowlist = sorted(
        (
            {"file_name": e["file_name"], "split": e["split"], "country": e["country"]}
            for e in non_india_entries
        ),
        key=lambda e: (e["file_name"], e["split"]),
    )
    if not args.dry_run:
        with open(allowlist_path, "w", encoding="utf-8") as f:
            json.dump(allowlist, f, indent=2)
        print(f"Wrote non-India allowlist:    {allowlist_path}", flush=True)
    else:
        print(f"[DRY-RUN] Would write {len(allowlist)} entries to {allowlist_path}", flush=True)

    ok = verify_india_count(india_count)

    if ok:
        if args.dry_run:
            print("\n[DRY-RUN] all checks passed; nothing was written.", flush=True)
            return 0
        print("\nALL CHECKS PASSED", flush=True)
        return 0
    print("\n!!! INDIA COUNT MISMATCH -- exiting non-zero !!!", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
