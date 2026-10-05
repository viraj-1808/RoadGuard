# Dataset B Taxonomy Mapping

## Project Taxonomy (Locked)

| Project ID | Class Name | Description |
|------------|------------|-------------|
| 0 | longitudinal_crack | Linear cracks aligned with direction of travel |
| 1 | transverse_crack | Cracks perpendicular to direction of travel |
| 2 | alligator_crack | Interconnected cracks forming alligator-skin pattern |
| 3 | pothole | Pothole, rutting, bump, separation |

## RDD2022 Source Classes

| Source Code | Source Name | Source Definition (CRDDC) |
|-------------|-------------|---------------------------|
| D00 | Longitudinal Crack | Cracks aligned with direction of travel |
| D10 | Transverse Crack | Cracks perpendicular to direction of travel |
| D20 | Alligator Crack | Interconnected cracks forming alligator-skin pattern |
| D40 | Pothole (Other Corruption) | Pothole, rutting, bump, separation |

## Mapping Table

| Source Class | Source Meaning | Target Class | Mapping Confidence | Reason | Risks |
|--------------|----------------|--------------|--------------------|--------|-------|
| D00 | Longitudinal Crack | 0 longitudinal_crack | HIGH | Direct semantic match; same definition | None |
| D10 | Transverse Crack | 1 transverse_crack | HIGH | Direct semantic match; same definition | None |
| D20 | Alligator Crack | 2 alligator_crack | HIGH | Direct semantic match; same definition | None |
| D40 | Pothole (Other Corruption) | 3 pothole | MEDIUM | D40 includes pothole but also rutting, bump, separation | Broader semantics than "pure pothole"; may introduce label noise if model learns rutting/bump as pothole |

## D40 Semantic Expansion — Critical Analysis

The CRDDC D40 class is defined as **"Other Corruption"** encompassing:
1. Pothole (bowl-shaped depression)
2. Rutting (longitudinal surface deformation)
3. Bump (localized elevation)
4. Separation (joint/pavement separation)

Our project class "pothole" (ID 3) is intended for **pothole** specifically.

### Mapping Options

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **Option A (Selected)** | Map all D40 → project pothole | Simple; uses all D40 data; aligns with CRDDC task | Dilutes "pothole" semantics; model may learn rutting/bump as pothole |
| Option B | Filter D40 to only pothole-like annotations | Pure pothole class | Requires manual re-annotation; no official sub-class labels; high effort |
| Option C | Split D40 into sub-classes | Semantic precision | Not supported by annotations; no ground truth for sub-classes |
| Option D | Exclude D40 entirely | Avoids semantic mismatch | Loses pothole data entirely; defeats H1 |

## Selected Mapping: Option A with Caveats

We map D40 → project pothole (ID 3) but acknowledge:
- The learned "pothole" class will be a **composite detector** for D40 corruption types
- This matches the official CRDDC evaluation (where D40 is a single class)
- It addresses H1 by providing diverse D40 examples across countries
- It does NOT create a "pure pothole" detector; it creates a "D40 corruption" detector

### Risk Mitigation

1. **Documentation**: Explicitly state that class 3 corresponds to CRDDC D40 "Other Corruption"
2. **Evaluation**: Report per-class metrics but note the semantic broadening
3. **Downstream**: If pure pothole detection is required, a secondary classifier or post-processing would be needed
4. **Comparison**: Baseline also uses D40→pothole mapping, so comparison is fair

## Unmapped Classes

RDD2022 has no other classes beyond D00, D10, D20, D40.
No unmapped classes exist.

## Compatibility Assessment

| Criterion | Assessment |
|-----------|------------|
| Class count match | ✅ 4 source classes → 4 project classes |
| Semantic match (D00, D10, D20) | ✅ HIGH |
| Semantic match (D40) | ⚠️ MEDIUM (broader semantics) |
| Annotation format | Pascal VOC XML → requires conversion to YOLO |
| Coordinate convention | Pascal VOC [xmin, ymin, xmax, ymax] → project pixel format [x1, y1, x2, y2] (compatible) |
| License | ✅ CC BY 4.0 |

## Conclusion

Taxonomy is **compatible** for Experiment 2 with the caveat that the pothole class (ID 3) corresponds to CRDDC D40 "Other Corruption" rather than strictly "pothole".
This is identical to the baseline's mapping, so no new semantic mismatch is introduced.
The mapping is consistent, documented, and auditable.