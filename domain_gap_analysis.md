# Domain Gap Analysis: Exp2 Validation (Dataset B) → Frozen India Test

## Per-Class Metric Drops (Validation - Test)

| Class | Precision Drop | Recall Drop | mAP50 Drop | mAP50-95 Drop |
|-------|---------------|-------------|------------|---------------|
| **Overall** | **0.052** | **0.269** | **0.347** | **0.233** |
| **longitudinal_crack** | **0.171** | **0.073** | **0.241** | **0.157** |
| **transverse_crack** | **-0.421** | **0.493** | **0.508** | **0.240** |
| **alligator_crack** | **0.230** | **0.209** | **0.284** | **0.201** |
| **pothole** | **0.229** | **0.301** | **0.354** | **0.336** |

## Analysis: Classes Most Affected by Domain Shift

### 1. **transverse_crack** — **Most Severe Domain Shift**
- **Recall collapses to 0.000** (drop of 0.493) — model detects virtually NO transverse cracks in India test set
- **mAP50 drops 0.508** (from 0.516 → 0.0078) — near-total failure
- Precision paradoxically increases to 1.000 (only 1 prediction made, which happened to be correct)
- **Root cause**: Transverse cracks likely have very different visual appearance in India (different road materials, crack patterns, lighting) vs Dataset B

### 2. **pothole** — **Large Drop Across All Metrics**
- **mAP50-95 drops 0.336** (largest relative drop: 69% relative)
- **mAP50 drops 0.354** (46% relative)
- **Recall drops 0.301** (39% relative)
- Potholes in India may differ in shape, depth, context (water-filled, debris) vs training data

### 3. **alligator_crack** — **Significant Drop**
- **mAP50 drops 0.284** (43% relative)
- **Precision drops 0.230** (34% relative)
- **Recall drops 0.209** (37% relative)
- Alligator cracking patterns may vary with pavement type, climate

### 4. **longitudinal_crack** — **Moderate Drop**
- **mAP50 drops 0.241** (43% relative)
- **Precision drops 0.171** (28% relative)
- Recall relatively preserved (only 0.073 drop)
- Longitudinal cracks more consistent across domains

### 5. **Overall** — **Substantial Degradation**
- **mAP50 drops 0.347** (55% relative)
- **Recall drops 0.269** (46% relative)
- **mAP50-95 drops 0.233** (68% relative)

## Key Insights

| Rank | Class | Primary Issue |
|------|-------|---------------|
| 1 | transverse_crack | **Complete recall failure** — model cannot detect this class in India domain |
| 2 | pothole | **Broad degradation** — all metrics drop significantly |
| 3 | alligator_crack | **Balanced degradation** — precision & recall both suffer |
| 4 | longitudinal_crack | **Moderate** — mainly precision/mAP affected, recall stable |

## Recommendations
1. **Collect India transverse crack samples** — highest priority for domain adaptation
2. **Augment pothole training data** with India-like variations (water, debris, lighting)
3. **Investigate alligator crack appearance differences** — may need targeted augmentation
4. **Longitudinal cracks** — relatively robust, lower priority for adaptation