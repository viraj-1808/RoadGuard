"""
Visualization module for RDD2022 India sample analysis.

This module generates PNG charts from the RDD2022 analysis results.
All operations are read-only and do not modify source data.
"""
from pathlib import Path
from typing import Dict, Any, List

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
except ImportError:
    plt = None
    patches = None

from ml.data.inspection.voc_parser import parse_voc_annotation


class RDD2022Visualizer:
    """Generate visualizations for RDD2022 India analysis results."""
    
    def __init__(self, output_dir: Path, dpi: int = 150):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dpi = dpi
    
    def _save(self, fig, filename: str):
        """Save figure to output directory."""
        if plt is None:
            return
        fig.savefig(self.output_dir / filename, dpi=self.dpi, bbox_inches='tight')
        plt.close(fig)
    
    def plot_class_counts(self, class_counts: Dict[str, int], filename: str = 'class_counts.png'):
        """Plot object counts by class."""
        if plt is None or not class_counts:
            return
        
        classes = sorted(class_counts.items(), key=lambda item: item[1], reverse=True)
        labels = [item[0] for item in classes]
        counts = [item[1] for item in classes]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, counts, color=['#d62728', '#1f77b4', '#9467bd', '#8c564b', '#2ca02c', '#ff7f0e', '#7f7f7f', '#bcbd22', '#17becf'])
        ax.set_title('RDD2022 India - Object Counts by Class')
        ax.set_xlabel('Class')
        ax.set_ylabel('Object Count')
        ax.grid(axis='y', alpha=0.3)
        
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.02,
                    f'{count}', ha='center', va='bottom', fontsize=9)
        
        self._save(fig, filename)
    
    def plot_class_counts_horizontal(self, class_counts: Dict[str, int], filename: str = 'class_counts_horizontal.png'):
        """Plot object counts by class (horizontal)."""
        if plt is None or not class_counts:
            return
        
        classes = sorted(class_counts.items(), key=lambda item: item[1], reverse=True)
        labels = [item[0] for item in classes]
        counts = [item[1] for item in classes]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.barh(labels, counts, color=['#d62728', '#1f77b4', '#9467bd', '#8c564b', '#2ca02c', '#ff7f0e', '#7f7f7f', '#bcbd22', '#17becf'])
        ax.set_title('RDD2022 India - Object Counts by Class')
        ax.set_xlabel('Object Count')
        ax.set_ylabel('Class')
        ax.grid(axis='x', alpha=0.3)
        
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + max(counts) * 0.02, bar.get_y() + bar.get_height() / 2,
                    f'{count}', ha='left', va='center', fontsize=9)
        
        ax.invert_yaxis()
        self._save(fig, filename)
    
    def plot_d40_bbox_area(self, bbox_stats: Dict[str, float], filename: str = 'd40_bbox_area.png'):
        """Plot D40/Pothole bounding box area distribution."""
        if plt is None:
            return
        
        fig, ax = plt.subplots(figsize=(8, 5))
        counts = [bbox_stats['area_min'], bbox_stats['area_mean'], bbox_stats['area_max']]
        labels = ['Min', 'Mean', 'Max']
        values = [bbox_stats['area_min'], bbox_stats['area_mean'], bbox_stats['area_max']]
        
        bars = ax.bar(labels, values, color=['#2ca02c', '#1f77b4', '#d62728'])
        ax.set_title('D40 / Pothole Bounding Box Area (px²)')
        ax.set_xlabel('Statistic')
        ax.set_ylabel('Area (px²)')
        ax.grid(axis='y', alpha=0.3)
        
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    f'{value:,.0f}', ha='center', va='bottom', fontsize=9)
        
        self._save(fig, filename)
    
    def plot_d40_spatial_scatter(self, annotation_dir: Path, filename: str = 'd40_spatial_scatter.png'):
        """Plot D40/Pothole normalized center scatter from annotation files."""
        if plt is None:
            return
        
        xml_files = list(annotation_dir.glob('*.xml'))
        d40_center_x: List[float] = []
        d40_center_y: List[float] = []
        
        for xml_path in xml_files:
            try:
                annotation = parse_voc_annotation(xml_path)
            except Exception:
                continue
            
            for obj in annotation.objects:
                if obj.name == 'D40':
                    d40_center_x.append(obj.center_x / annotation.width)
                    d40_center_y.append(obj.center_y / annotation.height)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Normalized Center X')
        ax.set_ylabel('Normalized Center Y')
        ax.set_title(f'D40 / Pothole Spatial Distribution (India Sample, n={len(d40_center_x)})')
        ax.set_aspect('equal', adjustable='box')
        
        # Quadrant guides
        ax.axvline(0.5, color='gray', linestyle='--', alpha=0.5)
        ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(0.25, color='gray', linestyle=':', alpha=0.3)
        ax.axvline(0.75, color='gray', linestyle=':', alpha=0.3)
        ax.axhline(0.25, color='gray', linestyle=':', alpha=0.3)
        ax.axhline(0.75, color='gray', linestyle=':', alpha=0.3)
        
        if d40_center_x:
            ax.scatter(d40_center_x, d40_center_y, s=2, alpha=0.4, c='#d62728', edgecolors='none')
            # Add mean marker
            mean_x = sum(d40_center_x) / len(d40_center_x)
            mean_y = sum(d40_center_y) / len(d40_center_y)
            ax.plot(mean_x, mean_y, 'w+', markersize=15, markeredgewidth=2, label=f'Mean ({mean_x:.3f}, {mean_y:.3f})')
            ax.legend(loc='upper right', fontsize=9)
        
        self._save(fig, filename)
    
    def plot_d40_spatial_heatmap(self, annotation_dir: Path, filename: str = 'd40_spatial_heatmap.png', bins: int = 20):
        """Plot D40/Pothole normalized center 2D histogram (heatmap)."""
        if plt is None:
            return
        
        xml_files = list(annotation_dir.glob('*.xml'))
        d40_center_x: List[float] = []
        d40_center_y: List[float] = []
        
        for xml_path in xml_files:
            try:
                annotation = parse_voc_annotation(xml_path)
            except Exception:
                continue
            
            for obj in annotation.objects:
                if obj.name == 'D40':
                    d40_center_x.append(obj.center_x / annotation.width)
                    d40_center_y.append(obj.center_y / annotation.height)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Normalized Center X')
        ax.set_ylabel('Normalized Center Y')
        ax.set_title(f'D40 / Pothole Spatial Density (India Sample, n={len(d40_center_x)})')
        ax.set_aspect('equal', adjustable='box')
        
        if d40_center_x:
            h = ax.hist2d(d40_center_x, d40_center_y, bins=bins, cmap='Reds', range=[[0, 1], [0, 1]], cmin=1)
            plt.colorbar(h[3], ax=ax, label='Count')
        
        self._save(fig, filename)
    
    def plot_class_cooccurrence(self, cooccurrence: Dict[str, Dict[str, int]], filename: str = 'class_cooccurrence.png'):
        """Plot class co-occurrence as heatmap."""
        if plt is None or not cooccurrence:
            return
        
        # Get all unique classes
        all_classes = set()
        for cls_a, pairs in cooccurrence.items():
            all_classes.add(cls_a)
            for cls_b in pairs:
                all_classes.add(cls_b)
        
        sorted_classes = sorted(all_classes)
        n = len(sorted_classes)
        
        # Build matrix
        matrix = [[0] * n for _ in range(n)]
        for i, cls_a in enumerate(sorted_classes):
            for j, cls_b in enumerate(sorted_classes):
                if cls_a in cooccurrence and cls_b in cooccurrence[cls_a]:
                    matrix[i][j] = cooccurrence[cls_a][cls_b]
        
        fig, ax = plt.subplots(figsize=(8, 7))
        im = ax.imshow(matrix, cmap='Blues', aspect='auto')
        
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(sorted_classes, fontsize=9)
        ax.set_yticklabels(sorted_classes, fontsize=9)
        ax.set_title('RDD2022 India - Class Co-occurrence (images containing both classes)')
        
        # Add text annotations
        for i in range(n):
            for j in range(n):
                if matrix[i][j] > 0:
                    ax.text(j, i, str(matrix[i][j]), ha='center', va='center', fontsize=8)
        
        plt.colorbar(im, ax=ax, label='Number of images')
        self._save(fig, filename)
    
    def plot_bbox_size_distribution(self, annotation_dir: Path, filename: str = 'bbox_size_distribution.png'):
        """Plot bounding box size distribution by class."""
        if plt is None:
            return
        
        xml_files = list(annotation_dir.glob('*.xml'))
        class_areas: Dict[str, List[float]] = {}
        
        for xml_path in xml_files:
            try:
                annotation = parse_voc_annotation(xml_path)
            except Exception:
                continue
            
            for obj in annotation.objects:
                class_areas.setdefault(obj.name, []).append(obj.area)
        
        # Filter to classes with enough data
        class_areas = {k: v for k, v in class_areas.items() if len(v) >= 10}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#d62728', '#1f77b4', '#9467bd', '#8c564b', '#2ca02c', '#ff7f0e', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, (cls_name, areas) in enumerate(sorted(class_areas.items(), key=lambda item: len(item[1]), reverse=True)):
            ax.hist(areas, bins=50, alpha=0.5, label=f'{cls_name} (n={len(areas)})', 
                    color=colors[i % len(colors)], density=True)
        
        ax.set_xlabel('Bounding Box Area (px²)')
        ax.set_ylabel('Density')
        ax.set_title('RDD2022 India - Bounding Box Area Distribution by Class')
        ax.set_yscale('log')
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(alpha=0.3)
        
        self._save(fig, filename)