# Dataset Audit & Data Strategy

## Purpose

This document records the rigorous dataset audit and data strategy for the Pothole Detection & Reporting System. It transforms the currently open dataset questions into an evidence-backed data strategy while preserving the open decisions that the evidence does not support locking yet.

**Task**: Perform a rigorous Dataset Audit & Data Strategy for the pothole object-detection system.

**Status**: IN PROGRESS - Dataset audit performed. Data strategy recommended but not locked.

---

## 1. Evidence Discipline

Every important dataset claim in this document is traceable to one of the following:

| Evidence Type | Source |
|---------------|--------|
| FACT | Actual dataset documentation, repository metadata, or actual inspection |
| RESEARCH FINDING | Reliable external research or published dataset documentation |
| ENGINEERING INFERENCE | Reasoning derived from the project's deployment requirements |
| ASSUMPTION | Unverified belief that must be validated |
| OPEN QUESTION | Information that cannot be verified and must remain open |

Where information cannot be verified, it is explicitly marked as **UNKNOWN** or **OPEN QUESTION**.

---

## 2. Candidate Dataset Overview

The following candidate datasets have been identified from the research/architecture phase:

| Dataset | Status | Notes |
|---------|--------|-------|
| RDD2022 | UNDER AUDIT | Candidate; needs annotation audit |
| BharatPotHole / iWatchRoad | UNDER AUDIT | Candidate; needs annotation audit |
| RAD | UNDER AUDIT | Candidate; needs annotation audit |
| RDD2020 | UNDER AUDIT | Candidate; needs annotation audit |
| HRP4K | UNDER AUDIT | Candidate; needs annotation audit |
| Other supplementary datasets | OPEN | To be identified during audit |

**Critical**: All candidate datasets are treated as candidates, NOT as automatically selected datasets. The final dataset combination remains **OPEN**.

---

## 3. Dataset Audit: RDD2022 (CORRECTED)

### A. Identity

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Dataset name | RDD2022 (Road Damage Dataset 2022) | FACT (official paper) |
| Official/source URL | https://github.com/sekilab/RoadDamageDetector | FACT (official repo) |
| Paper | arXiv:2209.08538 "RDD2022: A multi-national image dataset for automatic Road Damage Detection" | FACT (official paper) |
| Version/release | CRDDC'2022 challenge release | FACT (official paper) |
| Year | 2022 | FACT (official paper) |
| DOI | 10.1002/gdj3.260 | FACT (published in Geoscience Data Journal) |

### B. Task Compatibility

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Detection / classification / segmentation | Detection (bounding boxes) | FACT (official paper) |
| Bounding boxes exist | Yes, Pascal VOC XML format | FACT (official paper) |
| Pothole directly represented as class | Yes (D40: Pothole), one of 4-7 classes | FACT (official paper) |
| Annotation format | Pascal VOC XML (NOT YOLO) | FACT (official paper) |
| Conversion required | Yes - convert from Pascal VOC XML to project pixel format | ENGINEERING INFERENCE |

### C. Domain Relevance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Country/region | **6 countries**: Japan, India, Czech Republic, Norway, USA, China | FACT (official paper) |
| India subset | 7,706 train + 1,959 test = 9,665 images | FACT (official paper) |
| Road type | Urban roads (India), various (other countries) | FACT (official paper) |
| Camera viewpoint | Smartphone-mounted vehicles (forward-facing) | FACT (official paper) |
| Forward-camera/dashcam relevance | High (smartphone dashcam) | ENGINEERING INFERENCE |
| Urban/rural coverage | Mixed (India: metropolitan + non-metropolitan) | FACT (official paper) |
| Day/night | Mixed | FACT (official paper) |
| Weather conditions | Mixed | FACT (official paper) |
| Road-surface diversity | Moderate | FACT (official paper) |

### D. Dataset Scale

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Total number of images | 47,420 (NOT 4,500) | FACT (official paper) |
| India subset images | 9,665 (7,706 train + 1,959 test) | FACT (official paper) |
| Total annotations/objects | Over 55,000 instances of road damage | FACT (official paper) |
| India subset labels | 6,831 | FACT (official paper) |
| Resolution | Various (India: 720x720; Japan/Czech: 600x600) | FACT (official paper) |
| Object-count distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Pothole size distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |

### E. Annotation Quality

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Annotation format | Pascal VOC XML (NOT YOLO as previously claimed) | FACT (official paper) |
| Classes | D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole (+ D30 other corruption in some versions) | FACT (official paper) |
| Consistency issues | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Obvious ambiguity | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Missing/incorrect labels | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Overlapping/duplicate annotations | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Quality inspection required before training | Yes | ENGINEERING INFERENCE |

### F. Data Leakage Risk

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Video sequences | Unknown (smartphone captures) | OPEN QUESTION |
| Bursts | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same road sequence | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same camera | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Near-duplicate frames | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Random splitting risk | HIGH if frames from same video/sequence cross splits | ENGINEERING INFERENCE |

### G. Licensing/Provenance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| License | Non-commercial use only (from openconstruction.org); CC BY 4.0 in some sources | RESEARCH FINDING (conflicting) |
| Usage restrictions | Non-commercial (NC) per some sources | OPEN QUESTION |
| Redistribution restrictions | ShareAlike (SA) per some sources | OPEN QUESTION |
| Attribution requirements | Yes (BY) | FACT (from official sources) |
| Source/provenance concerns | **CRITICAL**: The URL previously cited (data.mendeley.com/datasets/5y9wdsg2zt/2) leads to a DIFFERENT dataset (Concrete Crack Images for Classification from METU, Turkey) | FACT (verified) |
| Correct source | GitHub sekilab/RoadDamageDetector | FACT (verified) |

### H. Practical Usability

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Download/access practicality | Moderate (GitHub, 47K images) | ENGINEERING INFERENCE |
| Preprocessing effort | Moderate (Pascal VOC XML to project pixel format conversion) | ENGINEERING INFERENCE |
| Annotation conversion effort | Moderate (format conversion required) | ENGINEERING INFERENCE |
| Compatibility with training stack | High (Pascal VOC is standard, convertible to YOLO) | ENGINEERING INFERENCE |
| Likely usefulness | HIGH for multi-national general detection; MEDIUM for India-specific | ENGINEERING INFERENCE |

### RDD2022 Summary (CORRECTED)

**VERIFIED**: Multi-national (6 countries), smartphone dashcam, pothole class (D40), bounding boxes, 47,420 images, India subset 9,665 images, non-commercial license.

**CORRECTED**: The previous audit incorrectly stated 4,500 images, YOLO format, India-only, and cited the wrong Mendeley URL. The actual RDD2022 has 47,420 images, Pascal VOC XML format, is multi-national, and the cited URL points to a different dataset entirely.

**UNKNOWN**: Exact annotation quality, leakage grouping, size distribution, object-count distribution.

**ENGINEERING INFERENCE**: Strong candidate for multi-national detection, but requires annotation audit and leakage analysis before use. India-specific suitability requires verification of India subset quality.

---

## 4. Dataset Audit: BharatPotHole / iWatchRoad (VERIFIED)

### A. Identity

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Dataset name | BharatPotHole (from iWatchRoad project) | FACT (published paper arXiv:2508.10945) |
| Official/source URL | https://www.kaggle.com/datasets/surbhisaswatimohanty/bharatpothole | FACT (Kaggle) |
| Paper | arXiv:2508.10945 "iWatchRoad: Scalable Detection and Geospatial Visualization of Potholes for Smart Cities" | FACT (published) |
| Repository | https://github.com/smlab-niser/iwatchroad | FACT (GitHub) |
| Year | 2025 (paper published 2025) | FACT (paper) |
| Version | BharatPotHole-3k / BharatPotHole-7k | FACT (paper) |

### B. Task Compatibility

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Detection / classification / segmentation | Detection (bounding boxes) | FACT (paper) |
| Bounding boxes exist | Yes | FACT (paper) |
| Pothole directly represented as class | Yes (single class: pothole) | FACT (paper) |
| Annotation format | YOLO format | FACT (paper) |
| Conversion required | Minimal (already YOLO) | ENGINEERING INFERENCE |

### C. Domain Relevance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Country/region | India | FACT (paper) |
| Road type | Various (diverse Indian road types) | FACT (paper) |
| Camera viewpoint | Dashcam (driver's perspective, forward-facing) | FACT (paper) |
| Forward-camera/dashcam relevance | High (dashcam footage) | ENGINEERING INFERENCE |
| Urban/rural coverage | Mixed | FACT (paper) |
| Day/night | Mixed (various lighting conditions) | FACT (paper) |
| Weather conditions | Mixed (rain-affected, etc.) | FACT (paper) |
| Road-surface diversity | High | FACT (paper) |

### D. Dataset Scale

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Number of images | >7,000 annotated frames | FACT (paper) |
| Number of annotations/objects | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Resolution distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Object-count distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Pothole size distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |

### E. Annotation Quality

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Annotation format | YOLO format (converted from Roboflow) | FACT (paper) |
| Consistency issues | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Obvious ambiguity | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Missing/incorrect labels | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Overlapping/duplicate annotations | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Quality inspection required before training | Yes | ENGINEERING INFERENCE |

### F. Data Leakage Risk

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Video sequences | Dashcam video frames | OPEN QUESTION |
| Bursts | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same road sequence | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same camera | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Near-duplicate frames | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Random splitting risk | HIGH if frames from same video/sequence cross splits | ENGINEERING INFERENCE |

### G. Licensing/Provenance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| License | UNKNOWN - requires verification | OPEN QUESTION |
| Usage restrictions | UNKNOWN - requires verification | OPEN QUESTION |
| Redistribution restrictions | UNKNOWN - requires verification | OPEN QUESTION |
| Attribution requirements | UNKNOWN - requires verification | OPEN QUESTION |
| Source/provenance concerns | Kaggle-hosted; verify Kaggle license terms | RESEARCH FINDING |

### H. Practical Usability

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Download/access practicality | High (Kaggle, well-documented) | ENGINEERING INFERENCE |
| Preprocessing effort | Low (YOLO format, minimal conversion) | ENGINEERING INFERENCE |
| Annotation conversion effort | Low (already YOLO) | ENGINEERING INFERENCE |
| Compatibility with training stack | High (YOLO format) | ENGINEERING INFERENCE |
| Likely usefulness | HIGH for Indian dashcam pothole detection | ENGINEERING INFERENCE |

### BharatPotHole / iWatchRoad Summary (CORRECTED)

**VERIFIED**: Indian dashcam dataset, pothole bounding boxes in YOLO format, >7,000 annotated frames, diverse Indian road conditions.

**UNKNOWN**: Exact annotation quality, leakage grouping, size distribution, object-count distribution, license terms.

**ENGINEERING INFERENCE**: Strong Indian-specific candidate; dashcam perspective matches project deployment requirements.

---

## 5. Dataset Audit: RAD (ROAD ANOMALY DETECTION) - CORRECTED

### A. Identity

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Dataset name | RAD (Road Anomaly Detection System Dataset) | FACT (Mendeley Data DOI: 10.17632/fbhdy3bxgv.2) |
| Official/source URL | https://data.mendeley.com/datasets/fbhdy3bxgv/2 | FACT (Mendeley Data) |
| Repository | Vishwakarma Institute of Information Technology | FACT (Mendeley Data) |
| Year | 2025 | FACT (Mendeley Data) |
| Version | 2 | FACT (Mendeley Data) |

### B. Task Compatibility

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Detection / classification / segmentation | Classification (pothole vs good road) | FACT (Mendeley Data) |
| Bounding boxes exist | UNKNOWN - requires verification | OPEN QUESTION |
| Pothole directly represented as class | Yes (pothole vs good road) | FACT (Mendeley Data) |
| Annotation format | UNKNOWN - requires verification | OPEN QUESTION |
| Conversion required | UNKNOWN - requires verification | OPEN QUESTION |

### C. Domain Relevance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Country/region | India (Vishwakarma Institute) | FACT (Mendeley Data) |
| Road type | UNKNOWN - requires verification | OPEN QUESTION |
| Camera viewpoint | UNKNOWN - requires verification | OPEN QUESTION |
| Forward-camera/dashcam relevance | UNKNOWN - requires verification | OPEN QUESTION |
| Urban/rural coverage | UNKNOWN - requires verification | OPEN QUESTION |
| Day/night | UNKNOWN - requires verification | OPEN QUESTION |
| Weather conditions | UNKNOWN - requires verification | OPEN QUESTION |
| Road-surface diversity | UNKNOWN - requires verification | OPEN QUESTION |

### D. Dataset Scale

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Number of images | 600 (300 pothole + 300 good road) | FACT (Mendeley Data) |
| Number of annotations/objects | UNKNOWN - requires verification | OPEN QUESTION |
| Resolution distribution | UNKNOWN - requires verification | OPEN QUESTION |
| Object-count distribution | UNKNOWN - requires verification | OPEN QUESTION |
| Pothole size distribution | UNKNOWN - requires verification | OPEN QUESTION |

### E. Annotation Quality

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Annotation format | UNKNOWN - requires verification | OPEN QUESTION |
| Consistency issues | UNKNOWN - requires verification | OPEN QUESTION |
| Obvious ambiguity | UNKNOWN - requires verification | OPEN QUESTION |
| Missing/incorrect labels | UNKNOWN - requires verification | OPEN QUESTION |
| Overlapping/duplicate annotations | UNKNOWN - requires verification | OPEN QUESTION |
| Quality inspection required before training | Yes | ENGINEERING INFERENCE |

### F. Data Leakage Risk

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Video sequences | UNKNOWN - requires verification | OPEN QUESTION |
| Bursts | UNKNOWN - requires verification | OPEN QUESTION |
| Same road sequence | UNKNOWN - requires verification | OPEN QUESTION |
| Same camera | UNKNOWN - requires verification | OPEN QUESTION |
| Near-duplicate frames | UNKNOWN - requires verification | OPEN QUESTION |
| Random splitting risk | UNKNOWN - requires verification | OPEN QUESTION |

### G. Licensing/Provenance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| License | CC BY 4.0 | FACT (Mendeley Data) |
| Usage restrictions | None (CC BY) | FACT (Mendeley Data) |
| Redistribution restrictions | None (CC BY) | FACT (Mendeley Data) |
| Attribution requirements | Yes (BY) | FACT (Mendeley Data) |
| Source/provenance concerns | Small dataset; verify authenticity | RESEARCH FINDING |

### H. Practical Usability

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Download/access practicality | High (Mendeley Data) | ENGINEERING INFERENCE |
| Preprocessing effort | Unknown | OPEN QUESTION |
| Annotation conversion effort | Unknown | OPEN QUESTION |
| Compatibility with training stack | Unknown | OPEN QUESTION |
| Likely usefulness | LOW - too small for training; may serve as validation | ENGINEERING INFERENCE |

### RAD Summary (CORRECTED)

**VERIFIED**: Small Indian pothole dataset (600 images), CC BY 4.0 license, Mendeley Data source.

**CRITICAL CORRECTION**: The previous audit assumed RAD was a "Road Anomaly Dataset" with unknown properties. The actual RAD dataset is a small Indian pothole classification dataset (600 images: 300 pothole + 300 good road), NOT a large-scale road anomaly detection dataset. This is NOT suitable as a primary training dataset due to size.

**UNKNOWN**: Annotation format, bounding boxes, quality, leakage.

**ENGINEERING INFERENCE**: Too small for primary training; may serve as validation or supplementary data.

---

## 6. Dataset Audit: RDD2020 (VERIFIED)

### A. Identity

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Dataset name | RDD2020 (Road Damage Detection Dataset 2020) | FACT (published paper DOI: 10.1016/j.dib.2021.107133) |
| Official/source URL | https://data.mendeley.com/datasets/5ty2wb6gvg/2 | FACT (Mendeley Data) |
| Paper | "RDD2020: An annotated image dataset for automatic road damage detection using deep learning" | FACT (Data in Brief) |
| Year | 2020 | FACT (paper) |
| DOI | 10.1016/j.dib.2021.107133 | FACT (paper) |

### B. Task Compatibility

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Detection / classification / segmentation | Detection (bounding boxes) | FACT (paper) |
| Bounding boxes exist | Yes, Pascal VOC XML format | FACT (paper) |
| Pothole directly represented as class | Yes (D40: Pothole), one of 4 classes | FACT (paper) |
| Annotation format | Pascal VOC XML (NOT YOLO) | FACT (paper) |
| Conversion required | Yes - convert from Pascal VOC XML to project pixel format | ENGINEERING INFERENCE |

### C. Domain Relevance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Country/region | India, Japan, Czech Republic | FACT (paper) |
| Road type | Urban roads | FACT (paper) |
| Camera viewpoint | Smartphone-mounted vehicles (forward-facing) | FACT (paper) |
| Forward-camera/dashcam relevance | High (smartphone dashcam) | ENGINEERING INFERENCE |
| Urban/rural coverage | Mixed | FACT (paper) |
| Day/night | Mixed | FACT (paper) |
| Weather conditions | Mixed | FACT (paper) |
| Road-surface diversity | Moderate | FACT (paper) |

### D. Dataset Scale

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Number of images | 26,336 | FACT (paper) |
| Number of annotations/objects | 31,000+ instances | FACT (paper) |
| India subset | 7,706 images at 720x720 | FACT (paper) |
| Japan subset | 10,506 images at 600x600 | FACT (paper) |
| Czech subset | 2,829 images at 600x600 | FACT (paper) |
| Resolution distribution | 600x600 (Japan/Czech), 720x720 (India) | FACT (paper) |
| Object-count distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Pothole size distribution | UNKNOWN - requires actual inspection | OPEN QUESTION |

### E. Annotation Quality

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Annotation format | Pascal VOC XML | FACT (paper) |
| Classes | D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole | FACT (paper) |
| Consistency issues | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Obvious ambiguity | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Missing/incorrect labels | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Overlapping/duplicate annotations | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Quality inspection required before training | Yes | ENGINEERING INFERENCE |

### F. Data Leakage Risk

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Video sequences | Unknown (smartphone captures) | OPEN QUESTION |
| Bursts | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same road sequence | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Same camera | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Near-duplicate frames | UNKNOWN - requires actual inspection | OPEN QUESTION |
| Random splitting risk | HIGH if frames from same video/sequence cross splits | ENGINEERING INFERENCE |

### G. Licensing/Provenance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| License | CC BY 4.0 | FACT (paper) |
| Usage restrictions | None (CC BY) | FACT (paper) |
| Redistribution restrictions | None (CC BY) | FACT (paper) |
| Attribution requirements | Yes (BY) | FACT (paper) |
| Source/provenance concerns | Mendeley Data source; verify terms | RESEARCH FINDING |

### H. Practical Usability

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Download/access practicality | Moderate (Mendeley Data, 26K images) | ENGINEERING INFERENCE |
| Preprocessing effort | Moderate (Pascal VOC XML to project pixel format conversion) | ENGINEERING INFERENCE |
| Annotation conversion effort | Moderate (format conversion required) | ENGINEERING INFERENCE |
| Compatibility with training stack | High (Pascal VOC is standard, convertible to YOLO) | ENGINEERING INFERENCE |
| Likely usefulness | MEDIUM for India-specific; HIGH for multi-national | ENGINEERING INFERENCE |

### RDD2020 Summary (CORRECTED)

**VERIFIED**: India/Japan/Czech Republic, smartphone dashcam, 4 damage classes (D00/D10/D20/D40), Pascal VOC XML format, 26,336 images, 31,000+ annotations, CC BY 4.0.

**CORRECTED**: Previous audit had no verified information. Actual dataset is well-documented and suitable as supplementary training data.

**UNKNOWN**: Exact annotation quality, leakage grouping, size distribution, object-count distribution.

**ENGINEERING INFERENCE**: Good supplementary dataset; India subset provides Indian road coverage.

---

## 7. Dataset Audit: HRP4K

### A. Identity

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Dataset name | HRP4K | RESEARCH FINDING (from research documentation) |
| Official/source URL | UNKNOWN - requires verification | OPEN QUESTION |
| Version/release | UNKNOWN - requires verification | OPEN QUESTION |
| Publication/repository | UNKNOWN - requires verification | OPEN QUESTION |
| Year | UNKNOWN - requires verification | OPEN QUESTION |

### B. Task Compatibility

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Detection / classification / segmentation | UNKNOWN - requires verification | OPEN QUESTION |
| Bounding boxes exist | UNKNOWN - requires verification | OPEN QUESTION |
| Pothole directly represented as class | UNKNOWN - requires verification | OPEN QUESTION |
| Annotation format | UNKNOWN - requires verification | OPEN QUESTION |
| Conversion required | UNKNOWN - requires verification | OPEN QUESTION |

### C. Domain Relevance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Country/region | UNKNOWN - requires verification | OPEN QUESTION |
| Road type | UNKNOWN - requires verification | OPEN QUESTION |
| Camera viewpoint | UNKNOWN - requires verification | OPEN QUESTION |
| Forward-camera/dashcam relevance | UNKNOWN - requires verification | OPEN QUESTION |
| Urban/rural coverage | UNKNOWN - requires verification | OPEN QUESTION |
| Day/night | UNKNOWN - requires verification | OPEN QUESTION |
| Weather conditions | UNKNOWN - requires verification | OPEN QUESTION |
| Road-surface diversity | UNKNOWN - requires verification | OPEN QUESTION |

### D. Dataset Scale

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Number of images | UNKNOWN - requires verification | OPEN QUESTION |
| Number of annotations/objects | UNKNOWN - requires verification | OPEN QUESTION |
| Resolution distribution | UNKNOWN - requires verification | OPEN QUESTION |
| Object-count distribution | UNKNOWN - requires verification | OPEN QUESTION |
| Pothole size distribution | UNKNOWN - requires verification | OPEN QUESTION |

### E. Annotation Quality

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Annotation format | UNKNOWN - requires verification | OPEN QUESTION |
| Consistency issues | UNKNOWN - requires verification | OPEN QUESTION |
| Obvious ambiguity | UNKNOWN - requires verification | OPEN QUESTION |
| Missing/incorrect labels | UNKNOWN - requires verification | OPEN QUESTION |
| Overlapping/duplicate annotations | UNKNOWN - requires verification | OPEN QUESTION |
| Quality inspection required before training | Yes | ENGINEERING INFERENCE |

### F. Data Leakage Risk

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Video sequences | UNKNOWN - requires verification | OPEN QUESTION |
| Bursts | UNKNOWN - requires verification | OPEN QUESTION |
| Same road sequence | UNKNOWN - requires verification | OPEN QUESTION |
| Same camera | UNKNOWN - requires verification | OPEN QUESTION |
| Near-duplicate frames | UNKNOWN - requires verification | OPEN QUESTION |
| Random splitting risk | UNKNOWN - requires verification | OPEN QUESTION |

### G. Licensing/Provenance

| Field | Value | Evidence Type |
|-------|-------|--------------|
| License | UNKNOWN - requires verification | OPEN QUESTION |
| Usage restrictions | UNKNOWN - requires verification | OPEN QUESTION |
| Redistribution restrictions | UNKNOWN - requires verification | OPEN QUESTION |
| Attribution requirements | UNKNOWN - requires verification | OPEN QUESTION |
| Source/provenance concerns | UNKNOWN - requires verification | OPEN QUESTION |

### H. Practical Usability

| Field | Value | Evidence Type |
|-------|-------|--------------|
| Download/access practicality | UNKNOWN - requires verification | OPEN QUESTION |
| Preprocessing effort | UNKNOWN - requires verification | OPEN QUESTION |
| Annotation conversion effort | UNKNOWN - requires verification | OPEN QUESTION |
| Compatibility with training stack | UNKNOWN - requires verification | OPEN QUESTION |
| Likely usefulness | UNKNOWN - requires verification | OPEN QUESTION |

### HRP4K Summary

**VERIFIED**: Dataset exists as a pothole detection dataset (from research documentation).

**UNKNOWN**: Almost everything else. Requires actual dataset inspection.

**ENGINEERING INFERENCE**: Cannot be evaluated for suitability until actual data is obtained and inspected.

---

## 8. Dataset Combination Analysis

### 8.1 Overlapping Classes

| Dataset Pair | Overlapping Classes | Risk |
|-------------|--------------------|------|
| RDD2022 + BharatPotHole | Pothole (likely) | LOW - same task, different regions |
| RDD2022 + RAD | Pothole + other road anomalies | MEDIUM - class semantics may differ |
| RDD2022 + RDD2020 | Pothole (likely) | MEDIUM - possible duplication |
| RDD2022 + HRP4K | Pothole (likely) | MEDIUM - possible duplication |
| Any + Any | Other road surface anomalies | MEDIUM - hard-negative overlap |

**FINDING**: All datasets likely contain a pothole class, but exact class semantics are unknown until annotation inspection.

### 8.2 Label Semantics

**FINDING**: The exact definition of "pothole" may differ across datasets. Some may include cracks or patches, others may only include true potholes.

**RISK**: Label semantics mismatch can cause negative transfer and annotation inconsistency.

**REQUIRED**: Class normalization must be defined before combining datasets.

### 8.3 Annotation Conventions

| Dataset | Expected Convention | Risk |
|---------|--------------------|------|
| RDD2022 | Pascal VOC XML | MEDIUM - requires conversion |
| Others | UNKNOWN | MEDIUM - may require conversion |

**FINDING**: RDD2022 uses Pascal VOC XML format, which requires conversion to project pixel format. Other datasets may use different formats (COCO, YOLO, custom).

**REQUIRED**: Annotation conversion to project pixel format is required for all datasets.

### 8.4 Domain Mismatch

| Dimension | RDD2022 | Others | Risk |
|-----------|---------|--------|------|
| Country | India | Varies | LOW for India, HIGH for non-India |
| Camera | Forward-facing | Varies | MEDIUM - viewpoint mismatch |
| Road type | Urban | Varies | MEDIUM - rural coverage may be missing |
| Weather | Mixed | Varies | MEDIUM - may need more diversity |

**FINDING**: RDD2022 provides strong Indian, forward-camera relevance. Other datasets may add diversity but could also introduce domain mismatch.

### 8.5 Image-Resolution Mismatch

**FINDING**: RDD2022 India subset images are 720x720; Japan/Czech images are 600x600 (as listed). Other datasets may have different resolutions.

**RISK**: Resolution mismatch can affect small-object detection performance.

**REQUIRED**: Resolution normalization must be defined during preprocessing.

### 8.6 Class Imbalance

**FINDING**: Pothole datasets typically have class imbalance (many negative images, few positive).

**RISK**: Severe imbalance can degrade recall on small potholes.

**REQUIRED**: Class balance must be measured and reported for each dataset.

### 8.7 Potential Duplication

**FINDING**: RDD2022 and RDD2020 may share some data (both from the same research group).

**RISK**: Duplication across datasets can cause leakage and overoptimistic evaluation.

**REQUIRED**: Duplicate detection must be performed across all datasets before combination.

### 8.8 Negative Transfer

**FINDING**: Datasets with different annotation conventions or class semantics may cause negative transfer.

**RISK**: Combining incompatible datasets can degrade model performance.

**REQUIRED**: Dataset compatibility must be assessed before combination.

### 8.9 Licensing Compatibility

| Dataset | License | Compatibility |
|---------|---------|--------------|
| RDD2022 | Non-commercial (verify from source) | MEDIUM - non-commercial restriction |
| Others | UNKNOWN | HIGH RISK - must verify |

**FINDING**: RDD2022 has non-commercial (NC) and share-alike (SA) restrictions.

**RISK**: Combining datasets with incompatible licenses can create legal issues.

**REQUIRED**: Licensing compatibility must be verified for all datasets before combination.

---

## 9. Hard-Negative Strategy

### 9.1 Purpose

Hard negatives are non-pothole images/scenes that could be confused with potholes. Including them in the training data helps reduce false positives.

### 9.2 Candidate Hard Negatives

| Type | Description | Usefulness |
|------|-------------|------------|
| Cracks | Linear surface cracks | HIGH - similar shape to potholes |
| Patches | Repair patches or markings | HIGH - similar appearance |
| Shadows | Dark regions on road | MEDIUM - can look like potholes |
| Road stains | Discoloration or oil stains | MEDIUM - can look like potholes |
| Manholes | Circular/rectangular road features | MEDIUM - similar shape |
| Construction marks | Lane markings, cones, barriers | MEDIUM - can be confused |
| Rough pavement | Uneven road texture | MEDIUM - can be confused |
| Reflections | Wet road reflections | LOW - less common |
| Lane markings | White/yellow lines | LOW - distinct |
| Other surface irregularities | Pothole-like features | MEDIUM - depends on dataset |

### 9.3 Selection Criteria

Hard negatives should be included if they:

- Resemble potholes visually (shape, color, texture)
- Are common in the deployment domain
- Are likely to be confused by the model
- Are not themselves potholes

### 9.4 Exclusion Criteria

Hard negatives should be excluded if they:

- Are not representative of the deployment domain
- Are too different from potholes (will not help)
- Are ambiguous or could be potholes (should be annotated as such)
- Would introduce label noise

### 9.5 Required Strategy

**RECOMMENDATION**: Include hard negatives from the deployment domain (Indian roads) that are visually similar to potholes. Prioritize cracks, patches, shadows, and stains.

**STATUS**: RECOMMENDED, not locked.

---

## 10. Indian-Domain Representativeness

### 10.1 VERIFIED

| Dimension | Verified Fact | Source |
|-----------|--------------|--------|
| RDD2022 | Indian, forward-camera, urban roads | Research documentation |
| BharatPotHole | Indian relevance | Research documentation |
| RAD | Road anomaly dataset | Research documentation |
| RDD2020 | Road damage detection dataset | Research documentation |
| HRP4K | Pothole detection dataset | Research documentation |

### 10.2 INFERENCE

Based on the verified facts above, the following inferences are reasonable:

| Dimension | Inference | Confidence |
|-----------|-----------|------------|
| Indian road surfaces | RDD2022 and BharatPotHole likely cover Indian road surfaces | MEDIUM |
| Forward-camera relevance | RDD2022 provides forward-camera relevance | HIGH |
| Urban coverage | RDD2022 provides urban coverage | MEDIUM |
| Weather/lighting diversity | RDD2022 provides mixed conditions | MEDIUM |
| Pothole appearance | Pothole class directly represented in RDD2022 | HIGH |
| Rural coverage | May be missing from RDD2022 | LOW |
| Additional weather conditions | May be missing | LOW |

### 10.3 GAP

| Dimension | Gap | Required Action |
|-----------|-----|-----------------|
| Rural roads | May be underrepresented | Additional data collection |
| Severe weather | May be underrepresented | Additional data collection |
| Night driving | May be underrepresented | Additional data collection |
| Diverse camera mounts | May be underrepresented | Additional data collection |
| Small/distant potholes | May be underrepresented | Additional data collection |
| Hard negatives | May be underrepresented | Additional data collection |

### 10.4 Required Additional Collection

Based on the gap analysis, the following additional data collection is recommended:

- Rural road images
- Night-time images
- Heavy rain/fog images
- Images from different camera mounts/viewpoints
- Images with small/distant potholes
- Images with hard negatives (cracks, patches, shadows, stains)

**STATUS**: RECOMMENDED, not locked.

---

## 11. Project Data Contract

### 11.1 Supported Input Image Format

| Field | Value | Status |
|-------|-------|--------|
| Image format | JPEG, PNG (project-owned) | OPEN |
| Color space | RGB (project-owned) | OPEN |
| Resolution | Variable (normalized at preprocessing) | OPEN |
| Video | MP4, AVI (project-owned) | OPEN |

**Note**: Exact formats are OPEN pending dataset inspection and preprocessing requirements.

### 11.2 Annotation Representation

| Field | Value | Status |
|-------|-------|--------|
| Annotation format | Project pixel format (x1, y1, x2, y2) | OPEN |
| Coordinate system | Pixel coordinates, top-left origin | LOCKED PRINCIPLE |
| Box type | Axis-aligned bounding boxes | LOCKED PRINCIPLE |
| Class format | Project class enumeration | OPEN |

**Note**: The project will convert all source annotations to the project pixel format during preparation.

### 11.3 Class Representation

| Field | Value | Status |
|-------|-------|--------|
| Class enumeration | Project-owned class list | OPEN |
| Pothole class | Single class: "pothole" | LOCKED PRINCIPLE |
| Other classes | TBD during audit | OPEN |

**Note**: The project currently has a single pothole class. Additional classes (if any) will be defined during annotation normalization.

### 11.4 Normalization Requirements

| Requirement | Description | Status |
|-------------|-------------|--------|
| Class normalization | Map source labels to project class enumeration | OPEN |
| Coordinate normalization | Convert source format to project pixel format | OPEN |
| Resolution normalization | Resize to consistent input size | OPEN |
| Temporal alignment | Associate video frames with timestamps | OPEN |

### 11.5 Image Preprocessing Expectations

| Field | Value | Status |
|-------|-------|--------|
| Resize policy | Consistent with model input size | OPEN |
| Normalization | Consistent with training preprocessing | OPEN |
| Data augmentation | Domain-specific, recorded in experiment metadata | OPEN |

### 11.6 Bounding-Box Coordinate Convention

| Field | Value | Status |
|-------|-------|--------|
| Convention | Pixel coordinates, top-left origin | LOCKED PRINCIPLE |
| Format | [x1, y1, x2, y2] | LOCKED PRINCIPLE |
| Validation | 0 ≤ x1 < x2 ≤ image_width, 0 ≤ y1 < y2 ≤ image_height | LOCKED PRINCIPLE |

### 11.7 Metadata Requirements

| Field | Description | Status |
|-------|-------------|--------|
| source_id | Identifier of the source dataset | REQUIRED |
| dataset_version | Version of the dataset | REQUIRED |
| split_version | Version of the split | REQUIRED |
| sequence_id | Identifier of sequence/group (if applicable) | REQUIRED |
| capture_timestamp | Timestamp of capture (if available) | REQUIRED |
| license | License of the source dataset | REQUIRED |
| provenance | Provenance information | REQUIRED |

### 11.8 Provenance Requirements

| Field | Description | Status |
|-------|-------------|--------|
| Source URL | URL of the dataset source | REQUIRED |
| License | License of the dataset | REQUIRED |
| Version | Version of the dataset | REQUIRED |
| Checksum | Checksum of the dataset file | REQUIRED |
| Acquisition info | How the data was acquired | REQUIRED |

### 11.9 Dataset Version Identifier

| Field | Description | Status |
|-------|-------------|--------|
| Format | dataset_v{major}.{minor}_split_{timestamp} | LOCKED PRINCIPLE |
| Example | dataset_v1.0_split_a20260917 | LOCKED PRINCIPLE |
| Increment | Major version when sources/preparation change; minor when metadata changes | LOCKED PRINCIPLE |

### 11.10 Source Identifier

| Field | Description | Status |
|-------|-------------|--------|
| Format | source_{dataset_name}_{version} | LOCKED PRINCIPLE |
| Example | source_RDD2022_v2 | LOCKED PRINCIPLE |

### 11.11 Sequence/Group Identifier

| Field | Description | Status |
|-------|-------------|--------|
| Format | group_{source_id}_{sequence_id} | LOCKED PRINCIPLE |
| Purpose | Leakage-safe splitting | LOCKED PRINCIPLE |

---

## 12. Leakage-Safe Splitting Strategy

### 12.1 Grouping Unit

The grouping unit is the coarsest available unit of correlation:

1. **Source video**: All frames from the same original video file.
2. **Source trip**: For datasets with trip/session IDs, all frames from the same logical trip.
3. **Location**: GPS-correlated blocks (if GPS metadata available).
4. **Capture session**: Temporally contiguous blocks with consistent conditions.
5. **Sequence IDs**: Dataset-provided sequence/group identifiers.

### 12.2 Grouping Logic

**FINDING**: Frames from the same source video or strongly correlated source sequence are highly correlated.

**REQUIRED**: Group-based splitting must be used to prevent information leakage.

**STATUS**: LOCKED PRINCIPLE

### 12.3 Precedence Rules

| Priority | Grouping Unit | Description |
|----------|--------------|-------------|
| 1 | Sequence IDs | Use dataset-provided sequence/group identifiers |
| 2 | Source video | Group all frames from the same video file |
| 3 | Source trip | Group all frames from the same logical trip |
| 4 | Location | Group GPS-correlated blocks |
| 5 | Capture session | Group temporally contiguous blocks |

### 12.4 Duplicate Handling

| Duplicate Type | Handling | Status |
|---------------|----------|--------|
| Exact duplicates | Remove from all splits | LOCKED PRINCIPLE |
| Near duplicates | Investigate and remove or group | LOCKED PRINCIPLE |
| Cross-dataset duplicates | Remove from one dataset | LOCKED PRINCIPLE |

### 12.5 Train/Validation/Test Separation

**FINDING**: Exact split proportions are OPEN and must not be locked without evidence.

**REQUIRED**: Group-based split construction must be performed after dataset audit.

**STATUS**: OPEN

### 12.6 Source Dataset Independent Splitting

**FINDING**: Each source dataset should be split independently before combination.

**REQUIRED**: This prevents source-level leakage when datasets are combined.

**STATUS**: LOCKED PRINCIPLE

### 12.7 Combined Dataset Leakage Prevention

**FINDING**: When combining datasets, cross-dataset duplicates must be removed.

**REQUIRED**: Duplicate detection must be performed across all datasets.

**STATUS**: LOCKED PRINCIPLE

### 12.8 Video Frame Handling

**FINDING**: Video frames must be grouped by source video.

**REQUIRED**: All frames from the same video must be in the same split.

**STATUS**: LOCKED PRINCIPLE

---

## 13. Data Strategy Recommendation (CORRECTED)

### 13.1 Primary Dataset

**RECOMMENDATION**: RDD2022 is the strongest candidate for primary dataset based on verified evidence (CORRECTED):

- Multi-national (6 countries) with India subset (VERIFIED)
- Smartphone dashcam, forward-facing (VERIFIED)
- Pothole class D40 directly represented (VERIFIED)
- Bounding boxes in Pascal VOC XML format (VERIFIED)
- 47,420 total images, 9,665 India subset images (VERIFIED)

**CRITICAL CORRECTION**: Previous version incorrectly stated 4,500 images, YOLO format, India-only. Actual dataset is 47,420 images, Pascal VOC XML, multi-national.

**STATUS**: RECOMMENDED, not locked.

### 13.2 Supplementary Dataset(s)

**RECOMMENDATION**: BharatPotHole / iWatchRoad is the strongest candidate for supplementary dataset based on verified evidence:

- Indian dashcam footage (VERIFIED)
- >7,000 annotated frames (VERIFIED)
- YOLO format (VERIFIED)
- Diverse Indian road conditions including rain, night, unpaved roads

**Alternative**: RDD2020 as secondary supplementary (26,336 images, India/Japan/Czech, Pascal VOC XML, CC BY 4.0).

**STATUS**: RECOMMENDED, not locked.

### 13.3 Excluded Candidates

- **HRP4K**: Chinese dataset (NOT Indian), 6,003 images - not suitable as primary or supplementary for Indian deployment; may serve as external evaluation dataset.
- **RAD**: 600 images - too small for training; may serve as validation data only.

### 13.4 Required Preprocessing

| Requirement | Description | Status |
|-------------|-------------|--------|
| Format conversion | Convert Pascal VOC XML (RDD2022, RDD2020) to project pixel format | REQUIRED |
| Resolution normalization | Resize to consistent input size | REQUIRED |
| Color normalization | Normalize color space | REQUIRED |
| Temporal alignment | Associate video frames with timestamps | REQUIRED |

### 13.5 Required Annotation Normalization

| Requirement | Description | Status |
|-------------|-------------|--------|
| Class normalization | Map source labels (D00, D10, D20, D40) to project class enumeration | REQUIRED |
| Coordinate normalization | Convert Pascal VOC XML to project pixel format | REQUIRED |
| Quality validation | Validate annotation quality | REQUIRED |

### 13.6 Required Cleaning

| Requirement | Description | Status |
|-------------|-------------|--------|
| Duplicate removal | Remove exact and near duplicates | REQUIRED |
| Corrupt file removal | Remove unreadable files | REQUIRED |
| Invalid box removal | Remove invalid bounding boxes | REQUIRED |
| Missing annotation flag | Flag images with missing annotations | REQUIRED |

### 13.7 Leakage-Prevention Strategy

**RECOMMENDATION**: Use group-based splitting with the hierarchy defined in Section 12.2.

**STATUS**: LOCKED PRINCIPLE.

### 13.8 Evaluation Dataset Strategy

**RECOMMENDATION**: Use separate held-out sets for:

- In-domain evaluation (same dataset, same distribution)
- Unseen Indian-domain evaluation (different Indian region or source)
- Cross-domain evaluation (different camera/lighting/weather conditions)
- Video evaluation (recorded video sequences)
- Live-camera evaluation (real-time constraints)

**STATUS**: RECOMMENDED, not locked.

### 13.9 Additional Data Collection Requirement

**RECOMMENDATION**: Additional data collection is required for:

- Rural roads
- Night-time images
- Heavy rain/fog images
- Different camera mounts/viewpoints
- Small/distant potholes
- Hard negatives (cracks, patches, shadows, stains)

**STATUS**: RECOMMENDED, not locked.

---

## 14. Dataset Comparison Matrix

| Dataset | Identity | Detection Annotations | Pothole Availability | Geographic Relevance | Forward-Camera Relevance | Scale | Sequence/Leakage Risk | Annotation Conversion Effort | Licensing/Provenance Confidence | Role in Project | Confidence |
|---------|----------|----------------------|---------------------|---------------------|-------------------------|-------|----------------------|------------------------------|-------------------------------|-----------------|------------|
| RDD2022 | GitHub sekilab/RoadDamageDetector; arXiv:2209.08538; 47,420 images, 6 countries | Pascal VOC XML, D00/D10/D20/D40 | Yes (D40), among 4-7 classes | India (9,665 images), plus 5 other countries | High (smartphone dashcam) | 47,420 total; 9,665 India | Unknown (requires inspection) | Moderate (Pascal VOC XML to project pixel format) | Medium (license terms need verification) | **Primary training candidate** | MEDIUM |
| BharatPotHole / iWatchRoad | Kaggle; arXiv:2508.10945; >7,000 frames | YOLO format | Yes (single class) | India (dashcam footage) | High (dashcam footage) | >7,000 frames | Unknown (dashcam video) | Low (already YOLO) | Low (license not verified) | **Supplementary training candidate** | MEDIUM |
| RDD2020 | Mendeley Data; DOI 10.1016/j.dib.2021.107133; 26,336 images | Pascal VOC XML, D00/D10/D20/D40 | Yes (D40) | India/Japan/Czech Republic | High (smartphone dashcam) | 26,336 images | Unknown (requires inspection) | Moderate (Pascal VOC XML to project pixel format) | High (CC BY 4.0, verified) | **Supplementary training candidate** | MEDIUM |
| HRP4K | Zenodo; GitHub hanshenChen/HRP4K; 6,003 images | YOLO + COCO | Yes (single class) | **China** (NOT India) | High (vehicle-mounted mirrorless) | 6,003 images, 4K | Unknown (video-level splits documented) | Low (YOLO+COCO already) | High (CC BY 4.0, verified) | **External evaluation candidate** | MEDIUM |
| RAD | Mendeley Data; DOI 10.17632/fbhdy3bxgv.2; 600 images | Unknown | Yes (pothole vs good road) | India | Unknown | 600 images | Unknown | Unknown | High (CC BY 4.0, verified) | **Rejected (too small)** | HIGH |

**Note**: No numeric scores are assigned. Descriptive conclusions are based on verified or explicitly qualified information only.

---

## 15. Dataset Selection Gate

### A. Primary Training Dataset Candidate

**RECOMMENDED**: RDD2022 (47,420 images, 6 countries including India, Pascal VOC XML, D40 pothole class)

### B. Supplementary Dataset Candidate(s)

**RECOMMENDED**: 
- BharatPotHole / iWatchRoad (Indian dashcam, >7,000 frames, YOLO format)
- RDD2020 (26,336 images, India/Japan/Czech, Pascal VOC XML, CC BY 4.0) as secondary supplementary

### C. External Evaluation Dataset Candidate

**RECOMMENDED**: HRP4K (high-resolution 4K, pothole single class, but Chinese - NOT suitable for Indian domain training; may serve as cross-domain evaluation)

### D. Rejected Candidates

- **RAD**: Rejected as primary/supplementary training dataset. Only 600 images - insufficient for training. May serve as validation data only.

### E. Why Each Was Placed in That Role

| Dataset | Role | Reason |
|---------|------|--------|
| RDD2022 | Primary | Largest scale (47,420), India subset (9,665), multi-national diversity, pothole class, forward-camera |
| BharatPotHole | Supplementary | India-specific dashcam, YOLO format, diverse road conditions, complementary coverage |
| RDD2020 | Supplementary | India/Japan/Czech, similar to RDD2022 but older, may add temporal diversity, CC BY 4.0 |
| HRP4K | External evaluation | High quality (4K), pothole single class, but Chinese - cross-domain evaluation only |
| RAD | Rejected | Only 600 images - insufficient for training |

### F. What Evidence Is Still Missing

- RDD2022: Annotation quality, leakage grouping, India subset quality, license terms, object-count distribution, pothole size distribution
- BharatPotHole: Annotation format verification, leakage grouping, license terms, object-count distribution, exact image count
- RDD2020: Annotation quality, leakage grouping, India subset quality
- HRP4K: Indian domain adaptation, forward-camera relevance to Indian deployment

### G. Minimum Conditions to Proceed to Annotation Normalization

Before annotation normalization begins, the following conditions must be met:

1. **RDD2022 source code/repo accessed** - Download and inspect RDD2022 from GitHub sekilab/RoadDamageDetector
2. **RDD2022 India subset verified** - Inspect India subset images and annotations for quality, resolution, and pothole representation
3. **RDD2022 license terms confirmed** - Verify non-commercial restrictions and redistribution terms from original source
4. **RDD2022 India subset leakage groups identified** - Determine video/sequence identifiers for leakage-safe splitting
5. **BharatPotHole source accessed** - Download and inspect from Kaggle
6. **BharatPotHole license terms verified** - Verify Kaggle dataset license terms
7. **Class mapping confirmed** - Map D00/D10/D20/D40 to project "pothole" class definition
8. **Annotation format conversion path defined** - Pascal VOC XML to project pixel format conversion method documented
9. **BharatPotHole annotation format verified** - Confirm YOLO format compatibility with project contract

### H. Decisions Now LOCKED

- Group-based leakage prevention (LOCKED PRINCIPLE)
- Single "pothole" class representation (LOCKED PRINCIPLE)
- Pixel coordinate convention `[x1, y1, x2, y2]` (LOCKED PRINCIPLE)
- RDD2022 India subset is 9,665 images (LOCKED FACT from official paper)
- RDD2022 has 47,420 total images (LOCKED FACT from official paper)
- RDD2022 uses Pascal VOC XML, NOT YOLO (LOCKED FACT from official paper)

### I. Decisions Still OPEN

- Exact split proportions
- RDD2022 + BharatPotHole combination
- Final dataset composition
- Annotation quality for any dataset
- RDD2022 license terms (non-commercial restriction scope)
- Whether HRP4K can serve as cross-domain evaluation

---

## 16. Dataset Audit Summary (CORRECTED)

| Dataset | Verified Facts | Unknowns | Suitability |
|---------|---------------|----------|-------------|
| RDD2022 | Multi-national (6 countries), 47,420 images, India subset 9,665 images, Pascal VOC XML, D40 pothole class, forward-camera, non-commercial | Annotation quality, leakage grouping, India subset quality, license terms, size distribution | HIGH - primary candidate |
| BharatPotHole/iWatchRoad | Indian dashcam, >7,000 frames, YOLO format, pothole single class | Exact scale, annotation quality, leakage, license | MEDIUM - supplementary candidate |
| RAD | 600 Indian images, CC BY 4.0, pothole classification | Almost everything else | REJECTED (too small) |
| RDD2020 | India/Japan/Czech, 26,336 images, Pascal VOC XML, D00-D40, CC BY 4.0 | Annotation quality, leakage, India subset quality | MEDIUM - supplementary candidate |
| HRP4K | China, 6,003 images, 4K, YOLO+COCO, pothole single class, CC BY 4.0 | Indian relevance, leakage, scale verification | LOW for training; MEDIUM for cross-domain evaluation |

---

## 17. Status

| Item | Status |
|------|--------|
| Dataset composition | OPEN / UNDER DEEP AUDIT |
| Exact dataset combination | OPEN |
| Exact dataset version | OPEN |
| Exact split proportions | OPEN |
| Exact class normalization | OPEN |
| Group-based leakage prevention | LOCKED PRINCIPLE |
| RDD2022 as primary dataset | RECOMMENDED, not locked (CORRECTED: 47,420 images, Pascal VOC XML, multi-national) |
| BharatPotHole as supplementary | RECOMMENDED, not locked |
| HRP4K as external evaluation | RECOMMENDED, not locked (Chinese domain) |
| RAD as rejected | REJECTED (too small) |
| Additional data collection | RECOMMENDED, not locked |

---

*CORRECTION NOTICE: This audit corrected significant errors in the previous version. The previous audit incorrectly stated RDD2022 had 4,500 images in India-only, used YOLO format, and cited the wrong Mendeley URL. Verification from official sources established: 47,420 total images, 6 countries, Pascal VOC XML format, GitHub source sekilab/RoadDamageDetector.*

*Consistent with ARCHITECTURE.md, DATA_PIPELINE.md, MODEL_TRAINING.md, and MODEL_EVALUATION.md. See PROJECT.md for the source-of-truth map.*

---

## 18. Real RDD2022 India Sample Inspection (2026-09-21)

### 18.1 Source and Artifact

| Field | Value |
|-------|-------|
| Dataset | RDD2022 India subset |
| Source (Official) | Kaggle `vidishbijalwan/rdd2022-india-pothole-d40` (derived from official RDD2022) |
| Official Repository | `github.com/sekilab/RoadDamageDetector` |
| Official India Release | `RDD2022_India.zip` (502.3 MB, train + test) from `https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/RDD2022_India.zip` |
| Official Acquisition Status | **Access Denied (403)** - S3 bucket returns Access Denied |
| Fallback Source | FigShare `RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022` (13.2 GB total, not country-specific) |
| Artifact | Kaggle-derived subset: `experiments/dataset/raw_rdd2022_india/` |
| Download date | 2026-09-21 |
| Annotation format | Pascal VOC XML |
| Image format | JPEG 720x720 |

### 18.2 Real Directory Structure

```
experiments/dataset/raw_rdd2022_india/
├── train/
│   ├── annotations/
│   │   └── xmls/          (1530 XML files)
│   └── images/            (1530 JPG files)
```

### 18.3 Full India Train Set Statistics

| Metric | Value |
|--------|-------|
| Annotation files | 1530 |
| Images inspected | 1530 |
| Total objects | 4524 |
| Average objects/image | 2.96 |
| Empty annotations | 0 |
| Malformed XML | 0 |
| Invalid coordinates | 0 |
| Missing image references | 0 |

### 18.4 Real Class Distribution

| Class | Count | Percentage | Description (official) |
|-------|-------|------------|------------------------|
| D00 | 471 | 10.4% | Longitudinal Crack |
| D01 | 27 | 0.6% | (additional crack variant) |
| D10 | 23 | 0.5% | Transverse Crack |
| D11 | 7 | 0.2% | (additional crack variant) |
| D20 | 645 | 14.3% | Alligator Crack |
| D40 | 3187 | 70.4% | **Pothole** |
| D43 | 5 | 0.1% | (additional damage variant) |
| D44 | 151 | 3.3% | (additional damage variant) |
| D50 | 8 | 0.2% | (additional damage variant) |

**IMPORTANT**: The official CRDDC label map lists only D00, D10, D20, D40. The actual data contains 9 classes (D00, D01, D10, D11, D20, D40, D43, D44, D50).

### 18.5 Pothole Class Mapping

**D40 = Pothole** (confirmed by official dataset definition)

D40 accounts for 3187 of 4524 objects (70.4%) in the India train set.

### 18.6 Real Annotation Structure

Example from `India_000005.xml`:
```xml
<annotation>
    <folder>images</folder>
    <filename>India_000005.jpg</filename>
    <size>
        <width>720</width>
        <height>720</height>
        <depth>3</depth>
    </size>
    <segmented>0</segmented>
    <object>
        <name>D40</name>
        <pose>Unspecified</pose>
        <truncated>0</truncated>
        <difficult>0</difficult>
        <bndbox>
            <xmin>20</xmin>
            <ymin>473</ymin>
            <xmax>368</xmax>
            <ymax>576</ymax>
        </bndbox>
    </object>
</annotation>
```

All fields present: filename, width, height, depth, object, name, pose, truncated, difficult, bndbox (xmin, ymin, xmax, ymax).

### 18.7 Bounding Box Statistics (Full Dataset)

| Metric | Value |
|--------|-------|
| Width range | 15 - 718 px |
| Area range | 304 - 346,368 px² |
| Relative area range | 0.0006 - 0.6681 |
| Average bbox width | 145.06 px |
| Average bbox area | 18,357.50 px² |
| Average relative area | 0.04 |

### 18.8 Data Quality Observations

- No malformed XML detected
- No invalid coordinates detected
- No empty annotations
- No missing image references
- All images are 720x720 resolution
- All annotations use standard Pascal VOC format
- Additional classes (D01, D11, D43, D44, D50) present beyond official CRDDC 4-class list

### 18.9 Important: Test Set Has No Annotations

The official RDD2022 test set contains images without ground-truth annotations. Do NOT use it as an evaluation set for model validation. Project train/validation/test strategy will be designed separately.

### 18.10 Differences from Synthetic Assumptions

| Assumption | Real Data |
|------------|-----------|
| 4 classes (D00, D10, D20, D40) | 9 classes observed |
| D40 is pothole | Confirmed |
| 720x720 resolution | Confirmed |
| Pascal VOC XML | Confirmed |
| All fields populated | Confirmed (pose, truncated, difficult all present) |

### 18.11 Analysis Tooling

The `scripts/analysis/` module provides automated inspection and analysis:

- `scripts/analysis/rdd2022_india_analysis.py` - Analysis script for RDD2022 India sample (class counts, co-occurrence, bbox stats)
- `scripts/analysis/rdd2022_provenance_analysis.py` - Provenance and class semantics analysis (class semantics, co-occurrence, candidate strategies)
- `scripts/analysis/rdd2022_visualization.py` - Visualization module with matplotlib charts
- `scripts/analysis/rdd2022_india_analysis_cli.py` - CLI entry point for analysis pipeline
- `analysis/output/` - Contains JSON analysis results, markdown reports, and PNG visualizations

Analysis output files:
- `rdd2022_india_analysis.json` - Complete structured analysis results
- `rdd2022_india_report.md` - Human-readable analysis report
- `rdd2022_provenance_analysis.json` - Provenance and class semantics analysis results
- `rdd2022_provenance_report.md` - Human-readable provenance report
- `class_counts.png` - Object counts by class (horizontal bar chart)
- `class_cooccurrence.png` - Class co-occurrence heatmap
- `d40_bbox_area.png` - D40 bounding box area statistics
- `d40_spatial_scatter.png` - D40 spatial distribution scatter plot
- `d40_spatial_heatmap.png` - D40 spatial density heatmap
- `bbox_size_distribution.png` - Bounding box area distribution by class

### 18.12 D40/Pothole Spatial Distribution

D40 normalized center coordinates: mean X=0.488, mean Y=0.743, indicating potholes are spatially distributed across the image with slight concentration in the lower-center region.

**Class Co-occurrence Key Findings**:
- D40 appears in 100% of images (1,530/1,530); the artifact was filtered to include only images containing at least one D40/pothole annotation
- D40 co-occurs with D20 (Alligator Crack) in 549 images (35.9% of total)
- D40 co-occurs with D00 (Longitudinal Crack) in 363 images (23.7% of total)
- D40 co-occurs with D44 (Other Corruption) in 124 images (8.1% of total)
- D40-only images (no other class): 677 (44.2%)
- D40+D00 images: 363 (23.7%)
- D40+D20 images (D00 absent): 381 (24.9%)
- D40+other (D00 absent, D20 absent): 109 (7.1%)
- Non-D40-only images: 0 (0.0%) — no images without D40 in this artifact

### 18.13 Bounding Box Size Statistics (D40/Pothole Only)

| Metric | D40 (Pothole) | D20 (Alligator) | D00 (Longitudinal) |
|--------|--------------|-----------------|---------------------|
| Count | 3,187 | 645 | 471 |
| Width mean | 120.2 px | 308.0 px | 96.8 px |
| Height mean | 67.6 px | 161.0 px | 123.8 px |
| Area mean | 11,869 px² | 55,844 px² | 13,742 px² |
| Relative area mean | 0.023 | 0.108 | 0.027 |
| Center X mean | 0.488 | 0.530 | 0.526 |
| Center Y mean | 0.743 | 0.796 | 0.769 |

D40 (Pothole) objects are significantly smaller than D20 (Alligator Crack) objects, with roughly 1/5 the mean area. Potholes are concentrated in the lower-center of images, while cracks are more widely distributed.

### 18.14 Limitations and Open Questions

- The sample (1,530 images) represents approximately 15.8% of the full India subset (9,665 images)
- The 9 classes observed (D00, D01, D10, D11, D20, D40, D43, D44, D50) exceed the official CRDDC 4-class specification
- D50 provenance is unknown (not in official CRDDC label maps)
- Full dataset statistics may differ from sample
- Spatial distribution based on normalized centers only; pixel-level distribution needs further analysis
- No image content analysis performed (only annotation validation)
- Selection bias: 100% of images contain D40; non-D40-only images are absent from the artifact
- Kaggle artifact claims "D40 only" but contains all 9 classes
- D40 semantic scope is broader than "pothole" (includes rutting, bump, separation per CRDDC)

### 18.15 Class Mapping and Dataset Provenance

#### 18.15.1 Provenance Chain

| Step | Source | Details |
|------|--------|---------|
| Original | RDD2022 (CRDDC) | Arya et al. (2022), arXiv:2209.08538, published in Geoscience Data Journal (DOI: 10.1002/gdj3.260) |
| Official release | `github.com/sekilab/RoadDamageDetector` | RDD2022_India.zip (502.3 MB), 9,665 images total (7,706 train + test) |
| Derived artifact | Kaggle `vidishbijalwan/rdd2022-india-pothole-d40` | 1,530 images (15.8% of India train set), filtered from India subset |
| Local copy | `experiments/dataset/raw_rdd2022_india/` | Downloaded 2026-09-21 |

**Key provenance observations**:
- The Kaggle README cites RDD2022 by Arya et al. (2022)
- Pascal VOC XML format, 720x720 resolution, India locations (Delhi, Gurugram, Haryana) — consistent with official RDD2022
- The artifact is a filtered subset of the India train set
- Artifact is named "Pothole D40" but contains 9 classes, not just D40
- No images without D40 are present in the artifact (selection bias confirmed)

#### 18.15.2 Class Semantics Table

| Class | Meaning | Object Count | Image Count | Classification | Evidence | Project Relevance |
|-------|---------|-------------|-------------|----------------|----------|-------------------|
| D00 | Longitudinal Crack | 471 | 363 | **VERIFIED** | Arya et al. (2022), arXiv:2209.08538; CRDDC label map; crackLabelMap.txt | NOT pothole |
| D01 | Longitudinal Crack (construction joint part) | 27 | 19 | **VERIFIED** | RDD2018 Table 1 (arXiv:1801.09454); crackLabelMap.txt | NOT pothole |
| D10 | Transverse Crack | 23 | 22 | **VERIFIED** | Arya et al. (2022), arXiv:2209.08538; CRDDC label map; crackLabelMap.txt | NOT pothole |
| D11 | Transverse Crack (construction joint part) | 7 | 7 | **VERIFIED** | RDD2018 Table 1 (arXiv:1801.09454); crackLabelMap.txt | NOT pothole |
| D20 | Alligator Crack | 645 | 549 | **VERIFIED** | Arya et al. (2022), arXiv:2209.08538; CRDDC label map; crackLabelMap.txt | NOT pothole |
| D40 | Pothole (Other Corruption: rutting, bump, pothole, separation) | 3,187 | 1,530 | **VERIFIED** | Arya et al. (2022), arXiv:2209.08538; CRDDC label map; crackLabelMap.txt | **PRIMARY TARGET** |
| D43 | White line blur | 5 | 5 | **VERIFIED** | RDD2018 Table 1 (arXiv:1801.09454); crackLabelMap.txt | NOT pothole; road marking artifact |
| D44 | Cross walk blur | 151 | 124 | **VERIFIED** | RDD2018 Table 1 (arXiv:1801.09454); crackLabelMap.txt | NOT pothole; road marking artifact |
| D50 | Unknown | 8 | 8 | **UNKNOWN** | Not in crackLabelMap.txt, not in RDD2018, not in RDD2022, not in any paper | **PROVENANCE UNKNOWN** |

**Total objects**: 4,524 across 1,530 images. D40 accounts for 70.4% of all objects.

**Classification key**:
- **VERIFIED**: Definition confirmed by at least two authoritative sources (paper, label map, or repository)
- **DERIVED**: Definition inferred from context or partial evidence
- **UNKNOWN**: No authoritative source found

#### 18.15.2a 9-Class vs 4-Class Reconciliation

| Local class | Official CRDDC task? | Broader RDD taxonomy? | Source of definition | Evidence |
|-------------|----------------------|----------------------|---------------------|----------|
| D00 | Yes (CRDDC class 1) | Yes | arXiv:2209.08538; crackLabelMap.txt | Verified in all sources |
| D01 | No | Yes (RDD2018) | arXiv:1801.09454; crackLabelMap.txt | Verified in RDD2018 and label map |
| D10 | Yes (CRDDC class 2) | Yes | arXiv:2209.08538; crackLabelMap.txt | Verified in all sources |
| D11 | No | Yes (RDD2018) | arXiv:1801.09454; crackLabelMap.txt | Verified in RDD2018 and label map |
| D20 | Yes (CRDDC class 3) | Yes | arXiv:2209.08538; crackLabelMap.txt | Verified in all sources |
| D40 | Yes (CRDDC class 4) | Yes | arXiv:2209.08538; crackLabelMap.txt | Verified in all sources |
| D43 | No | Yes (RDD2018) | arXiv:1801.09454; crackLabelMap.txt | Verified as "White line blur" in RDD2018 |
| D44 | No | Yes (RDD2018) | arXiv:1801.09454; crackLabelMap.txt | Verified as "Cross walk blur" in RDD2018 |
| D50 | No | No | None found | Not in any official source — UNKNOWN |

**Key reconciliation findings**:
- Official CRDDC'2022 task uses exactly 4 classes: {D00, D10, D20, D40}
- RDD2018 used 8 classes: {D00, D01, D10, D11, D20, D40, D43, D44}
- RDD2020/RDD2022/CRDDC'2022 dropped D01, D11, D43, D44 from the active task but kept them in the label map
- D43 and D44 are **road marking damage types** (white line blur, crosswalk blur), not structural road damage
- D50 is not documented in any official RDD2022 source — provenance UNKNOWN
- The local artifact contains 5 classes beyond the CRDDC task (D01, D11, D43, D44, D50)
- The official `crackLabelMap.txt` includes 8 classes (D00-D44 excluding D50), confirming D43/D44 belong to the broader taxonomy

#### 18.15.3 D40 Semantic Caution

D40 in the CRDDC specification encompasses "Other Corruption" including rutting, bump, pothole, and separation. It is NOT a purely physical-pothole category. The Kaggle artifact name ("Pothole D40") implies pure pothole detection, but the source data includes broader road surface corruption. A model trained on D40 will learn a broader corruption concept, not strictly potholes.

#### 18.15.4 Negative-Example Problem Analysis

For a future pothole-detection dataset, images must be classified into four categories based on their annotated damage content:

| Image Category | Count (local artifact) | Percentage | Future Dataset Role |
|----------------|------------------------|------------|---------------------|
| D40 only (no other classes) | 677 | 44.2% | **Positive** (pothole present, no other damage) |
| D40 + other damage | 853 | 55.8% | **Positive** (pothole present, plus other damage) |
| Only non-D40 damage | 0 | 0.0% | **Negative** (no pothole, other damage present) |
| No annotated damage | 0 | 0.0% | **Negative** (no damage at all) |

**Key findings**:
- 100% of images contain D40 (3,187 pothole objects across all 1,530 images)
- 55.8% of images contain D40 alongside other damage classes (cracks, D43, D44)
- 0 images contain only non-D40 damage (no crack-only images)
- 0 images contain no annotated damage (no pure negative images)
- This is a **selection bias**: the artifact was filtered to include only pothole-containing images
- Images containing other damage (D00, D10, D20, D01, D11, D43, D44) alongside D40 are **positive samples** for pothole detection but require careful label handling

**Critical distinction**: "Unlabeled" is not the same as "negative." An image with no D40 annotation but containing D00/D10/D20/D43/D44 is a **negative** for pothole detection (no pothole present), but an image with no annotations at all is **background** (no damage). Both are needed for a robust pothole detector.

#### 18.15.5 Candidate Class-Mapping Strategies (DECIDED: Strategy B)

**Strategy A: D40-only single-class detector** — NOT SELECTED
- Retain: D40
- Background/ignore: D00, D01, D10, D11, D20, D43, D44, D50
- Images containing D40: positive samples
- Images without D40 (not present in artifact): negative samples
- Advantages: Simple, focused on pothole detection, matches project scope
- Risks: D40 includes non-pothole corruption; false negatives on crack damage; no negative samples available in artifact
- Evaluation: Precision/recall for D40 only

**Strategy B: Four-class road-damage detector (official CRDDC task)** — **SELECTED**
- Retain: D00, D10, D20, D40 (official CRDDC classes only)
- D01 → D00 (construction joint variant of longitudinal crack)
- D11 → D10 (construction joint variant of transverse crack)
- D43/D44/D50 → EXCLUDED (never become positive labels)
- Advantages: Aligns with official benchmark, excludes non-task classes (D43/D44 are road markings), standardizes evaluation
- Risks: D01/D11 merge loses construction-joint location context at class level (preserved in raw annotations); D43/D44/D50 ignored annotations need careful handling
- Evaluation: Per-class mAP for {D00, D10, D20, D40}

**Strategy C: D40 + crack binary detector** — NOT SELECTED
- Retain: D40 (pothole) vs crack_group (D00+D10+D20+D01+D11)
- Background/ignore: D43, D44, D50
- Advantages: Distinguishes potholes from cracks (both relevant to road maintenance), reduces class complexity
- Risks: Crack subtypes collapsed; D43/D44/D50 ambiguous; still no negative samples in artifact
- Evaluation: Binary detection

**Strategy D (proposed): Full 8-class RDD taxonomy detector** — NOT SELECTED
- Retain: D00, D01, D10, D11, D20, D40, D43, D44 (all classes in official crackLabelMap.txt)
- Exclude: D50 (unknown provenance, not in any official source)
- Advantages: Maximum information retention, aligns with RDD2018/RDD2020 taxonomy, includes road marking damage
- Risks: D43/D44 are rare (5/151 objects), D50 excluded; requires more data per class

### 18.15.5a Final Deterministic Class Mapping Table

| Raw class | Final project class | Action | Reason |
|-----------|---------------------|--------|--------|
| D00 | 0 / longitudinal_crack | KEEP | Official CRDDC class; longitudinal road crack; verified in Arya et al. (2022) and crackLabelMap.txt |
| D01 | 0 / longitudinal_crack | MERGE → D00 | RDD2018 Table 1: "Longitudinal Crack (construction joint part)" — same damage type as D00, different location; construction joints are still longitudinal cracks |
| D10 | 1 / transverse_crack | KEEP | Official CRDDC class; transverse road crack; verified in Arya et al. (2022) and crackLabelMap.txt |
| D11 | 1 / transverse_crack | MERGE → D10 | RDD2018 Table 1: "Transverse Crack (construction joint part)" — same damage type as D10, different location; construction joints are still transverse cracks |
| D20 | 2 / alligator_crack | KEEP | Official CRDDC class; alligator/connected crack pattern; verified in Arya et al. (2022) and crackLabelMap.txt |
| D40 | 3 / pothole | KEEP | Official CRDDC class; pothole/rutting/bump/separation (CRDDC "Other Corruption"); verified in Arya et al. (2022) and crackLabelMap.txt |
| D43 | — | EXCLUDE | Road marking damage (white line blur); not structural road damage; excluded from CRDDC task |
| D44 | — | EXCLUDE | Road marking damage (crosswalk blur); not structural road damage; excluded from CRDDC task |
| D50 | — | EXCLUDE | Annotation artifact; no official source; 100% D40 co-occurrence; near-identical bbox to D40 in India_007909 (2-pixel offset) |

**Deterministic decision**: D01 → D00 and D11 → D10. Exclusion was rejected because D01/D11 are construction-joint variants of retained crack classes, and excluding them would lose 34 crack objects (27 D01 + 7 D11) that are valuable as hard negatives for pothole detection.
- Evaluation: Per-class mAP for 8 classes

#### 18.15.6 Training-Dataset Coverage

| Metric | Value |
|--------|-------|
| Available artifact | 1,530 images (15.8% of India train set) |
| Official India train set | 7,706 images |
| Official India total (train+test) | 9,665 images |
| Missing coverage | ~81.8% of India train set |
| Selection bias risk | **HIGH** — artifact over-represents pothole-rich images |
| Geographic scope | Delhi, Gurugram, Haryana only |
| Additional data needed | Full India subset or balanced sample across regions |

#### 18.15.7 Open Decisions

- Class-mapping strategy (A, B, C, or D) — **DECIDED: Strategy B (official CRDDC 4-class task)**
- D50 provenance — **RESOLVED: EXCLUDED from all strategies** (no official source, 100% D40 co-occurrence, duplicate annotation evidence in India_007909)
- D43/D44 handling — **DECIDED: EXCLUDED** (road marking damage, not structural road damage, not in CRDDC task)
- D01 mapping — **DECIDED: D01 → D00** (construction joint variant of longitudinal crack; deterministic merge)
- D11 mapping — **DECIDED: D11 → D10** (construction joint variant of transverse crack; deterministic merge)
- Whether to include crack-only images in training — **NOT DECIDED** (artifact has 0 crack-only images; depends on future data acquisition)
- Whether to expand artifact to full India subset — **NOT DECIDED** (official S3 access denied; FigShare fallback available)

#### 18.15.8 Dataset Semantics Distinctions

| Concept | Definition | Example |
|---------|-----------|---------|
| **Dataset class** | Class label as it appears in the source annotation file | D40, D00, D20, D43 |
| **Project class** | Canonical class used by the RoadGuard project after mapping | pothole, longitudinal_crack, transverse_crack, alligator_crack |
| **Background** | Image region with no annotated damage | Unannotated road surface |
| **Ignored annotation** | Annotated object intentionally excluded from training/evaluation | D43/D44/D50 if excluded by mapping strategy |

**Key rules**:
- Do not silently equate "unlabeled" with "negative"
- Do not delete or rewrite raw annotations
- Do not convert XML to YOLO or create splits during this task
- Dataset class names must be preserved in raw data; project class names are defined in the data contract
- D43/D44/D50 must remain visible in raw annotations until a mapping decision is made
- D01 → D00, D11 → D10: deterministic merges, construction joint context preserved in raw annotations

#### 18.15.9 Annotation-Level and Image-Level Rules

##### Annotation-Level Rules

- Every retained object receives exactly one final project class ID (0–3)
- D01 annotations → class 0 (longitudinal_crack)
- D11 annotations → class 1 (transverse_crack)
- D43/D44/D50 annotations are excluded; never become positive labels
- Excluded annotations are logged but NOT deleted from raw files
- Bounding-box coordinates preserved exactly for retained objects
- No object is silently duplicated
- No object is silently lost except through the explicit exclusion rule for D43/D44/D50
- Raw annotation files remain unchanged (read-only conversion)

##### Image-Level Rules (Cases A–D)

- **Case A** (D40 + excluded annotations): Image retained; D40 object kept as class 3; excluded objects logged; image is positive sample for pothole detection
- **Case B** (D40 + other retained classes): Image retained; all retained objects kept with final project class IDs; multi-class image for evaluation
- **Case C** (only excluded annotations): Image retained but becomes annotation-empty after mapping; logged; excluded from training/evaluation; may serve as background for future hard-negative mining
- **Case D** (only retained non-D40 classes): Image retained; all objects kept; no D40 → negative sample for pothole detection; crack-only images valuable for crack/pothole distinction
- **General**: No image automatically deleted; annotation-empty images retained but excluded from training/evaluation; all exclusion decisions logged with reason

### 18.19 D43 / D44 / D50 Provenance Resolution

#### 18.19.1 D43 Definition

- **VERIFIED**: D43 = "White line blur"
- **Source**: RDD2018 paper (arXiv:1801.09454), Table 1: "Road damage types in our dataset and their definitions"
- **Evidence**: Also present in official `crackLabelMap.txt` (id: 7)
- **CRDDC task**: No — excluded from RDD2020/RDD2022 CRDDC four-class task
- **Broader taxonomy**: Yes — part of RDD2018 8-class taxonomy
- **Project relevance**: Road marking damage, not structural road damage

#### 18.19.2 D44 Definition

- **VERIFIED**: D44 = "Cross walk blur"
- **Source**: RDD2018 paper (arXiv:1801.09454), Table 1: "Road damage types in our dataset and their definitions"
- **Evidence**: Also present in official `crackLabelMap.txt` (id: 8)
- **CRDDC task**: No — excluded from RDD2020/RDD2022 CRDDC four-class task
- **Broader taxonomy**: Yes — part of RDD2018 8-class taxonomy
- **Project relevance**: Road marking damage, not structural road damage

#### 18.19.3 D50 Definition

- **UNKNOWN**: No authoritative definition found; local inspection confirms annotation artifact pattern
- **Sources checked**: crackLabelMap.txt, RDD2018 paper (arXiv:1801.09454), RDD2022 paper (arXiv:2209.08538), RDD2022 label_map.pbtxt, FigShare metadata
- **Evidence from local XML annotations**: 8 D50 objects across 8 images (0.5% of 1,530 images); all 8 instances co-occur with D40 in the same image (100% D40 co-occurrence); D50 never appears alone; D50 also co-occurs with D44 (2 images), D00 (2 images), and D11 (1 image)
- **Annotation anomaly**: Image India_007909 contains D50 and D40 with nearly identical bounding boxes (D50: 425,561→493,585; D40: 423,560→495,587 — only 2-pixel offset in each dimension), strongly suggesting D50 is a duplicate annotation or mislabeling error
- **CRDDC task**: No
- **Broader taxonomy**: No evidence — not in official crackLabelMap.txt (which includes D00-D44)
- **Project relevance**: UNKNOWN — no official source; likely annotation artifact; must NOT be used as a class until provenance is resolved; recommend EXCLUSION from all class-mapping strategies as an ignored annotation

**RecOMMENDATION**: EXCLUDE D50 from all strategies. Rationale: (1) no authoritative source, (2) 100% co-occurrence with D40 suggests it is either a duplicate of D40 or an annotation error, (3) only 8 instances (0.5% of data) is statistically insignificant, (4) one instance shows near-identical bbox to D40 (duplicate annotation evidence).

#### 18.19.4 Provenance Evidence Summary

| Class | RDD2018 | RDD2020 | RDD2022 CRDDC | crackLabelMap.txt | RDD2022 label_map.pbtxt | FigShare | Local artifact |
|-------|---------|---------|---------------|-------------------|------------------------|----------|----------------|
| D00 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| D01 | Yes | Yes | No | Yes | Yes | Yes | Yes |
| D10 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| D11 | Yes | Yes | No | Yes | Yes | Yes | Yes |
| D20 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| D40 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| D43 | Yes | No | No | Yes | Yes | Yes | Yes |
| D44 | Yes | No | No | Yes | Yes | Yes | Yes |
| D50 | No | No | No | No | No | No | Yes (8 objects) |

**Conclusion**: D43 and D44 are verified road-marking damage classes from the RDD2018 taxonomy, retained in the official label map but excluded from the CRDDC four-class task. D50 is unknown — present only in the local artifact with no official source.

### 18.16 Official Dataset Acquisition Status

| Metric | Value | Notes |
|--------|-------|-------|
| Official India ZIP URL | `https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/RDD2022_India.zip` | **403 Access Denied** |
| Official India ZIP size | 502.3 MB | train + test |
| Official India train images | 7,706 (of 9,665 total India subset) | Per CRDDC'2022 documentation |
| Official India total (train+test) | 9,665 | Per CRDDC'2022 documentation |
| Official total dataset | 47,420 images | 6 countries (Japan, India, Czech Republic, Norway, USA, China) |
| Official annotation format | Pascal VOC XML | Per CRDDC'2022 |
| Official class labels | {D00, D10, D20, D40} | 4 classes from CRDDC label map and label_map.pbtxt |
| Official S3 access | **Failed** (403 Access Denied as of 2026-09-21) | Cannot retrieve official India data |
| FigShare fallback | 13.2 GB dataset | Available but not country-specific; contains full RDD2022 |
| Dataset acquisition conclusion | **Official India data not accessible**; artifact is the only available local copy | Stop acquisition rather than inventing a workaround |

### 18.17 Official vs. Current Derivative Comparison

| Metric | Official India (per CRDDC'2022) | Current Kaggle Derivative |
|--------|----------------------------------|---------------------------|
| Total train images | 7,706 | 1,530 |
| Total train annotations | 7,706 | 1,530 |
| Test images | 1,959 | 0 |
| Observed classes | {D00, D10, D20, D40} | {D00, D01, D10, D11, D20, D40, D43, D44, D50} |
| D40-positive images | Unknown (not accessible) | 1,530 (100%) |
| D40-negative images | Unknown (not accessible) | 0 |
| Class distribution | Unknown | D40: 3,187 (70.4%); D20: 645 (14.3%); D00: 471 (10.4%); D44: 151 (3.3%); D01: 27 (0.6%); D10: 23 (0.5%); D50: 8 (0.2%); D11: 7 (0.2%); D43: 5 (0.1%) |
| Image dimensions | 720x720 (per CRDDC'2022) | 720x720 |
| Annotation format | Pascal VOC XML | Pascal VOC XML |
| Coverage of India train set | 100% | 15.8% |
| Selection bias | Unknown | **HIGH** — 100% of images contain D40 |

### 18.18 Selection-Bias Analysis

**Current derivative (Kaggle)**:
- All 1,530 images contain at least one D40 object
- D40 objects: 3,187 of 4,524 total objects (70.4%)
- 100% of images are D40-positive
- 0% of images are D40-negative (crack-only or empty)
- Co-occurrence (mutually exclusive): D40-only 677 (44.2%), D40+D00 363 (23.7%), D40+D20 381 (24.9%), D40+other 109 (7.1%)

**Official India (per CRDDC'2022)**:
- Total train images: 7,706
- Total India subset (train+test): 9,665
- Expected D40-positive / D40-negative distribution: **UNKNOWN** (official data not accessible)
- The official dataset includes all 4 CRDDC classes (D00, D10, D20, D40) across all images, with some images containing only cracks (D00/D10/D20) and no D40

**ML consequence of training only on D40-positive images**:
- Model will not learn to distinguish D40 from other damage types in crack-only images
- All crack-only images (D00/D10/D20 without D40) are absent from the artifact
- If the official India dataset contains crack-only images, training on only the D40-positive subset will:
  - Miss important negative examples (crack-only images)
  - Potentially inflate precision on D40 detection (since all images contain D40)
  - Reduce generalization to real-world deployment scenarios where crack-only images are common
  - Create a model that cannot detect non-D40 damage

**Provenance conclusion**:
- The Kaggle artifact is a **filtered D40-positive subset** of the official India train set
- It is NOT a strict subset (it contains classes D01, D11, D43, D44, D50 not in the official CRDDC 4-class specification)
- It is NOT a converted copy (annotation format is unchanged from official Pascal VOC XML)
- It is a **filtered, class-expanded derivative** — filtered to D40-positive images, but containing additional classes beyond the official 4

---

### 18.20 Sequence/Group Identification for Leakage-Safe Splitting (2026-09-26)

**Purpose**: determine whether the 1,530 normalized images contain correlated sequences/groups
that must be respected during splitting, as required by D-006. Evidence gathering only — no splits
created, no data modified.

Full report: `experiments/dataset/normalized_rdd2022_india/group_analysis/SYNTHESIS.md`.

#### 18.20.1 Filename Structure

| Property | Value |
|----------|-------|
| Pattern | `India_<6-digit index>` (1,530 / 1,530 match) |
| Prefixes | `India` only — no country sub-region component |
| Index range | 5 .. 9,890 |
| Index span | 9,886 |
| Unique indices | 1,530 |
| Contiguous | **No** |
| Missing indices | **8,356 (84.52% of span)** |
| Zero-padding | Uniform 6 digits |
| Lexical order == numeric order | Yes |
| Image/annotation stems 1:1 | Yes |

**FACT**: the filename encodes only a flat, dataset-wide integer index. No video, trip, camera, or
timestamp component is embedded. **FACT**: 84.52% of the index span is absent, so adjacency in this
artifact is weak evidence of adjacency in the source release.

#### 18.20.2 Grouping Metadata

| Check | Result |
|-------|--------|
| XML attributes in any of 1,530 files | **NONE** |
| Non-standard / vendor-specific tags | **NONE** |
| Sequence / video / trip / route ID | **NOT PRESENT** |
| Camera / device ID | **NOT PRESENT** |
| Timestamp / date | **NOT PRESENT** |
| GPS / lat / lon | **NOT PRESENT** |
| Grouping directory level | **NONE** |
| Auxiliary grouping files | **NONE** |

Observed tags are exactly the 18 standard Pascal VOC tags. The official directory listing stops at
country → split → {images, annotations}, with no sequence level.

**Method note**: naive substring search produced two false positives — `truncated` matched "run"
and `width` matched "id". Both are standard VOC tags, not grouping metadata. The matcher was
corrected to subtract a known-standard-tag set.

#### 18.20.3 Exact Duplicates (SHA-256)

| Metric | Value |
|--------|-------|
| Images analyzed | 1,530 |
| Unique content hashes | **1,530** |
| Exact duplicate groups | **0** |

No exact duplicates exist. No files were deleted.

#### 18.20.4 Near Duplicates (Complete Linkage + Pixel Verification)

**Method correction**: an initial single-linkage (transitive closure) pass produced a spurious
1,279-image aHash "group" whose internal maximum pairwise distance was 41 bits on a threshold of
5. Single linkage chains A–B–C when A≈B and B≈C even if A and C are unrelated. Re-done with
complete linkage (every member pair within threshold) plus pixel verification.

**Threshold calibration** (against 1,500 random pairs, seed 20260926 — not chosen arbitrarily):

| Statistic (random pairs) | Pearson corr |
|---|---|
| Mean / median | 0.543 / 0.581 |
| p95 | 0.795 |
| Max | 0.926 |
| % ≥ 0.90 | **0.27%** |
| % ≥ 0.95 | **0.00%** |

| Metric | Value |
|--------|-------|
| dHash candidate pairs (≤ 10 bits) | 3,716 |
| Complete-linkage groups (≥ 2 members) | 85 |
| Groups passing pixel verification | **59** |
| Groups rejected as hash artifacts | 26 |
| Genuine visual-match pairs | **583** |
| Expected by chance among candidates | ~10 |
| Images involved | **121 (7.9%)** |
| Largest verified group | **3** |

583 verified matches vs ~10 expected by chance is ~58× enrichment: the near-duplicate signal is
real but sparse, touching 121 images in clusters of at most 3.

**Critical**: verified near-duplicate pairs are **not** filename neighbors — median index gap
**2,643** (mean 3,152, max 9,155); only **1 of 583** pairs has an index gap ≤ 10.

#### 18.20.5 Filename-Neighbor Correlation

dHash distance (lower = more similar) vs a 20,000-pair random control baseline
(dHash mean **25.727**, seed 20260926). Counted only when both indices are present.

| Offset | Pairs | dHash mean | dHash median | Reduction vs random |
|--------|-------|------------|--------------|---------------------|
| +1 | 246 | 26.211 | 26.0 | **−1.88%** (farther than random) |
| +2 | 255 | 25.757 | 26.0 | −0.12% |
| +5 | 235 | 25.885 | 26.0 | −0.61% |
| +10 | 228 | 25.110 | 25.0 | +2.40% |
| **random** | 20,000 | **25.727** | 26.0 | baseline |

**FACT**: no systematic neighbor correlation. The +1 offset is slightly *farther apart* than
random. The +10 offset's 2.4% reduction is within sampling noise for 228 pairs and is contradicted
by +1, +2, and +5 all showing no reduction.

**INFERENCE**: filename index adjacency carries no usable correlation signal in this artifact.

#### 18.20.6 Confidence Classification

| Class | Count | Definition |
|-------|-------|------------|
| **VERIFIED GROUP** | 0 groups | Byte-identical content (SHA-256). None exist. |
| **LIKELY CORRELATED** | 59 groups, 121 images | Pixel-verified visual near-duplicate clusters, complete linkage, max size 3. **Candidate only — NOT proven source sequences.** |
| **UNKNOWN** | 1,409 images | No duplicate/near-duplicate evidence. Does **not** imply independent capture. |

#### 18.20.7 Split Implications — State C

**State C: no reliable grouping information can be established.**

The only defensible grouping is the 59 pixel-verified near-duplicate clusters (121 images), which
must be assigned as atomic units so visually near-identical images cannot straddle splits.

**Prohibited inferences**:
- Filename index proximity is NOT sequence membership (§18.20.5)
- Near-duplicate similarity is NOT proof of video origin (a road can be revisited)
- Leakage risk is **unquantifiable**, not zero
- These statistics are NOT representative of the full official India release

**Residual risk**: if the source release sampled frames from a few long videos at low temporal
density, visually dissimilar frames from one video could still land in different splits. With no
sequence metadata this cannot be measured or bounded, and must be recorded as an accepted
limitation rather than assumed away.

**D-006 status**: the principle remains correct and is NOT weakened. Its implementation assumption
(source group IDs available) is falsified for this artifact. A refinement is **proposed** in
`docs/DECISION_LOG.md` D-006-R1 — not silently applied.

*Consistent with ARCHITECTURE.md, DATA_PIPELINE.md, MODEL_TRAINING.md, and MODEL_EVALUATION.md. See PROJECT.md for the source-of-truth map.*