# Dataset B Identity

## Exact Source
CRDDC'2022 (IEEE Big Data Cup) Road Damage Dataset (RDD2022)

## URL/Source Location
- FigShare: https://doi.org/10.6084/m9.figshare.21431547
- GitHub: https://github.com/sekilab/RoadDamageDetector

## Exact Archive/File
- FigShare download: RoadDamageDataset.zip (approx 13.2 GB compressed)
- Contains: images/, annotations/ (Pascal VOC XML for train split), ImageSets/

## Subset/Country Consideration
Full RDD2022 includes data from 6 countries: Japan, India, Czech Republic, Norway, United States, China.

## Number of Images
- Total: 47,420 road images
- Labeled images: 25,727 (54%)
- Unlabeled images: 21,693 (46%)

## Number of Annotations
Total damage instances: 55,000+ (approximate; exact counts vary by source extraction)
Per-class distribution (approximate, from published analyses):
- D00 Longitudinal Crack: most frequent
- D10 Transverse Crack: least frequent
- D20 Alligator Crack: moderate
- D40 Pothole: moderate

## Classes
Exactly four classes matching CRDDC taxonomy:
- D00: Longitudinal Crack
- D10: Transverse Crack
- D20: Alligator Crack
- D40: Pothole (defined as "Other Corruption" including pothole, rutting, bump, separation)

## Class Definitions (per CRDDC)
- Longitudinal Crack: cracks aligned with direction of travel
- Transverse Crack: cracks perpendicular to direction of travel
- Alligator Crack: interconnected cracks forming alligator-skin pattern
- Pothole (D40): pothole, rutting, bump, separation (broader than pure pothole)

## Annotation Format
- Training set: Pascal VOC XML (.xml) files
- Test set: images only (no public ground truth)
- XML structure: standard Pascal VOC with <object><name>D00</name>... etc.

## License
CC BY 4.0 (Creative Commons Attribution 4.0 International) — permits commercial use with attribution.

## Geographic Distribution
- Japan
- India
- Czech Republic
- Norway
- United States
- China

## Negative/Background Images
Yes: 21,693 images (46%) have no damage annotations (unlabeled). These serve as hard negatives.

## Normal Road Images without Damage
Yes, the unlabeled images include normal road surfaces without visible damage.

## Pothole Images (D40)
Yes, D40 class images are present.

## Overlap with Current 1530-Image Artifact
The current artifact (`experiments/dataset/normalized_rdd2022_india/`) is the **India subset** of RDD2022.
- Current artifact: 1,530 images (all from India)
- Full RDD2022 India subset size: approximately 9,665 images (per earlier audit)
- Therefore, the current artifact is a subset of the India portion of RDD2022.

## Overlap with Existing 230-Image Test Set
The current test set (230 images) is drawn from the India subset (specifically from `normalized_rdd2022_india/images/test/`).
Thus, the test set images are part of the India subset and therefore **overlap** with the India portion of RDD2022.

## Acquisition Practicality
- Download size: ~13.2 GB (compressed)
- Download time: feasible with decent internet
- Storage required: ~15-20 GB after extraction
- Can be acquired within reasonable constraints.

## Notes
To avoid leakage, Experiment 2 must **exclude the India subset** (or at least exclude overlapping images with current train/val/test) when using RDD2022 as Dataset B.
Using only non-India portions of RDD2022 would yield approximately 47,420 - 9,665 ≈ 37,755 images, with 46% unlabeled (negatives) distributed across countries.