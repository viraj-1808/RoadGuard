"""
Phase 2 — Measure before training.

Validates candidate checkpoints on the labelled India validation split
(experiments/dataset/yolo_rdd2022_india, val = 229 images, ground-truth labels).

This split is fully held out from Experiment 2 training (Exp2 train = India train
+ non-India Dataset B; Exp2 val = non-India Dataset B only). It is the same
labelled split used for Experiment 1, enabling a fair same-split comparison.

NO training is performed. NO frozen test set is touched here.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Ground-truth labelled India validation split (Dataset A val).
INDIA_DATA_YAML = PROJECT_ROOT / "experiments/dataset/yolo_rdd2022_india/data.yaml"

SPRINT_DIR = PROJECT_ROOT / "experiments/results/20261010_model_improvement_sprint"
SPRINT_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    {
        "id": "exp1_best",
        "label": "Experiment 1 best (Dataset A only, epoch 100)",
        "ckpt": PROJECT_ROOT / "runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt",
    },
    {
        "id": "exp2_best_stale",
        "label": "Experiment 2 best.pt (stale, epoch 29)",
        "ckpt": PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2/weights/best.pt",
    },
    {
        "id": "exp2_epoch72",
        "label": "Experiment 2 epoch72.pt (strongest by recorded metrics)",
        "ckpt": PROJECT_ROOT / "runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt",
    },
]


def load_model(ckpt_path: Path) -> YOLO:
    """Load a YOLO model from a checkpoint.

    ultralytics YOLO() can load pure state_dicts (best.pt/last.pt) and full
    training checkpoints (epochN.pt, which contain a 'model' key). We try the
    direct load first; if it fails we extract the model state_dict into a
    temporary file inside the sprint directory and load that instead.
    """
    try:
        return YOLO(str(ckpt_path))
    except Exception as exc:  # noqa: BLE001
        print(f"[load] Direct load of {ckpt_path.name} failed ({exc}); "
              f"attempting state_dict extraction.")
        import torch

        ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
        if isinstance(ckpt, dict) and "model" in ckpt:
            model_obj = ckpt["model"]
            # EMA model may be a DetectionModel; try its state_dict
            state = model_obj.state_dict() if hasattr(model_obj, "state_dict") else model_obj
            tmp = SPRINT_DIR / f"_extracted_{ckpt_path.stem}.pt"
            torch.save(state, tmp)
            print(f"[load] Extracted state_dict to {tmp}")
            return YOLO(str(tmp))
        raise


def run_val(candidate: dict) -> dict:
    ckpt = candidate["ckpt"]
    print("=" * 70)
    print(f"Evaluating: {candidate['id']} — {candidate['label']}")
    print(f"Checkpoint: {ckpt}")
    print("=" * 70)

    if not ckpt.exists():
        return {"id": candidate["id"], "error": f"checkpoint not found: {ckpt}"}

    model = load_model(ckpt)

    t0 = time.time()
    metrics = model.val(
        data=str(INDIA_DATA_YAML),
        imgsz=720,
        batch=16,
        device=0,
        rect=True,
        save_json=True,
        project=str(SPRINT_DIR / "val_runs"),
        name=candidate["id"],
        exist_ok=False,
        verbose=True,
    )
    elapsed = time.time() - t0

    box = metrics.box
    result = {
        "id": candidate["id"],
        "label": candidate["label"],
        "checkpoint": str(ckpt),
        "elapsed_sec": round(elapsed, 1),
        "precision": float(box.mp),
        "recall": float(box.mr),
        "mAP50": float(box.map50),
        "mAP50_95": float(box.map),
        "fitness": float(box.fitness),
        "maps_per_class": [float(m) for m in metrics.maps],
        "class_names": list(metrics.names.values()),
        "nt_per_class": (
            [int(x) for x in metrics.nt_per_class]
            if getattr(metrics, "nt_per_class", None) is not None
            else None
        ),
        "results_dict": {k: (float(v) if isinstance(v, (int, float)) else v)
                         for k, v in metrics.results_dict.items()},
    }
    print(f"[val] {candidate['id']}: P={result['precision']:.4f} "
          f"R={result['recall']:.4f} mAP50={result['mAP50']:.4f} "
          f"mAP50-95={result['mAP50_95']:.4f} fitness={result['fitness']:.4f}")
    print(f"[val] per-class mAP50-95 (maps): {result['maps_per_class']}")
    return result


def main() -> int:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Sprint dir:   {SPRINT_DIR}")
    print(f"India val yaml: {INDIA_DATA_YAML} (exists={INDIA_DATA_YAML.exists()})")
    print()

    all_results = []
    for candidate in CANDIDATES:
        try:
            result = run_val(candidate)
        except Exception as exc:  # noqa: BLE001
            import traceback
            result = {
                "id": candidate["id"],
                "label": candidate["label"],
                "checkpoint": str(candidate["ckpt"]),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
            print(f"[val] {candidate['id']} FAILED: {exc}")
        all_results.append(result)
        print()

    out_json = SPRINT_DIR / "phase2_india_val_metrics.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"Wrote {out_json}")

    print()
    print("=" * 70)
    print("SUMMARY — India validation split (229 images, ground truth)")
    print("=" * 70)
    print(f"{'id':<18}{'P':>8}{'R':>8}{'mAP50':>8}{'mAP50-95':>10}{'fitness':>9}")
    for r in all_results:
        if "error" in r:
            print(f"{r['id']:<18} ERROR: {r['error'][:40]}")
        else:
            print(f"{r['id']:<18}{r['precision']:>8.4f}{r['recall']:>8.4f}"
                  f"{r['mAP50']:>8.4f}{r['mAP50_95']:>10.4f}{r['fitness']:>9.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
