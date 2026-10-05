# Taxonomy Audit

## Project Taxonomy (Locked)

| Project Class ID | Project Class Name |
|-----------------|---------------------|
| 0 | longitudinal_crack |
| 1 | transverse_crack |
| 2 | alligator_crack |
| 3 | pothole |

## RDD2022 Source Taxonomy

| Source Code | Source Name | Description |
|-------------|-------------|-------------|
| D00 | Longitudinal Crack | Longitudinal (wheel-path) crack |
| D10 | Transverse Crack | Transverse (lateral) crack |
| D20 | Alligator Crack | Alligator / fatigue crack |
| D40 | Pothole | Pothole |

## Class Mapping

| Source Code | Source Name | Project Class ID | Project Class Name | Confidence |
|-------------|-------------|------------------|-------------------|------------|
| D00 | Longitudinal Crack | 0 | longitudinal_crack | HIGH |
| D10 | Transverse Crack | 1 | transverse_crack | HIGH |
| D20 | Alligator Crack | 2 | alligator_crack | HIGH |
| D40 | Pothole | 3 | pothole | MEDIUM |

## D40 Semantic Caveat (Critical)

**D40 has broader "Other Corruption" semantics in the source CRDDC taxonomy.**

From the CRDDC2022 challenge documentation:
- D40 = "Other Corruption" — includes pothole, rutting, bump, separation
- This is NOT purely "pothole" — it's a broader damage category

**Our project maps D40 → pothole with a documented semantic-broadening caveat.**

This caveat is identical to the baseline's mapping and is preserved in Experiment 2.

## Candidate Dataset Taxonomy

The `dronefreak/RDD2022` dataset has already performed the 4-class reduction:
- Class 0: longitudinal_crack (D00)
- Class 1: transverse_crack (D10)
- Class 2: alligator_crack (D20)
- Class 3: pothole (D40)

**Class IDs match project taxonomy exactly (0-3).**

## Class ID Audit (from Arrow metadata)

| Split | Class IDs Found | Valid? |
|-------|-----------------|--------|
| train | [0, 1, 2, 3] | ✅ |
| validation | [0, 1, 2, 3] | ✅ |
| test | [0, 1, 2, 3] | ✅ |

**No unmapped class IDs found.** Class 4 ("other") was already dropped by the redistribution.

## data.yaml Verification

```yaml
nc: 4
names:
  0: longitudinal_crack
  1: transverse_crack
  2: alligator_crack
  3: pothole
```

**SHA256**: `49f3606a45dca2f83a175aeb8f5299e823f46e07172b2555b39d39a0d41f0828`

Matches project taxonomy exactly.

## Semantic Preservation

| Aspect | Assessment |
|--------|------------|
| D00→0 | ✅ Exact match (longitudinal crack) |
| D10→1 | ✅ Exact match (transverse crack) |
| D20→2 | ✅ Exact match (alligator crack) |
| D40→3 | ⚠️ **Semantic broadening** (D40 = "Other Corruption" including pothole, rutting, bump, separation) |
| Class 4 (other) | ✅ Dropped (not in candidate dataset) |

## Consistency with Baseline

The baseline Experiment 1 uses the SAME mapping (D40→pothole with caveat). Experiment 2 preserves this mapping — no new semantic mismatch is introduced.

## Taxonomy Compatibility Assessment

| Criterion | Status |
|-----------|--------|
| Class count matches (4) | ✅ PASS |
| Class names match | ✅ PASS |
| Class IDs match (0-3) | ✅ PASS |
| D40 caveat preserved | ✅ PASS |
| No new semantic issues | ✅ PASS |
| Overall taxonomy compatibility | **SUFFICIENTLY COMPATIBLE** |

## Conclusion

The candidate dataset's taxonomy is **sufficiently compatible** with the project taxonomy. The D40→pothole semantic broadening caveat is documented and preserved — identical to the baseline. No taxonomy modifications are needed for Experiment 2.

**Confidence: HIGH**