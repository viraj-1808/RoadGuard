# Experiment 2 Conversion Report

## Status: NOT CREATED

**Dataset B not acquired — YOLO conversion cannot be performed.**

## Proposed Conversion Design (Theoretical)

If Dataset B were acquired, the conversion would be:

### Source Format
- **Annotations**: Pascal VOC XML (.xml) in `train/annotations/xmls/` per country
- **Images**: JPEG (.jpg) in `train/images/` per country
- **Classes**: D00, D10, D20, D40 (CRDDC taxonomy)

### Target Format (YOLO)
- **Annotations**: YOLO format (.txt) with normalized center coordinates [class cx cy w h]
- **Images**: JPEG (.jpg) unchanged
- **Classes**: 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole

### Class Mapping
| Source Class | Source Meaning | Target Class | Target ID | Confidence |
|--------------|----------------|--------------|-----------|------------|
| D00 | Longitudinal Crack | longitudinal_crack | 0 | HIGH |
| D10 | Transverse Crack | transverse_crack | 1 | HIGH |
| D20 | Alligator Crack | alligator_crack | 2 | HIGH |
| D40 | Pothole (Other Corruption) | pothole | 3 | MEDIUM |

### D40 Semantics Caveat
D40 = "Other Corruption" in CRDDC taxonomy (pothole + rutting + bump + separation).
Our project class 3 maps to this broader definition, not purely "pothole".
Same mapping as baseline — no new semantic mismatch introduced.

### Excluded Classes
No classes excluded from RDD2022 (only 4 classes present).

### Conversion Validation (Would Be Performed)
- Image-label correspondence (every image has label file, every label has image)
- Object count conservation (no objects lost/gained)
- Valid normalized coordinates (0-1 range, cx+w/2 <= 1, cy+h/2 <= 1)
- Class IDs in range [0-3]
- Bbox geometry valid (w>0, h>0)
- No duplicate images in output splits
- No split leakage (group-based)

## data.yaml (Proposed)

```yaml
names:
  - longitudinal_crack
  - transverse_crack
  - alligator_crack
  - pothole
nc: 4
path: experiments/dataset/experiment2
train: images/train
val: images/val
test: images/test
```

Note: `test` points to frozen test set at `experiments/dataset/yolo_rdd2022_india/images/test/`

## Gate Failures Preventing Conversion

| Gate | Status | Notes |
|------|--------|-------|
| G1 Dataset B acquisition | FAIL | S3 403, FigShare too slow |
| G4 Exact image count | N/A | No data |
| G5 Annotation validation | N/A | No data |
| G13 YOLO conversion validation | N/A | No data |

## Conclusion

**Conversion cannot be performed without Dataset B.**
Experiment 2 blocked until Dataset B acquisition succeeds.