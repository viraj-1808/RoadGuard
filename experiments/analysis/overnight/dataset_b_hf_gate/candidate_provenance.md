# Dataset B Provenance

## Acquisition Status

Acquired via Hugging Face Hub:
- **Repository**: `dronefreak/RDD2022`
- **Revision**: `d597e2962458f7242a72aaa1b7909118d40f5d29`
- **Method**: Hugging Face Hub download (`snapshot_download` + `load_from_disk`)
- **Data format**: Arrow format (Hugging Face `datasets` library)
- **Local path**: `experiments/dataset/raw_hf_rdd2022/`
- **Download timestamp**: 2026-09-30 (based on directory metadata)

## Provenance Chain

### Hop 1: Official RDD2022 Release
- **Authors**: Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal, Yoshihide Sekimoto
- **Institutions**: University of Tokyo and collaborators
- **Paper**: arXiv:2209.08538
- **Official repository**: https://github.com/sekilab/RoadDamageDetector
- **Original format**: Per-country Pascal-VOC XML annotations
- **Release context**: Crowdsensing-based Road Damage Detection Challenge (CRDDC'2022)

### Hop 2: RDD_SPLIT YOLO Conversion
- **Format change**: Pascal-VOC XML → YOLO .txt format
- **Structural change**: Merged six national subsets into single train/val/test split
- **Split**: 70/15/15 (26,869 / 5,758 / 5,758 images)
- **Source**: The official RDD2022 release converted to YOLO format

### Hop 3: dronefreak/RDD2022 (this candidate)
- **Repository**: `dronefreak/RDD2022`
- **License**: CC BY-SA 4.0 (same as original)
- **Changes from RDD_SPLIT**:
  1. Reduced to 4-class CRDDC2022 taxonomy (dropped class 4: "other")
  2. Reorganized into canonical COCO JSON + YOLO .txt layout
  3. No image pixel content modified
  4. No splits changed relative to RDD_SPLIT
  5. Degenerate zero-area boxes skipped (<5 per split)

## License

**CC BY-SA 4.0** (Creative Commons Attribution-ShareAlike 4.0 International)

- **Commercial use**: Permitted (with attribution + share-alike)
- **Attribution**: Required (original authors: Arya, Maeda, Ghosh, Toshniwal, Sekimoto)
- **Share-alike**: Required (any derivative work must be distributed under CC BY-SA 4.0)

## Dataset Card Content (abbreviated)

> RDD2022 is a multi-national street-level road-damage detection benchmark: 47,420 road images from six countries (Japan, India, the Czech Republic, Norway, the United States, and China), captured with vehicle-mounted smartphones, dashboard cameras, and drones, and annotated for pavement distress.

> This export covers the publicly-labelled portion of RDD2022 (38,385 images — the official train release), merged across all six countries and re-split into train/val/test. It keeps the four damage types scored by the CRDDC2022 challenge.

> Roughly one third of images have no in-taxonomy damage and are kept with an empty label file — consistent with the source data (clean-road frames).

## Important Disclaimer

> This repository is not an official release of the RDD2022 dataset.
> RDD2022 was created by Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal, and Yoshihide Sekimoto...
> The original authors and contributing institutions retain all copyright and intellectual property rights.

## Provenance Verification

- ✅ Source traced to official RDD2022 (arXiv:2209.08538)
- ✅ Original authors credited (Arya, Maeda, Ghosh, Toshniwal, Sekimoto)
- ✅ License documented (CC BY-SA 4.0)
- ✅ Two-hop provenance chain verifiable
- ✅ Dataset card includes disclaimer (not official release)
- ⚠️ Unofficial redistribution (not the official release)

## Conclusion

Provenance is **sufficiently clear** for Experiment 2. The dataset traces back to the official RDD2022 release through two verifiable hops, with proper attribution to original authors. The license is documented and compatible with research use.