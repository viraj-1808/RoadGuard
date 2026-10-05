# Dataset Research for Road Damage Detection

This report evaluates candidate road-damage datasets for potential use in Experiment 2.

## Datasets Evaluated

- RDD2022 (official, beyond India subset)
- RDD2020
- Pothole-600
- BharatPotHole
- iWatchRoad
- Other credible road-damage datasets

## Evaluation Criteria

For each dataset, we report:
- SOURCE
- LICENSE
- SIZE
- TASK
- CLASSES
- POTHOLE SEMANTICS
- NEGATIVE IMAGES
- GEOGRAPHY
- ANNOTATION FORMAT
- COMPATIBILITY with our 4 classes (longitudinal_crack, transverse_crack, alligator_crack, pothole)
- RISKS
- RECOMMENDATION (usable/potentially usable/unsuitable/requires manual review)

---

## 1. RDD2022

**SOURCE**: CRDDC'2022 (IEEE Big Data Cup), released via FigShare (DOI: 10.6084/m9.figshare.21431547). GitHub: github.com/sekilab/RoadDamageDetector

**LICENSE**: CC BY 4.0 (permissive, commercial use allowed with attribution)

**SIZE**: 47,420 road images, 55,000+ damage instances; 21,693 (46%) unlabeled images

**TASK**: Multi-class object detection & classification (4 damage categories + other corruption)

**CLASSES**: D00 Longitudinal Crack, D10 Transverse Crack, D20 Alligator Crack, D40 Pothole

**POTHOLE SEMANTICS**: D40 = pothole; clearly defined as a top-level category; bounding box annotation

**NEGATIVE IMAGES**: Yes — 46% of images have no damage annotations (hard negatives included)

**GEOGRAPHY**: Japan, India, Czech Republic, Norway, United States, China (6 countries)

**ANNOTATION FORMAT**: Pascal VOC XML (train), images only (test)

**COMPATIBILITY**: Perfect match — exactly our 4 classes (D00/D10/D20/D40). Direct class-name mapping.

**RISKS**: Class imbalance (longitudinal cracks most frequent, alligator/pothole underrepresented); China subset uses top-down drone/handheld images differing from street-level perspective of other countries; test set unlabeled (no evaluation ground truth publicly available)

**RECOMMENDATION**: USABLE — primary candidate for Experiment 2

---

## 2. RDD2020

**SOURCE**: Arya et al., Data in Brief, 2021 (DOI: 10.1016/j.dib.2021.107133). Mendeley Data: doi:10.17632/5ty2wb6gvg.2

**LICENSE**: CC BY-NC-SA 3.0 (non-commercial restriction)

**SIZE**: 26,336 road images, 31,000+ damage instances

**TASK**: Road damage detection & classification (4 categories)

**CLASSES**: D00 Longitudinal Crack, D10 Transverse Crack, D20 Alligator Crack, D40 Pothole

**POTHOLe SEMANTICS**: D40 = pothole; same schema as RDD2022

**NEGATIVE IMAGES**: Yes — includes un-cracked road images for false positive mitigation

**GEOGRAPHY**: India, Japan, Czech Republic (3 countries)

**ANNOTATION FORMAT**: Pascal VOC XML (.xml), Label Map (.pbtxt)

**COMPATIBILITY**: Perfect match — same 4 classes as RDD2022 (subset of RDD2022 data)

**RISKS**: CC BY-NC-SA restricts commercial use; smaller than RDD2022; RDD2022 is superset including RDD2020 data plus Norway/US/China

**RECOMMENDATION**: POTENTIALLY USABLE — but RDD2022 superset preferred; license non-commercial restriction is a blocker for commercial deployment

---

## 3. Pothole-600

**SOURCE**: Fan et al., IEEE T-IP, 2019/2020 (DOI: 10.1109/TIP.2019.2941537). GitHub: github.com/ruirangerfan/stereo_pothole_datasets

**LICENSE**: MIT (permissive, from GitHub repository)

**SIZE**: 600 RGB images + disparity maps + binary segmentation masks + 3D point clouds

**TASK**: Pothole detection via disparity transformation and road surface modeling

**CLASSES**: Binary pothole / non-pothole (single-class segmentation)

**POTHOLE SEMANTICS**: Pixel-level pothole labels via binary masks; top-down stereo view; depth-informed

**NEGATIVE IMAGES**: Yes (undamaged road regions included)

**GEOGRAPHY**: Not explicitly stated (likely North America based on author affiliations)

**ANNOTATION FORMAT**: Binary segmentation masks, disparity maps, color-transformed disparity, 3D point clouds

**COMPATIBILITY**: PARTIAL — only pothole class, no crack types; pixel-level segmentation not bounding-box detection; top-down stereo perspective differs from street-level imagery

**RISKS**: Only 600 images; binary classification only; requires stereo camera data (not standard RGB); small scale; no crack classes at all

**RECOMMENDATION**: UNUSABLE for 4-class detection; potentially usable for pothole-only sub-task or depth-aware models

---

## 4. BharatPotHole

**SOURCE**: Sahoo, Mohanty, Mishra (NISER), arXiv:2508.10945, 2025. Kaggle: kaggle.com/datasets/surbhisaswatimohanty/bharatpothole

**LICENSE**: Not explicitly stated (Kaggle dataset, self-annotated)

**SIZE**: 7,000+ annotated frames (BharatPotHole-7K)

**TASK**: Pothole detection (YOLOv8 fine-tuned); severity rating included

**CLASSES**: Pothole only (single class)

**POTHOLE SEMANTICS**: Bounding box via Roboflow; severity ratings; dashcam perspective

**NEGATIVE IMAGES**: Yes (frames without potholes in training)

**GEOGRAPHY**: India only (diverse Indian road conditions, weather, lighting)

**ANNOTATION FORMAT**: YOLO format (converted from Roboflow)

**COMPATIBILITY**: PARTIAL — only pothole class; no crack classes; single-class detection only

**RISKS**: Self-annotated (quality concerns); single class only; Indian roads only; license unclear; no explicit negative class definition; small scale (~7K frames)

**RECOMMENDATION**: POTENTIALLY USABLE for pothole-only transfer learning; requires manual review of annotation quality and license clarification

---

## 5. iWatchRoad

**SOURCE**: Sahoo, Mohanty, Mishra (NISER), arXiv:2508.10945, 2025. GitHub: github.com/smlab-niser/iwatchroad

**LICENSE**: Not explicitly stated (publicly available on Kaggle)

**SIZE**: 7,000+ dashcam frames (same underlying dataset as BharatPotHole)

**TASK**: Pothole detection + geospatial mapping + OCR-based GPS tagging

**CLASSES**: Pothole only (single class)

**POTHOLE SEMANTICS**: YOLO bounding boxes; GPS-tagged; severity ratings; OCR-synced timestamps

**NEGATIVE IMAGES**: Yes

**GEOGRAPHY**: India only

**ANNOTATION FORMAT**: YOLO format

**COMPATIBILITY**: PARTIAL — only pothole class; no crack classes; same dataset as BharatPotHole (iWatchRoad is the system, BharatPotHole is the data)

**RISKS**: Same as BharatPotHole (self-annotated, single class, unclear license); iWatchRoad and BharatPotHole are essentially the same dataset/system; not a separate independent dataset

**RECOMMENDATION**: POTENTIALLY USABLE for pothole-only; requires manual review; likely redundant with BharatPotHole

---

## 6. Cracks and Potholes in Road Images (Brazil)

**SOURCE**: Passos et al., Mendeley Data, 2020 (DOI: 10.17632/t576ydh9v8.4). GitHub: github.com/biankatpas/Cracks-and-Potholes-in-Road-Images-Dataset

**LICENSE**: MIT (permissive)

**SIZE**: 2,235 images

**TASK**: Crack and pothole detection using texture descriptors + ML (SVM, KNN, MLP)

**CLASSES**: Crack (binary mask), Pothole (binary mask), Road (mask) — 3 masks per image

**POTHOLE SEMANTICS**: Binary pothole mask; not a multi-class distinction between crack types

**NEGATIVE IMAGES**: Road background mask serves as negative

**GEOGRAPHY**: Brazil (Espírito Santo, Rio Grande do Sul, Federal District)

**ANNOTATION FORMAT**: PNG binary masks (3 per image)

**COMPATIBILITY**: PARTIAL — only cracks + potholes (binary), no class distinction between longitudinal/transverse/alligator; segmentation masks not bounding boxes

**RISKS**: Small (2,235 images); only 2 damage types; binary segmentation masks not bounding boxes; Brazil-specific road conditions

**RECOMMENDATION**: UNUSABLE for 4-class detection; potentially usable for crack/pothole binary segmentation research

---

## 7. DeepCrack

**SOURCE**: Liu et al., Neurocomputing, 2019 (DOI: 10.1016/j.neucom.2019.01.036). GitHub: github.com/yhlleo/DeepCrack

**LICENSE**: Restricted — non-commercial research/educational only (per GitHub README)

**SIZE**: 537 images (DeepCrack benchmark); CrackTree260: 260 images (augmented to 35,100)

**TASK**: Crack detection (semantic segmentation)

**CLASSES**: Crack (binary segmentation)

**POTHOLE SEMANTICS**: N/A — cracks only, no potholes

**NEGATIVE IMAGES**: Yes (background)

**GEOGRAPHY**: Various pavement surfaces

**ANNOTATION FORMAT**: Pixel-level binary masks

**COMPATIBILITY**: PARTIAL — cracks only, no potholes; segmentation not detection; small scale

**RISKS**: License restricts commercial use; crack-only; small scale; not compatible with object detection pipeline

**RECOMMENDATION**: UNUSABLE for 4-class detection

---

## 8. RoadDamageVision

**SOURCE**: Zendron & Leithardt, Mendeley Data, 2026 (DOI: 10.17632/ypm4h4z25c.3)

**LICENSE**: Not explicitly stated (Mendeley Data)

**SIZE**: 4,049 images, 7,647 instances

**TASK**: Road damage detection (drone/aerial imagery)

**CLASSES**: D00, D10, D20, D40, Repair, Block Crack (6 classes)

**POTHOLE SEMANTICS**: D40 = pothole (most common, 3,566 instances; primarily Spanish subset)

**NEGATIVE IMAGES**: Yes

**GEOGRAPHY**: China, Spain (aerial/drone perspective)

**ANNOTATION FORMAT**: COCO format bounding boxes

**COMPATIBILITY**: PARTIAL — has D00/D10/D20/D40 plus extra classes (Repair, Block Crack); aerial view differs from street-level

**RISKS**: Aerial perspective differs from ground-level; Spanish potholes dominant; extra classes not in our schema; license unclear; mixed countries

**RECOMMENDATION**: POTENTIALLY USABLE with domain adaptation; requires manual review of aerial vs. street-level compatibility

---

## 9. GAPs (German Asphalt Pavement Distress)

**SOURCE**: Eisenbach et al., CASE 2021. TU Ilmenau

**LICENSE**: Free for academic use only (restricted)

**SIZE**: 1,969 grayscale images

**TASK**: Pavement distress detection (6 classes)

**CLASSES**: Crack, Pothole, Inlaid patch, Applied patch, Open joint, Bleeding

**POTHOLE SEMANTICS**: Pothole is one class; not differentiated from other distresses in crack taxonomy

**NEGATIVE IMAGES**: Yes

**GEOGRAPHY**: Germany (federal roads)

**ANNOTATION FORMAT**: Bounding boxes + pixel-level annotations

**COMPATIBILITY**: PARTIAL — has pothole + cracks but not our specific 4-class breakdown; grayscale; German roads only

**RISKS**: Restricted license (academic only); grayscale; German roads only; crack types not distinguished (longitudinal/transverse/alligator not separated)

**RECOMMENDATION**: UNUSABLE for our 4-class schema; requires manual review

---

## 10. UDTIRI-Crack

**SOURCE**: Song et al., 2023 (arXiv). Kaggle: kaggle.com/datasets/jefffffffsong/udtiri-crack

**LICENSE**: Not specified

**SIZE**: 2,500 images (320×320 px)

**TASK**: Crack detection (benchmark dataset)

**CLASSES**: Crack (binary)

**POTHOLE SEMANTICS**: N/A — cracks only

**NEGATIVE IMAGES**: Yes

**GEOGRAPHY**: Multi-source (7 public datasets)

**ANNOTATION FORMAT**: Pixel-level binary masks

**COMPATIBILITY**: PARTIAL — cracks only, no potholes; segmentation not detection

**RISKS**: Crack-only; small scale; no pothole class; not compatible with 4-class detection

**RECOMMENDATION**: UNUSABLE for 4-class detection

---

## Summary Table

| Dataset | License | Size | Classes | Pothole | Compatibility | Recommendation |
|---------|---------|------|---------|---------|---------------|----------------|
| RDD2022 | CC BY 4.0 | 47K images, 55K instances | 4 (D00/D10/D20/D40) | D40 | Perfect | USABLE |
| RDD2020 | CC BY-NC-SA 3.0 | 26K images, 31K instances | 4 (D00/D10/D20/D40) | D40 | Perfect | POTENTIALLY (license restrict) |
| Pothole-600 | MIT | 600 images | Binary pothole | Pixel mask | Partial | UNUSABLE (4-class) |
| BharatPotHole | Unclear | 7K frames | Pothole only | Bounding box | Partial | POTENTIALLY (review) |
| iWatchRoad | Unclear | 7K frames | Pothole only | Bounding box | Partial | POTENTIALLY (review) |
| Brazil Cracks/Potholes | MIT | 2,235 images | Crack + Pothole (binary) | Binary mask | Partial | UNUSABLE |
| DeepCrack | Restricted | 537 images | Crack only | N/A | Partial | UNUSABLE |
| RoadDamageVision | Unclear | 4K images | 6 (incl. D00-D40) | D40 | Partial | POTENTIALLY (review) |
| GAPs | Academic only | 1,969 images | 6 distress types | Pothole | Partial | UNUSABLE |
| UDTIRI-Crack | Unclear | 2,500 images | Crack only | N/A | Partial | UNUSABLE |

---

## Key Findings

1. **RDD2022 is the clear primary candidate**: CC BY 4.0 license, 47K images, perfect 4-class match, 6-country geography, 46% negative images, widely used benchmark.

2. **RDD2020 is a subset of RDD2022**: Same 4 classes but CC BY-NC-SA (non-commercial) and smaller. Not recommended if RDD2022 is available.

3. **Pothole-600 is pothole-only**: Binary pothole detection with stereo depth; not compatible with 4-class crack+pothole detection.

4. **BharatPotHole / iWatchRoad are India-specific**: Single-class (pothole only), self-annotated, license unclear. Useful for pothole-only fine-tuning but not full 4-class detection.

5. **Other datasets (Brazil, DeepCrack, GAPs, UDTIRI-Crack)**: All have significant limitations — small scale, crack-only, binary segmentation, restrictive licenses, or geography mismatch.

6. **RoadDamageVision** is interesting but aerial perspective and mixed classes require domain adaptation.

## Recommendations for Experiment 2

1. **Primary**: Use RDD2022 as the main training dataset (CC BY 4.0, 4-class perfect match).
2. **Secondary**: Consider RoadDamageVision for additional pothole examples (Spanish subset) if domain adaptation is feasible.
3. **Auxiliary**: BharatPotHole for pothole-specific fine-tuning under challenging Indian conditions, pending license clarification.
4. **Avoid**: Pothole-600 (binary only), DeepCrack (restricted license), GAPs (academic-only license), UDTIRI-Crack (cracks only).

---

*Research compiled 2026-09-29 by Agent E (Dataset Researcher). READ-ONLY task — no datasets downloaded.*