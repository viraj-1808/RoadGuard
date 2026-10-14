# Holdout Set Evaluation Report

**Generated**: 2026-10-11T05:20:18.478818Z
**Holdout Images**: 14
**CLEAR Status Images**: 5
**UNCERTAIN Status Images**: 9

## Holdout Set Composition

| Image | Status | Annotations | Classes |
|-------|--------|-------------|---------|
| road001.webp | CLEAR | 2 | pothole(3), pothole(3) |
| road002.jpg | CLEAR | 1 | pothole(3) |
| road003.jpg | CLEAR | 1 | alligator_crack(2) |
| road005.jpg | UNCERTAIN | 0 | None |
| road007.jpg | CLEAR | 1 | pothole(3) |
| road012.jpg | UNCERTAIN | 0 | None |
| road016.jpg | UNCERTAIN | 0 | None |
| road019.jpg | UNCERTAIN | 0 | None |
| road023.jpg | UNCERTAIN | 0 | None |
| road026.jpg | CLEAR | 1 | alligator_crack(2) |
| road029.jpg | UNCERTAIN | 0 | None |
| road037.jpg | UNCERTAIN | 0 | None |
| road038.jpg | UNCERTAIN | 0 | None |
| road039.jpg | UNCERTAIN | 0 | None |

## Threshold Comparison: Original (Epoch72) vs Fine-Tuned

### Overall Micro Metrics

| Model | Conf | Micro_P | Micro_R | Micro_F1 | Pothole_P | Pothole_R | Pothole_F1 | Img_Acc |
|-------|------|---------|---------|----------|-----------|-----------|------------|---------|
| Original_Epoch72 | 0.05 | 0.0556 | 0.1667 | 0.0833 | 0.2500 | 0.2500 | 0.2500 | 0.5000 |
| Original_Epoch72 | 0.10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Original_Epoch72 | 0.15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Original_Epoch72 | 0.20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Original_Epoch72 | 0.25 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Original_Epoch72 | 0.30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| FineTuned | 0.05 | 0.0556 | 0.1667 | 0.0833 | 0.2500 | 0.2500 | 0.2500 | 0.5000 |
| FineTuned | 0.10 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| FineTuned | 0.15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| FineTuned | 0.20 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| FineTuned | 0.25 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| FineTuned | 0.30 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |

### Per-Class Metrics at Each Threshold

#### Original_Epoch72

| Conf | Class | TP | FP | FN | Precision | Recall | F1 |
|------|-------|----|----|----|-----------|--------|----|
| 0.05 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | transverse_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | alligator_crack | 0 | 12 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | pothole | 1 | 3 | 3 | 0.2500 | 0.2500 | 0.2500 |
| 0.10 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | alligator_crack | 0 | 7 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | pothole | 0 | 1 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | alligator_crack | 0 | 4 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | alligator_crack | 0 | 4 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | longitudinal_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | alligator_crack | 0 | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | longitudinal_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | alligator_crack | 0 | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |

#### FineTuned

| Conf | Class | TP | FP | FN | Precision | Recall | F1 |
|------|-------|----|----|----|-----------|--------|----|
| 0.05 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | transverse_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | alligator_crack | 0 | 12 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.05 | pothole | 1 | 3 | 3 | 0.2500 | 0.2500 | 0.2500 |
| 0.10 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | alligator_crack | 0 | 7 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.10 | pothole | 0 | 1 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | alligator_crack | 0 | 4 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.15 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | longitudinal_crack | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | alligator_crack | 0 | 4 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.20 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | longitudinal_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | alligator_crack | 0 | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.25 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | longitudinal_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | transverse_crack | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | alligator_crack | 0 | 2 | 2 | 0.0000 | 0.0000 | 0.0000 |
| 0.30 | pothole | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |

### Image-Level Correctness

| Model | Conf | Correct/Total | Accuracy | CLEAR Correct | CLEAR Total |
|-------|------|---------------|----------|---------------|-------------|
| Original_Epoch72 | 0.05 | 7/14 | 0.5000 | 0/5 | 5 |
| Original_Epoch72 | 0.10 | 7/14 | 0.5000 | 0/5 | 5 |
| Original_Epoch72 | 0.15 | 7/14 | 0.5000 | 0/5 | 5 |
| Original_Epoch72 | 0.20 | 7/14 | 0.5000 | 0/5 | 5 |
| Original_Epoch72 | 0.25 | 7/14 | 0.5000 | 0/5 | 5 |
| Original_Epoch72 | 0.30 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.05 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.10 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.15 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.20 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.25 | 7/14 | 0.5000 | 0/5 | 5 |
| FineTuned | 0.30 | 7/14 | 0.5000 | 0/5 | 5 |

### Pothole-Specific Performance

| Model | Conf | TP | FP | FN | Precision | Recall | F1 |
|-------|------|----|----|----|-----------|--------|----|
| Original_Epoch72 | 0.05 | 1 | 3 | 3 | 0.2500 | 0.2500 | 0.2500 |
| Original_Epoch72 | 0.10 | 0 | 1 | 4 | 0.0000 | 0.0000 | 0.0000 |
| Original_Epoch72 | 0.15 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| Original_Epoch72 | 0.20 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| Original_Epoch72 | 0.25 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| Original_Epoch72 | 0.30 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| FineTuned | 0.05 | 1 | 3 | 3 | 0.2500 | 0.2500 | 0.2500 |
| FineTuned | 0.10 | 0 | 1 | 4 | 0.0000 | 0.0000 | 0.0000 |
| FineTuned | 0.15 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| FineTuned | 0.20 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| FineTuned | 0.25 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |
| FineTuned | 0.30 | 0 | 0 | 4 | 0.0000 | 0.0000 | 0.0000 |

## Best Operating Points

### Original_Epoch72
- **Best Confidence Threshold**: 0.05
- **Micro F1**: 0.0833
- **Pothole F1**: 0.2500
- **Image Accuracy**: 0.5000 (7/14)

### FineTuned
- **Best Confidence Threshold**: 0.05
- **Micro F1**: 0.0833
- **Pothole F1**: 0.2500
- **Image Accuracy**: 0.5000 (7/14)

## Extrapolation to 100-Image Target

Only 39 images total available (14 in holdout, 5 with CLEAR annotations).
The 75/100 target requires evaluation on a larger, fully-annotated test set.

**Current Holdout Results (5 CLEAR images):**

- **Original_Epoch72** (conf=0.05): 0/5 CLEAR images correct
  - Extrapolated to 100 CLEAR images: ~0/100

- **FineTuned** (conf=0.05): 0/5 CLEAR images correct
  - Extrapolated to 100 CLEAR images: ~0/100

### Gap Analysis

- **Available CLEAR annotations**: 5/14 holdout images (36%)
- **Total dataset**: 39 images (vs 100 target)
- **UNCERTAIN images**: 9/14 holdout images have no ground truth
- **Recommendation**: Human annotation of UNCERTAIN images needed for reliable 100-image evaluation

---
*Generated by holdout_evaluation.py*