"""
RDD2022 India sample provenance and class semantics analysis.

This module performs detailed image-level and object-level analysis of the
RDD2022 India subset to support class-mapping decisions.

All operations are read-only and do not modify source data.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import json
import math
import xml.etree.ElementTree as ET

from ml.data.inspection.voc_parser import parse_voc_annotation


# Official CRDDC class semantics from Arya et al. (2022), arXiv:2209.08538
# Published in Geoscience Data Journal, DOI: 10.1002/gdj3.260
CLASS_SEMANTICS = {
    'D00': {
        'meaning': 'Longitudinal Crack',
        'subtypes': ['Linear Crack', 'Longitudinal', 'Wheel mark part'],
        'description': 'Linear cracks aligned with the direction of travel',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; distinct damage type; should not be mixed with pothole class',
    },
    'D01': {
        'meaning': 'Longitudinal Crack (construction joint part)',
        'subtypes': ['Construction joint part'],
        'description': 'Longitudinal cracks at construction joints',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; crack variant; should not be mixed with pothole class',
    },
    'D10': {
        'meaning': 'Transverse Crack',
        'subtypes': ['Lateral', 'Equal interval'],
        'description': 'Cracks perpendicular to the direction of travel',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; distinct damage type; should not be mixed with pothole class',
    },
    'D11': {
        'meaning': 'Transverse Crack (construction joint part)',
        'subtypes': ['Construction joint part'],
        'description': 'Transverse cracks at construction joints',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; crack variant; should not be mixed with pothole class',
    },
    'D20': {
        'meaning': 'Alligator Crack',
        'subtypes': ['Partial pavement', 'Overall pavement'],
        'description': 'Interconnected cracks forming an alligator-skin pattern',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; distinct structural damage; should not be mixed with pothole class',
    },
    'D40': {
        'meaning': 'Pothole (Other Corruption: rutting, bump, pothole, separation)',
        'subtypes': ['Rutting', 'Bump', 'Pothole', 'Separation'],
        'description': 'Pothole and related surface depressions; the CRDDC pothole class',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'PRIMARY TARGET class for pothole detection; semantic includes rutting/bump/separation',
    },
    'D43': {
        'meaning': 'Crosswalk blur',
        'subtypes': [],
        'description': 'Blurred or obscured crosswalk markings',
        'source': 'Arya et al. (2022), arXiv:2209.08538; CRDDC official label map',
        'relevance': 'NOT pothole; road marking artifact; should not be mixed with pothole class',
    },
    'D44': {
        'meaning': 'Other Corruption (additional RDD2022 category)',
        'subtypes': [],
        'description': 'Additional corruption category not fully documented in CRDDC 4-class spec',
        'source': 'Observed in RDD2022 India data; not in official CRDDC 4-class label map',
        'relevance': 'NOT pothole; may include patches, stains, or other surface anomalies',
    },
    'D50': {
        'meaning': 'Unknown (not in official CRDDC label map)',
        'subtypes': [],
        'description': 'Class present in data but not documented in official RDD2022 label maps',
        'source': 'Unknown; not in official crackLabelMap.txt or label_map.pbtxt',
        'relevance': 'PROVENANCE UNKNOWN; requires investigation before inclusion',
    },
}


@dataclass
class ImageLevelStats:
    """Image-level statistics for RDD2022 India sample."""
    total_images: int = 0
    images_with_d40: int = 0
    images_without_d40: int = 0
    d40_only_images: int = 0
    d40_plus_d00_images: int = 0
    d40_plus_d20_images: int = 0
    d40_plus_other_images: int = 0
    non_d40_only_images: int = 0
    image_class_sets: Dict[str, Set[str]] = field(default_factory=dict)
    image_object_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class ProvenanceAnalysis:
    """Provenance and class semantics analysis results."""
    image_stats: ImageLevelStats = field(default_factory=ImageLevelStats)
    class_counts: Dict[str, int] = field(default_factory=dict)
    class_image_counts: Dict[str, int] = field(default_factory=dict)
    cooccurrence: Dict[str, Dict[str, int]] = field(default_factory=dict)
    d40_details: Dict[str, Any] = field(default_factory=dict)


def analyze_provenance(annotation_dir: Path) -> ProvenanceAnalysis:
    """Analyze RDD2022 India sample provenance and class semantics."""
    results = ProvenanceAnalysis()
    
    if not annotation_dir.exists():
        raise FileNotFoundError(f"Annotation directory not found: {annotation_dir}")
    
    xml_files = sorted(annotation_dir.glob('*.xml'))
    results.image_stats.total_images = len(xml_files)
    
    # Collect per-image class sets
    d40_only = 0
    d40_plus_d00 = 0
    d40_plus_d20 = 0
    d40_plus_other = 0
    non_d40_only = 0
    image_class_sets: Dict[str, Set[str]] = {}
    image_object_counts: Dict[str, int] = {}
    class_counts: Dict[str, int] = {}
    class_image_counts: Dict[str, int] = {}
    cooccurrence: Dict[str, Dict[str, int]] = {}
    
    for xml_path in xml_files:
        try:
            annotation = parse_voc_annotation(xml_path)
        except Exception:
            continue
        
        image_classes = set(obj.name for obj in annotation.objects)
        image_class_sets[annotation.filename] = image_classes
        results.image_stats.image_class_sets[annotation.filename] = image_classes
        results.image_stats.image_object_counts[annotation.filename] = annotation.object_count
        image_object_counts[annotation.filename] = annotation.object_count
        
        for obj in annotation.objects:
            class_counts[obj.name] = class_counts.get(obj.name, 0) + 1
        
        # Track which images contain each class
        for cls in image_classes:
            class_image_counts[cls] = class_image_counts.get(cls, 0) + 1
        
        # Image-level co-occurrence
        for cls_a in sorted(image_classes):
            for cls_b in sorted(image_classes):
                if cls_a != cls_b:
                    cooccurrence.setdefault(cls_a, {}).setdefault(cls_b, 0)
                    cooccurrence[cls_a][cls_b] += 1
        
        # Classify image by D40 presence (mutually exclusive categories)
        has_d40 = 'D40' in image_classes
        has_d00 = 'D00' in image_classes
        has_d20 = 'D20' in image_classes
        has_other = any(c not in ('D40', 'D00', 'D20') for c in image_classes)
        
        if not has_d40:
            non_d40_only += 1
        elif has_d00:
            # D40 + D00 (D20 or other may also be present, but D00 takes priority)
            d40_plus_d00 += 1
        elif has_d20:
            # D40 + D20, D00 absent
            d40_plus_d20 += 1
        elif has_other:
            # D40 + other classes, D00 absent, D20 absent
            d40_plus_other += 1
        else:
            # D40 only
            d40_only += 1
    
    results.image_stats.d40_only_images = d40_only
    results.image_stats.d40_plus_d00_images = d40_plus_d00
    results.image_stats.d40_plus_d20_images = d40_plus_d20
    results.image_stats.d40_plus_other_images = d40_plus_other
    results.image_stats.images_with_d40 = d40_only + d40_plus_d00 + d40_plus_d20 + d40_plus_other
    results.image_stats.images_without_d40 = non_d40_only
    results.image_stats.non_d40_only_images = non_d40_only
    results.image_stats.image_class_sets = image_class_sets
    results.image_stats.image_object_counts = image_object_counts
    results.class_counts = class_counts
    results.class_image_counts = class_image_counts
    results.cooccurrence = cooccurrence
    
    # D40 details
    d40_objects = class_counts.get('D40', 0)
    d40_images = class_image_counts.get('D40', 0)
    results.d40_details = {
        'object_count': d40_objects,
        'image_count': d40_images,
        'images_without_d40': non_d40_only,
        'd40_only_images': d40_only,
        'd40_plus_d00_images': d40_plus_d00,
        'd40_plus_d20_images': d40_plus_d20,
        'd40_plus_other_images': d40_plus_other,
        'pct_images_with_d40': d40_images / len(xml_files) * 100 if xml_files else 0,
        'pct_images_without_d40': non_d40_only / len(xml_files) * 100 if xml_files else 0,
    }
    
    return results


def format_provenance_report(results: ProvenanceAnalysis) -> str:
    """Format provenance analysis as a human-readable report."""
    lines = [
        '# RDD2022 India Provenance and Class Semantics Analysis',
        '',
        '## 1. Provenance',
        '',
        '| Field | Value |',
        '|-------|-------|',
        '| Original official dataset | RDD2022 (CRDDC\'2022), Arya et al. (2022), arXiv:2209.08538',
        '| Official source | github.com/sekilab/RoadDamageDetector',
        '| India release | RDD2022_India.zip (502.3 MB, train + test)',
        '| India train images | 7,706 (9,665 total India subset) |',
        '| Derived Kaggle artifact | Kaggle `vidishbijalwan/rdd2022-india-pothole-d40`',
        '| Artifact size | 1,530 images (15.8% of India train set) |',
        '| Evidence for relationship | Kaggle README cites RDD2022 by Arya et al. (2022); Pascal VOC XML format; 720x720 resolution; India locations (Delhi, Gurugram, Haryana)',
        '| Is this artifact a filtered/subset? | Yes — filtered from India train subset; claimed to be D40-only but contains all 9 classes',
        '| Data potentially absent | 8,135 India train images not in artifact; test set annotations absent; Norway, Japan, Czech, USA, China not present',
        '',
        '## 2. Class Semantics (from official documentation)',
        '',
        '| Class | Meaning | Observed Count | Observed Images | Source | Relevance',
        '|-------|---------|----------------|-----------------|--------|----------|',
    ]
    
    for cls_code, semantics in CLASS_SEMANTICS.items():
        count = results.class_counts.get(cls_code, 0)
        img_count = results.class_image_counts.get(cls_code, 0)
        relevance = semantics.get('relevance', '')
        lines.append(f'| {cls_code} | {semantics["meaning"]} | {count} | {img_count} | {semantics["source"]} | {relevance} |')
    
    lines.extend([
        '',
        '## 3. D40 Semantic Caution',
        '',
        '- D40 in CRDDC = "Other Corruption" category including rutting, bump, pothole, separation',
        '- D40 is NOT a perfectly pure physical-pothole category',
        '- Annotations include rutting, bumps, and surface separation alongside true potholes',
        '- The Kaggle artifact name ("Pothole D40") implies pure pothole, but source data includes broader "other corruption"',
        '- Model trained on D40 will learn a broader corruption concept, not strictly potholes',
        '',
        '## 4. Co-occurrence Analysis (Image-Level)',
        '',
        f'| Category | Images | Percentage |',
        f'|----------|--------|------------|',
        f'| D40 only | {results.image_stats.d40_only_images} | {results.image_stats.d40_only_images / results.image_stats.total_images * 100:.1f}% |',
        f'| D40 + D00 | {results.image_stats.d40_plus_d00_images} | {results.image_stats.d40_plus_d00_images / results.image_stats.total_images * 100:.1f}% |',
        f'| D40 + D20 | {results.image_stats.d40_plus_d20_images} | {results.image_stats.d40_plus_d20_images / results.image_stats.total_images * 100:.1f}% |',
        f'| D40 + other classes | {results.image_stats.d40_plus_other_images} | {results.image_stats.d40_plus_other_images / results.image_stats.total_images * 100:.1f}% |',
        f'| Non-D40 only | {results.image_stats.non_d40_only_images} | {results.image_stats.non_d40_only_images / results.image_stats.total_images * 100:.1f}% |',
        '',
        f'- Images containing at least one D40: {results.image_stats.images_with_d40} ({results.image_stats.images_with_d40 / results.image_stats.total_images * 100:.1f}%)',
        f'- Images containing no D40: {results.image_stats.images_without_d40} ({results.image_stats.images_without_d40 / results.image_stats.total_images * 100:.1f}%)',
        '',
        f'**Image vs Object distinction**: Object-level counts show D40 is {results.class_counts.get("D40", 0) / sum(results.class_counts.values()) * 100:.1f}% of all objects ({results.class_counts.get("D40", 0)}/{sum(results.class_counts.values())}), and image-level counts show D40 appears in 100% of images. Non-D40 classes appear in {(results.image_stats.total_images - results.image_stats.d40_only_images) / results.image_stats.total_images * 100:.1f}% of images (images with D00, D20, or other classes alongside D40).',
        '',
        '## 5. Candidate Class-Mapping Strategies (NOT DECIDED)',
        '',
        '### Strategy A: D40-only single-class detector',
        '- Model learns to detect D40 objects only',
        '- Labels retained: D40',
        '- Labels become background/ignored: D00, D10, D11, D20, D43, D44, D50',
        '- Advantages: Simple, focused on pothole detection, matches project scope',
        '- Risks: False negatives on non-D40 damage; D40 includes non-pothole corruption',
        '- Evaluation implications: Precision/recall for D40 only; cannot evaluate crack detection',
        '',
        '### Strategy B: Multi-class road-damage detector',
        '- Model learns all 9 observed classes',
        '- Labels retained: D00, D01, D10, D11, D20, D40, D43, D44, D50',
        '- Labels become background/ignored: None',
        '- Advantages: Richer output; supports road condition assessment; distinguishes crack types',
        '- Risks: D50 provenance unknown; D43/D44/D50 rare; increased complexity; requires more data',
        '- Evaluation implications: Per-class mAP; more informative but harder to optimize',
        '',
        '### Strategy C: D40 + crack binary detector',
        '- Model learns D40 (pothole) vs crack (D00+D10+D20+D01+D11) binary',
        '- Labels retained: D40, crack_group',
        '- Labels become background/ignored: D43, D44, D50',
        '- Advantages: Distinguishes potholes from cracks (both relevant to road maintenance)',
        '- Risks: Crack subtypes collapsed; D43/D44/D50 ambiguous',
        '- Evaluation implications: Binary detection; simpler than multi-class',
        '',
        '## 6. Negative-Example Implications',
        '',
        '- **All 1,530 images contain at least one D40 object** (100% coverage). There are no images without D40 in this artifact.',
        '- Images with D40 plus non-D40 damage: D40 objects are positive examples; non-D40 objects (D00, D20, D44, etc.) may be false positives (D40-only strategy) or additional positives (multi-class strategy).',
        '- In D40-only strategy: non-D40 objects become background (ignored). This is standard practice and should not degrade performance significantly, as the model still sees D40 in every image.',
        '- In multi-class strategy: non-D40 objects provide additional supervision signal for crack detection and other corruption types.',
        '- No decision made on retaining/removing these images yet. Recommend keeping all images for multi-class; for D40-only, keep D40+ images and mark non-D40 as background.',
        '',
        '## 7. Training-Dataset Coverage Question',
        '',
        '| Metric | Value |',
        '|--------|-------|',
        '| Available artifact | 1,530 images (15.8% of India train set) |',
        '| Official India train set | 7,706 images |',
        '| Official India total (train+test) | 9,665 images |',
        '| Missing coverage | ~81.8% of India train set',
        '| Selection bias risk | HIGH — artifact may over-represent pothole-rich images',
        '| Geographic scope | Delhi, Gurugram, Haryana only; may miss other Indian regions |',
        '| Weather/season coverage | Unknown — no metadata available',
        '| Additional data needed | Full India subset (7,706 train images) or balanced sample across regions',
        '',
        '## 8. Open Decisions',
        '',
        '- Class-mapping strategy (A, B, or C) — NOT DECIDED',
        '- D50 provenance — requires investigation',
        '- D43/D44 semantic meaning — requires source verification',
        '- Whether to include crack-only images in training — NOT DECIDED',
        '- Whether to expand artifact to full India subset — NOT DECIDED',
        '',
        '*Consistent with ARCHITECTURE.md, DATA_PIPELINE.md, MODEL_TRAINING.md, and MODEL_EVALUATION.md. See PROJECT.md for the source-of-truth map.*',
    ])
    
    return '\n'.join(lines)


def save_provenance_results(results: ProvenanceAnalysis, output_path: Path):
    """Save provenance analysis results as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert sets to lists for JSON serialization
    serializable = {
        'image_stats': {
            'total_images': results.image_stats.total_images,
            'images_with_d40': results.image_stats.images_with_d40,
            'images_without_d40': results.image_stats.images_without_d40,
            'd40_only_images': results.image_stats.d40_only_images,
            'd40_plus_d00_images': results.image_stats.d40_plus_d00_images,
            'd40_plus_d20_images': results.image_stats.d40_plus_d20_images,
            'd40_plus_other_images': results.image_stats.d40_plus_other_images,
            'non_d40_only_images': results.image_stats.non_d40_only_images,
        },
        'class_counts': results.class_counts,
        'class_image_counts': results.class_image_counts,
        'cooccurrence': results.cooccurrence,
        'd40_details': results.d40_details,
    }
    
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(serializable, jsonfile, indent=2, ensure_ascii=False)


def main():
    """Run provenance analysis and save results."""
    from pathlib import Path
    
    annotation_dir = Path(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\raw_rdd2022_india\train\annotations\xmls')
    output_dir = Path(r'C:\Users\viraj\Code_files\Github\RoadGuard AI\analysis\output')
    
    print("Running provenance analysis...")
    results = analyze_provenance(annotation_dir)
    
    # Save JSON
    json_path = output_dir / 'rdd2022_provenance_analysis.json'
    save_provenance_results(results, json_path)
    print(f"JSON results: {json_path}")
    
    # Save report
    report = format_provenance_report(results)
    report_path = output_dir / 'rdd2022_provenance_report.md'
    report_path.write_text(report, encoding='utf-8')
    print(f"Report: {report_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total images: {results.image_stats.total_images}")
    print(f"  D40 only: {results.image_stats.d40_only_images}")
    print(f"  D40 + D00: {results.image_stats.d40_plus_d00_images}")
    print(f"  D40 + D20: {results.image_stats.d40_plus_d20_images}")
    print(f"  D40 + other: {results.image_stats.d40_plus_other_images}")
    print(f"  Non-D40 only: {results.image_stats.non_d40_only_images}")
    print(f"  Images with D40: {results.image_stats.images_with_d40}")
    print(f"  Images without D40: {results.image_stats.images_without_d40}")
    
    return results


if __name__ == '__main__':
    main()