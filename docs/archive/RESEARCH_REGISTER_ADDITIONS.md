# Research Register - Additional Entries (CORRECTED)

## Additional Research Entries from Dataset Audit

### R-004: RDD2022 Dataset Audit (CORRECTED)

- **Question**: What are the verified properties of RDD2022?
- **Topic**: Dataset audit
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022
- **Version**: CRDDC'2022 challenge release
- **Finding**: 
  - **FACT**: Multi-national (6 countries: Japan, India, Czech Republic, Norway, USA, China), smartphone dashcam, pothole class (D40), bounding boxes, 47,420 total images, India subset 9,665 images, non-commercial license
  - **CRITICAL CORRECTION**: Previous research finding was incorrect - it stated 4,500 images, YOLO format, India-only, and cited wrong Mendeley URL.
  - **VERIFIED**: Actual dataset is GitHub sekilab/RoadDamageDetector, 47,420 images, Pascal VOC XML, multi-national.
  - **OPEN**: Exact annotation quality, leakage grouping, size distribution, object-count distribution.
- **Evidence**: docs/DATASET_AUDIT.md#3
- **Engineering implication**: Strong multi-national candidate for general detection, requires annotation audit and leakage analysis before use. India-specific suitability requires verification of India subset quality.
- **Confidence**: MEDIUM (verified facts are FACT; previous incorrect facts have been corrected)
- **Affected decision**: D-005 (Indian + forward-camera priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: After annotation quality inspection.
- **Status**: LOCKED (properties verified after correction)

---

### R-005: Dataset Combination Analysis (CORRECTED)

- **Question**: Can multiple candidate datasets be combined effectively?
- **Topic**: Dataset combination analysis
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RDD2022 + BharatPotHole (potential primary + supplementary)
- **Version**: N/A (analysis)
- **Finding**: 
  - FACT: Class semantics may differ between datasets (D00/D10/D20/D40 vs single pothole class)
  - FACT: RDD2022 uses Pascal VOC XML; BharatPotHole uses YOLO format; RDD2020 uses Pascal VOC XML
  - FACT: RDD2020 is subset of RDD2022 (confirmed by paper) - potential duplication
  - INFERENCE: Label semantics mismatch can cause negative transfer
  - INFERENCE: Licensing (non-commercial vs CC BY 4.0) may restrict combination
- **Evidence**: docs/DATASET_AUDIT.md#8
- **Engineering implication**: Dataset compatibility requires annotation inspection and licensing verification before combination.
- **Confidence**: MEDIUM
- **Affected decision**: D-005 (dataset priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: After annotation inspection and licensing verification.
- **Status**: PENDING

---

### R-006: Hard Negative Taxonomy for Pothole Detection

- **Question**: What non-pothole examples should be included as hard negatives?
- **Topic**: Hard negative strategy
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: N/A (taxonomy)
- **Version**: N/A
- **Finding**: 
  - FACT: Cracks, patches, shadows, and stains are visually similar to potholes
  - INFERENCE: These should be included in negative samples
  - INFERENCE: Manholes and water puddles may also be helpful
- **Evidence**: docs/DATASET_AUDIT.md#9
- **Engineering implication**: Add hard negatives from deployment domain during dataset preparation.
- **Confidence**: HIGH (visual similarity is well-established)
- **Affected decision**: None (future task)
- **Date checked**: 2026-09-21
- **Revisit condition**: After model training with hard negatives.
- **Status**: RECOMMENDED

---

### R-007: BharatPotHole / iWatchRoad Dataset Verification

- **Question**: What are the verified properties of BharatPotHole / iWatchRoad?
- **Topic**: Dataset audit
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: BharatPotHole
- **Version**: BharatPotHole-3k / BharatPotHole-7k
- **Finding**: 
  - FACT: Indian dashcam dataset, >7,000 annotated frames, YOLO format, single pothole class
  - FACT: Diverse Indian road conditions (rain, night, unpaved roads)
  - FACT: Paper: arXiv:2508.10945 "iWatchRoad: Scalable Detection and Geospatial Visualization of Potholes for Smart Cities"
  - FACT: Kaggle source: surbhisaswatimohanty/bharatpothole
  - OPEN: Exact image count, annotation quality, leakage grouping, license terms
- **Evidence**: docs/DATASET_AUDIT.md#4
- **Engineering implication**: Strong Indian-specific supplementary candidate; dashcam perspective matches project deployment requirements.
- **Confidence**: MEDIUM
- **Affected decision**: D-005 (Indian + forward-camera priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: After dataset download and annotation inspection.
- **Status**: PENDING

---

### R-008: HRP4K Dataset Verification

- **Question**: What are the verified properties of HRP4K?
- **Topic**: Dataset audit
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: HRP4K
- **Version**: N/A
- **Finding**: 
  - FACT: Chinese dataset (Hangzhou, Huzhou, Jiaxing), NOT Indian
  - FACT: 6,003 images, 7,217 pothole instances, 4K resolution (3840x2160)
  - FACT: Vehicle-mounted mirrorless cameras (Sony A7IV, A9III)
  - FACT: YOLO + COCO annotation formats
  - FACT: CC BY 4.0 license
  - FACT: Video-level splits documented (prevents leakage)
  - OPEN: Indian domain adaptation, exact scale verification
- **Evidence**: docs/DATASET_AUDIT.md#7, PMCID: PMC13328687
- **Engineering implication**: NOT suitable as Indian training data; may serve as cross-domain evaluation dataset.
- **Confidence**: HIGH
- **Affected decision**: D-005 (Indian + forward-camera priority)
- **Date checked**: 2026-09-21
- **Revisit condition**: If Indian domain adaptation is required.
- **Status**: LOCKED (properties verified)

---

### R-009: RAD Dataset Verification

- **Question**: What are the verified properties of RAD?
- **Topic**: Dataset audit
- **Source**: Dataset audit performed (docs/DATASET_AUDIT.md)
- **Source date**: 2026-09-21
- **Technology / Dataset**: RAD (Road Anomaly Detection System Dataset)
- **Version**: 2 (Mendeley Data)
- **Finding**: 
  - FACT: 600 images (300 pothole + 300 good road), CC BY 4.0
  - FACT: Indian origin (Vishwakarma Institute of Information Technology)
  - FACT: Mendeley Data DOI: 10.17632/fbhdy3bxgv.2
  - CRITICAL CORRECTION: Previous audit assumed RAD was a large "Road Anomaly Dataset" with unknown properties. Actual dataset is a small pothole classification dataset (600 images), NOT a large-scale road anomaly detection dataset.
  - OPEN: Annotation format, bounding boxes, quality, leakage
- **Evidence**: docs/DATASET_AUDIT.md#5
- **Engineering implication**: Too small for primary training; may serve as validation data only.
- **Confidence**: HIGH
- **Affected decision**: None
- **Date checked**: 2026-09-21
- **Revisit condition**: If additional validation data needed.
- **Status**: LOCKED (properties verified)

---

*This register supplements the original entries in RESEARCH_REGISTER.md. See DATASET_AUDIT.md for the full audit findings.*