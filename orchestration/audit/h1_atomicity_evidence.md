# H1 Atomicity Evidence — Agent D

## Executive Summary

**Status**: READ-ONLY evidence collection — no decisions made
**Agent**: D (Connected-Component / H1 Atomicity Audit)
**Timestamp**: 2026-09-27

---

## Graph Definition

- **Nodes**: 413 images (with ≥1 verified pixel edge)
- **Edges**: 583 verified pixel-matches (genuine_visual_match == true)
- **Singletons**: 1,117 images outside graph
- **Total atomic units**: 1,212 (95 multi-image + 1,117 singletons)

---

## Component Size Distribution

| Size | Count | Cumulative Images |
|------|-------|-------------------|
| 2 | 65 | 130 |
| 3 | 11 | 163 |
| 4 | 3 | 175 |
| 5 | 2 | 185 |
| 6 | 1 | 191 |
| 7 | 1 | 198 |
| 8 | 1 | 206 |
| 10 | 2 | 226 |
| 13 | 2 | 252 |
| 16 | 2 | 284 |
| 18 | 1 | 302 |
| 20 | 1 | 322 |
| 24 | 1 | 346 |
| 27 | 1 | 373 |
| 40 | 1 | 413 |

**Total**: 95 components, 413 nodes, 583 edges

---

## 40-Image Component Analysis (CC_0001)

### Structural Properties
- **Size**: 40 images
- **Edges**: 104 internal edges
- **Density**: 0.133 (sparse)
- **Diameter**: 8 (long chains)
- **Degree histogram**: 6 nodes degree=1, 8 nodes degree=2, 3 nodes degree=3, 3 nodes degree=4, 2 nodes degree=5, 3 nodes degree=6, 4 nodes degree=7, 3 nodes degree=8, 2 nodes degree=9, 2 nodes degree=10, 1 node degree=11, 1 node degree=12, 1 node degree=13

### Tarjan Analysis
- **Bridges**: 7 bridges (India_000439↔India_000579, India_000439↔India_001550, India_000557↔India_008670, India_001247↔India_001338, India_001550↔India_001552, India_001550↔India_004331, India_007578↔India_008209)
- **Articulation points**: 5 (India_000439, India_001247, India_001550, India_008209, India_008670)
- **Biconnected components**: 8 (largest: 33 nodes)
- **2-edge-connected**: NO
- **2-vertex-connected**: NO

### Core Decomposition
- **Max core number**: 5
- **Core-5 nodes**: 19 (India_001247, India_001527, India_001550, India_002549, India_002696, India_003083, India_003565, India_003993, India_004695, India_005701, India_005870, India_006362, India_006672, India_007204, India_008249, India_008301, India_008826, India_008860, India_009171)
- **Core-1 nodes**: 7 (peripheral nodes)

### Class Presence
- alligator_crack+pothole: 21 images
- longitudinal_crack+alligator_crack+pothole: 9 images
- longitudinal_crack+pothole: 3 images
- pothole: 7 images
- **Rare class (transverse_crack)**: 0 images in this component

### Structural Classification: **dominant_block_with_bridges**
- A large cohesive core (19 nodes, core number 5) with peripheral chains connected via bridges
- NOT a dense clique, NOT a pure chain — hybrid structure

---

## All Component Shapes

| Component ID | Size | Density | Bridges | Articulation | Biconnected | Shape | Rare Class |
|-------------|------|---------|---------|--------------|-------------|-------|------------|
| CC_0001 | 40 | 0.133 | 7 | 5 | 8 | dominant_block_with_bridges | 0 |
| CC_0002 | 27 | 0.154 | 3 | 5 | 6 | dominant_block_with_bridges | 0 |
| CC_0003 | 24 | 0.203 | 5 | 6 | 7 | dominant_block_with_bridges | 0 |
| CC_0004 | 20 | 0.284 | 4 | 4 | 5 | dominant_block_with_bridges | 0 |
| CC_0005 | 18 | 0.196 | 4 | 5 | 7 | multi_block | 0 |
| CC_0006 | 16 | 0.408 | 4 | 4 | 5 | dominant_block_with_bridges | 0 |
| CC_0007 | 16 | 0.192 | 5 | 5 | 7 | dominant_block_with_bridges | 0 |
| CC_0008 | 13 | 0.282 | 6 | 6 | 7 | dominant_block_with_bridges | 1 |
| CC_0009 | 13 | 0.397 | 0 | 0 | 1 | **cohesive_block** | 0 |
| CC_0010 | 10 | 0.444 | 2 | 2 | 3 | multi_block | 0 |
| CC_0011+ | ≤8 | — | — | — | — | various | — |

---

## Rare-Class (transverse_crack) Impact

- **Total transverse_crack images**: 29 (across all 1,530 images)
- **Components containing transverse_crack**: CC_0008 has 1 transverse_crack image (1 object)
- **Rare class distribution**: Only 1 of 95 components contains transverse_crack
- **Impact**: If CC_0008 (13 images) is split across train/val/test, the rare class distribution is violated
- **Recommendation**: CC_0008 must stay in ONE split as an atomic unit

---

## Graph Density Analysis

| Metric | Value |
|--------|-------|
| Graph edges | 583 |
| Graph nodes | 413 |
| Max possible edges | 85,146 |
| Actual density | 0.000685 |
| Average degree | 2.82 |
| Median degree | 1 |
| Max degree | 13 |

**Interpretation**: Very sparse graph. Edges represent verified visual near-duplicates, not general similarity. A component of size N with E edges has E/(N*(N-1)/2) density.

---

## Chain Sensitivity

| dHash threshold | Edges | Largest component |
|----------------|-------|-------------------|
| ≤5 | ~200 | ~11 |
| ≤8 | ~350 | ~25 |
| ≤10 | 583 | 40 |

As weaker edges are admitted, the largest component grows from 11→25→40. The 40-image component is driven by edges at dHash 8-10 (weaker evidence).

---

## Evidence, Not Decisions

**This evidence describes the graph structure. It does NOT decide that connected components are the correct atomic unit.**

### Key Questions for Orchestrator

1. **Is the 40-image component too large to split?** Yes — it must stay together as an atomic unit under any connected-component scheme.
2. **Is the component too dense to be a "source video"?** Density 0.133 is low — it is NOT a clique. It is a chain-like structure with a dominant block.
3. **Should the 40-image component be treated as one atomic unit?** The evidence supports this: all 583 verified pairs must stay together, and CC_0001 contains 104 verified pairs.
4. **Is the rare-class impact acceptable?** Only 1 of 95 components contains transverse_crack (13 images). This is manageable with stratified assignment.

### Provisional H1 Default

**H1 = connected components of the accepted 583-edge graph**
- 1,212 atomic units (95 multi-image + 1,117 singletons)
- No atomic unit crossing splits
- Rare-class component (CC_0008) must stay together

**STATUS**: PROVISIONAL — PENDING HUMAN REVIEW

---

## Limitations (Explicit)

- Connected components describe detected visual-correlation relationships, NOT source-video groups
- No sequence/video/timestamp metadata exists for this artifact
- Residual source-level leakage risk is unquantifiable
- The 40-image component's internal structure (bridges, articulation points) suggests it is NOT a single capture event
- Singletons are NOT proven independent
