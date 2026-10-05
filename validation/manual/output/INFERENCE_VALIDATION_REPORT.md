# EXP-INF-001 — Unseen Image Inference Smoke Test

## Experiment Identity

- **Experiment ID**: EXP-INF-001
- **Timestamp**: 2026-10-03T17:03:00.314838Z
- **Source Directory**: validation\manual\input
- **Number of Images**: 15

## Model Provenance

- **Model Path**: runs\detect\experiments\training\yol11s_dataset_v2_split_v2\weights\best.pt
- **Model SHA256**: 721277b9d066715bc82d3d4fa34fcbcfb6147cb4265b216f41fc68c8beb59823
- **Model Name**: YOLO11s
- **Training Run ID**: yol11s_dataset_v2_split_v2

## Inference Configuration

- **Confidence Threshold**: 0.25
- **NMS/IoU Threshold**: 0.7
- **Image Size**: 720
- **Device**: 0

## Processing Results

- **Images Discovered**: 15
- **Successfully Processed**: 15
- **Failed**: 0
- **Total Detections**: 26
- **Detections by Class**:
  - alligator_crack: 4
  - longitudinal_crack: 2
  - pothole: 20

## Inference Timing

- **Average Inference Time**: 33.1 ms
- **Minimum Inference Time**: 16.7 ms
- **Maximum Inference Time**: 54.5 ms

## Output Artifacts

- Annotated images: validation\manual\output/
- Predictions JSON: validation\manual\output/predictions.json
- Report: validation\manual\output/INFERENCE_VALIDATION_REPORT.md

## Important Limitation

> **This experiment measures whether the inference pipeline operates correctly on unseen images and allows qualitative inspection of predictions. It does NOT establish real-world precision, recall, F1, IoU, or model accuracy because the images do not currently have ground-truth annotations.**

## Verification Status

### VERIFIED

- [x] Checkpoint loaded
- [x] Inference executed
- [x] Images processed
- [x] Predictions generated
- [x] Annotated outputs generated
- [x] JSON generated
- [x] Report generated

### NOT YET VERIFIED

- [ ] Correctness of every predicted bounding box
- [ ] Real-world precision
- [ ] Real-world recall
- [ ] Real-world F1
- [ ] Real-world IoU
- [ ] Live-camera performance

---

*This is a smoke test for the inference pipeline. Do not interpret as model accuracy validation.*