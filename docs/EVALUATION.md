# Evaluation

## Known Metrics (Experiment 2, 30/100 Epochs)

Evaluated on the frozen 230-image India test set (Dataset A, 679 objects). Protocol: Ultralytics `model.val()` with imgsz=720, conf=0.001, iou=0.7, max_det=300, rect=True, split=test.

### Overall Metrics

| Metric       | Exp1 (India-only) | Exp2 (Combined) | Delta   |
|--------------|-------------------|-----------------|---------|
| mAP50        | 0.252             | 0.279           | +10.7%  |
| mAP50-95     | 0.090             | 0.111           | +22.9%  |
| Precision    | 0.299             | 0.586           | +96%    |
| Recall       | 0.312             | 0.321           | +2.9%   |

### Per-Class mAP50-95

| Class              | Exp1    | Exp2    | Delta   |
|--------------------|---------|---------|---------|
| longitudinal_crack | 0.087   | 0.136   | +56%    |
| transverse_crack   | 0.009   | 0.005   | -41%    |
| alligator_crack    | 0.135   | 0.151   | +12%    |
| pothole            | 0.130   | 0.152   | +17%    |

### Dataset B Validation (Not Predictive of India Performance)

| Metric       | Value  |
|--------------|--------|
| mAP50-95     | 0.344  |
| Gap to India | -68%   |

Dataset B validation metrics are **not predictive** of India-domain performance. A 68% mAP50-95 drop from Dataset B validation (0.344) to the India test set (0.111) is observed.

## Unresolved Discrepancies

### 1. transverse_crack Zero Recall

**Status**: UNRESOLVED. On the frozen India test set, transverse_crack achieves **0.000 recall** — the model fails to detect transverse cracks from the India domain entirely. Dataset B provides 7,313 transverse examples (347× Dataset A's 21), but continued training has not resolved this yet.

**Next steps**: Targeted India-specific transverse crack data collection; investigate class-weighted loss or focal loss for rare classes.

### 2. Domain Gap

**Status**: UNRESOLVED. The 68% mAP50-95 drop from Dataset B validation to the India test set indicates a significant domain gap. Dataset B validation is not a reliable predictor of India-domain performance.

**Next steps**: Evaluate on India-specific validation sets; investigate domain adaptation techniques.

### 3. Selection Bias

**Status**: UNRESOLVED. 100% of the RDD2022 India artifact (1,530 images) contains D40. Zero pothole-negative and zero crack-only images exist. This makes evaluation unreliable and introduces selection bias risk.

**Next steps**: Acquire official India data (S3 returns 403); collect additional negative-class images.

### 4. Residual Leakage Risk

**Status**: UNRESOLVED. The RDD2022 India artifact has no sequence/video/trip/GPS metadata. State C — no reliable grouping can be established. Five verified near-duplicate clusters (121 images) are treated as atomic units; all other images' group membership is UNKNOWN. Residual leakage risk is **unquantifiable, not zero**. D-006-R1 refinement proposed but not applied.

**Next steps**: Await official India data with sequence metadata; apply D-006-R1 refinement.

### 5. Checkpoint Under-Training

**Status**: UNRESOLVED. The protected epoch-72 baseline (SHA-256: `e455893192790a65fccf44c483775375aaebc837397bcbf16082533639eae6e5`) is from an under-trained run (30/100 epochs). Further training is required for production readiness.

**Next steps**: Resume training to 100 epochs using `python experiments/training/resume_realworld_finetune.py`.

### 6. Inference Accuracy Unverified

**Status**: UNRESOLVED. Manual inference (`predict.py`) runs correctly on unseen images but **does not establish real-world precision/recall** — the manual input set has no ground-truth annotations.

**Next steps**: Annotate a validation set; run `eval_frozen_test.py` for quantitative evaluation.

## Evaluation Protocol (DRAFTED)

- **Required metrics**: Precision, Recall, F1, IoU, AP, mAP50, mAP75, mAP50-95 (per class and aggregate).
- **Evaluation sets**: Validation (tuning), Test (final), Unseen Indian-domain (generalization), Cross-domain (robustness), Video (temporal stability), Live-camera (real-time constraints).
- **Small-object evaluation**: Size categories to be determined from actual bounding box distribution (do not invent thresholds).
- **False-positive taxonomy**: Shadow, Manhole, Road patch, Water, Crack, Stain, Other (OPEN pending dataset inspection).
- **False-negative taxonomy**: Small/distant, Low contrast, Blur, Occlusion, Lighting, Shape, Other (OPEN pending dataset inspection).
- **Qualitative analysis**: Visual inspection of detection overlays; review of FP/FN examples; assessment of detection stability across video frames.
- **Runtime benchmarking**: Hardware, resolution, preprocessing latency, inference latency, postprocessing latency, end-to-end latency, throughput (FPS), GPU memory, CPU/GPU utilization.

## Model Selection Rule

**No single metric automatically determines the winner.** Model selection considers: Accuracy, Recall, False-positive behavior, Small-object performance, Generalization, Latency, Throughput, Memory, Deployment practicality.

A model with slightly lower mAP but better recall on small potholes may be preferable for a safety-critical application.

## Status

- **Evaluation protocol**: DRAFTED (required metrics defined; exact thresholds OPEN)
- **Final model**: OPEN
- **Experiments run**: NOT STARTED

---

*All terminology and status labels are consistent with ARCHITECTURE.md and other documentation. See PROJECT.md for the source-of-truth map.*