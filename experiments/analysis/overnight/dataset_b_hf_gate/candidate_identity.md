# Dataset B Candidate Identity

## Candidate Dataset Identification

| Field | Value |
|-------|-------|
| **Repository** | `dronefreak/RDD2022` |
| **Revision/Commit Hash** | `d597e2962458f7242a72aaa1b7909118d40f5d29` |
| **Download Method** | Hugging Face Hub via `snapshot_download` + `load_from_disk` |
| **Local Path** | `experiments/dataset/raw_hf_rdd2022/` |
| **File Format** | Arrow format (`.arrow` files) for metadata/annotations |
| **Storage System** | Uses Hugging Face Xet storage system |
| **Dataset Type** | Hugging Face DatasetDict |

## License

| Field | Value |
|-------|-------|
| **Stated License** | CC BY-SA 4.0 (Creative Commons Attribution-ShareAlike 4.0 International) |
| **Commercial Use** | Permitted (with attribution + share-alike) |
| **Attribution Requirement** | Required |
| **Share-Alike Requirement** | Required |

## Repository Metadata (from Hugging Face API)

| Field | Value |
|-------|-------|
| **Pretty Name** | RDD2022 Multi-National Road Damage Detection Dataset (4-Class YOLO Export) |
| **Description** | Unofficial redistribution of the RDD2022 multi-national road-damage dataset, reduced to the 4-class CRDDC2022 taxonomy and reformatted into a standardized YOLO-compatible directory layout, under the original CC BY-SA 4.0 license. |
| **Task Category** | object-detection |
| **Language** | en |
| **Size Category** | 10K<n<100K (10K-100K samples) |
| **Modalities** | image, text |
| **ArXiv** | arxiv:2209.08538 |
| **Downloads** | 30,489 |
| **Likes** | 0 |
| **Private** | No |
| **Gated** | No |
| **Disabled** | No |

## Provenance Statement (from dataset card)

> This repository is not an official release of the RDD2022 dataset.
> RDD2022 was created by Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal, and Yoshihide Sekimoto (University of Tokyo and collaborators), and released as part of the Crowdsensing-based Road Damage Detection Challenge (CRDDC'2022). The original authors and contributing institutions retain all copyright and intellectual property rights. This repository does not claim ownership of any images, annotations, or metadata.

## Two-Hop Provenance

1. **Original release**: RDD2022 (Arya et al., arXiv:2209.08538, CRDDC'2022)
   - Source: https://github.com/sekilab/RoadDamageDetector
   - Per-country Pascal-VOC XML annotations

2. **Intermediate conversion**: RDD_SPLIT (YOLO format conversion)
   - Merged six national subsets
   - Re-split 70/15/15 into train/val/test
   - Converted Pascal-VOC XML to YOLO format

3. **This repository**: dronefreak/RDD2022
   - Reduced to 4-class CRDDC2022 taxonomy (dropped class 4: "other")
   - Reorganized into canonical directory structure
   - Preserved RDD_SPLIT train/val/test splits

> **Two-hop provenance**: The repository is built from a YOLO-format conversion of the official release, followed by the 4-class reduction described below. The original authors are credited below; cite the RDD2022 paper, not this repository.

## Local Artifact Verification

### Downloaded Files
- Arrow files: 3 shards (train, validation, test) - complete metadata
- data.yaml: present
- Image files: partially available on disk (see Acquisition Status below)

### data.yaml Integrity

| Field | Value |
|-------|-------|
| **data.yaml SHA256** | `49f3606a45dca2f83a175aeb8f5299e823f46e07172b2555b39d39a0d41f0828` |
| **Content** | `path: .`, `train: images/train`, `val: images/valid`, `test: images/test`, `nc: 4`, `names: [longitudinal_crack, transverse_crack, alligator_crack, pothole]` |

## Acquisition Status

### Download Method
The dataset was downloaded using Hugging Face's `snapshot_download` function with `repo_id=dronefreak/RDD2022` and `revision=d597e2962458f7242a72aaa1b7909118d40f5d29`.

### Download Result
- **Arrow metadata**: Fully downloaded and verified (all 3 splits load successfully)
- **Image files**: Partially downloaded (~38% on disk)
- **Label files**: Not present as separate files (labels are in Arrow format)
- **Error encountered**: 401 Client Error on Xet read token endpoint during full download
- **Root cause**: The Xet storage system requires authentication token, which is not available

### Image File Availability on Disk

| Split | Expected Images | Images on Disk | Coverage |
|-------|----------------|----------------|----------|
| train | 26,869 | 8,900 | 33.1% |
| validation | 5,758 | 0 | 0.0% |
| test | 5,758 | 5,758 | 100% |
| **Total** | **38,385** | **14,658** | **38.2%** |

### Note on Image Availability
The Arrow format metadata is complete (all 38,385 examples with annotations). However, the raw image files on disk are only 38.2% complete. The remaining images are referenced by `file_name` in the Arrow format and can be retrieved from the Hugging Face Hub or the original RDD2022 source.

For YOLO training, the images would need to be fully available. However, for the purpose of this dataset verification gate, the Arrow format metadata is sufficient to verify all properties (country distribution, class balance, negative diversity, overlap, etc.).

## Dataset Card

The full dataset card is available at: https://huggingface.co/datasets/dronefreak/RDD2022

## Conclusion

- **Repo ID**: dronefreak/RDD2022
- **Revision**: d597e2962458f7242a72aaa1b7909118d40f5d29
- **License**: CC BY-SA 4.0 (documented)
- **Provenance**: Two-hop (official RDD2022 → RDD_SPLIT → dronefreak/RDD2022)
- **Status**: Candidate verified as legitimate (not a random mirror)
- **Caveat**: Unofficial redistribution (not the official release)