#!/usr/bin/env python3
"""
RoadGuard AI Manual Inference Workflow

Mandatory deliverable for Phase 4. This script provides a clean interface for
running inference on images in the fixed manual input directory.

Default input and output paths are fixed as per project requirements:
- Input: C:\\Users\\viraj\\Code_files\\Github\\RoadGuard AI\\validation\\manual\\input
- Output root: C:\\Users\\viraj\\Code_files\\Github\\RoadGuard AI\\validation\\manual\\output

Each invocation creates a unique run directory with timestamp.
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from inference.adapters.yolo_adapter import (
    YOLOAdapter,
    create_annotated_image,
    InferenceResult,
    Detection,
    ModelInfo,
)

# Fixed paths as per Phase 4 requirements
FIXED_INPUT_DIR = Path("validation/manual/input")
FIXED_OUTPUT_ROOT = Path("validation/manual/output")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for inference."""
    parser = argparse.ArgumentParser(
        description="RoadGuard AI Manual Inference - Run YOLO model on images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Default to fixed paths as per requirements
    parser.add_argument(
        "--source",
        type=str,
        default=str(FIXED_INPUT_DIR),
        help="Source directory containing images (default: fixed manual input directory)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=str(FIXED_OUTPUT_ROOT),
        help="Output root directory for runs (default: fixed manual output root)",
    )

    parser.add_argument(
        "--weights",
        type=str,
        default="runs/detect/experiments/training/yol11s_experiment2/weights/epoch72.pt",
        help="Path to model checkpoint (default: epoch-72 protected baseline)",
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
        "--experiment-id",
        type=str,
        default="MANUAL-INF",
        help="Experiment identifier",
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
        help="Save summary.txt",
    )

    parser.add_argument(
        "--no-save-report",
        action="store_false",
        dest="save_report",
        help="Do not save summary.txt",
    )

    parser.add_argument(
        "--create-annotated",
        action="store_true",
        default=True,
        help="Create annotated images",
    )

    parser.add_argument(
        "--no-create-annotated",
        action="store_false",
        dest="create_annotated",
        help="Do not create annotated images",
    )

    return parser.parse_args()


def generate_run_directory_name(output_root: Path) -> Path:
    """Generate a unique run directory name with timestamp.
    
    Creates directories like: validation/manual/output/run_20261013_220000
    Each invocation gets a unique timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir_name = f"run_{timestamp}"
    run_path = output_root / run_dir_name
    run_path.mkdir(parents=True, exist_ok=True)
    return run_path


def load_model_and_validate(weights_path: str) -> tuple[YOLOAdapter, ModelInfo]:
    """Load the model and return adapter with model info."""
    print(f"Loading model from: {weights_path}")

    try:
        adapter = YOLOAdapter(
            model_path=weights_path,
            confidence_threshold=0.25,
            iou_threshold=0.7,
            imgsz=720,
            device="0",
        )

        model_info = adapter.get_model_info(training_run_id="yol11s_experiment2")
        print(f"Model loaded: {model_info.model_name}")
        print(f"Model SHA256: {model_info.model_sha256}")
        print(f"Classes: {model_info.class_names}")
        return adapter, model_info

    except Exception as e:
        print(f"FATAL: Failed to load model: {e}")
        sys.exit(1)


def validate_input_source(source_dir: Path) -> list[Path]:
    """Validate input source and return list of supported image files.
    
    Supported extensions: .jpg, .jpeg, .png, .webp (matching YOLOAdapter)
    """
    if not source_dir.exists():
        print(f"ERROR: Input source directory does not exist: {source_dir}")
        print("Please place images in the fixed manual input directory:")
        print(f"  {FIXED_INPUT_DIR}")
        sys.exit(1)

    # Supported extensions (matching YOLOAdapter)
    supported_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    # Find image files
    image_files = []
    for ext in supported_extensions:
        image_files.extend(source_dir.glob(f"*{ext.lower()}"))
        image_files.extend(source_dir.glob(f"*{ext.upper()}"))

    # Deduplicate and sort
    image_files = sorted(set(image_files))

    if not image_files:
        print(f"WARNING: No supported images found in {source_dir}")
        print("Supported formats: .jpg, .jpeg, .png, .webp")

    print(f"Found {len(image_files)} supported images in {source_dir}")
    return image_files


def collect_inference_results(
    adapter: YOLOAdapter, 
    image_files: list[Path]
) -> list[InferenceResult]:
    """Run inference on all images and return results."""
    results = []

    print("-" * 60)
    print("Running inference on images...")
    print("-" * 60)

    for image_path in image_files:
        print(f"Processing: {image_path.name}")
        result = adapter.predict_image(str(image_path))
        results.append(result)

        if result.error:
            print(f"  WARNING: {result.error}")
        else:
            print(f"  Found {len(result.detections)} detections in {result.inference_time_ms:.1f}ms")

    return results


def create_annotated_images(
    image_files: list[Path],
    results: list[InferenceResult],
    run_dir: Path,
    create_annotated: bool,
) -> list[Path]:
    """Create annotated images and save them in run_dir/annotated/."""
    if not create_annotated:
        return []

    annotated_dir = run_dir / "annotated"
    annotated_dir.mkdir(exist_ok=True)

    annotated_count = 0

    for result in results:
        if result.error:
            continue

        input_path = Path(result.image_path)
        output_name = f"{input_path.stem}_annotated{input_path.suffix}"
        output_path = annotated_dir / output_name

        if create_annotated_image(input_path, result, output_path):
            annotated_count += 1
        else:
            print(f"WARNING: Failed to create annotated image for {input_path.name}")

    print(f"Annotated images created: {annotated_count}")
    return list(annotated_dir.iterdir())


def save_predictions_json(
    run_dir: Path,
    experiment_id: str,
    model_info: ModelInfo,
    source_dir: Path,
    inference_config: dict[str, Any],
    results: list[InferenceResult],
    save_json: bool,
) -> Path | None:
    """Save predictions.json in the run directory."""
    if not save_json:
        return None

    predictions_path = run_dir / "predictions.json"

    # Convert results to predictions structure
    def convert(obj):
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
        "timestamp": datetime.utcnow().isoformat().replace("+00:00", "Z"),
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

    predictions = convert(predictions)

    with open(predictions_path, "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"Predictions saved to: {predictions_path}")
    return predictions_path


def save_summary_txt(
    run_dir: Path,
    experiment_id: str,
    model_info: ModelInfo,
    source_dir: Path,
    inference_config: dict[str, Any],
    results: list[InferenceResult],
    annotated_count: int,
    run_metadata_path: Path,
    save_report: bool,
) -> Path | None:
    """Save summary.txt in the run directory."""
    if not save_report:
        return None

    summary_path = run_dir / "summary.txt"

    # Collect statistics
    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    total_detections = sum(len(r.detections) for r in successful)
    detections_by_class = {}
    inference_times = [r.inference_time_ms for r in successful if r.inference_time_ms > 0]

    for r in successful:
        for det in r.detections:
            detections_by_class[det.class_name] = detections_by_class.get(det.class_name, 0) + 1

    lines = [
        f"# {experiment_id} — Manual Inference Smoke Test",
        "",
        "## Experiment Identity",
        "",
        f"- **Experiment ID**: {experiment_id}",
        f"- **Timestamp**: {datetime.utcnow().isoformat()}Z",
        f"- **Source Directory**: {source_dir}",
        f"- **Number of Images**: {len(results)}",
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
        f"- **Images Discovered**: {len(results)}",
        f"- **Successfully Processed**: {len(successful)}",
        f"- **Failed**: {len(failed)}",
        f"- **Total Detections**: {total_detections}",
        f"- **Detections by Class**:",
    ]

    for class_name, count in sorted(detections_by_class.items()):
        lines.append(f"  - {class_name}: {count}")

    lines.extend([
        "",
        "## Inference Timing",
        "",
        f"- **Average Inference Time**: {sum(inference_times) / len(inference_times) if inference_times else 0:.1f} ms",
        f"- **Minimum Inference Time**: {min(inference_times) if inference_times else 0:.1f} ms",
        f"- **Maximum Inference Time**: {max(inference_times) if inference_times else 0:.1f} ms",
        "",
        "## Output Artifacts",
        "",
        f"- Annotated images: {annotated_count} images in {run_dir / 'annotated'}",
        f"- Predictions JSON: {run_dir / 'predictions.json'}",
        f"- Summary report: {run_dir / 'summary.txt'}",
        f"- Run metadata: {run_metadata_path}",
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
        "- [x] Summary generated",
        "- [x] Run directory created uniquely",
    ])

    if failed:
        lines.extend([
            "",
            "## Failed Files",
            "",
        ])
        for failed in failed:
            lines.append(f"- **{Path(failed.image_path).name}**: {failed.error}")

    with open(summary_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Summary saved to: {summary_path}")
    return summary_path


def save_results_csv(
    run_dir: Path,
    results: list[InferenceResult],
) -> Path:
    """Save results.csv in the run directory."""
    csv_path = run_dir / "results.csv"

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Image",
            "Width",
            "Height", 
            "Inference_Time_ms",
            "Status",
            "Detections_Count",
            "Detections_Summary"
        ])

        for result in results:
            image_name = Path(result.image_path).name
            status = "SUCCESS" if result.error is None else "FAILED"
            detections_count = len(result.detections) if result.error is None else 0

            # Create summary string of detections
            detections_summary = ""
            if result.error is None and result.detections:
                det_summaries = []
                for det in result.detections:
                    det_summaries.append(
                        f"{det.class_name}:{det.confidence:.2f}@{det.bbox_xyxy}"
                    )
                detections_summary = "|".join(det_summaries)

            writer.writerow([
                image_name,
                result.image_width,
                result.image_height,
                f"{result.inference_time_ms:.1f}",
                status,
                detections_count,
                detections_summary
            ])

    print(f"Results CSV saved to: {csv_path}")
    return csv_path


def save_run_metadata(
    run_dir: Path,
    model_info: ModelInfo,
    inference_config: dict[str, Any],
    weights_path: str,
) -> Path:
    """Save run_metadata.json with checkpoint info, config, etc."""
    metadata_path = run_dir / "run_metadata.json"

    metadata = {
        "timestamp": datetime.utcnow().isoformat().replace("+00:00", "Z"),
        "experiment_id": "MANUAL-INF",
        "checkpoint": {
            "path": weights_path,
            "sha256": model_info.model_sha256,
            "name": model_info.model_name,
            "protected": True,  # This is the epoch-72 baseline
        },
        "inference_config": inference_config,
        "class_mapping": model_info.class_names,
        "input_directory": str(FIXED_INPUT_DIR),
        "output_directory": str(run_dir),
        "output_root": str(FIXED_OUTPUT_ROOT),
        "device": inference_config["device"],
        "requirements": {
            "protected_checkpoint": "e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5",
            "manual_input_path": str(FIXED_INPUT_DIR),
            "manual_output_path": str(FIXED_OUTPUT_ROOT),
        },
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Run metadata saved to: {metadata_path}")
    return metadata_path


def print_summary(
    experiment_id: str,
    results: list[InferenceResult],
    run_dir: Path,
    model_info: ModelInfo,
):
    """Print concise summary of the run."""
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r.error is None]
    failed = [r for r in results if r.error is not None]

    total_detections = sum(len(r.detections) for r in successful)

    print(f"  Experiment ID: {experiment_id}")
    print(f"  Images discovered: {len(results)}")
    print(f"  Successfully processed: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Total detections: {total_detections}")

    # Count detections by class
    detections_by_class = {}
    for r in successful:
        for det in r.detections:
            detections_by_class[det.class_name] = detections_by_class.get(det.class_name, 0) + 1

    for class_name, count in sorted(detections_by_class.items()):
        print(f"  {class_name}: {count}")

    print(f"  Run directory: {run_dir}")
    print(f"  Checkpoint: {model_info.model_path}")
    print("=" * 60)


def main() -> int:
    """Main inference workflow."""
    args = parse_args()

    # Create unique run directory
    run_dir = generate_run_directory_name(Path(args.output))
    print(f"Run directory: {run_dir}")

    # Load model
    adapter, model_info = load_model_and_validate(args.weights)

    # Validate and get input images
    image_files = validate_input_source(Path(args.source))

    # Build inference config
    inference_config = {
        "confidence_threshold": args.conf,
        "iou_threshold": args.iou,
        "imgsz": args.imgsz,
        "device": args.device,
    }

    # Run inference
    results = collect_inference_results(adapter, image_files)

    # Create annotated images
    annotated_paths = create_annotated_images(
        image_files, results, run_dir, args.create_annotated
    )

    # Save predictions.json
    save_predictions_json(
        run_dir, args.experiment_id, model_info, 
        Path(args.source), inference_config, results, args.save_json
    )

    # Save results.csv
    save_results_csv(run_dir, results)

    # Save run_metadata.json
    run_metadata_path = save_run_metadata(
        run_dir, model_info, inference_config, args.weights
    )

    # Save summary.txt
    save_summary_txt(
        run_dir, args.experiment_id, model_info, Path(args.source),
        inference_config, results, len(annotated_paths), run_metadata_path,
        args.save_report
    )

    # Print final summary
    print_summary(args.experiment_id, results, run_dir, model_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())