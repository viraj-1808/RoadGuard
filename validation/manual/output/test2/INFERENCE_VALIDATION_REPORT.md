# EXP-INF-003 — Unseen Image Inference Smoke Test

## Experiment Identity

- **Experiment ID**: EXP-INF-003
- **Timestamp**: 2026-10-10T18:22:02.868977Z
- **Source Directory**: validation\manual\input
- **Number of Images**: 39

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

- **Images Discovered**: 39
- **Successfully Processed**: 39
- **Failed**: 0
- **Total Detections**: 39
- **Detections by Class**:
  - alligator_crack: 14
  - longitudinal_crack: 2
  - pothole: 23

## Inference Timing

- **Average Inference Time**: 88.1 ms
- **Minimum Inference Time**: 25.1 ms
- **Maximum Inference Time**: 176.3 ms

## Output Artifacts

- Annotated images: validation\manual\output\test2/
- Predictions JSON: validation\manual\output\test2/predictions.json
- Report: validation\manual\output\test2/INFERENCE_VALIDATION_REPORT.md

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