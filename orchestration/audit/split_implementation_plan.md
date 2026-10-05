# Deterministic Split Builder Specification

**Status**: DESIGN ONLY — No split created, no image assigned, no data modified.
**Inputs**: `experiments/dataset/normalized_rdd2022_india/` (1,530 images, 4,360 objects, 4 classes)
**Dependencies**: Agent C (Group Analysis — `group_analysis/correlation_graph.json`), Agent D (Validation — `validation_report.json`)

---

## 1. Atomic Unit Definition

**Definition**: An atomic unit is a connected component of the accepted correlation graph (Graph A: 583 verified pixel-matched edges, dHash ≤ 5, Pearson corr ≥ 0.9, MAD ≤ 0.1, complete linkage).

**Source**: `experiments/dataset/normalized_rdd2022_india/group_analysis/correlation_graph.json` → `graph` + `component_manifest`

**Counts**:
- Graph nodes: 413 images
- Graph edges: 583 (verified visual matches)
- Connected components: 95 (sizes 2–40)
- Singletons (images outside graph): 1,117 images
- Total atomic units: **1,212** (95 multi-image + 1,117 singletons)

**Rule**: No atomic unit may be split across train/val/test. All member images of a component receive the same split assignment.

**Rationale**: The 583 verified pairs represent genuine visual near-duplicates (583 vs ~10 expected by chance = 58× enrichment). Splitting them would constitute leakage.

---

## 2. Stratification Strategy

**Unit-level class-presence vector**: For each atomic unit, compute the set of classes present across its member images.

**Classes**: 0=longitudinal_crack, 1=transverse_crack, 2=alligator_crack, 3=pothole

**Strata**: Distinct class-presence combinations observed in the dataset (from `correlation_graph.json:dataset_statistics.class_presence_strata`):

| Stratum | Classes Present | Image Count |
|---------|----------------|-------------|
| S0 | {pothole} | 760 |
| S1 | {alligator_crack, pothole} | 380 |
| S2 | {longitudinal_crack, pothole} | 198 |
| S3 | {longitudinal_crack, alligator_crack, pothole} | 163 |
| S4 | {longitudinal_crack, transverse_crack, pothole} | 14 |
| S5 | {transverse_crack, pothole} | 9 |
| S6 | {longitudinal_crack, transverse_crack, alligator_crack, pothole} | 5 |
| S7 | {transverse_crack, alligator_crack, pothole} | 1 |

**Unit assignment to strata**: Each atomic unit inherits the union of class-presence across its members. Singletons map 1:1 to their image's stratum.

**Stratification objective**: Preserve stratum proportions in each split (±2% absolute tolerance per stratum per split).

---

## 3. Rare-Class Handling (transverse_crack — Class 1)

**Profile**: 30 objects / 29 images total. Distributed across 5 connected components:

| Component | Size | transverse_crack Images | % of Component |
|-----------|------|------------------------|----------------|
| CC_0049 | 2 | 1 | 50% |
| CC_0051 | 2 | 2 | 100% |
| CC_0016 | 5 | 1 | 20% |
| CC_0008 | 13 | 1 | 7.7% |
| CC_0091 | 2 | 1 | 50% |
| **Singletons** | 1,117 | 23 | — |

**Policy**: Soft proportional target per split unless impossible.

- **Target per split** (70/15/15 of 29 images): train=20, val=4, test=5 images containing transverse_crack
- **Constraint**: Atomic units containing transverse_crack must be assigned together
- **Feasibility**: The 6 multi-image units (5 components + 1 singleton with 2 objects) contain 6 transverse_crack images. The remaining 23 are singletons.
- **Algorithm**: Assign rare-class units first using deterministic priority (see §4), then fill remaining quota from singletons.

**Fallback**: If exact quota cannot be met due to atomicity, allow ±1 image deviation per split and record the shortfall in the manifest.

---

## 4. Deterministic Assignment Algorithm

### 4.1 Seed and Ordering

- **Master seed**: `SEED = 0x52444432_32303232` (ASCII "RDD2022" as u64, little-endian)
- **Per-unit sort key**: `hash = SipHash-2-4(SEED, unit_id)` where `unit_id` is:
  - For components: `CC_XXXX` (zero-padded 4-digit from `component_manifest`)
  - For singletons: `IMG_XXXXXXXX` (image stem, e.g., `India_000005`)

**Rationale**: SipHash provides deterministic pseudorandom permutation without crypto dependencies. Unit IDs are stable across runs.

### 4.2 Assignment Procedure

```python
def assign_splits(units, seed=SEED, ratios=(0.70, 0.15, 0.15), strata_targets=None):
    # units: list of {unit_id, member_images, class_presence_set, size}
    # strata_targets: {stratum: {train: n, val: n, test: n}} (optional soft targets)
    
    # 1. Sort units by SipHash(seed, unit_id)
    units_sorted = sorted(units, key=lambda u: siphash24(seed, u['unit_id']))
    
    # 2. Initialize split quotas from ratios * total_images
    total_images = sum(u['size'] for u in units)
    quotas = {split: int(ratio * total_images) for split, ratio in zip(('train','val','test'), ratios)}
    
    # 3. Initialize stratum quotas (proportional to dataset stratum counts)
    stratum_counts = Counter(u['stratum'] for u in units for _ in range(u['size']))
    stratum_quotas = {
        split: {stratum: int(count * ratios[i]) for stratum, count in stratum_counts.items()}
        for i, split in enumerate(('train','val','test'))
    }
    
    # 4. Assign units in sorted order
    assignments = {}
    remaining_quotas = {split: quotas[split] for split in quotas}
    remaining_stratum = {split: dict(stratum_quotas[split]) for split in stratum_quotas}
    
    for unit in units_sorted:
        # Determine feasible splits (those with sufficient quota for unit.size)
        feasible = [s for s in ('train','val','test') if remaining_quotas[s] >= unit['size']]
        
        # Among feasible, prefer split that most improves stratum balance
        def stratum_score(split):
            return sum(
                max(0, remaining_stratum[split].get(strat, 0) - unit['stratum_count'].get(strat, 0))
                for strat in unit['stratum_count']
            )
        
        chosen = max(feasible, key=stratum_score) if feasible else 'train'  # fallback
        
        assignments[unit['unit_id']] = chosen
        remaining_quotas[chosen] -= unit['size']
        for strat, cnt in unit['stratum_count'].items():
            remaining_stratum[chosen][strat] = max(0, remaining_stratum[chosen].get(strat, 0) - cnt)
    
    return assignments
```

### 4.3 Rare-Class Priority (Pre-pass)

Before main assignment, identify all units containing transverse_crack (class 1). Assign these first using the same deterministic ordering but with a **rare-class-aware score**:

```python
def rare_class_score(split, unit):
    # Prefer splits that need more rare-class images
    need = rare_quota_remaining[split]  # target - assigned_so_far
    has_rare = 1 if unit['has_transverse_crack'] else 0
    return need * has_rare * 1000 + stratum_score(split)
```

This ensures rare-class units are placed to satisfy soft targets before general population.

---

## 5. Bounded Swap Improvement Procedure

After initial deterministic assignment, perform a bounded local search to improve stratum balance without violating atomicity or rare-class targets.

### 5.1 Swap Definition

A **valid swap** exchanges the split assignments of two units `u1`, `u2` iff:
1. `u1.split != u2.split`
2. `size(u1) == size(u2)` (exact size match — preserves split totals exactly)
3. Neither unit contains transverse_crack, OR both do (preserves rare-class balance)
4. After swap, all stratum counts remain within ±2% of proportional targets

### 5.2 Search Algorithm

```python
def bounded_swap_improvement(assignments, units, max_iterations=1000):
    unit_by_id = {u['unit_id']: u for u in units}
    current = dict(assignments)
    
    # Compute initial imbalance score
    def imbalance_score(assign):
        score = 0
        for split in ('train','val','test'):
            for stratum in all_strata:
                target = stratum_quotas[split][stratum]
                actual = sum(
                    unit_by_id[uid]['stratum_count'].get(stratum, 0)
                    for uid, s in assign.items() if s == split
                )
                score += abs(actual - target)
        return score
    
    best_score = imbalance_score(current)
    best_assign = dict(current)
    
    for _ in range(max_iterations):
        # Find all valid swap pairs
        candidates = []
        for u1_id, u2_id in combinations(current.keys(), 2):
            if current[u1_id] == current[u2_id]:
                continue
            u1, u2 = unit_by_id[u1_id], unit_by_id[u2_id]
            if u1['size'] != u2['size']:
                continue
            if u1['has_transverse_crack'] != u2['has_transverse_crack']:
                continue
            # Test swap
            test = dict(current)
            test[u1_id], test[u2_id] = test[u2_id], test[u1_id]
            if all_strata_within_tolerance(test):
                candidates.append((u1_id, u2_id, imbalance_score(test)))
        
        if not candidates:
            break
        
        # Take best improving swap
        candidates.sort(key=lambda x: x[2])
        if candidates[0][2] < best_score:
            u1_id, u2_id, _ = candidates[0]
            current[u1_id], current[u2_id] = current[u2_id], current[u1_id]
            best_score = candidates[0][2]
            best_assign = dict(current)
        else:
            break
    
    return best_assign, best_score
```

### 5.3 Bounds

- **Max iterations**: 1,000
- **Size-matching only**: Prevents split total drift
- **No rare-class crossing**: Transverse_crack units only swap with other transverse_crack units of same size
- **Deterministic**: Iterate pairs in lexicographic order of `(u1_id, u2_id)`

---

## 6. Manifest Schema (split_manifest.json)

```json
{
  "split_version": "1.0.0",
  "dataset": {
    "identifier": "RDD2022_CRDDC_India",
    "version": "CRDDC'2022",
    "normalized_path": "experiments/dataset/normalized_rdd2022_india",
    "total_images": 1530,
    "total_objects": 4360
  },
  "split_ratios": {"train": 0.70, "val": 0.15, "test": 0.15},
  "atomicity": {
    "rule": "connected_components_of_accepted_graph",
    "graph_edge_count": 583,
    "graph_node_count": 413,
    "component_count": 95,
    "singleton_count": 1117,
    "total_atomic_units": 1212
  },
  "stratification": {
    "method": "class_presence_strata",
    "strata": {
      "pothole_only": {"train": 532, "val": 114, "test": 114},
      "alligator_crack+pothole": {"train": 266, "val": 57, "test": 57},
      "longitudinal_crack+pothole": {"train": 139, "val": 30, "test": 29},
      "longitudinal_crack+alligator_crack+pothole": {"train": 114, "val": 24, "test": 25},
      "longitudinal_crack+transverse_crack+pothole": {"train": 10, "val": 2, "test": 2},
      "transverse_crack+pothole": {"train": 6, "val": 2, "test": 1},
      "all_four_classes": {"train": 4, "val": 1, "test": 0},
      "transverse_crack+alligator_crack+pothole": {"train": 1, "val": 0, "test": 0}
    },
    "tolerance_pct": 2.0
  },
  "rare_class": {
    "class": "transverse_crack",
    "total_images": 29,
    "total_objects": 30,
    "target_per_split": {"train": 20, "val": 4, "test": 5},
    "achieved_per_split": {"train": 20, "val": 4, "test": 5},
    "units_with_class": 6,
    "assignment_method": "priority_prepass_then_proportional"
  },
  "assignments": {
    "CC_0001": "train",
    "CC_0002": "val",
    "...": "...",
    "India_000005": "train",
    "India_000017": "test"
  },
  "split_statistics": {
    "train": {"images": 1071, "objects": 3052, "class_counts": {...}},
    "val": {"images": 230, "objects": 654, "class_counts": {...}},
    "test": {"images": 229, "objects": 654, "class_counts": {...}}
  },
  "validation": {
    "atomicity_verified": true,
    "strata_within_tolerance": true,
    "rare_class_targets_met": true,
    "split_totals_match_ratios": true,
    "no_image_duplicate_across_splits": true,
    "checksum": "sha256_of_assignments_json"
  },
  "reproducibility": {
    "seed": "0x52444432_32303232",
    "algorithm": "SipHash-2-4 + bounded_swap",
    "swap_iterations": 847,
    "final_imbalance_score": 12
  }
}
```

**Output path**: `experiments/dataset/normalized_rdd2022_india/split_manifest.json`

---

## 7. Validation Checklist

The split builder MUST produce a manifest that passes all checks:

| Check | Description | Pass Criteria |
|-------|-------------|---------------|
| **V1 Atomicity** | No connected component crosses splits | All members of each CC_XXXX have same split |
| **V2 Split Ratios** | Image counts match 70/15/15 ±1 | `abs(actual - expected) <= 1` per split |
| **V3 Strata Balance** | Each stratum within ±2% of proportional target | `abs(actual_pct - target_pct) <= 2.0` |
| **V4 Rare Class** | Transverse_crack images per split meet soft target ±1 | `abs(actual - target) <= 1` |
| **V5 No Duplicates** | No image appears in more than one split | Set intersections are empty |
| **V6 Coverage** | All 1,530 images assigned exactly once | `sum(split_counts) == 1530` |
| **V7 Determinism** | Rerun with same seed produces identical manifest | Byte-identical JSON |
| **V8 Checksum** | Manifest includes SHA-256 of assignments | Verifiable independently |

---

## 8. Split Ratio Specification

| Split | Ratio | Target Images | Tolerance |
|-------|-------|---------------|-----------|
| train | 0.70 | 1,071 | ±1 |
| val | 0.15 | 230 | ±1 |
| test | 0.15 | 229 | ±1 |

**Note**: 1,530 × 0.70 = 1,071.0; 1,530 × 0.15 = 229.5 → val=230, test=229 (round val up, test down).

---

## 9. Edge Cases and Fallback Rules

| Scenario | Rule |
|----------|------|
| **Largest component (40 images) exceeds val/test quota** | Assign to train; val/test quotas satisfied from smaller units |
| **Rare-class unit too large for remaining val/test quota** | Assign to train; record shortfall; compensate from singletons |
| **Stratum quota exhausted for a split** | Assign to next-best split; track deviation in manifest |
| **No valid swap improves balance** | Terminate early; report final imbalance score |
| **Singleton with rare class but val/test full** | Assign to train; val/test get other rare-class singletons |
| **Rerun produces different result** | FAIL — determinism violation (V7) |

---

## 10. Dependencies on Agent C/D Outputs

| Dependency | Source | Used For |
|------------|--------|----------|
| `correlation_graph.json` | Agent C (`analysis/analyze_correlation_graph.py`) | Atomic units (CC_XXXX), class-presence strata, rare-class component mapping |
| `near_duplicate_verification.json` | Agent C (`analysis/verify_near_duplicates.py`) | Verification that accepted graph edges are pixel-verified |
| `h11_evidence.json` | Agent C (`analysis/audit_h11_evidence_scope.py`) | Confirmation that Graph A (583 edges) is authoritative |
| `validation_report.json` | Agent D (`analysis/validate_transformation.py`) | Confirmation that normalized dataset is invariant-valid |
| `manifest.json` | Agent C/D shared | Per-image class counts, checksums, paths |

**Required before split execution**: All above files must exist and have `overall_status: PASS` (validation) or `purpose: "Analysis only"` (group analysis).

---

## 11. Implementation Checklist (for Agent F)

- [ ] Read `correlation_graph.json` → build atomic units (95 CCs + 1,117 singletons)
- [ ] Compute per-unit class-presence stratum
- [ ] Compute per-unit rare-class flag and count
- [ ] Run deterministic assignment (SipHash seed + stratum scoring)
- [ ] Run bounded swap improvement (max 1,000 iterations, size-matched only)
- [ ] Validate against checklist V1–V8
- [ ] Write `split_manifest.json` with full schema
- [ ] Verify byte-identical rerun

---

## 12. Reproducibility Guarantee

Given identical:
- `correlation_graph.json` (SHA-256 verified)
- `manifest.json` (SHA-256 verified)
- Master seed `0x52444432_32303232`
- Algorithm version `1.0.0`

**The split manifest will be byte-identical across all runs, machines, and Python versions.**

---

*End of specification. This document is the contract for split implementation. No code executed; no data modified.*