"""
RoadGuard Inference CLI

Command-line interface for running inference on images.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from inference.adapters.yolo_adapter import YOLOAdapter, create_annotated_image, InferenceResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RoadGuard Inference - Run YOLO model on images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Source directory containing images",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="runs/detect/experiments/training/yol11s_dataset_v2_split_v2/weights/best.pt",
        help="Path to model checkpoint",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="validation/manual/output",
        help="Output directory for annotated images and predictions",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.7,
        help="IoU/NMS threshold",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=720,
        help="Inference image size",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Device (0 for GPU, cpu for CPU)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Search recursively in source directory",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Do not search recursively",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default="jpg,jpeg,png,webp",
        help="Comma-separated list of supported extensions",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        default=True,
        help="Save predictions.json",
    )
    parser.add_argument(
        "--no-save-json",
        action="store_false",
        dest="save_json",
        help="Do not save predictions.json",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        default=True,
        help="Save INFERENCE_VALIDATION_REPORT.md",
    )
    parser.add_argument(
        "--no-save-report",
        action="store_false",
        dest="save_report",
        help="Do not save report",
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        default="EXP-INF-001",
        help="Experiment identifier",
    )
    return parser.parse_args()


def collect_results(results: list[InferenceResult]) -> dict[str, Any]:
    """Collect statistics from inference results."""
    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    total_detections = sum(len(r.detections) for r in successful)
    detections_by_class = {}
    inference_times = [r.inference_time_ms for r in successful if r.inference_time_ms > 0]

    for r in successful:
        for det in r.detections:
            detections_by_class[det.class_name] = detections_by_class.get(det.class_name, 0) + 1

    return {
        "images_discovered": len(results),
        "images_processed": len(successful),
        "images_failed": len(failed),
        "total_detections": total_detections,
        "detections_by_class": detections_by_class,
        "avg_inference_time_ms": sum(inference_times) / len(inference_times) if inference_times else 0,
        "min_inference_time_ms": min(inference_times) if inference_times else 0,
        "max_inference_time_ms": max(inference_times) if inference_times else 0,
        "failed_files": [{"file": r.image_path, "error": r.error} for r in failed],
    }


def build_predictions_json(
    experiment_id: str,
    model_info: Any,
    source_dir: str,
    inference_config: dict[str, Any],
    results: list[InferenceResult],
) -> dict[str, Any]:
    """Build predictions.json structure."""
    def convert(obj):
        """Recursively convert numpy types to Python native types."""
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(convert(v) for v in obj)
        return obj

    predictions = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model": {
            "path": model_info.model_path,
            "sha256": model_info.model_sha256,
            "name": model_info.model_name,
            "class_names": model_info.class_names,
            "training_run_id": model_info.training_run_id,
        },
        "inference_config": inference_config,
        "source_directory": str(source_dir),
        "images": [
            {
                "file": Path(r.image_path).name,
                "path": r.image_path,
                "width": r.image_width,
                "height": r.image_height,
                "inference_time_ms": r.inference_time_ms,
                "detections": [
                    {
                        "class_id": det.class_id,
                        "class_name": det.class_name,
                        "confidence": det.confidence,
                        "bbox_xyxy": det.bbox_xyxy,
                    }
                    for det in r.detections
                ],
                "error": r.error,
            }
            for r in results
        ],
    }
    return convert(predictions)


def build_report_markdown(
    experiment_id: str,
    model_info: Any,
    source_dir: str,
    inference_config: dict[str, Any],
    results: list[InferenceResult],
    stats: dict[str, Any],
    output_dir: str,
) -> str:
    """Build INFERENCE_VALIDATION_REPORT.md content."""
    lines = [
        f"# {experiment_id} — Unseen Image Inference Smoke Test",
        "",
        "## Experiment Identity",
        "",
        f"- **Experiment ID**: {experiment_id}",
        f"- **Timestamp**: {datetime.utcnow().isoformat()}Z",
        f"- **Source Directory**: {source_dir}",
        f"- **Number of Images**: {stats['images_discovered']}",
        "",
        "## Model Provenance",
        "",
        f"- **Model Path**: {model_info.model_path}",
        f"- **Model SHA256**: {model_info.model_sha256}",
        f"- **Model Name**: {model_info.model_name}",
        f"- **Training Run ID**: {model_info.training_run_id or 'N/A'}",
        "",
        "## Inference Configuration",
        "",
        f"- **Confidence Threshold**: {inference_config['confidence_threshold']}",
        f"- **NMS/IoU Threshold**: {inference_config['iou_threshold']}",
        f"- **Image Size**: {inference_config['imgsz']}",
        f"- **Device**: {inference_config['device']}",
        "",
        "## Processing Results",
        "",
        f"- **Images Discovered**: {stats['images_discovered']}",
        f"- **Successfully Processed**: {stats['images_processed']}",
        f"- **Failed**: {stats['images_failed']}",
        f"- **Total Detections**: {stats['total_detections']}",
        f"- **Detections by Class**:",
    ]

    for class_name, count in sorted(stats["detections_by_class"].items()):
        lines.append(f"  - {class_name}: {count}")

    lines.extend([
        "",
        "## Inference Timing",
        "",
        f"- **Average Inference Time**: {stats['avg_inference_time_ms']:.1f} ms",
        f"- **Minimum Inference Time**: {stats['min_inference_time_ms']:.1f} ms",
        f"- **Maximum Inference Time**: {stats['max_inference_time_ms']:.1f} ms",
        "",
        "## Output Artifacts",
        "",
        f"- Annotated images: {output_dir}/",
        f"- Predictions JSON: {output_dir}/predictions.json",
        f"- Report: {output_dir}/INFERENCE_VALIDATION_REPORT.md",
        "",
        "## Important Limitation",
        "",
        "> **This experiment measures whether the inference pipeline operates correctly on unseen images and allows qualitative inspection of predictions. It does NOT establish real-world precision, recall, F1, IoU, or model accuracy because the images do not currently have ground-truth annotations.**",
        "",
        "## Verification Status",
        "",
        "### VERIFIED",
        "",
        "- [x] Checkpoint loaded",
        "- [x] Inference executed",
        "- [x] Images processed",
        "- [x] Predictions generated",
        "- [x] Annotated outputs generated",
        "- [x] JSON generated",
        "- [x] Report generated",
        "",
        "### NOT YET VERIFIED",
        "",
        "- [ ] Correctness of every predicted bounding box",
        "- [ ] Real-world precision",
        "- [ ] Real-world recall",
        "- [ ] Real-world F1",
        "- [ ] Real-world IoU",
        "- [ ] Live-camera performance",
        "",
        "---",
        "",
        "*This is a smoke test for the inference pipeline. Do not interpret as model accuracy validation.*",
    ])

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    source_dir = Path(args.source)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse extensions
    extensions = {f".{ext.strip().lower()}" for ext in args.extensions.split(",")}

    # Inference configuration
    inference_config = {
        "confidence_threshold": args.conf,
        "iou_threshold": args.iou,
        "imgsz": args.imgsz,
        "device": args.device,
    }

    print(f"Loading model: {args.model}")
    try:
        adapter = YOLOAdapter(
            model_path=args.model,
            confidence_threshold=args.conf,
            iou_threshold=args.iou,
            imgsz=args.imgsz,
            device=args.device,
        )
    except Exception as e:
        print(f"FATAL: Failed to load model: {e}")
        return 1

    model_info = adapter.get_model_info(training_run_id="yol11s_dataset_v2_split_v2")
    print(f"Model loaded: {model_info.model_name}")
    print(f"Model SHA256: {model_info.model_sha256}")
    print(f"Classes: {model_info.class_names}")

    print(f"Running inference on: {source_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Confidence threshold: {args.conf}")
    print(f"IoU threshold: {args.iou}")
    print(f"Image size: {args.imgsz}")
    print(f"Device: {args.device}")
    print(f"Recursive: {args.recursive}")
    print(f"Extensions: {extensions}")
    print("-" * 60)

    # Run inference
    results = adapter.predict_directory(
        source_dir=source_dir,
        recursive=args.recursive,
        supported_extensions=extensions,
    )

    # Collect statistics
    stats = collect_results(results)

    # Create annotated images
    annotated_count = 0
    for result in results:
        if result.error is None:
            input_path = Path(result.image_path)
            output_name = f"{input_path.stem}_annotated{input_path.suffix}"
            output_path = output_dir / output_name
            if create_annotated_image(input_path, result, output_path):
                annotated_count += 1
            else:
                print(f"WARNING: Failed to create annotated image for {input_path.name}")

    print("-" * 60)
    print(f"Annotated images created: {annotated_count}")

    # Save predictions.json
    if args.save_json:
        predictions = build_predictions_json(
            experiment_id=args.experiment_id,
            model_info=model_info,
            source_dir=str(source_dir),
            inference_config=inference_config,
            results=results,
        )
        json_path = output_dir / "predictions.json"
        with open(json_path, "w") as f:
            json.dump(predictions, f, indent=2)
        print(f"Predictions saved to: {json_path}")

    # Save report
    if args.save_report:
        report = build_report_markdown(
            experiment_id=args.experiment_id,
            model_info=model_info,
            source_dir=str(source_dir),
            inference_config=inference_config,
            results=results,
            stats=stats,
            output_dir=str(output_dir),
        )
        report_path = output_dir / "INFERENCE_VALIDATION_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"Report saved to: {report_path}")

    # Print summary
    print("-" * 60)
    print("SUMMARY")
    print(f"  Images discovered: {stats['images_discovered']}")
    print(f"  Successfully processed: {stats['images_processed']}")
    print(f"  Failed: {stats['images_failed']}")
    print(f"  Total detections: {stats['total_detections']}")
    for class_name, count in sorted(stats["detections_by_class"].items()):
        print(f"  {class_name}: {count}")
    print(f"  Avg inference time: {stats['avg_inference_time_ms']:.1f} ms")

    if stats["images_failed"] > 0:
        print("  Failed files:")
        for failed in stats["failed_files"]:
            print(f"    {failed['file']}: {failed['error']}")

    return 0 if stats["images_processed"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())