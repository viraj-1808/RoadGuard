"""
Command-line interface for RDD2022 India sample analysis.

Usage:
    python -m analysis.rdd2022_india_analysis_cli \
        --annotation-dir experiments/dataset/raw_rdd2022_india/train/annotations/xmls \
        --image-dir experiments/dataset/raw_rdd2022_india/train/images \
        --output-dir analysis/output
"""
import argparse
import sys
from pathlib import Path

from scripts.analysis.rdd2022_india_analysis import (
    analyze_rdd2022_india,
    save_analysis_results,
    format_analysis_report,
)
from scripts.analysis.rdd2022_visualization import RDD2022Visualizer


def main():
    parser = argparse.ArgumentParser(
        description='Analyze RDD2022 India sample annotations'
    )
    parser.add_argument(
        '--annotation-dir',
        type=Path,
        required=True,
        help='Directory containing Pascal VOC XML annotations',
    )
    parser.add_argument(
        '--image-dir',
        type=Path,
        default=None,
        help='Optional directory containing images (for reference checking)',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('analysis/output'),
        help='Directory to write analysis outputs (default: analysis/output)',
    )
    parser.add_argument(
        '--report',
        type=Path,
        default=None,
        help='Optional path to write human-readable report',
    )
    args = parser.parse_args()
    
    annotation_dir = args.annotation_dir
    if not annotation_dir.exists():
        print(f"Error: annotation directory not found: {annotation_dir}", file=sys.stderr)
        return 1
    
    print(f"Analyzing annotations in: {annotation_dir}")
    results = analyze_rdd2022_india(annotation_dir, args.image_dir)
    
    print(f"  Images inspected: {results.image_count}")
    print(f"  Objects detected: {results.object_count}")
    print(f"  Empty annotations: {len(results.empty_annotations)}")
    print(f"  Invalid annotations: {len(results.invalid_annotations)}")
    
    # Write JSON output
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'rdd2022_india_analysis.json'
    save_analysis_results(results, json_path)
    print(f"\nJSON results written to: {json_path}")
    
    # Write human-readable report
    report_text = format_analysis_report(results)
    report_path = args.report or (output_dir / 'rdd2022_india_report.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding='utf-8')
    print(f"Report written to: {report_path}")
    
    # Generate visualizations
    visualizer = RDD2022Visualizer(output_dir)
    visualizer.plot_class_counts_horizontal(results.class_counts, 'class_counts.png')
    visualizer.plot_d40_bbox_area(results.class_bbox_stats.get('D40', {}))
    visualizer.plot_d40_spatial_scatter(annotation_dir, 'd40_spatial_scatter.png')
    visualizer.plot_d40_spatial_heatmap(annotation_dir, 'd40_spatial_heatmap.png')
    visualizer.plot_class_cooccurrence(results.cooccurrence)
    visualizer.plot_bbox_size_distribution(annotation_dir, 'bbox_size_distribution.png')
    print(f"Visualizations written to: {output_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

