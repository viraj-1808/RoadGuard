# Experiment 2 Hypotheses

## Context
- Dataset: Selection-biased (D40 derived)
- Limited negative/background diversity for pothole class
- transverse_crack: only 30 instances total
- mAP50-95: 0.0903 (very low)

---

## H1: Negative/Background Diversity Deficiency

**OBSERVATION**: Pothole class lacks diverse negative samples (normal road textures, shadows, patches, repairs). Model likely overfits to D40-specific background patterns.

**HYPOTHESIS**: Adding diverse normal road images (asphalt variations, lighting conditions, occlusions) as negative samples will reduce false positives and improve pothole precision.

**EXPECTED EFFECT**: 
- Precision@pothole: +15-25%
- mAP50-95: +0.02-0.04
- Recall may drop slightly (-3-5%)

**EXPERIMENT DESIGN**:
- Source: Collect 2000-5000 normal road images from public datasets (Mapillary, KITTI, custom collection)
- Split: 80/10/10 train/val/test
- Training: Add as background class (class_id = background) or as negative samples in pothole training
- Augmentation: Match pothole augmentation pipeline

**CONTROL**: Current D40-derived dataset unchanged

**MEASUREMENT**:
- Per-class AP50, AP75, AP50-95
- Confusion matrix (FP sources)
- Precision-recall curves
- Inference on held-out diverse road scenes

**RISKS**:
- Domain shift if new negatives differ significantly from D40
- Annotation quality of sourced negatives
- Compute cost for 2-5x dataset size

---

## H2: Class Imbalance — Rare Class Under-representation

**OBSERVATION**: transverse_crack has only 30 instances. Other classes likely similarly imbalanced. Standard training ignores rare classes.

**HYPOTHESIS**: Reweighting loss (inverse frequency) or oversampling rare classes will improve recall on rare classes without collapsing precision.

**EXPECTED EFFECT**:
- transverse_crack recall: +30-50%
- transverse_crack AP50: +0.10-0.20
- mAP50-95: +0.01-0.03
- Majority class metrics: stable or -2-3%

**EXPERIMENT DESIGN**:
- Variant A: Class-balanced loss (CB loss, effective number of samples)
- Variant B: Oversampling rare classes to 100+ instances via augmentation
- Variant C: Focal loss (γ=2.0) + class weights
- Compare all three against baseline

**CONTROL**: Standard cross-entropy / YOLO default loss

**MEASUREMENT**:
- Per-class recall, precision, AP
- Training loss curves per class
- Gradient norm per class

**RISKS**:
- Overfitting to 30 transverse_crack samples even with augmentation
- Loss instability with extreme weights
- Augmentation may not capture true variance

---

## H3: Geographic/Domain Diversity for Pothole Generalization

**OBSERVATION**: D40 is geographically limited. Potholes vary by climate, asphalt mix, traffic, maintenance practices.

**HYPOTHESIS**: Adding geographically diverse pothole data (different countries, climates, road types) improves out-of-distribution generalization.

**EXPECTED EFFECT**:
- mAP50-95 on external test set: +0.03-0.06
- Robustness to lighting/weather: measurable improvement
- In-domain (D40) mAP: stable or slight drop (-0.01)

**EXPERIMENT DESIGN**:
- Source: RDD2022 (Japan, India, Czech), custom international collections
- Target: 500-1000 additional pothole instances across 5+ regions
- Stratify by: climate zone, asphalt type, lighting
- Train: Mixed batches (D40 + diverse) with domain labels

**CONTROL**: D40-only training

**MEASUREMENT**:
- In-domain (D40 test) vs out-of-domain (RDD2022, custom) AP
- Domain classifier accuracy on features (should decrease)
- t-SNE/UMAP of backbone features colored by domain

**RISKS**:
- Annotation inconsistency across sources
- Label noise in public datasets
- Class definition mismatch (what counts as pothole)

---

## H4: Low mAP50-95 Driven by Localization Quality

**OBSERVATION**: mAP50-95 (0.0903) << mAP50 (likely ~0.3-0.4 based on typical gap). Boxes are loose/imprecise.

**HYPOTHESIS**: Improving localization (IoU) via better anchors, loss functions, or post-processing will raise mAP50-95 disproportionately.

**EXPECTED EFFECT**:
- mAP50-95: +0.05-0.10
- mAP50: stable
- mAP75: +0.08-0.15

**EXPERIMENT DESIGN**:
- Variant A: CIoU/DIoU loss instead of standard bbox loss
- Variant B: Anchor optimization (k-means on D40 boxes)
- Variant C: Test-time augmentation (TTA) + NMS tuning
- Variant D: RefineDet-style refinement head

**CONTROL**: Current loss + default anchors

**MEASUREMENT**:
- mAP@50, @75, @50-95
- Average IoU of TP detections
- Box regression loss curves

**RISKS**:
- CIoU may slow convergence
- Anchor optimization needs sufficient boxes (may not help rare classes)
- TTA increases inference latency 3-5x

---

## H5: Transverse Crack — Synthetic Augmentation vs Collection

**OBSERVATION**: Only 30 transverse_crack instances — below viable training threshold.

**HYPOTHESIS**: Synthetic generation (copy-paste, GAN, diffusion) can create viable training data for transverse_crack, but real collection is better if feasible.

**EXPECTED EFFECT**:
- Synthetic: recall +20-30%, precision -10-15% (domain gap)
- Real collection (100+): recall +40-60%, precision stable

**EXPERIMENT DESIGN**:
- Track A: Copy-paste + strong augmentation (elastic, perspective, lighting)
- Track B: Stable Diffusion inpainting (prompt: "transverse crack on asphalt road")
- Track C: Active collection — label 100+ new instances
- Evaluate all three

**CONTROL**: 30-instance baseline

**MEASUREMENT**:
- Per-class AP on held-out real transverse_crack
- Visual inspection of synthetic quality
- FID/CLIP score synthetic vs real

**RISKS**:
- Synthetic data may teach artifacts
- Collection cost/time
- 30 real samples insufficient for reliable evaluation

---

## H6: Selection Bias — D40 Derivation Artifacts

**OBSERVATION**: D40 derived from selection process (unknown criteria). May have systematic biases (time of day, camera, road type).

**HYPOTHESIS**: Identifying and countering selection bias (reweighting, adversarial debiasing) improves robustness.

**EXPECTED EFFECT**:
- OOD generalization: +0.02-0.04 mAP
- In-domain: stable

**EXPERIMENT DESIGN**:
- Audit: Analyze D40 metadata (time, location, camera, annotator)
- Train domain classifier to predict D40 vs external
- Adversarial: Gradient reversal layer to remove domain info from features
- Reweight: Importance weighting by domain density

**CONTROL**: Standard training

**MEASUREMENT**:
- Domain classifier accuracy (target: 50%)
- OOD test set performance
- Feature distribution alignment (MMD)

**RISKS**:
- Metadata may be unavailable
- Adversarial training unstable
- May reduce in-domain performance

---

## H7: Multi-scale Feature Deficiency for Small Cracks

**OBSERVATION**: Cracks (especially transverse) are thin, elongated, small. Standard FPN may not capture well.

**HYPOTHESIS**: Adding high-resolution detection head (P2/8x) or specialized crack head improves small object AP.

**EXPECTED EFFECT**:
- transverse_crack AP50: +0.15-0.25
- longitudinal_crack AP50: +0.10-0.20
- mAP50-95: +0.02-0.04

**EXPERIMENT DESIGN**:
- Variant A: Add P2 head (8x stride) to YOLO neck
- Variant B: Crack-specific head (dilated conv, larger receptive field)
- Variant C: Feature pyramid attention (PANet + attention)

**CONTROL**: Standard YOLOv8/v11 neck

**MEASUREMENT**:
- Per-class AP by object size (small/medium/large)
- Feature map activation visualization
- FLOPs/latency impact

**RISKS**:
- P2 head increases compute significantly
- May overfit to noise at high resolution
- Requires architectural changes

---

## Prioritization Matrix

| Hypothesis | Impact | Effort | Risk | Priority |
|------------|--------|--------|------|----------|
| H1: Negative diversity | High | Medium | Medium | 1 |
| H2: Class imbalance | High | Low | Low | 2 |
| H4: Localization quality | High | Low | Low | 3 |
| H3: Geographic diversity | High | High | High | 4 |
| H5: Transverse crack synthetic | Medium | Medium | High | 5 |
| H7: Multi-scale features | Medium | High | Medium | 6 |
| H6: Selection bias | Low | High | High | 7 |

---

## Gate Criteria for Experiment 2 Selection

At evaluation gate, select hypotheses meeting:
1. **Feasibility**: Can execute in 1-2 weeks with available compute
2. **Impact**: Expected mAP50-95 delta ≥ 0.02
3. **Risk**: Mitigatable with validation checks
4. **Orthogonality**: Not redundant with other selected hypotheses

Target: Select 2-3 hypotheses for parallel Experiment 2 execution.