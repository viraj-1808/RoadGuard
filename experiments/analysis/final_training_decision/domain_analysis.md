# Dataset A vs Dataset B Domain Analysis

**Generated:** 2026-10-06

## Executive Summary

This analysis compares Dataset A (RDD2022 India subset, 1,530 images) and Dataset B (RDD2022 non-India, 22,020 images) across all available metadata and computed statistics.

---

## 1. Country/Source Distribution

| Dataset | Countries | Images | Source |
|---------|-----------|--------|--------|
| **Dataset A** | India only (Delhi, Gurugram, Haryana) | 1,530 | RDD2022 India subset (Kaggle derivative) |
| **Dataset B** | Japan, Czech Republic, Norway, USA, China | 22,020 | Hugging Face RDD2022 (non-India) |

**Status:** ESTABLISHED from dataset provenance

---

## 2. Camera/Viewpoint Characteristics

| Property | Dataset A | Dataset B |
|----------|-----------|-----------|
| Camera type | Smartphone dashcam | Smartphone dashcam (RDD2022 standard) |
| Viewpoint | Forward-facing vehicle camera | Forward-facing vehicle camera |
| Mounting | Dashboard/windshield | Dashboard/windshield |

**Status:** ESTABLISHED from RDD2022 documentation (both use same acquisition protocol)

---

## 3. Image Resolution & Aspect Ratio

| Property | Dataset A | Dataset B |
|----------|-----------|-----------|
| Primary resolution | 720×720 (100%) | 600×600 (41%), 640×640 (15%), 512×512 (13%), 4040×2035 (13%), 3643×2041 (9%) |
| Aspect ratio | 1.0 (square, 100%) | 1.0 (69%), ~2.0 wide (22%), other (9%) |
| Unique dimensions | 1 | 10 (train), 9 (val) |

**Status:** ESTABLISHED from computed image dimension statistics

---

## 4. Road Appearance / Urban-Rural / Lighting-Weather

| Property | Dataset A | Dataset B |
|----------|-----------|-----------|
| Road surface type | NOT AVAILABLE / NOT ESTABLISHED | NOT AVAILABLE / NOT ESTABLISHED |
| Urban vs rural | NOT AVAILABLE / NOT ESTABLISHED | NOT AVAILABLE / NOT ESTABLISHED |
| Lighting conditions | NOT AVAILABLE / NOT ESTABLISHED | NOT AVAILABLE / NOT ESTABLISHED |
| Weather conditions | NOT AVAILABLE / NOT ESTABLISHED | NOT AVAILABLE / NOT ESTABLISHED |
| Road texture appearance | NOT AVAILABLE / NOT ESTABLISHED | NOT AVAILABLE / NOT ESTABLISHED |

**Status:** NOT AVAILABLE / NOT ESTABLISHED — RDD2022 metadata does not contain these attributes in the available annotations

---

## 5. Damage Scale (Bounding Box Statistics)

### Normalized Coordinates (YOLO format)

| Subset | Width Mean | Height Mean | Area Mean (rel) |
|--------|------------|-------------|-----------------|
| Dataset A train | 0.2015 | 0.1213 | 3.55% |
| Dataset B train | 0.2138 | 0.1673 | 4.69% |

**Key finding:** Dataset B objects are on average **32% larger in relative area** and have **38% taller boxes** (height mean 0.1673 vs 0.1213).

### Pixel Coordinates (720×720 for A, various for B)

| Subset | Area Mean (px²) | Rel Area Mean |
|--------|-----------------|---------------|
| Dataset A train | 18,389 | 3.55% |
| Dataset B train | 27,771 | 4.69% |

**Status:** ESTABLISHED from computed statistics

---

## 6. Damage Appearance / Background Texture

| Property | Status |
|----------|--------|
| Damage visual appearance (crack width, pothole shape, edge characteristics) | NOT AVAILABLE / NOT ESTABLISHED |
| Background road texture variation | NOT AVAILABLE / NOT ESTABLISHED |
| Occlusion/clutter | NOT AVAILABLE / NOT ESTABLISHED |

**Reason:** No visual inspection or feature extraction was performed on the actual images; only metadata and bbox statistics are available.

---

## 7. Annotation Style

| Property | Dataset A | Dataset B |
|----------|-----------|-----------|
| Source format | Pascal VOC XML → converted to YOLO | Hugging Face RDD2022 (pre-converted) |
| Conversion tool | `scripts/analysis/transform_rdd2022_annotations.py` + `convert_to_yolo.py` | HF dataset download scripts |
| Class mapping | D00/D01→0, D10/D11→1, D20→2, D40→3, D43/D44/D50 excluded | Same 4-class mapping applied |
| Coordinate convention | YOLO normalized (cx, cy, w, h) | YOLO normalized (cx, cy, w, h) |

**Status:** ESTABLISHED from conversion pipeline documentation

---

## 8. Class Distribution Comparison

| Class | Dataset A (train) | Dataset B (train) | Ratio B/A |
|-------|-------------------|-------------------|-----------|
| Longitudinal crack (0) | 356 (11.7%) | 15,206 (41.8%) | **42.7×** |
| Transverse crack (1) | **21 (0.7%)** | **7,292 (20.1%)** | **347×** |
| Alligator crack (2) | 453 (14.9%) | 5,816 (16.0%) | 12.8× |
| Pothole (3) | 2,219 (72.8%) | 8,044 (22.1%) | 3.6× |

**Critical finding:** Dataset A has **extreme class imbalance** (pothole 106:1 vs transverse). Dataset B provides **balanced multi-class distribution** with 278× more transverse cracks.

---

## 9. Class-Specific Object-Size Distribution

### Transverse Crack (the critical class)
| Dataset | Very Small | Small | Medium | Large | Total |
|---------|------------|-------|--------|-------|-------|
| Dataset A train | 0.0% | 23.8% | 76.2% | 0.0% | 21 |
| Dataset B train | 3.4% | 44.4% | 49.2% | 3.1% | 7,292 |

**Key finding:** Dataset B provides **full size spectrum** including very small and large transverse cracks absent in Dataset A.

### Pothole
| Dataset | Very Small | Small | Medium | Large | Total |
|---------|------------|-------|--------|-------|-------|
| Dataset A train | 1.1% | 53.1% | 41.3% | 4.5% | 2,219 |
| Dataset B train | 3.2% | 38.4% | 38.6% | 19.8% | 8,044 |

**Key finding:** Dataset B has **4.4× more large potholes** (19.8% vs 4.5%) and more very small potholes.

### Longitudinal Crack
| Dataset | Very Small | Small | Medium | Large | Total |
|---------|------------|-------|--------|-------|-------|
| Dataset A train | 0.0% | 32.0% | 64.3% | 3.7% | 356 |
| Dataset B train | 11.5% | 35.9% | 48.2% | 4.4% | 15,206 |

**Key finding:** Dataset B has **substantial very small longitudinal cracks** (11.5%) absent in Dataset A.

### Alligator Crack
| Dataset | Very Small | Small | Medium | Large | Total |
|---------|------------|-------|--------|-------|-------|
| Dataset A train | 0.0% | 3.5% | 54.1% | 42.4% | 453 |
| Dataset B train | 0.5% | 6.7% | 50.1% | 42.7% | 5,816 |

**Key finding:** Similar size distribution, but Dataset B has 12.8× more samples.

---

## 10. Visual Characteristics Likely to Matter for Unseen Real-World Imagery

| Characteristic | Likely Matters? | Evidence |
|----------------|-----------------|----------|
| Forward-facing viewpoint | YES | Both datasets use this; matches deployment |
| Variable resolution/aspect | YES | Dataset B covers 600-4040px; real cameras vary |
| Diverse road surfaces | UNKNOWN | NOT ESTABLISHED |
| Diverse lighting/weather | UNKNOWN | NOT ESTABLISHED |
| Small/distant damage | YES | Dataset B has more very small objects |
| Large/close damage | YES | Dataset B has more large objects |
| Transverse crack appearance | CRITICAL | Dataset A has only 21; Dataset B has 7,292 |
| Class balance | YES | Dataset A 106:1 pothole:transverse ratio is pathological |

---

## 11. Domain Gap Summary

| Aspect | Domain Gap Severity | Impact on Deployment |
|--------|---------------------|----------------------|
| Resolution/aspect | MODERATE | Dataset B provides robustness to variable camera specs |
| Transverse crack coverage | **CRITICAL** | 347× more examples in B; A alone cannot learn this class |
| Pothole size diversity | MODERATE | B provides more large and very small potholes |
| Class balance | **CRITICAL** | A's extreme imbalance biases model toward pothole-only |
| Background diversity | UNKNOWN | NOT ESTABLISHED — likely improved by B's 5 countries |
| Annotation consistency | LOW | Same conversion pipeline applied |

---

## Conclusion

**Dataset B addresses the most critical deficiencies of Dataset A:**
1. **Transverse crack data scarcity** (347× increase)
2. **Extreme class imbalance** (106:1 → ~1:1)
3. **Limited object size diversity** (especially very small/large objects)
4. **Single-country/appearance bias** (India-only → 5 countries)

**However, key real-world factors remain UNKNOWN:**
- Road surface texture diversity
- Lighting/weather conditions
- Urban vs rural road types
- Night/low-light performance

The frozen India test evaluation shows a **68% mAP50-95 drop** from Dataset B validation (0.345) to India test (0.111), confirming significant domain shift that additional training on current data may not fully resolve.