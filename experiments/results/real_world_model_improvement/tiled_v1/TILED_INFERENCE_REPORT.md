# SAHI Tiled Inference vs Standard Inference Comparison

## Experiment Overview

- **Checkpoint**: `epoch72.pt` (YOLO11s)
- **Images**: road018.jpg (4096x3072), road021.jpg (3072x4096)
- **Ground Truth**: Both images labeled as CLEAR with single defect each
- **Standard Inference**: imgsz=720 (letterbox to 736x736), conf=0.05, NMS IoU=0.7
- **SAHI Tiled Inference**: 640x640 slices, 20% overlap, NMS post-process (IoU=0.5), conf=0.05

## Per-Image Results

### road018.jpg

- **GT Status**: CLEAR
- **GT Annotations**: 1 box(es)
  - Class 3 (pothole): [9.009171485900879, 0.0, 1785.255126953125, 1042.561279296875]

#### STANDARD

- **Detections**: 0
- **TP**: 0, **FP**: 0, **FN**: 1
- **Precision**: 0.0000, **Recall**: 0.0000, **F1**: 0.0000
- **Inference Time**: 188.8 ms
- **Tile Count**: 1
- **Matched Any GT**: False
- **Best IoU (pothole)**: 0.0000

#### SAHI_TILED

- **Detections**: 6
- **TP**: 0, **FP**: 6, **FN**: 1
- **Precision**: 0.0000, **Recall**: 0.0000, **F1**: 0.0000
- **Inference Time**: 4005.8 ms
- **Tile Count**: 6
- **Matched Any GT**: False
- **Best IoU (pothole)**: 0.0000

### road021.jpg

- **GT Status**: CLEAR
- **GT Annotations**: 1 box(es)
  - Class 2 (alligator_crack): [222.919158935547, 0.0, 2268.623291015625, 2095.621337890625]

#### STANDARD

- **Detections**: 0
- **TP**: 0, **FP**: 0, **FN**: 1
- **Precision**: 0.0000, **Recall**: 0.0000, **F1**: 0.0000
- **Inference Time**: 154.6 ms
- **Tile Count**: 1
- **Matched Any GT**: False
- **Best IoU (alligator_crack)**: 0.0000

#### SAHI_TILED

- **Detections**: 2
- **TP**: 0, **FP**: 2, **FN**: 1
- **Precision**: 0.0000, **Recall**: 0.0000, **F1**: 0.0000
- **Inference Time**: 1527.8 ms
- **Tile Count**: 2
- **Matched Any GT**: False
- **Best IoU (alligator_crack)**: 0.0000

## Summary Comparison

| Image | Method | TP | FP | FN | Precision | Recall | F1 | Time (ms) | Tiles |
|-------|--------|----|----|----|-----------|--------|----|-----------|-------|
| road018.jpg | standard | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 188.8 | 1 |
| road018.jpg | sahi_tiled | 0 | 6 | 1 | 0.0000 | 0.0000 | 0.0000 | 4005.8 | 6 |
| road021.jpg | standard | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 | 154.6 | 1 |
| road021.jpg | sahi_tiled | 0 | 2 | 1 | 0.0000 | 0.0000 | 0.0000 | 1527.8 | 2 |

## Key Findings

1. **Standard Inference**: 0 detections on both 4K images (confirmed by audit_v2)
2. **SAHI Tiled Inference**: Finds detections but they are **false positives** (wrong location/class)
   - road018: 6 detections (3 pothole, 3 transverse_crack) - all far from GT pothole
   - road021: 2 detections (1 transverse_crack, 1 pothole) - all far from GT alligator_crack
3. **Root Cause**: Model detects artifacts/other patterns, not the annotated defects
4. **Qualitative Assessment**: Ground truth may be incomplete or model has domain gap
5. **Runtime**: SAHI is ~10-25x slower than standard inference (expected)
