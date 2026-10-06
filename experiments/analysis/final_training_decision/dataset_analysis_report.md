# RoadGuard AI - Dataset Coverage and Size Analysis Report

**Generated:** 2026-10-06 13:08:40

## Executive Summary

- **Total subsets analyzed:** 5
- **Total images:** 23550
- **Total annotated objects:** 44755
- **Classes:** longitudinal_crack, transverse_crack, alligator_crack, pothole

## Dataset Overview

| Subset | Dataset | Split | Images | Valid | Objects | Unique Dims |
|--------|---------|-------|--------|-------|---------|-------------|
| dataset_a_train | A | train | 1071 | 1071 | 3049 | 1 |
| dataset_a_val | A | val | 229 | 229 | 632 | 1 |
| dataset_a_test | A | test | 230 | 230 | 679 | 1 |
| dataset_b_train | B | train | 19719 | 19719 | 36358 | 10 |
| dataset_b_val | B | val | 2301 | 2301 | 4037 | 9 |

## Class Distribution per Subset

| Subset | Lc | Tc | Ac | Ph | Total |
|--------|--------|--------|--------|--------|--------|
| dataset_a_train | 356 (11.7%) | 21 (0.7%) | 453 (14.9%) | 2219 (72.8%) | 3049 |
| dataset_a_val | 76 (12.0%) | 4 (0.6%) | 96 (15.2%) | 456 (72.2%) | 632 |
| dataset_a_test | 66 (9.7%) | 5 (0.7%) | 96 (14.1%) | 512 (75.4%) | 679 |
| dataset_b_train | 15206 (41.8%) | 7292 (20.1%) | 5816 (16.0%) | 8044 (22.1%) | 36358 |
| dataset_b_val | 1758 (43.5%) | 918 (22.7%) | 664 (16.4%) | 697 (17.3%) | 4037 |

## Bounding Box Statistics (Normalized Coordinates)

| Subset | W Min | W Max | W Mean | H Min | H Max | H Mean |
|--------|-------|-------|--------|-------|-------|--------|
| dataset_a_train | 0.0208 | 0.9972 | 0.2015 | 0.0167 | 0.6833 | 0.1213 |
| dataset_a_val | 0.0278 | 0.9264 | 0.2038 | 0.0194 | 0.4972 | 0.1212 |
| dataset_a_test | 0.0250 | 0.9597 | 0.2109 | 0.0167 | 0.4819 | 0.1240 |
| dataset_b_train | 0.0017 | 0.9990 | 0.2138 | 0.0017 | 0.9980 | 0.1673 |
| dataset_b_val | 0.0030 | 0.9983 | 0.2156 | 0.0047 | 0.9980 | 0.1733 |

## Bounding Box Statistics (Pixel Coordinates)

| Subset | Area Min | Area Max | Area Mean | Rel Area Min | Rel Area Max | Rel Area Mean |
|--------|----------|----------|-----------|--------------|--------------|---------------|
| dataset_a_train | 304.0 | 346367.9 | 18389.3 | 0.000586 | 0.668148 | 0.035473 |
| dataset_a_val | 400.0 | 238785.9 | 18547.2 | 0.000772 | 0.460621 | 0.035778 |
| dataset_a_test | 340.0 | 179095.2 | 19541.6 | 0.000656 | 0.345477 | 0.037696 |
| dataset_b_train | 1.0 | 1001129.0 | 27771.5 | 0.000003 | 0.923319 | 0.046923 |
| dataset_b_val | 138.0 | 776734.1 | 27991.5 | 0.000037 | 0.830406 | 0.048085 |

## Object Size Distribution by Relative Area

- **Very Small:** < 0.1% of image area
- **Small:** 0.1% – 1% of image area
- **Medium:** 1% – 10% of image area
- **Large:** > 10% of image area

| Subset | Class | Very Small | Small | Medium | Large | Total | Very Small % | Small % | Medium % | Large % |
|--------|-------|------------|-------|--------|-------|-------|--------------|---------|----------|---------|
| dataset_a_train | longitudinal_crack | 0 | 114 | 229 | 13 | 356 | 0.00% | 32.02% | 64.33% | 3.65% |
| dataset_a_train | transverse_crack | 0 | 5 | 16 | 0 | 21 | 0.00% | 23.81% | 76.19% | 0.00% |
| dataset_a_train | alligator_crack | 0 | 16 | 245 | 192 | 453 | 0.00% | 3.53% | 54.08% | 42.38% |
| dataset_a_train | pothole | 25 | 1179 | 916 | 99 | 2219 | 1.13% | 53.13% | 41.28% | 4.46% |
| dataset_a_val | longitudinal_crack | 0 | 29 | 47 | 0 | 76 | 0.00% | 38.16% | 61.84% | 0.00% |
| dataset_a_val | transverse_crack | 0 | 1 | 3 | 0 | 4 | 0.00% | 25.00% | 75.00% | 0.00% |
| dataset_a_val | alligator_crack | 0 | 2 | 52 | 42 | 96 | 0.00% | 2.08% | 54.17% | 43.75% |
| dataset_a_val | pothole | 3 | 251 | 170 | 32 | 456 | 0.66% | 55.04% | 37.28% | 7.02% |
| dataset_a_test | longitudinal_crack | 0 | 24 | 41 | 1 | 66 | 0.00% | 36.36% | 62.12% | 1.52% |
| dataset_a_test | transverse_crack | 0 | 2 | 3 | 0 | 5 | 0.00% | 40.00% | 60.00% | 0.00% |
| dataset_a_test | alligator_crack | 0 | 1 | 51 | 44 | 96 | 0.00% | 1.04% | 53.12% | 45.83% |
| dataset_a_test | pothole | 4 | 265 | 199 | 44 | 512 | 0.78% | 51.76% | 38.87% | 8.59% |
| dataset_b_train | longitudinal_crack | 1754 | 5453 | 7325 | 674 | 15206 | 11.53% | 35.86% | 48.17% | 4.43% |
| dataset_b_train | transverse_crack | 245 | 3234 | 3589 | 224 | 7292 | 3.36% | 44.35% | 49.22% | 3.07% |
| dataset_b_train | alligator_crack | 27 | 392 | 2913 | 2484 | 5816 | 0.46% | 6.74% | 50.09% | 42.71% |
| dataset_b_train | pothole | 257 | 3089 | 3107 | 1591 | 8044 | 3.19% | 38.40% | 38.63% | 19.78% |
| dataset_b_val | longitudinal_crack | 181 | 631 | 879 | 67 | 1758 | 10.30% | 35.89% | 50.00% | 3.81% |
| dataset_b_val | transverse_crack | 47 | 375 | 470 | 26 | 918 | 5.12% | 40.85% | 51.20% | 2.83% |
| dataset_b_val | alligator_crack | 2 | 45 | 351 | 266 | 664 | 0.30% | 6.78% | 52.86% | 40.06% |
| dataset_b_val | pothole | 31 | 220 | 262 | 184 | 697 | 4.45% | 31.56% | 37.59% | 26.40% |

## Image Dimensions

| Subset | Most Common Dimensions | Count |
|--------|------------------------|-------|
| dataset_a_train | 720x720 (1071) | 1 unique |
| dataset_a_val | 720x720 (229) | 1 unique |
| dataset_a_test | 720x720 (230) | 1 unique |
| dataset_b_train | 600x600 (8101), 640x640 (2980), 512x512 (2518), 4040x2035 (2514), 3643x2041 (1771) | 10 unique |
| dataset_b_val | 600x600 (998), 640x640 (368), 4040x2035 (309), 512x512 (307), 3643x2041 (217) | 9 unique |

## Key Observations

### dataset_a_train
- **Total objects:** 3049
- **Images with valid annotations:** 1071
- **Missing image files:** 0
- **Relative area range:** 0.000586 – 0.668148
- **Mean relative area:** 0.035473
- **longitudinal_crack:** very_small=0.00%, small=32.02%, medium=64.33%, large=3.65%
- **transverse_crack:** very_small=0.00%, small=23.81%, medium=76.19%, large=0.00%
- **alligator_crack:** very_small=0.00%, small=3.53%, medium=54.08%, large=42.38%
- **pothole:** very_small=1.13%, small=53.13%, medium=41.28%, large=4.46%

### dataset_a_val
- **Total objects:** 632
- **Images with valid annotations:** 229
- **Missing image files:** 0
- **Relative area range:** 0.000772 – 0.460621
- **Mean relative area:** 0.035778
- **longitudinal_crack:** very_small=0.00%, small=38.16%, medium=61.84%, large=0.00%
- **transverse_crack:** very_small=0.00%, small=25.00%, medium=75.00%, large=0.00%
- **alligator_crack:** very_small=0.00%, small=2.08%, medium=54.17%, large=43.75%
- **pothole:** very_small=0.66%, small=55.04%, medium=37.28%, large=7.02%

### dataset_a_test
- **Total objects:** 679
- **Images with valid annotations:** 230
- **Missing image files:** 0
- **Relative area range:** 0.000656 – 0.345477
- **Mean relative area:** 0.037696
- **longitudinal_crack:** very_small=0.00%, small=36.36%, medium=62.12%, large=1.52%
- **transverse_crack:** very_small=0.00%, small=40.00%, medium=60.00%, large=0.00%
- **alligator_crack:** very_small=0.00%, small=1.04%, medium=53.12%, large=45.83%
- **pothole:** very_small=0.78%, small=51.76%, medium=38.87%, large=8.59%

### dataset_b_train
- **Total objects:** 36358
- **Images with valid annotations:** 19719
- **Missing image files:** 0
- **Relative area range:** 0.000003 – 0.923319
- **Mean relative area:** 0.046923
- **longitudinal_crack:** very_small=11.53%, small=35.86%, medium=48.17%, large=4.43%
- **transverse_crack:** very_small=3.36%, small=44.35%, medium=49.22%, large=3.07%
- **alligator_crack:** very_small=0.46%, small=6.74%, medium=50.09%, large=42.71%
- **pothole:** very_small=3.19%, small=38.40%, medium=38.63%, large=19.78%

### dataset_b_val
- **Total objects:** 4037
- **Images with valid annotations:** 2301
- **Missing image files:** 0
- **Relative area range:** 0.000037 – 0.830406
- **Mean relative area:** 0.048085
- **longitudinal_crack:** very_small=10.30%, small=35.89%, medium=50.00%, large=3.81%
- **transverse_crack:** very_small=5.12%, small=40.85%, medium=51.20%, large=2.83%
- **alligator_crack:** very_small=0.30%, small=6.78%, medium=52.86%, large=40.06%
- **pothole:** very_small=4.45%, small=31.56%, medium=37.59%, large=26.40%
