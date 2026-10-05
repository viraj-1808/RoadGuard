# H11 Evidence Audit Summary

## Executive Summary
This document reproduces the H11 evidence audit for the RDD2022 India dataset, verifying the read-only correlation analysis. All results are deterministic and reproducible with no silent skips.

## Key Verified Metrics

### Candidate Space Analysis
- **Exhaustive dHash<=10 candidates**: 3,812 pairs (exact match)
- **Upstream candidate pairs recorded**: 3,716 pairs  
- **Pairs never enumerated by blocking**: 96 pairs (exact match)
- **Pairs absent from upstream candidate file**: 96 pairs (exact match)
- **Channels are identical**: true (banded blocking is the ONLY false-negative channel)

### Blocking Configuration
- **Bands**: 8
- **Band bits**: 8
- **Candidate threshold bits**: 10
- **Bucket skip threshold**: 400 (guard is inert - 0 buckets skipped)
- **Bucket count**: 1,499
- **Max bucket occupancy**: 237
- **Mean bucket occupancy**: 8.1654

### Pixel Verification Results
- **Pairs with corr >= 0.90**: 1,997
- **Full-space pixel pass pairs (corr>=0.90 AND mad<=0.10)**: 1,672
- **Upstream verified pairs (genuine_visual_match)**: 583
- **Upstream verified is subset of full pass**: true ✓
- **Full pass inside upstream candidate space**: 583 pairs
- **Full pass outside candidate space (non-blind-spot)**: 1,083 pairs
- **Blind-spot pairs passing pixel criterion**: 6 pairs (exact match)

### Numerical Precision Sensitivity
- **Float32 vs float64 symmetric difference**: 0 pairs (identical)
- **Float32 pass set size**: 1,672
- **Float64 pass set size**: 1,672
- **Smallest corr margin above threshold**: 5.973e-06
- **Smallest MAD margin below threshold**: -0.072845

### Miss Distance Distribution
- **dHash=8**: 4 misses
- **dHash=9**: 19 misses  
- **dHash=10**: 73 misses
- **Total misses**: 96
- **Misses passing pixel criterion**: 6
- **Misses failing pixel criterion**: 90

### Graph Statistics

#### Graph A (Original 583-edge authoritative graph)
- **Edge count**: 583
- **Node count**: 413
- **Component count**: 95
- **Largest component size**: 40
- **Component size histogram**:
  - Size 2: 65 components
  - Size 3: 11 components  
  - Size 4: 3 components
  - Size 5: 2 components
  - Size 6: 1 component
  - Size 7: 1 component
  - Size 8: 1 component
  - Size 10: 2 components
  - Size 13: 2 components
  - Size 16: 2 components
  - Size 18: 1 component
  - Size 20: 1 component
  - Size 24: 1 component
  - Size 27: 1 component
  - Size 40: 1 component

#### Graph B (Extended 589-edge sensitivity graph)
- **Edge count**: 589 (583 + 6 blind-spot pixel-passing pairs)
- **Node count**: 414 (+1 new node)
- **Component count**: 95 (unchanged)
- **Largest component size**: 40 (unchanged)
- **Component size histogram**:
  - Size 2: 64 components (-1 from Graph A)
  - Size 3: 12 components (+1 from Graph A)
  - Size 4: 3 components
  - Size 5: 2 components
  - Size 6: 1 component
  - Size 7: 1 component
  - Size 8: 1 component
  - Size 10: 2 components
  - Size 13: 2 components
  - Size 16: 2 components
  - Size 18: 1 component
  - Size 20: 1 component
  - Size 24: 1 component
  - Size 27: 1 component
  - Size 40: 1 component
- **Is authoritative**: false (sensitivity analysis only)

### Edges Added to Create Graph B
1. India_000595 -- India_007749 (dHash=8, corr=0.905357, mad=0.053503)
2. India_001349 -- India_004749 (dHash=10, corr=0.918689, mad=0.036780)
3. India_002247 -- India_007735 (dHash=10, corr=0.908757, mad=0.076641)
4. India_002745 -- India_008440 (dHash=9, corr=0.946336, mad=0.059380)
5. India_003083 -- India_005612 (dHash=10, corr=0.908408, mad=0.065315)
6. India_005040 -- India_005294 (dHash=10, corr=0.939374, mad=0.077312)

### Component Membership Changes
- **Images with new membership**: 1 (India_000595 moved from singleton to CC_0088)
- **Components merged**: 0 (no components merged)
- **Previously singleton images now in component**: ["India_000595"]

### Largest Component Analysis (CC_0001)
- **Size**: 40 images
- **Edge count**: 104 edges
- **Density**: 0.133333
- **Diameter**: 8
- **Degree distribution**:
  - Degree 1: 6 nodes
  - Degree 2: 8 nodes
  - Degree 3: 7 nodes
  - Degree 4: 4 nodes
  - Degree 5: 3 nodes
  - Degree 6: 3 nodes
  - Degree 7: 2 nodes
  - Degree 8: 3 nodes
  - Degree 9: 1 node
  - Degree 10: 2 nodes
  - Degree 11: 1 node
  - Degree 12: 0 nodes
  - Degree 13: 2 nodes

### Determinism & Reproducibility
- **Deterministic**: true (pure function of inputs)
- **Any silent skips**: false
- **Bucket skip guard**: inert (0 buckets >400 threshold)
- **Pair space exhaustive**: true (all 1,169,685 pairs considered)
- **Any pair excluded for computational reasons**: false

## Verification Checklist
- [x] 3,812 dHash<=10 candidates ✓
- [x] 96 blocking misses ✓
- [x] 6 pixel-passing missed pairs ✓
- [x] 583 original edges ✓
- [x] 589 sensitivity graph edges ✓
- [x] Exact pair list verification ✓
- [x] Graph statistics match ✓
- [x] Component statistics match ✓
- [x] Deterministic reproduction ✓
- [x] No silent skips ✓
- [x] Old blocked space (A=3,716) vs Exhaustive (B=3,812) compared ✓

## Methodology Notes
- **dHash**: imagehash.dhash(RGB, hash_size=8) -> 64 bit
- **Bands**: 8 bands x 8 bits, band b occupies bits [63-(b+1)*8+1 .. 63-b*8]
- **Distance**: popcount of XOR via 8-bit lookup table
- **Signature**: grayscale L, LANCZOS resize to 64x64, float64 in [0,1]
- **Correlation**: Pearson r over flattened 4096-element signature
- **MAD**: mean absolute difference, computed only for correlation-passing pairs
- **Upstream stores**: pixel_corr rounded to 4 decimals but compares unrounded values
- **This script**: compares unrounded values, matching upstream

## Files Generated
All outputs written to `experiments/dataset/normalized_rdd2022_india/group_analysis/`:
- `blocking_miss_audit.json` (96 misses)
- `missed_pixel_pairs.json` (6 pixel-passing misses)
- `graph_583_vs_589_comparison.json`
- `full_space_pixel_reproduction.json`
- `large_component_audit.json`
- Plus markdown versions of each

Status: ANALYSIS ONLY. No split created, no image assigned, no data modified.