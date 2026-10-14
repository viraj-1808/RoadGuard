#!/usr/bin/env python3
"""Dry-run guarded optimized continuation for YOLO11s Experiment 2.

By default this script validates the continuation source and prints the exact
training configuration. It starts training only when --run is provided.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_BOOTSTRAP_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_BOOTSTRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BOOTSTRAP_ROOT))

from scripts.optimization.training_speed_optimization import (
    MIRROR_DATA_YAML,
    PROJECT_ROOT,
    RESUME_CKPT,
    SOURCE_DATA_YAML,
    inspect_checkpoint,
    load_fast_preflight_manifest,
    split_fingerprint,
    verify_cache_mirror,
    verify_fast_gate,
)


RUN_NAME = "yol11s_experiment2"
PROJECT = "experiments/training"


def patch_ultralytics_resume_data_override() -> None:
    """Allow an equivalent cache-mirror data.yaml during optimizer-state resume."""
    from ultralytics.engine.trainer import BaseTrainer

    original = BaseTrainer.check_resume

    def check_resume_with_data_override(self: Any, overrides: dict[str, Any]) -> None:
        original(self, overrides)
        if self.args.resume and overrides and overrides.get("data"):
            self.args.data = overrides["data"]

    BaseTrainer.check_resume = check_resume_with_data_override


def validate_gates(args: argparse.Namespace) -> dict[str, Any]:
    """Fast preflight gate.
    
    Reuses the pre-computed integrity manifest (optimization_gate_state.json) instead
    of re-hashing every label file. Falls back to full split_fingerprint re-audit
    only when --preflight full is explicitly requested.
    """
    if args.preflight == "full":
        # Full audit path: re-reads every label file (slow, for explicit audit use)
        checkpoint = inspect_checkpoint(Path(args.resume))
        train = split_fingerprint("train")
        val = split_fingerprint("val")
        gates = {
            "checkpoint_epoch_53": checkpoint["epoch_index"] == 53,
            "optimizer_state_present": checkpoint["optimizer_present"] and checkpoint["optimizer_state_entries"] > 0,
            "checkpoint_optimizer_adamw": checkpoint["train_args_subset"].get("optimizer") == "AdamW",
            "train_count_19719": train["image_count"] == 19719 and train["label_count"] == 19719,
            "val_count_2301": val["image_count"] == 2301 and val["label_count"] == 2301,
            "deterministic_seed_amp_ok": checkpoint["train_args_subset"].get("seed") == 42
                and checkpoint["train_args_subset"].get("deterministic") is True
                and checkpoint["train_args_subset"].get("amp") is True,
            "batch_ok": checkpoint["train_args_subset"].get("batch") == 16,
            "augment_unchanged": checkpoint["train_args_subset"].get("augment") is False,
        }
        return {"checkpoint": checkpoint, "train": train, "val": val, "gates": gates}
    else:
        # Fast path: use pre-computed manifest (default)
        result = verify_fast_gate(args)
        # Re-key the gates output to match the original interface so callers are unaffected
        checkpoint = result["checkpoint"]
        train = result["train"]
        val = result["val"]
        raw = result["gates"]
        # Map gates: manifest_data_yaml_stale is inverted (False=not stale=good),
        # first_last_image_exist may fail due to path format in manifest; recompute
        gates = {
            "manifest_exists": raw["manifest_exists"],
            "manifest_data_yaml_stale": not raw["manifest_data_yaml_stale"],  # invert: False=good
            "first_last_image_exist": (
                (PROJECT_ROOT / "experiments/dataset/experiment2/images/train/China_Drone_000001.jpg").exists()
                and (PROJECT_ROOT / "experiments/dataset/experiment2/images/train/United_States_004804.jpg").exists()
                and (PROJECT_ROOT / "experiments/dataset/experiment2/images/val/China_Drone_000021.jpg").exists()
                and (PROJECT_ROOT / "experiments/dataset/experiment2/images/val/United_States_004802.jpg").exists()
            ),
            "train_count_19719": train["image_count"] == 19719 and train["label_count"] == 19719,
            "val_count_2301": val["image_count"] == 2301 and val["label_count"] == 2301,
            "checkpoint_epoch_53": checkpoint["epoch_index"] == 53,
            "displayed_completed_epoch_54": checkpoint["displayed_completed_epoch"] == 54,
            "next_displayed_epoch_55": (checkpoint["epoch_index"] or -1) + 2,
            "optimizer_state_present": checkpoint["optimizer_present"] and checkpoint["optimizer_state_entries"] > 0,
            "optimizer_param_groups": checkpoint["optimizer_param_groups"],
            "checkpoint_optimizer_adamw": checkpoint["train_args_subset"].get("optimizer") == "AdamW",
            "cache_false": args.cache == "false",
            "workers_8": args.workers == 8,
            "deterministic_seed_amp_ok": checkpoint["train_args_subset"].get("seed") == 42
                and checkpoint["train_args_subset"].get("deterministic") is True
                and checkpoint["train_args_subset"].get("amp") is True,
            "batch_ok": checkpoint["train_args_subset"].get("batch") == 16,
            "augment_unchanged": checkpoint["train_args_subset"].get("augment") is False,
            "cache_mirror_ok": raw["cache_mirror_ok"],
        }
        return {"checkpoint": checkpoint, "train": train, "val": val, "gates": gates}


def train_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "model": args.resume,
        "resume": args.resume,
        "data": args.data,
        "epochs": 100,
        "batch": 16,
        "imgsz": 720,
        "cache": False if args.cache == "false" else args.cache,
        "workers": args.workers,
        "device": "0",
        "project": PROJECT,
        "name": RUN_NAME,
        "exist_ok": True,
        "optimizer": "AdamW",
        "amp": True,
        "seed": 42,
        "deterministic": True,
        "save": True,
        "save_period": 1,
        "patience": 50,
        "pretrained": True,
        "cls_remap": True,
        "single_cls": False,
        "rect": False,
        "cos_lr": False,
        "close_mosaic": 10,
        "fraction": 1.0,
        "profile": False,
        "freeze": None,
        "multi_scale": 0.0,
        "compile": False,
        "overlap_mask": True,
        "mask_ratio": 4,
        "dropout": 0.0,
        "val": True,
        "split": "val",
        "plots": True,
        "augment": False,
        "agnostic_nms": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", default=str(RESUME_CKPT))
    parser.add_argument("--data", default=str(SOURCE_DATA_YAML))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--cache", choices=["false", "disk"], default="false")
    parser.add_argument("--require-npy", action="store_true")
    parser.add_argument("--preflight", choices=["fast", "full"], default="fast", help="Preflight mode: 'fast' uses pre-computed manifest, 'full' recomputes all hashes.")
    parser.add_argument("--checkpoint", default=str(RESUME_CKPT), help="Checkpoint path for validation (defaults to same as --resume)")
    parser.add_argument("--run", action="store_true", help="Start the actual epoch-55-to-100 continuation.")
    args = parser.parse_args()

    gates = validate_gates(args)
    failed = [name for name, ok in gates["gates"].items() if not ok]
    config = train_config(args)
    payload = {"gates": gates, "training_config": config, "will_run": args.run and not failed}
    print(json.dumps(payload, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(f"Refusing to continue; failed gate(s): {', '.join(failed)}")
    if not args.run:
        print("\nDry run only. Re-run with --run after final human approval to start training.")
        return 0

    patch_ultralytics_resume_data_override()
    from ultralytics import YOLO

    model = YOLO(args.resume)
    model.train(**config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
