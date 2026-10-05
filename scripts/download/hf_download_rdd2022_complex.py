#!/usr/bin/env python
"""Download dronefreak/RDD2022 dataset from Hugging Face using plain HTTPS.

This script avoids snapshot_download (which fails with 401 Xet-token error)
and instead uses the tree API for enumeration and resolve URLs for downloads.

Usage:
  python scripts/download/hf_download_rdd2022_complex.py                    # Run all steps
  python scripts/download/hf_download_rdd2022_complex.py --step 1           # Only enumerate + manifests
  python scripts/download/hf_download_rdd2022_complex.py --step 2           # Only verify single download
  python scripts/download/hf_download_rdd2022_complex.py --step 3           # Only bulk download
  python scripts/download/hf_download_rdd2022_complex.py --step 4           # Only report + log
"""
import argparse
import os
import sys
import json
import time
import re
from datetime import datetime, timezone
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, FIRST_COMPLETED, wait

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ID = "dronefreak/RDD2022"
REV = "d597e2962458f7242a72aaa1b7909118d40f5d29"
TARGET_DIR = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_hf_rdd2022"
EXPECTED_IMAGES = 38385
EXPECTED_LABELS = 38385
MAX_WORKERS = 5
MAX_RETRIES = 6
RETRY_BASE_SLEEP = 4
RATE_LIMIT_SLEEP = 30
CHUNK_SIZE = 1024 * 1024  # 1 MB
LOG_INTERVAL = 2000
DOWNLOAD_TIMEOUT = 12 * 60  # 12 minutes wall-clock for the entire download phase

BASE_API = f"https://huggingface.co/api/datasets/{REPO_ID}"
BASE_RESOLVE = f"https://huggingface.co/datasets/{REPO_ID}"

IMAGES_PREFIX = "data/images"
LABELS_PREFIX = "data/labels"

MANIFEST_IMAGES = os.path.join(TARGET_DIR, "_manifest_images.json")
MANIFEST_LABELS = os.path.join(TARGET_DIR, "_manifest_labels.json")
DOWNLOAD_LOG = os.path.join(TARGET_DIR, "_download_log.txt")
ACQUISITION_LOG = os.path.join(
    r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\analysis\overnight\dataset_b_hf_gate",
    "acquisition_log.md",
)

EXPECTED_JPG_SIZE = 65334


# ---------------------------------------------------------------------------
# Tree API: enumerate files recursively with pagination
# ---------------------------------------------------------------------------
def parse_link_header(link_header: str) -> dict:
    """Parse a Link header into {rel: url}."""
    links = {}
    if not link_header:
        return links
    for part in link_header.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'<(.+?)\s*;\s*rel="(.+?)"', part)
        if m:
            links[m.group(2)] = m.group(1)
    return links


def tree_list(prefix: str, session: requests.Session) -> list:
    """List ALL entries (files AND directories) under *prefix* using the tree API.

    Follows pagination via the ``rel="next"`` Link header.
    """
    url = f"{BASE_API}/tree/{REV}/{prefix}"
    entries = []
    while url:
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        page = resp.json()
        if isinstance(page, list):
            entries.extend(page)
        else:
            print(f"  Unexpected response for {url}: {page}", flush=True)
            break
        links = parse_link_header(resp.headers.get("Link", ""))
        url = links.get("next")
    return entries


def enumerate_files(prefix: str, session: requests.Session) -> list:
    """Recursively enumerate all file entries under *prefix*.

    - Calls tree_list on the prefix (recursive=False at the API level).
    - If the response contains directories, recurse into each.
    - If the response contains files, collect them.
    - Pagination is handled inside tree_list.
    """
    entries = tree_list(prefix, session)
    files = []
    dirs = []
    for entry in entries:
        if entry.get("type") == "directory":
            dirs.append(entry["path"])
        elif entry.get("type") == "file":
            files.append(entry)
    for d in dirs:
        sub_files = enumerate_files(d, session)
        files.extend(sub_files)
    return files


def build_manifest(prefix: str, output_file: str, session: requests.Session) -> list:
    """Enumerate files under *prefix*, write a manifest JSON, and return the list."""
    print(f"Enumerating {prefix} ...", flush=True)
    start = time.time()
    files = enumerate_files(prefix, session)

    manifest = []
    for entry in files:
        manifest.append({
            "path": entry["path"],
            "size": entry["size"],
            "lfs_sha256": entry.get("lfs", {}).get("oid") if entry.get("lfs") else None,
            "xetHash": entry.get("xetHash"),
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # per-split / per-shard summary
    splits = {}
    total_bytes = 0
    ext_counts = {}
    for item in manifest:
        ext = os.path.splitext(item["path"])[1].lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        parts = item["path"].split("/")
        if len(parts) >= 4:
            split = parts[3]
            shard = parts[4] if len(parts) > 4 else "unknown"
        else:
            split = "unknown"
            shard = "unknown"
        key = f"{split}/{shard}"
        if key not in splits:
            splits[key] = {"count": 0, "bytes": 0}
        splits[key]["count"] += 1
        splits[key]["bytes"] += item["size"]
        total_bytes += item["size"]

    print(f"  Enumerated {prefix} in {time.time() - start:.1f}s", flush=True)
    print(f"  Total files: {len(manifest)}", flush=True)
    print(f"  Total bytes: {total_bytes:,} ({total_bytes / (1024**3):.2f} GB)", flush=True)
    print(f"  Extension breakdown: {ext_counts}", flush=True)
    print(f"  Per split/shard:", flush=True)
    for key in sorted(splits):
        s = splits[key]
        print(f"    {key}: {s['count']} files, {s['bytes']:,} bytes ({s['bytes'] / (1024**2):.1f} MB)", flush=True)

    return manifest


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------
def download_one(remote_path: str, local_path: str, size: int, session: requests.Session) -> tuple:
    """Download a single file via resolve URL.

    Returns (remote_path, local_path, status_code, error_or_none).
    Skips if the file already exists with the correct size.
    Uses atomic write (.part -> os.replace).
    """
    if os.path.exists(local_path) and os.path.getsize(local_path) == size:
        return (remote_path, local_path, 200, "skipped")

    url = f"{BASE_RESOLVE}/resolve/{REV}/{remote_path}"
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)

    part_path = local_path + ".part"
    last_status = None
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=120, stream=True)
            if resp.status_code == 200:
                with open(part_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                resp.close()
                actual_size = os.path.getsize(part_path)
                if actual_size == size:
                    for _ in range(10):
                        try:
                            os.replace(part_path, local_path)
                            break
                        except OSError:
                            time.sleep(0.5)
                    else:
                        last_error = "os.replace failed repeatedly (file locked)"
                        continue
                    return (remote_path, local_path, 200, None)
                else:
                    last_error = f"size mismatch: expected {size}, got {actual_size}"
                    if attempt < MAX_RETRIES:
                        time.sleep(2 ** attempt)
                    continue
            elif resp.status_code == 429:
                last_status = 429
                last_error = "rate limited (429)"
                if attempt < MAX_RETRIES:
                    time.sleep(RATE_LIMIT_SLEEP * attempt)
            elif resp.status_code in (401, 403):
                resp.close()
                return (remote_path, local_path, resp.status_code, resp.text[:500])
            else:
                last_status = resp.status_code
                last_error = resp.text[:500] if resp.text else f"HTTP {resp.status_code}"
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
        except requests.RequestException as e:
            last_status = 0
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BASE_SLEEP * attempt)

    if os.path.exists(part_path):
        try:
            os.remove(part_path)
        except OSError:
            pass
    return (remote_path, local_path, last_status, last_error)


def bulk_download(manifest: list, base_local_dir: str, session: requests.Session,
                  label: str = "", timeout: int = DOWNLOAD_TIMEOUT) -> dict:
    """Bulk download files from a manifest using ThreadPoolExecutor.

    Returns a dict with stats: total, completed, skipped, failed, total_bytes.
    Stops cleanly if *timeout* wall-clock seconds are exceeded.
    """
    total = len(manifest)
    completed = 0
    skipped = 0
    failed_files = []
    total_bytes = 0

    print(f"\n[{label}] Starting bulk download of {total} files...", flush=True)
    start = time.time()
    deadline = start + timeout

    tasks = []
    for item in manifest:
        remote_path = item["path"]
        local_path = os.path.join(base_local_dir, remote_path)
        tasks.append((remote_path, local_path, item["size"]))

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = {
        executor.submit(download_one, rp, lp, sz, session): (rp, lp, sz)
        for rp, lp, sz in tasks
    }

    done_count = 0
    timed_out = False
    for future in as_completed(futures):
        remote_path, local_path, size = futures[future]
        done_count += 1
        try:
            result = future.result()
            rp, lp, status, error = result
            if status == 200 and error == "skipped":
                skipped += 1
            elif status == 200 and error is None:
                completed += 1
                total_bytes += size
            else:
                failed_files.append((rp, status, error))
        except Exception as e:
            failed_files.append((remote_path, 0, str(e)))
            print(f"  Exception for {remote_path}: {e}", flush=True)

        if done_count % LOG_INTERVAL == 0:
            elapsed = time.time() - start
            rate = done_count / elapsed if elapsed > 0 else 0
            print(
                f"[{label}] {done_count}/{total} done "
                f"({completed} new, {skipped} skipped, {len(failed_files)} failed) "
                f"- {elapsed:.0f}s elapsed - {rate:.1f} files/s",
                flush=True,
            )

        if time.time() > deadline:
            timed_out = True
            print(
                f"[{label}] Timeout reached ({timeout}s). "
                f"Stopping cleanly with {done_count}/{total} processed. "
                f"Remaining futures will be cancelled.",
                flush=True,
            )
            # Cancel pending (not-yet-started) futures
            for f in futures:
                if not f.done():
                    f.cancel()
            break

    # Wait briefly for any currently-running futures to finish
    executor.shutdown(wait=True, cancel_futures=True)

    elapsed = time.time() - start
    suffix = " (TIMEOUT)" if timed_out else ""
    summary_line = (
        f"[{label}] DONE{suffix}: {completed} new, {skipped} skipped, "
        f"{len(failed_files)} failed, {total_bytes:,} bytes downloaded in {elapsed:.1f}s"
    )
    print(summary_line, flush=True)

    # Append to download log
    with open(DOWNLOAD_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"[{label}] Bulk download summary\n")
        f.write(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"Total files: {total}\n")
        f.write(f"Processed: {done_count}\n")
        f.write(f"New downloaded: {completed}\n")
        f.write(f"Skipped (already present): {skipped}\n")
        f.write(f"Failed: {len(failed_files)}\n")
        f.write(f"Timed out: {timed_out}\n")
        f.write(f"Total bytes downloaded: {total_bytes:,}\n")
        f.write(f"Elapsed: {elapsed:.1f}s\n")
        f.write(f"Timeout limit: {timeout}s\n")
        if failed_files:
            f.write("Failed files:\n")
            for rp, status, error in failed_files[:100]:
                f.write(f"  {rp} | status={status} | {error}\n")
            if len(failed_files) > 100:
                f.write(f"  ... and {len(failed_files) - 100} more\n")
        f.write(f"{'='*70}\n")

    return {
        "total": total,
        "processed": done_count,
        "completed": completed,
        "skipped": skipped,
        "failed": len(failed_files),
        "total_bytes": total_bytes,
        "failed_files": failed_files,
        "timed_out": timed_out,
    }


# ---------------------------------------------------------------------------
# Cleanup helpers
# ---------------------------------------------------------------------------
def cleanup_stale_files(base_dir: str):
    """Delete stale *.incomplete and zero-byte *.part files."""
    print("Cleaning up stale *.incomplete and zero-byte *.part files...", flush=True)
    count_incomplete = 0
    count_part = 0
    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname.endswith(".incomplete"):
                try:
                    os.remove(fpath)
                    count_incomplete += 1
                except OSError:
                    pass
            elif fname.endswith(".part"):
                try:
                    if os.path.getsize(fpath) == 0:
                        os.remove(fpath)
                        count_part += 1
                except OSError:
                    pass
    print(f"  Removed {count_incomplete} .incomplete files, {count_part} zero-byte .part files", flush=True)


# ---------------------------------------------------------------------------
# Verification: single file download
# ---------------------------------------------------------------------------
def verify_single_download(session: requests.Session) -> bool:
    """Download one known file and verify size + print label contents."""
    print("\n--- STEP 2: Single file download verification ---\n", flush=True)

    test_jpg_path = "data/images/train/shard_000/China_Drone_000001.jpg"
    test_txt_path = "data/labels/train/shard_000/China_Drone_000001.txt"

    # Download the jpg
    url_jpg = f"{BASE_RESOLVE}/resolve/{REV}/{test_jpg_path}"
    resp = session.get(url_jpg, timeout=120)
    print(f"GET {url_jpg}", flush=True)
    print(f"Status: {resp.status_code}", flush=True)
    if resp.status_code == 200:
        actual_size = len(resp.content)
        print(f"Expected size: {EXPECTED_JPG_SIZE}", flush=True)
        print(f"Actual size:   {actual_size}", flush=True)
        match = "MATCH" if actual_size == EXPECTED_JPG_SIZE else "MISMATCH"
        print(f"Size check: {match}", flush=True)
    else:
        print(f"FAILED: status {resp.status_code}, body: {resp.text[:200]}", flush=True)
        return False

    # Download the txt label
    url_txt = f"{BASE_RESOLVE}/resolve/{REV}/{test_txt_path}"
    resp_txt = session.get(url_txt, timeout=120)
    print(f"\nGET {url_txt}", flush=True)
    print(f"Status: {resp_txt.status_code}", flush=True)
    if resp_txt.status_code == 200:
        print(f"Label file contents:", flush=True)
        print(resp_txt.text, flush=True)
    else:
        print(f"FAILED: status {resp_txt.status_code}, body: {resp_txt.text[:200]}", flush=True)
        return False

    return True


# ---------------------------------------------------------------------------
# Counting helpers
# ---------------------------------------------------------------------------
def count_files_on_disk(directory: str, extensions: list) -> int:
    """Count files with given extensions under directory (recursive)."""
    count = 0
    if not os.path.isdir(directory):
        return 0
    for root, dirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in extensions:
                count += 1
    return count


def count_split_files_on_disk(directory: str, extension: str) -> dict:
    """Count files per split under directory. e.g. data/images -> {train: N, test: N, valid: N}."""
    result = {}
    if not os.path.isdir(directory):
        return result
    for split in sorted(os.listdir(directory)):
        split_dir = os.path.join(directory, split)
        if os.path.isdir(split_dir):
            count = count_files_on_disk(split_dir, [extension])
            result[split] = count
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_step1(session: requests.Session) -> tuple:
    """Enumerate and build manifests."""
    print("\n--- STEP 1: Enumerate files and build manifests ---\n", flush=True)
    images_manifest = build_manifest(IMAGES_PREFIX, MANIFEST_IMAGES, session)
    labels_manifest = build_manifest(LABELS_PREFIX, MANIFEST_LABELS, session)

    img_count = len(images_manifest)
    lbl_count = len(labels_manifest)
    print(f"\nManifest summary:", flush=True)
    print(f"  Images: {img_count} entries (expected {EXPECTED_IMAGES})", flush=True)
    print(f"  Labels: {lbl_count} entries (expected {EXPECTED_LABELS})", flush=True)
    if img_count != EXPECTED_IMAGES:
        print(f"  WARNING: Expected {EXPECTED_IMAGES} image paths but found {img_count}!", flush=True)
    if lbl_count != EXPECTED_LABELS:
        print(f"  WARNING: Expected {EXPECTED_LABELS} label paths but found {lbl_count}!", flush=True)
    return images_manifest, labels_manifest


def run_step2(session: requests.Session) -> bool:
    """Verify single file download."""
    return verify_single_download(session)


def run_step3(session: requests.Session, images_manifest: list, labels_manifest: list) -> tuple:
    """Bulk download images and labels."""
    print("\n--- STEP 3: Bulk download ---\n", flush=True)
    cleanup_stale_files(TARGET_DIR)

    img_stats = bulk_download(images_manifest, TARGET_DIR, session, label="images",
                              timeout=DOWNLOAD_TIMEOUT)
    lbl_stats = bulk_download(labels_manifest, TARGET_DIR, session, label="labels",
                              timeout=DOWNLOAD_TIMEOUT)
    return img_stats, lbl_stats


def run_step4(images_manifest: list, labels_manifest: list, img_stats: dict, lbl_stats: dict):
    """Final report and acquisition log."""
    print("\n--- STEP 4: Final report ---\n", flush=True)
    resp_ok = run_step4.resp_ok if hasattr(run_step4, "resp_ok") else True
    overall_start = getattr(run_step4, "_overall_start", time.time())

    img_dir = os.path.join(TARGET_DIR, IMAGES_PREFIX)
    lbl_dir = os.path.join(TARGET_DIR, LABELS_PREFIX)

    img_on_disk = count_files_on_disk(img_dir, [".jpg", ".jpeg"])
    lbl_on_disk = count_files_on_disk(lbl_dir, [".txt"])
    valid_dir_exists = os.path.isdir(os.path.join(img_dir, "valid"))
    valid_count = (
        count_files_on_disk(os.path.join(img_dir, "valid"), [".jpg", ".jpeg"])
        if valid_dir_exists else 0
    )

    img_splits = count_split_files_on_disk(img_dir, ".jpg")
    lbl_splits = count_split_files_on_disk(lbl_dir, ".txt")

    total_bytes_downloaded = img_stats["total_bytes"] + lbl_stats["total_bytes"]

    print(f"Images: expected={EXPECTED_IMAGES}, on_disk={img_on_disk}", flush=True)
    print(f"  Per split: {img_splits}", flush=True)
    print(f"Labels: expected={EXPECTED_LABELS}, on_disk={lbl_on_disk}", flush=True)
    print(f"  Per split: {lbl_splits}", flush=True)
    print(f"Valid directory exists: {valid_dir_exists}, valid count: {valid_count}", flush=True)
    print(f"Image download: {img_stats['completed']} new, {img_stats['skipped']} skipped, {img_stats['failed']} failed, {img_stats['total_bytes']:,} bytes", flush=True)
    print(f"Label download: {lbl_stats['completed']} new, {lbl_stats['skipped']} skipped, {lbl_stats['failed']} failed, {lbl_stats['total_bytes']:,} bytes", flush=True)
    print(f"Total bytes downloaded this session: {total_bytes_downloaded:,}", flush=True)

    total_failed = img_stats["failed_files"] + lbl_stats["failed_files"]
    if total_failed:
        print(f"\nPersistently failed files ({len(total_failed)}):", flush=True)
        for rp, status, error in total_failed[:20]:
            print(f"  {rp} | status={status} | {error}", flush=True)
    else:
        print(f"\nNo persistently failed files.", flush=True)

    # Write acquisition log
    log_dir = os.path.dirname(ACQUISITION_LOG)
    os.makedirs(log_dir, exist_ok=True)

    img_count = len(images_manifest)
    lbl_count = len(labels_manifest)
    img_mismatch = img_count != EXPECTED_IMAGES
    lbl_mismatch = lbl_count != EXPECTED_LABELS

    log_lines = [
        "# RDD2022 Dataset Acquisition Log",
        "",
        "## Session Info",
        f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}",
        f"- **Repository**: {REPO_ID}",
        f"- **Revision**: {REV}",
        f"- **Target directory**: `{TARGET_DIR}`",
        "- **Method**: Plain HTTPS via `resolve/{REV}/` URLs (snapshot_download fails with 401 Xet-token error)",
        "",
        "## Step 1 — Enumeration & Manifests",
        f"- **Image manifest**: `_manifest_images.json` ({img_count} entries)",
        f"- **Label manifest**: `_manifest_labels.json` ({lbl_count} entries)",
        f"- Expected images: {EXPECTED_IMAGES}, actual: {img_count}"
        + (" — **WARNING: mismatch!**" if img_mismatch else " — matches."),
        f"- Expected labels: {EXPECTED_LABELS}, actual: {lbl_count}"
        + (" — **WARNING: mismatch!**" if lbl_mismatch else " — matches."),
        "",
        "## Step 2 — Single File Verification",
        f"- Downloaded `data/images/train/shard_000/China_Drone_000001.jpg`",
        f"- Expected size: {EXPECTED_JPG_SIZE} bytes",
        f"- Status: {'verified' if resp_ok else 'FAILED'}",
        "- Label contents (`China_Drone_000001.txt`) printed to stdout.",
        "",
        "## Step 3 — Bulk Download",
        f"- **Images**: {img_stats['completed']} new, {img_stats['skipped']} skipped, {img_stats['failed']} failed, {img_stats['total_bytes']:,} bytes",
        f"- **Labels**: {lbl_stats['completed']} new, {lbl_stats['skipped']} skipped, {lbl_stats['failed']} failed, {lbl_stats['total_bytes']:,} bytes",
        f"- **Total bytes downloaded this session**: {total_bytes_downloaded:,}",
        f"- Concurrency: {MAX_WORKERS} threads, {MAX_RETRIES} retries with exponential backoff",
        f"- Image download timed out: {img_stats.get('timed_out', False)}",
        f"- Label download timed out: {lbl_stats.get('timed_out', False)}",
        "",
        "## Step 4 — Final Report",
        f"- **Images expected**: {EXPECTED_IMAGES}",
        f"- **Images on disk**: {img_on_disk}",
        f"- **Labels expected**: {EXPECTED_LABELS}",
        f"- **Labels on disk**: {lbl_on_disk}",
        f"- **`data/images/valid/` exists**: {valid_dir_exists}",
        f"- **Valid image count**: {valid_count}",
        f"- **Persistently failed files**: {len(total_failed)}",
        "",
        "### Per-split image counts (on disk)",
    ]
    for split, count in sorted(img_splits.items()):
        log_lines.append(f"- {split}: {count} .jpg files")
    log_lines.append("")
    log_lines.append("### Per-split label counts (on disk)")
    for split, count in sorted(lbl_splits.items()):
        log_lines.append(f"- {split}: {count} .txt files")
    log_lines.append("")
    log_lines.append("### Failed files (persistently)")
    if total_failed:
        for rp, status, error in total_failed[:50]:
            log_lines.append(f"- `{rp}` | status={status} | {error[:200]}")
        if len(total_failed) > 50:
            log_lines.append(f"- ... and {len(total_failed) - 50} more")
    else:
        log_lines.append("None.")
    log_lines.append("")
    log_lines.append(f"### Total bytes downloaded (this session): {total_bytes_downloaded:,}")
    log_lines.append("")
    log_content = "\n".join(log_lines)

    with open(ACQUISITION_LOG, "w", encoding="utf-8") as f:
        f.write(log_content)
    print(f"\nAcquisition log written to: {ACQUISITION_LOG}", flush=True)


def main():
    global MAX_WORKERS, DOWNLOAD_TIMEOUT

    parser = argparse.ArgumentParser(description="Download dronefreak/RDD2022 via plain HTTPS")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4], default=0,
                        help="Which step to run: 1=enumerate, 2=verify, 3=download, 4=report. Default 0 = all steps.")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"Number of download threads (default {MAX_WORKERS})")
    parser.add_argument("--timeout", type=int, default=DOWNLOAD_TIMEOUT,
                        help=f"Download timeout in seconds (default {DOWNLOAD_TIMEOUT})")
    args = parser.parse_args()

    MAX_WORKERS = args.workers
    DOWNLOAD_TIMEOUT = args.timeout

    overall_start = time.time()
    run_step4._overall_start = overall_start

    print("=" * 70, flush=True)
    print("Hugging Face RDD2022 Downloader (plain HTTPS)", flush=True)
    print(f"Repo: {REPO_ID}, Revision: {REV}", flush=True)
    print(f"Target: {TARGET_DIR}", flush=True)
    print(f"Expected: {EXPECTED_IMAGES} images, {EXPECTED_LABELS} labels", flush=True)
    print(f"Workers: {MAX_WORKERS}, Download timeout: {DOWNLOAD_TIMEOUT}s", flush=True)
    print("=" * 70, flush=True)

    os.makedirs(TARGET_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(ACQUISITION_LOG), exist_ok=True)

    # Create session with persistent connection
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Load manifests if they exist
    def load_manifest(path: str) -> list:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    images_manifest = load_manifest(MANIFEST_IMAGES)
    labels_manifest = load_manifest(MANIFEST_LABELS)

    run_all = args.step == 0

    # -- STEP 1: Enumerate --
    if run_all or args.step == 1:
        images_manifest, labels_manifest = run_step1(session)

    if images_manifest is None or labels_manifest is None:
        print("ERROR: Manifests not available. Run --step 1 first.", flush=True)
        return 1

    # -- STEP 2: Verify single download --
    resp_ok = True
    run_step4.resp_ok = True
    if run_all or args.step == 2:
        resp_ok = run_step2(session)
        run_step4.resp_ok = resp_ok

    # -- STEP 3: Bulk download --
    img_stats = {"total": 0, "completed": 0, "skipped": 0, "failed": 0,
                 "total_bytes": 0, "failed_files": [], "timed_out": False}
    lbl_stats = {"total": 0, "completed": 0, "skipped": 0, "failed": 0,
                 "total_bytes": 0, "failed_files": [], "timed_out": False}
    if run_all or args.step == 3:
        img_stats, lbl_stats = run_step3(session, images_manifest, labels_manifest)

    # -- STEP 4: Report --
    if run_all or args.step == 4:
        run_step4(images_manifest, labels_manifest, img_stats, lbl_stats)

    elapsed = time.time() - overall_start
    print(f"\nAll done. Total elapsed: {elapsed:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())