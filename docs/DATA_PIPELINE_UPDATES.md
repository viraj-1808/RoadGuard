# DATA_PIPELINE.md - Audit Updates

## Changes from Audit

The dataset audit (docs/DATASET_AUDIT.md) provides stronger evidence for the following updates:

### Primary Dataset Candidate

- RDD2022 is the strongest verified candidate for primary dataset (multi-national: Japan, India, Czech, Norway, USA, China; forward-camera; pothole class; Pascal VOC XML format; 47,420 total images; 9,665 India subset; non-commercial license).
- HRP4K is a candidate for supplementary dataset (pothole detection dataset, requires inspection).

### Dataset Source Registry Updates

| Field | Previous (DATA_PIPELINE.md) | Updated (DATASET_AUDIT.md) |
|-------|-----------------------------|---------------------------|
| RDD2022 source | Example values only | Full registry entry with all fields |
| BharatPotHole | Listed as candidate | Listed as candidate requiring inspection |
| RAD | Listed as candidate | Listed as candidate requiring inspection |
| RDD2020 | Listed as candidate | Listed as candidate requiring inspection |
| HRP4K | Listed as candidate | Listed as candidate requiring inspection |

### Combination Analysis

The audit provides combination analysis (Section 8 of DATASET_AUDIT.md):

- Overlapping classes: Likely pothole across all candidates
- Label semantics: UNKNOWN until annotation inspection
- Annotation conventions: Pascal VOC XML (RDD2022), UNKNOWN (others)
- Domain mismatch: MEDIUM risk for non-Indian datasets
- Image-resolution mismatch: RDD2022 at 720x720 (India) / 600x600 (Japan/Czech), others UNKNOWN
- Class imbalance: Typical for pothole datasets
- Potential duplication: RDD2022 and RDD2020 may share data
- Negative transfer: Risk from incompatible class semantics
- Licensing compatibility: RDD2022 is non-commercial (verify from source)

### Hard Negatives

The audit provides a hard-negative strategy (Section 9 of DATASET_AUDIT.md):

- Priority negatives: cracks, patches, shadows, stains
- Exclusion criteria: not representative, too different, ambiguous

### Leakage Prevention

The audit confirms the group-based leakage prevention strategy and adds:

- Grouping unit hierarchy (5 levels)
- Precedence rules for grouping
- Source dataset independent splitting
- Cross-dataset duplicate removal
- Video frame grouping

### Data Contract

The audit defines the project data contract (Section 11 of DATASET_AUDIT.md):

- Image format: OPEN
- Annotation representation: Project pixel format (OPEN)
- Class representation: Single "pothole" class (LOCKED PRINCIPLE)
- Coordinate convention: Pixel coordinates, top-left origin (LOCKED PRINCIPLE)
- Metadata requirements: Defined
- Provenance requirements: Defined
- Dataset version identifier: Defined
- Source identifier: Defined
- Sequence/group identifier: Defined
