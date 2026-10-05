Hugging Face Dataset B Gate Report
==================================================

This document documents the evaluation of the Hugging Face dataset `dronefreak/RDD2022` as a candidate for Dataset B in Experiment 2.

## Overview
The Hugging Face dataset `dronefreak/RDD2022` is an unofficial redistribution of the official RDD2022 multi-national road damage dataset, reduced to the 4-class CRDDC2022 taxonomy and reformatted for YOLO compatibility.

## Important Notes
- This is NOT an official release - the repository explicitly states: "This repository is not an official release of the RDD2022 dataset."
- License: CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0 International)
- Data is stored in Arrow format, not traditional YOLO folder structure
- Images are partially available on disk (~38% of total dataset)
- All analysis is based on the available Arrow format metadata

## Acquisition Status
- Repo: dronefreak/RDD2022
- Revision: d597e2962458f7242a72aaa1b7909118d40f5d29
- Method: Hugging Face Hub download via load_from_disk
- Status: Partial download (38% of images on disk, but metadata complete)

## Files Generated
This gate report includes the following audit files:
1. candidate_identity.md - Repository identification and provenance
2. candidate_provenance.md - Detailed data origin and licensing
3. candidate_statistics.md - Dataset size, object counts, split information
4. country_audit.md - Country distribution and India exclusion analysis
5. negative_diversity_audit.md - Background diversity comparison
6. class_audit.md - Class distribution and transverse-crack analysis
7. taxonomy_audit.md - Taxonomy compatibility with project standards
8. overlap_audit.md - Dataset A overlap and test leakage analysis
9. split_leakage_audit.md - Training/validation/test split structure
10. experiment2_dataset_plan.md - Proposed Dataset B composition for Experiment 2
11. decision.md - Final gate decision

## Dataset Details
- Total images: 38,385 (26,869 train + 5,758 validation + 5,758 test)
- Total objects: 59,167
- Classes: 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole
- License: CC BY-SA 4.0 (attribution + share-alike required)
- Origin: Follows official RDD2022 (Arya et al., arXiv:2209.08538)

## Key Findings
1. **India overlap**: All 1,071 Dataset A train + 230 Dataset A test images are in HF India subset
2. **Negative diversity**: Dataset B has 33.8% background/negative images vs 0% in Dataset A
3. **Transverse-crack**: Dataset B has ~8,336 instances vs 30 in Dataset A (massive increase)
4. **Taxonomy**: D00→0, D10→1, D20→2, D40→3 (with D40 semantic-broadening caveat)
5. **Country distribution**: Japan 10,506, Norway 8,161, India 7,706, United 4,805, China 4,378, Czech 2,829
6. **Data quality**: Arrow format is complete and validated

## Decision Outlook
Given the above findings, this dataset can serve as Dataset B for Experiment 2, provided that:
1. All India images are excluded from Dataset B
2. The D40→pothole semantic caveat is preserved
3. The frozen test set is protected (no leakage after India exclusion)
4. The dataset can be properly converted to YOLO format for training

DO NOT TRAIN, but prepare the Experiment 2 dataset structure as specified.
