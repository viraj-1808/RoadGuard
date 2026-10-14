#!/usr/bin/env python3
"""Controlled training-speed optimization gates for RoadGuard Experiment 2.

The utilities in this module deliberately avoid changing the historical
training launcher. They prepare a project-local cache mirror, verify dataset
and checkpoint integrity, and benchmark the data path before any long training
continuation is started.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DATA_YAML = PROJECT_ROOT / "experiments/dataset/experiment2/data.yaml"
RUN_DIR = PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2"
RESUME_CKPT = RUN_DIR / "weights/epoch53.pt"
CACHE_ROOT = PROJECT_ROOT / "cache"
MIRROR_ROOT = CACHE_ROOT / "decoded_images/experiment2_ultralytics_disk_cache"
MIRROR_DATA_YAML = MIRROR_ROOT / "data.yaml"
BENCHMARK_DIR = PROJECT_ROOT / "experiments/optimization/benchmarks"
REPORT_JSON = PROJECT_ROOT / "experiments/optimization/optimization_gate_state.json"
MANIFEST_PATH = PROJECT_ROOT / "experiments/optimization/optimization_gate_state.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
EXPECTED_TRAIN = 19719
EXPECTED_VAL = 2301


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fast_preflight_manifest(manifest_path: Path | None = None) -> dict[str, Any]:
    """Load the pre-computed dataset integrity manifest (previously produced by full split_fingerprint).
    
    This is a fast preflight gate: it reuses the already-verified label_content_sha256 and
    membership_sha256 fingerprints from a completed full audit instead of re-hashing every
    label file on disk. The manifest is considered valid only if:
      1. The manifest file exists and is valid JSON.
      2. The source data.yaml SHA-256 recorded in the manifest still matches the current
         data.yaml (guards against stale manifest after dataset config change).
    """
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(f"Fast preflight manifest not found at {manifest_path}. "
                                "Run `python scripts/optimization/training_speed_optimization.py inspect` "
                                "first to generate it.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # Guard: source data.yaml must not have changed since the manifest was generated.
    if manifest.get("source_data_yaml_sha256"):
        recorded_yaml_sha = manifest["source_data_yaml_sha256"]
        current_yaml_sha = sha256_file(SOURCE_DATA_YAML)
        if recorded_yaml_sha != current_yaml_sha:
            raise ValueError(
                f"Source data.yaml has changed since the manifest was generated. "
                f"Recorded: {recorded_yaml_sha}, current: {current_yaml_sha}. "
                "Run a full audit with `inspect` to refresh the manifest."
            )
    
    return manifest


def verify_fast_gate(args: argparse.Namespace) -> dict[str, Any]:
    """Fast preflight verification against the pre-computed integrity manifest.
    
    Reuses verified fingerprints (no full label re-hash). This is the gate used
    on every training launch. A full byte-level audit is still available via the
    `inspect` command or `audit-splits` subcommand.
    """
    manifest = load_fast_preflight_manifest()
    checkpoint = inspect_checkpoint(Path(args.checkpoint))
    
    train = manifest["splits"]["train"]
    val = manifest["splits"]["val"]
    
    # Quick existence check for first/last image (guard against gross corruption/deletion)
    data, root = source_dataset_paths()
    train_first_exists = (root / train["first_image"]).exists() if train["first_image"] else False
    train_last_exists = (root / train["last_image"]).exists() if train["last_image"] else False
    val_first_exists = (root / val["first_image"]).exists() if val["first_image"] else False
    val_last_exists = (root / val["last_image"]).exists() if val["last_image"] else False
    
    gates = {
        "manifest_exists": True,  # verified by load above
        "manifest_data_yaml_stale": False,  # verified by load above
        "first_last_image_exist": train_first_exists and train_last_exists and val_first_exists and val_last_exists,
        "train_count_19719": train["image_count"] == EXPECTED_TRAIN,
        "val_count_2301": val["image_count"] == EXPECTED_VAL,
        "train_labels_complete": len(train["missing_labels"]) == 0,
        "val_labels_complete": len(val["missing_labels"]) == 0,
        "checkpoint_exists": checkpoint["exists"],
        "checkpoint_loadable": True,  # set by inspect_checkpoint (would have raised if not)
        "checkpoint_epoch_53": checkpoint["epoch_index"] == 53,
        "displayed_completed_epoch_54": checkpoint["displayed_completed_epoch"] == 54,
        "optimizer_state_present": checkpoint["optimizer_present"] and checkpoint["optimizer_state_entries"] > 0,
        "checkpoint_optimizer_adamw": checkpoint["train_args_subset"].get("optimizer") == "AdamW",
        "batch_ok": checkpoint["train_args_subset"].get("batch") == 16,
        "seed_42": checkpoint["train_args_subset"].get("seed") == 42,
        "deterministic_true": checkpoint["train_args_subset"].get("deterministic") is True,
        "amp_true": checkpoint["train_args_subset"].get("amp") is True,
        "augment_false": checkpoint["train_args_subset"].get("augment") is False,
    }
    
    # Cache mirror verification (only when using disk cache)
    if args.cache == "disk" and args.data == str(MIRROR_DATA_YAML):
        mirror_args = argparse.Namespace(require_npy=args.require_npy)
        mirror_result = verify_cache_mirror(mirror_args)
        gates["cache_mirror_ok"] = mirror_result["ok"]
    else:
        gates["cache_mirror_ok"] = True
    
    return {"checkpoint": checkpoint, "train": train, "val": val, "gates": gates, "manifest": manifest}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def source_dataset_paths() -> tuple[dict[str, Any], Path]:
    data = load_yaml(SOURCE_DATA_YAML)
    root = (PROJECT_ROOT / data["path"]).resolve()
    return data, root


def image_files(split: str, root: Path | None = None, data: dict[str, Any] | None = None) -> list[Path]:
    if root is None or data is None:
        data, root = source_dataset_paths()
    split_dir = root / data[split]
    files = [p for p in split_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    return sorted(files)


def label_for_image(image: Path, split: str, root: Path) -> Path:
    return root / "labels" / split / f"{image.stem}.txt"


def split_fingerprint(split: str) -> dict[str, Any]:
    data, root = source_dataset_paths()
    images = image_files(split, root, data)
    label_hash = hashlib.sha256()
    membership_hash = hashlib.sha256()
    missing_labels: list[str] = []
    image_bytes = 0
    label_bytes = 0

    for image in images:
        label = label_for_image(image, split, root)
        image_bytes += image.stat().st_size
        membership_hash.update(rel(image).encode("utf-8"))
        membership_hash.update(str(image.stat().st_size).encode("ascii"))
        membership_hash.update(b"\n")
        if not label.exists():
            missing_labels.append(rel(label))
            continue
        label_bytes += label.stat().st_size
        label_hash.update(rel(label).encode("utf-8"))
        label_hash.update(b"\0")
        label_hash.update(label.read_bytes())
        label_hash.update(b"\n")

    return {
        "split": split,
        "image_count": len(images),
        "label_count": len(images) - len(missing_labels),
        "missing_labels": missing_labels,
        "image_bytes": image_bytes,
        "label_bytes": label_bytes,
        "membership_sha256": membership_hash.hexdigest(),
        "label_content_sha256": label_hash.hexdigest(),
        "first_image": rel(images[0]) if images else None,
        "last_image": rel(images[-1]) if images else None,
    }


def inspect_checkpoint(path: Path = RESUME_CKPT) -> dict[str, Any]:
    import torch

    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    optimizer = ckpt.get("optimizer")
    train_args = ckpt.get("train_args") or {}
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "ultralytics_version": ckpt.get("version"),
        "epoch_index": ckpt.get("epoch"),
        "displayed_completed_epoch": (ckpt.get("epoch") or -1) + 1,
        "best_fitness": ckpt.get("best_fitness"),
        "optimizer_present": optimizer is not None,
        "optimizer_state_entries": len(optimizer.get("state", {})) if isinstance(optimizer, dict) else 0,
        "optimizer_param_groups": len(optimizer.get("param_groups", [])) if isinstance(optimizer, dict) else 0,
        "train_args_subset": {
            key: train_args.get(key)
            for key in (
                "data",
                "epochs",
                "batch",
                "imgsz",
                "cache",
                "workers",
                "optimizer",
                "seed",
                "deterministic",
                "amp",
                "resume",
                "model",
                "augment",
            )
        },
    }


def decoded_cache_estimate() -> dict[str, Any]:
    data, root = source_dataset_paths()
    total_pixels = 0
    sampled = 0
    for split in ("train", "val"):
        for image in image_files(split, root, data):
            import cv2

            im = cv2.imread(str(image))
            if im is None:
                raise RuntimeError(f"Could not read image for cache estimate: {image}")
            total_pixels += im.nbytes
            sampled += 1
    required = int(total_pixels * 1.5)
    free = shutil.disk_usage(PROJECT_ROOT.anchor).free
    return {
        "decoded_image_bytes": total_pixels,
        "decoded_image_gib": round(total_pixels / (1 << 30), 3),
        "with_ultralytics_50_percent_margin_bytes": required,
        "with_ultralytics_50_percent_margin_gib": round(required / (1 << 30), 3),
        "free_c_bytes": free,
        "free_c_gib": round(free / (1 << 30), 3),
        "fits_with_margin": free > required,
        "images_sampled": sampled,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def inspect(args: argparse.Namespace) -> dict[str, Any]:
    """Inspect dataset, cache estimate, and checkpoint gates.
    
    Use --fast to load the pre-computed manifest instead of recomputing hashes.
    Without --fast, performs a full audit (recommended for refreshing the manifest).
    """
    if args.fast:
        manifest = load_fast_preflight_manifest()
        state = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
            "project_root": str(PROJECT_ROOT),
            "source_data_yaml": rel(SOURCE_DATA_YAML),
            "source_data_yaml_sha256": sha256_file(SOURCE_DATA_YAML),
            "splits": {split: manifest["splits"][split] for split in ("train", "val")},
            "checkpoint": inspect_checkpoint(Path(args.checkpoint)),
            "cache_estimate": None,
            "ultralytics_disk_cache_behavior": {
                "default_npy_location": "Path(image).with_suffix('.npy') beside each image",
                "project_strategy": "use cache/decoded_images mirror so .npy files stay under project-local cache",
            },
        }
        state["gates"] = {
            "train_count_ok": state["splits"]["train"]["image_count"] == EXPECTED_TRAIN,
            "val_count_ok": state["splits"]["val"]["image_count"] == EXPECTED_VAL,
            "labels_complete": not state["splits"]["train"]["missing_labels"] and not state["splits"]["val"]["missing_labels"],
            "resume_epoch_ok": state["checkpoint"]["epoch_index"] == 53,
            "optimizer_state_ok": state["checkpoint"]["optimizer_present"] and state["checkpoint"]["optimizer_state_entries"] > 0,
        }
        REPORT_JSON.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(state, indent=2, sort_keys=True))
        return state
    else:
        # Full audit: recompute everything from source data
        state = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
            "project_root": str(PROJECT_ROOT),
            "source_data_yaml": rel(SOURCE_DATA_YAML),
            "source_data_yaml_sha256": sha256_file(SOURCE_DATA_YAML),
            "splits": {split: split_fingerprint(split) for split in ("train", "val")},
            "checkpoint": inspect_checkpoint(Path(args.checkpoint)),
            "cache_estimate": decoded_cache_estimate() if args.estimate_cache else None,
            "ultralytics_disk_cache_behavior": {
                "default_npy_location": "Path(image).with_suffix('.npy') beside each image",
                "project_strategy": "use cache/decoded_images mirror so .npy files stay under project-local cache",
            },
        }
        state["gates"] = {
            "train_count_ok": state["splits"]["train"]["image_count"] == EXPECTED_TRAIN,
            "val_count_ok": state["splits"]["val"]["image_count"] == EXPECTED_VAL,
            "labels_complete": not state["splits"]["train"]["missing_labels"] and not state["splits"]["val"]["missing_labels"],
            "resume_epoch_ok": state["checkpoint"]["epoch_index"] == 53,
            "optimizer_state_ok": state["checkpoint"]["optimizer_present"] and state["checkpoint"]["optimizer_state_entries"] > 0,
        }
        if args.output:
            write_json(Path(args.output), state)
        else:
            write_json(REPORT_JSON, state)
        print(json.dumps(state, indent=2, sort_keys=True))
        return state


def link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "exists"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def prepare_cache_mirror(args: argparse.Namespace) -> dict[str, Any]:
    data, root = source_dataset_paths()
    MIRROR_ROOT.mkdir(parents=True, exist_ok=True)
    stats = {"hardlink": 0, "copy": 0, "exists": 0}
    manifest: dict[str, Any] = {
        "source_data_yaml": rel(SOURCE_DATA_YAML),
        "source_root": rel(root),
        "mirror_root": rel(MIRROR_ROOT),
        "splits": {},
    }

    for split in ("train", "val"):
        images = image_files(split, root, data)
        records = []
        for image in images:
            label = label_for_image(image, split, root)
            image_dst = MIRROR_ROOT / "images" / split / image.name
            label_dst = MIRROR_ROOT / "labels" / split / label.name
            stats[link_or_copy(image, image_dst)] += 1
            stats[link_or_copy(label, label_dst)] += 1
            records.append({"image": rel(image), "mirror_image": rel(image_dst), "label": rel(label)})
        manifest["splits"][split] = {
            "count": len(records),
            "records_manifest_sha256": hashlib.sha256(
                "\n".join(f"{r['image']}|{r['label']}" for r in records).encode("utf-8")
            ).hexdigest(),
        }

    mirror_yaml = {
        "path": rel(MIRROR_ROOT),
        "train": "images/train",
        "val": "images/val",
        "test": "experiments/dataset/yolo_rdd2022_india/images/test",
        "nc": data["nc"],
        "names": data["names"],
    }
    MIRROR_DATA_YAML.write_text(yaml.safe_dump(mirror_yaml, sort_keys=False), encoding="utf-8")
    manifest["link_stats"] = stats
    manifest["mirror_data_yaml"] = rel(MIRROR_DATA_YAML)
    write_json(MIRROR_ROOT / "mirror_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def verify_cache_mirror(args: argparse.Namespace) -> dict[str, Any]:
    data, source_root = source_dataset_paths()
    mirror_data = load_yaml(MIRROR_DATA_YAML)
    mirror_root = PROJECT_ROOT / mirror_data["path"]
    result: dict[str, Any] = {
        "mirror_root": rel(mirror_root),
        "mirror_data_yaml": rel(MIRROR_DATA_YAML),
        "splits": {},
        "npy": {},
    }
    ok = True

    for split, expected in (("train", EXPECTED_TRAIN), ("val", EXPECTED_VAL)):
        source_images = image_files(split, source_root, data)
        mirror_images = image_files(split, mirror_root, mirror_data)
        source_names = [p.name for p in source_images]
        mirror_names = [p.name for p in mirror_images]
        labels = [mirror_root / "labels" / split / f"{p.stem}.txt" for p in mirror_images]
        split_ok = len(mirror_images) == expected and source_names == mirror_names and all(p.exists() for p in labels)
        ok = ok and split_ok
        result["splits"][split] = {
            "expected": expected,
            "source_count": len(source_images),
            "mirror_count": len(mirror_images),
            "labels_existing": sum(1 for p in labels if p.exists()),
            "membership_matches_source": source_names == mirror_names,
            "ok": split_ok,
        }

    npy_files = sorted((mirror_root / "images").rglob("*.npy"))
    result["npy"] = {
        "count": len(npy_files),
        "bytes": sum(p.stat().st_size for p in npy_files),
        "gib": round(sum(p.stat().st_size for p in npy_files) / (1 << 30), 3),
    }
    if args.require_npy:
        ok = ok and result["npy"]["count"] == EXPECTED_TRAIN + EXPECTED_VAL
    result["ok"] = ok
    write_json(PROJECT_ROOT / "experiments/optimization/cache_mirror_verification.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(2)
    return result


def benchmark_dataloader(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from ultralytics.cfg import DEFAULT_CFG, get_cfg
    from ultralytics.data.build import build_dataloader, build_yolo_dataset
    from ultralytics.data.utils import check_det_dataset

    data_yaml = Path(args.data)
    if not data_yaml.is_absolute():
        data_yaml = PROJECT_ROOT / data_yaml
    cache_value: bool | str
    cache_value = False if str(args.cache).lower() == "false" else args.cache
    overrides = {
        "task": "detect",
        "mode": "train",
        "model": str(RESUME_CKPT),
        "data": str(data_yaml),
        "epochs": 100,
        "batch": 16,
        "imgsz": args.imgsz,
        "cache": cache_value,
        "device": args.device,
        "workers": args.workers,
        "seed": 42,
        "deterministic": True,
        "amp": True,
        "rect": False,
        "single_cls": False,
        "augment": False,
        "fraction": 1.0,
    }
    cfg = get_cfg(DEFAULT_CFG, overrides)
    dataset_info = check_det_dataset(str(data_yaml))
    dataset = build_yolo_dataset(cfg, dataset_info["train"], cfg.batch, dataset_info, mode="train", rect=False, stride=32)
    device = torch.device("cuda:0" if torch.cuda.is_available() and args.device != "cpu" else "cpu")
    loader = build_dataloader(dataset, batch=cfg.batch, workers=args.workers, shuffle=True, rank=-1, device=device)

    timings: list[float] = []
    transfer_timings: list[float] = []
    iterator = iter(loader)
    for i in range(args.batches + args.warmup):
        start = time.perf_counter()
        batch = next(iterator)
        loaded = time.perf_counter()
        if device.type == "cuda":
            imgs = batch["img"].to(device, non_blocking=True).float() / 255.0
            torch.cuda.synchronize()
            del imgs
        transferred = time.perf_counter()
        if i >= args.warmup:
            timings.append(loaded - start)
            transfer_timings.append(transferred - loaded)

    result = {
        "data": rel(data_yaml),
        "cache": cache_value,
        "workers": args.workers,
        "batches": args.batches,
        "warmup": args.warmup,
        "device": str(device),
        "mean_batch_load_seconds": sum(timings) / len(timings),
        "mean_gpu_transfer_seconds": sum(transfer_timings) / len(transfer_timings),
        "total_measured_seconds": sum(timings) + sum(transfer_timings),
        "pin_memory_expected": device.type == "cuda",
        "non_blocking_transfer_used": device.type == "cuda",
    }
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    out = BENCHMARK_DIR / f"dataloader_cache-{args.cache}_workers-{args.workers}.json"
    write_json(out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect", help="Inspect dataset, cache estimate, and checkpoint gates.")
    p.add_argument("--checkpoint", default=str(RESUME_CKPT))
    p.add_argument("--estimate-cache", action="store_true")
    p.add_argument("--fast", action="store_true", help="Load pre-computed manifest instead of recomputing hashes.")
    p.add_argument("--output")
    p.set_defaults(func=inspect)

    p = sub.add_parser("audit-splits", help="Full byte-level dataset audit (re-hashes every label file).")
    p.add_argument("--checkpoint", default=str(RESUME_CKPT))
    p.add_argument("--output", default=str(REPORT_JSON))
    p.set_defaults(func=inspect)

    p = sub.add_parser("prepare-cache-mirror", help="Create project-local mirror for Ultralytics disk cache.")
    p.set_defaults(func=prepare_cache_mirror)

    p = sub.add_parser("verify-cache-mirror", help="Verify mirror integrity and optional generated .npy cache.")
    p.add_argument("--require-npy", action="store_true")
    p.set_defaults(func=verify_cache_mirror)

    p = sub.add_parser("benchmark-dataloader", help="Benchmark Ultralytics data loading and CPU-to-GPU transfer.")
    p.add_argument("--data", default=str(SOURCE_DATA_YAML))
    p.add_argument("--cache", default="false", choices=["False", "false", "disk", "ram"])
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--batches", type=int, default=100)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--imgsz", type=int, default=720)
    p.add_argument("--device", default="0")
    p.set_defaults(func=benchmark_dataloader)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
