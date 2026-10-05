# Dataset B Provenance

## Acquisition Status: FAILED

Could not acquire Dataset B (RDD2022 non-India subset) due to:
1. **S3 bucket access denied** (403 Forbidden) for country-specific ZIPs
2. **FigShare full dataset download impractically slow** (~97 hours at 22 MB/min)
3. **No alternative public source identified**

All provenance information below is theoretical/expectational based on public documentation.

## Origin

RDD2022 is the official CRDDC'2022 (IEEE Big Data Cup) Road Damage Dataset.
It is the successor to RDD2020 and extends it with additional countries and images.

## Release Details

- **Release**: 2022, IEEE Big Data Cup (CRDDC'2022)
- **Maintainer**: Seki Laboratory, Nara Institute of Science and Technology (NAIST)
- **FigShare DOI**: 10.6084/m9.figshare.21431547
- **GitHub**: https://github.com/sekilab/RoadDamageDetector

## License

**CC BY 4.0** (Creative Commons Attribution 4.0 International)

Permits:
- Commercial use
- Distribution
- Derivative works
- Adaptation

Requires:
- Attribution to original authors

No restrictions on training ML models or using derived artifacts for commercial purposes.

## Predecessor

RDD2020 (CC BY-NC-SA 3.0, non-commercial restriction) is a subset of RDD2022.
RDD2022 extends RDD2020 with additional countries (Norway, United States, China).

## Acquisition Path

1. **Primary (Failed)**: FigShare download (https://doi.org/10.6084/m9.figshare.21431547)
   - Direct download link: https://figshare.com/ndownloader/files/39048529
   - File: RoadDamageDataset.zip (approx 13.2 GB)
   - Result: Download too slow (~22 MB/min); partial download corrupted

2. **Alternative (Failed)**: GitHub repository country-specific ZIPs
   - URLs: https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/[COUNTRY].zip
   - Result: All 6 URLs return 403 Forbidden (bucket access denied)

3. **Mirror**: No verified mirror exists.
   - Kaggle mirrors exist but are India-only derivative artifacts
   - Not equivalent to official release

## India Subset

The current local artifact (`normalized_rdd2022_india/`) is derived from the India portion of RDD2022.
- Original India subset size: approximately 9,665 images (per earlier audit)
- Current artifact: 1,530 images (a filtered subset of the India portion)
- The filtering criteria are documented in the conversion manifest

## Derivative Status

The current local artifact is a **derivative** of RDD2022, not the original.
It was filtered to include only images containing D40 (pothole) annotations.
This is the source of the selection bias identified in the dataset diagnosis.

## Verification

The provenance chain is:
1. RDD2022 official release (FigShare)
2. India subset extraction
3. D40-based filtering (current artifact)
4. YOLO format conversion (current artifact)

Each step is documented in the conversion manifest and split manifest.

## Notes

The full RDD2022 dataset has NOT been downloaded or verified locally.
All statistics cited are from published analyses and the official documentation.
Exact per-class counts for the full dataset require downloading and analyzing the archive.

**ACQUISITION FAILED** — Dataset B could not be obtained for Experiment 2.