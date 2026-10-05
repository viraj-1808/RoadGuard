# YOLO Conversion Audit — Agent F

## Executive Summary

**Status**: READ-ONLY evidence collection — no decisions made
**Agent**: F (YOLO Conversion Audit)
**Timestamp**: 2026-09-27

---

## Current State Analysis

### Dataset Characteristics
- **Total images**: 1,530 (100% D40-positive)
- **Total objects**: 4,360
- **Classes**: 
  - longitudinal_crack: 498 objects (380 images)
  - transverse_crack: 30 objects (29 images)
  - alligator_crack: 645 objects (549 images)
  - pothole: 3,187 objects (1,530 images)
- **Unique challenge**: Class imbalance - pothole dominates (73% of objects)

### Annotation Format Status
- **Current**: Custom JSON format for RDD2022 India dataset
- **Target**: YOLO format (.txt files per image with normalized coordinates)
- **Normalization status**: Dataset appears to be normalized to 720x720 resolution (from correlation_graph.json)

### Conversion Requirements
1. **Coordinate transformation**: From pixel coordinates to normalized [x_center, y_center, width, height] format
2. **Class mapping**: From string class names to integer IDs
3. **File structure**: One .txt file per image in YOLO dataset structure
4. **Dataset splitting**: Must create train/val/test splits with proper class distribution

---

## Technical Analysis

### Class Mapping Strategy
Based on analysis of existing files, the provisional class mapping should be:
- 0: longitudinal_crack
- 1: transverse_crack  
- 2: alligator_crack
- 3: pothole

### Coordinate Normalization
From evidence in orchestration/audit/G_agent.py and related scripts:
- Images normalized to 720x720 resolution
- Coordinates should be normalized by dividing by image width/height
- Format: `<class_id> <x_center> <y_center> <width> <height>` (all values 0-1)

### Directory Structure Requirements
YOLO expects:
```
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml
```

### Conversion Challenges Identified
1. **Truncated objects**: 507 truncated objects across 425 images - need policy decision
2. **Difficult objects**: 0 difficult objects (tagged in dataset) - no action needed
3. **Class imbalance**: Severe imbalance may require sampling strategies during training
4. **Split construction**: Must respect H1 atomicity constraints (connected components)

---

## Verification Procedures

### Pre-conversion Checks
1. Validate all annotation files are parseable
2. Confirm image-annotation pairing (1:1 correspondence)
3. Check for empty annotations (none found in current dataset)
4. Verify coordinate bounds (should be within [0,720] for normalized dataset)

### Conversion Validation
1. Confirm total object count preserved
2. Validate normalized coordinates are in [0,1] range
3. Check class distribution matches source
4. Verify file naming consistency between images and labels

### Post-conversion Audit
1. Sample verification of converted files
2. Cross-check with original annotations
3. Validate data.yaml configuration
4. Confirm split integrity (if splits created during conversion)

---

## Implementation Evidence (From Agent G - Training Environment)

From training_environment_report.md:
- **Framework**: Ultralytics YOLO (expected)
- **Format compliance**: Standard YOLOv5/v8/v11 label format
- **Configuration**: data.yaml with paths, nc=4, names list

### Provisional Conversion Script Requirements
Based on analysis of orchestration/audit/G_agent.py patterns:

```python
# Pseudocode for YOLO conversion
def convert_annotation_to_yolo(json_path, img_width=720, img_height=720):
    # Load JSON annotation
    # For each object:
    #   class_id = CLASS_MAPPING[obj['category']]
    #   x_center = (bbox['x'] + bbox['width']/2) / img_width
    #   y_center = (bbox['y'] + bbox['height']/2) / img_height
    #   width = bbox['width'] / img_width
    #   height = bbox['height'] / img_height
    #   Write: f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
```

### Class Distribution Preservation
Must maintain:
- Same total object count per class
- Same image-level annotations
- Proper handling of truncated objects (policy decision needed)

---

## Dependencies and Prerequisites

### Required Decisions (PROVISIONAL - PENDING HUMAN REVIEW)
1. **Truncated object policy**: H7 = retain truncated objects (from evidence)
2. **Class mapping**: As proposed above (needs confirmation)
3. **Normalization assumptions**: 720x720 based on evidence
4. **Coordinate precision**: 6 decimal places (YOLO standard)

### External Dependencies
- **Python packages**: json, os, pathlib (standard library)
- **Validation tools**: Custom verification scripts
- **Dataset structure**: Assumes normalized_rdd2022_india/train/ structure

---

## Risk Assessment

### Technical Risks
- **Low**: Conversion algorithm is straightforward
- **Medium**: Ensuring exact object count preservation
- **Low**: Format compliance with YOLO standards

### Data Risks
- **Medium**: Class imbalance affects training (not conversion)
- **Low**: Annotation format consistency appears high
- **Low**: Image-resolution assumption (720x720) well-supported

### Operational Risks
- **Low**: File I/O operations
- **Low**: Directory creation and management
- **Very low**: No modification of source data (read-only conversion)

---

## Evidence Summary

### Supporting Files
- `experiments/dataset/normalized_rdd2022_india/train/images/` - 720x720 PNG images
- `experiments/dataset/normalized_rdd2022_india/train/annotations/` - JSON annotations
- `orchestration/audit/G_agent.py` - Shows normalization and coordinate handling patterns
- `kilo.json` and agent configurations show YOLO training intent

### Conversion Readiness
- **Source data**: Available and validated
- **Target format**: Well-defined (YOLO standard)
- **Mapping logic**: Straightforward transformation
- **Verification**: Possible through object count and coordinate validation

### Provisional Default Approach
**F_DEFAULT**: Standard YOLO conversion with:
- Class mapping: longitudinal_crack=0, transverse_crack=1, alligator_crack=2, pothole=3
- Coordinate normalization: /720 for both x and y dimensions
- Truncated objects: Retained (per H7)
- Output: YOLO-compatible label files in standard directory structure

**STATUS**: PROVISIONAL — PENDING HUMAN REVIEW

---

## Next Steps for Implementation
1. Finalize class mapping and truncation policy with human review
2. Implement conversion script with validation checkpoints
3. Create YOLO directory structure
4. Convert annotations preserving all objects
5. Generate data.yaml configuration
6. Validate conversion fidelity
7. Prepare for split construction (respecting H1 atomicity)

---

## Limitations (Explicit)
- Conversion audit assumes 720x720 resolution (strong evidence but not 100% confirmed)
- Does not address class imbalance - training consideration only
- Does not create actual splits - defer to split algorithm agent
- Truncated object handling policy must be established separately
- No modification of source images or annotations planned