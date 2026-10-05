# Label Ordering Verification Report — Experiment 2 Dataset B

**Date**: 2026-10-02  
**Objective**: Empirically verify the load-bearing assumption in `scripts/experiment2/convert_arrow_to_yolo.py` that the Hugging Face repo's on-disk `.txt` YOLO label files use the class ordering `0→D00 longitudinal_crack, 1→D10 transverse_crack, 2→D20 alligator_crack, 3→D40 pothole`.

**Verdict**: **CORRECT** — The assumption holds exactly. The repo `.txt` class ids match the Arrow `categories` ids index-by-index for every image examined.

---

## Evidence Summary

| Check | Scope | Result |
|-------|-------|--------|
| **Sequence agreement (class-id order)** | Test split, 200 random images (seed 42) | **200/200 = 100%** |
| | Train split, 500 random images (seed 42) | **500/500 = 100%** |
| **Multiset agreement (class-id bag)** | Test split, 200 random images | **200/200 = 100%** |
| | Train split, 500 random images | **500/500 = 100%** |
| **Full recount (all files)** | Test split (5,758 files) | **Exact match**: repo `{0:3925, 1:1675, 2:1537, 3:1587}` = Arrow `{0:3925, 1:1675, 2:1537, 3:1587}` |
| | Train split (26,869 files) | **Exact match**: repo `{0:18201, 1:8386, 2:7526, 3:7554}` = Arrow `{0:18201, 1:8386, 2:7526, 3:7554}` |
| | Validation split (5,758 files) | **Exact match**: repo `{0:3890, 1:1769, 2:1553, 3:1564}` = Arrow `{0:3890, 1:1769, 2:1553, 3:1564}` |
| **Class IDs outside {0,1,2,3}** | All splits, all 38,385 files | **Zero occurrences** |
| **BBox token-count consistency** | All splits, all 38,385 files | **Zero files** deviate from 5-token format (`class cx cy w h`) |
| **Empty vs absent label files** | All splits | Empty (valid negatives): train=8,967, valid=2,015, test=1,973. **Absent: 0** |
| **Geometry fidelity** (normalized cx,cy,w,h) | 150 images / 234 boxes across splits | Max abs deviation: cx≤1.88e-4, cy≤2.63e-4, w≤1.23e-4, h≤2.45e-4. **100% within 1e-3** |

---

## Key Numbers

- **Total images**: 38,385 (train 26,869 + valid 5,758 + test 5,758)
- **Total boxes**: 59,167 (train 41,667 + valid 8,776 + test 8,724)
- **Negative images (empty label)**: 12,955 (33.8%)
- **Class distribution (repo = Arrow)**:
  - Class 0 (D00 longitudinal_crack): 26,016
  - Class 1 (D10 transverse_crack): 11,830
  - Class 2 (D20 alligator_crack): 10,616
  - Class 3 (D40 pothole/other): 10,705

---

## Conclusion

The assumption in `convert_arrow_to_yolo.py` (lines 80-97) is **correct and verified**. The repo's on-disk `.txt` label files:
1. Use exactly the class ordering asserted in `TAXONOMY` and `RDD_CODE_BY_INDEX`
2. Contain no stray class IDs
3. Are perfectly consistent with the Arrow metadata in both class sequence and box geometry
4. Have 1:1 correspondence with images (no missing labels, no orphan labels)
5. Use standard 5-token YOLO format throughout

**No changes to `convert_arrow_to_yolo.py` are required.**