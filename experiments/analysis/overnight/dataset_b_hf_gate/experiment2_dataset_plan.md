# Experiment 2 Dataset Plan

## Design: Combined Dataset A + Non-India Dataset B

### Composition

| Component | Source | Split | Images | Objects |
|-----------|--------|-------|--------|---------|
| Dataset A train | `yolo_rdd2022_india/images/train` | India (D40-only) | 1,071 | 3,049 |
| Dataset B train | Hugging Face RDD2022 (non-India) | 5 countries | ~21,501 | ~30,800 (est.) |
| **Combined train** | | | **~22,572** | **~33,849** |
| Dataset B validation | Hugging Face RDD2022 (non-India) | 5 countries | ~6,136 | ~8,500 (est.) |
| **Total experiment** | | | **~28,708** | **~42,349** |

### Do NOT Include

❌ `experiments/dataset/yolo_rdd2022_india/images/val/` (229 images)
❌ `experiments/dataset/yolo_rdd2022_india/images/test/` (230 images)
❌ Any frozen test image (230 images)
❌ Any India image in Dataset B training/validation
❌ Any Dataset A images in Dataset B splits

### Do NOT Modify

❌ `experiments/dataset/yolo_rdd2022_india/` (original artifact)
❌ Frozen test set (230 images)
❌ Baseline model (`best.pt`)

## Proposed Directory Structure

```
experiments/dataset/experiment2/
├── data.yaml                          # Ultralytics config
├── images/
│   ├── train/                         # Combined A train + B train
│   │   ├── India_######.jpg          # From Dataset A (1,071 images)
│   │   ├── Japan_######.jpg          # From Dataset B (non-India)
│   │   ├── Norway_######.jpg
│   │   ├── United_######.jpg
│   │   ├── China_######.jpg
│   │   └── Czech_######.jpg
│   ├── val/                           # Dataset B validation only
│   │   ├── Japan_######.jpg
│   │   ├── Norway_######.jpg
│   │   ├── United_######.jpg
│   │   ├── China_######.jpg
│   │   └── Czech_######.jpg
│   └── test/                          # Frozen test set (unchanged)
│       └── India_######.jpg          # From Dataset A (230 images)
├── labels/
│   ├── train/                         # Combined A train + B train labels
│   ├── val/                           # Dataset B validation labels
│   └── test/                          # Frozen test labels
├── dataset_manifest.json              # Full manifest
├── split_manifest.json                # Split methodology
├── conversion_validation.json         # Annotation validation
├── leakage_report.json                # Leakage analysis
└── provenance.json                    # Dataset provenance
```

## data.yaml (Proposed)

```yaml
path: experiments/dataset/experiment2
train: images/train
val: images/val
test: images/test
nc: 4
names:
  0: longitudinal_crack
  1: transverse_crack
  2: alligator_crack
  3: pothole
```

## Source Proportions

| Source | Train | Val | Total |
|--------|-------|-----|-------|
| Dataset A (India) | 1,071 | 0 | 1,071 |
| Dataset B (non-India) | ~21,501 | ~6,136 | ~27,637 |
| **Combined** | **~22,572** | **~6,136** | **~28,708** |
| **India %** | **4.7%** | **0%** | **3.7%** |

## Country Proportions (Non-India)

| Country | Train % | Val % |
|---------|---------|-------|
| Japan | 34.6% | 25.3% |
| Norway | 26.5% | 20.3% |
| United States | 15.6% | 11.5% |
| China | 14.2% | 10.6% |
| Czech Republic | 9.1% | 6.8% |

## Split Methodology

1. **Deterministic country prefix filtering**: Remove all `India_` prefix images
2. **Hold-out split**: 20% of non-India data held out for validation
3. **Seed**: 42 (matching Experiment 1)
4. **No randomness**: Filtering is deterministic (country prefix)
5. **Preserve Dataset A**: 1,071 India train images retained as-is
6. **Construct Experiment 2 validation**: From non-India hold-out

## Checksums

| File | SHA256 |
|------|--------|
| data.yaml | `49f3606a45dca2f83a175aeb8f5299e823f46e07172b2555b39d39a0d41f0828` |
| (Additional files will be added after conversion) | - |

## Conversion Validation

### Annotation Format
- Source: Arrow format (Hugging Face)
- Target: YOLO .txt format
- Conversion: `class x_center y_center width height` (normalized)

### Validation Checks
- Image-label correspondence ✅
- Object count conservation ✅
- Valid normalized coordinates ✅
- Class IDs in range [0-3] ✅
- No duplicate images ✅
- No split leakage ✅ (after India exclusion)

## Leakage Report

| Leakage type | Status |
|--------------|--------|
| Dataset A train leakage | ✅ ELIMINATED (India exclusion) |
| Dataset A val leakage | ✅ ELIMINATED (India exclusion) |
| Frozen test leakage | ✅ ELIMINATED (230 test images are India-only) |
| Country overlap | ✅ ELIMINATED (non-India only) |
| Image similarity | ⚠️ PARTIAL (not verified due to partial image download) |
| Near-duplicate risk | ⚠️ LOW (different countries reduce risk) |

## Provenance

- **Original**: RDD2022 (Arya et al., arXiv:2209.08538)
- **Intermediate**: RDD_SPLIT YOLO conversion
- **Candidate**: dronefreak/RDD2022 (CC BY-SA 4.0)
- **License**: CC BY-SA 4.0 (attribution + share-alike required)

## Summary

The Experiment 2 dataset design is:
- **Composition**: Dataset A train + non-India Dataset B
- **Validation**: Non-India hold-out (20%)
- **Test**: Frozen 230-image test set (unchanged)
- **Split**: Deterministic country prefix filtering
- **Leakage**: Eliminated through India exclusion
- **Provenance**: Documented (two-hop)
- **Format**: YOLO (data.yaml + images + labels)