"""
RDD2022 India sample analysis.

This module analyzes the RDD2022 India subset sample to characterize:
- Class semantics and class counts
- Object co-occurrence
- D40/Pothole bounding-box statistics
- Spatial distribution of potholes
- Annotation quality and consistency

All operations are read-only and do not modify source data.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import json
import math
import xml.etree.ElementTree as ET

from ml.data.inspection.voc_parser import parse_voc_annotation


CLASS_NAMES = {
    'D00': 'Longitudinal Crack',
    'D01': 'Longitudinal Crack',
    'D10': 'Transverse Crack',
    'D11': 'Transverse Crack',
    'D20': 'Alligator Crack',
    'D40': 'Pothole',
    'D43': 'Pothole',
    'D44': 'Pothole',
    'D50': 'Unknown',
}


@dataclass
class RDD2022Analysis:
    """Analysis results for RDD2022 India sample."""
    class_counts: Dict[str, int] = field(default_factory=dict)
    cooccurrence: Dict[str, Dict[str, int]] = field(default_factory=dict)
    class_bbox_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    d40_spatial: Dict[str, Any] = field(default_factory=dict)
    image_count: int = 0
    object_count: int = 0
    empty_annotations: List[str] = field(default_factory=list)
    invalid_annotations: List[str] = field(default_factory=list)


def _percentile(values: List[float], pct: float) -> float:
    """Compute percentile of a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


def _std(values: List[float]) -> float:
    """Compute population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def analyze_rdd2022_india(annotation_dir: Path, image_dir: Path = None) -> RDD2022Analysis:
    """Analyze RDD2022 India sample annotations."""
    results = RDD2022Analysis()
    
    if not annotation_dir.exists():
        raise FileNotFoundError(f"Annotation directory not found: {annotation_dir}")
    
    xml_files = sorted(annotation_dir.glob('*.xml'))
    results.image_count = len(xml_files)
    
    # Class counts and object-level statistics
    class_counts: Dict[str, int] = {}
    class_bbox_values: Dict[str, Dict[str, List[float]]] = {}
    cooccurrence_counts: Dict[str, Dict[str, int]] = {}
    
    # D40 spatial data
    d40_center_x: List[float] = []
    d40_center_y: List[float] = []
    
    for xml_path in xml_files:
        try:
            annotation = parse_voc_annotation(xml_path)
        except Exception as exc:
            results.invalid_annotations.append(f"{xml_path.name}: {exc}")
            continue
        
        if annotation.object_count == 0:
            results.empty_annotations.append(annotation.filename)
            continue
        
        image_classes = set(obj.name for obj in annotation.objects)
        results.object_count += annotation.object_count
        
        for obj in annotation.objects:
            class_counts[obj.name] = class_counts.get(obj.name, 0) + 1
            stats = class_bbox_values.setdefault(obj.name, {
                'width': [], 'height': [], 'area': [], 'relative_area': [],
                'center_x': [], 'center_y': [],
            })
            stats['width'].append(obj.width)
            stats['height'].append(obj.height)
            stats['area'].append(obj.area)
            stats['relative_area'].append(obj.area / annotation.image_area)
            stats['center_x'].append(obj.center_x / annotation.width)
            stats['center_y'].append(obj.center_y / annotation.height)
            
            # Collect D40 spatial data
            if obj.name == 'D40':
                d40_center_x.append(obj.center_x / annotation.width)
                d40_center_y.append(obj.center_y / annotation.height)
        
        # Class co-occurrence
        for cls_a in sorted(image_classes):
            for cls_b in sorted(image_classes):
                if cls_a != cls_b:
                    cooccurrence_counts.setdefault(cls_a, {}).setdefault(cls_b, 0)
                    cooccurrence_counts[cls_a][cls_b] += 1
    
    results.class_counts = class_counts
    results.cooccurrence = cooccurrence_counts
    
    # Class-level bounding box statistics
    for class_name, stats in class_bbox_values.items():
        results.class_bbox_stats[class_name] = {
            'count': len(stats['area']),
            'width_min': min(stats['width']),
            'width_max': max(stats['width']),
            'width_mean': sum(stats['width']) / len(stats['width']),
            'height_min': min(stats['height']),
            'height_max': max(stats['height']),
            'height_mean': sum(stats['height']) / len(stats['height']),
            'area_min': min(stats['area']),
            'area_max': max(stats['area']),
            'area_mean': sum(stats['area']) / len(stats['area']),
            'relative_area_min': min(stats['relative_area']),
            'relative_area_max': max(stats['relative_area']),
            'relative_area_mean': sum(stats['relative_area']) / len(stats['relative_area']),
            'center_x_mean': sum(stats['center_x']) / len(stats['center_x']),
            'center_y_mean': sum(stats['center_y']) / len(stats['center_y']),
        }
    
    # D40/Pothole spatial distribution
    results.d40_spatial = {
        'count': len(d40_center_x),
        'center_x_mean': sum(d40_center_x) / len(d40_center_x) if d40_center_x else 0,
        'center_y_mean': sum(d40_center_y) / len(d40_center_y) if d40_center_y else 0,
        'center_x_std': _std(d40_center_x),
        'center_y_std': _std(d40_center_y),
        'center_x_quartiles': [
            _percentile(d40_center_x, 25),
            _percentile(d40_center_x, 50),
            _percentile(d40_center_x, 75),
        ],
        'center_y_quartiles': [
            _percentile(d40_center_y, 25),
            _percentile(d40_center_y, 50),
            _percentile(d40_center_y, 75),
        ],
    }
    
    return results


def _json_default(value: Any):
    """Convert non-JSON-serializable values."""
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def save_analysis_results(results: RDD2022Analysis, output_path: Path):
    """Save analysis results as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(results.__dict__, jsonfile, indent=2, default=_json_default, ensure_ascii=False)


def format_analysis_report(results: RDD2022Analysis) -> str:
    """Format analysis results as a human-readable report."""
    lines = [
        '# RDD2022 India Sample Analysis',
        '',
        '## Summary',
        '',
        f'- Images inspected: {results.image_count}',
        f'- Objects detected: {results.object_count}',
        f'- Empty annotations: {len(results.empty_annotations)}',
        f'- Invalid annotations: {len(results.invalid_annotations)}',
        '',
        '## Class Counts',
        '',
        '| Class | Count | Percentage |',
        '|-------|-------|------------|',
    ]
    
    total = results.object_count or 1
    for class_name, count in sorted(results.class_counts.items(), key=lambda item: item[1], reverse=True):
        lines.append(f'| {class_name} | {count} | {count / total * 100:.1f}% |')
    
    lines.extend([
        '',
        '## D40 / Pothole Bounding Box Statistics',
        '',
    ])
    
    d40_stats = results.class_bbox_stats.get('D40', {})
    if d40_stats:
        lines.extend([
            f'- Count: {d40_stats["count"]}',
            f'- Width: {d40_stats["width_min"]:.0f} - {d40_stats["width_max"]:.0f} px (mean {d40_stats["width_mean"]:.1f})',
            f'- Height: {d40_stats["height_min"]:.0f} - {d40_stats["height_max"]:.0f} px (mean {d40_stats["height_mean"]:.1f})',
            f'- Area: {d40_stats["area_min"]:.0f} - {d40_stats["area_max"]:.0f} px² (mean {d40_stats["area_mean"]:.1f})',
            f'- Relative area: {d40_stats["relative_area_min"]:.4f} - {d40_stats["relative_area_max"]:.4f} (mean {d40_stats["relative_area_mean"]:.4f})',
            f'- Normalized center x: {d40_stats["center_x_mean"]:.3f}',
            f'- Normalized center y: {d40_stats["center_y_mean"]:.3f}',
        ])
    else:
        lines.append('- No D40 objects found')
    
    lines.extend([
        '',
        '## Class Co-occurrence',
        '',
        '| Class A | Class B | Images |',
        '|---------|---------|--------|',
    ])
    
    for class_a, pairs in sorted(results.cooccurrence.items()):
        for class_b, count in sorted(pairs.items()):
            lines.append(f'| {class_a} | {class_b} | {count} |')
    
    lines.extend([
        '',
        '## Annotation Quality',
        '',
    ])
    
    if results.empty_annotations:
        lines.append(f'- Empty annotations: {len(results.empty_annotations)}')
    else:
        lines.append('- No empty annotations')
    
    if results.invalid_annotations:
        lines.append(f'- Invalid annotations: {len(results.invalid_annotations)}')
        for item in results.invalid_annotations[:10]:
            lines.append(f'  - {item}')
    else:
        lines.append('- No invalid annotations')
    
    return '\n'.join(lines)
