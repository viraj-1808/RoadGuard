# Dataset B Country Audit

## Acquisition Status: FAILED

Could not acquire Dataset B (RDD2022 non-India subset) due to:
1. **S3 bucket access denied** (403 Forbidden) for country-specific ZIPs
   - URLs like https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/RDD2022_Japan.zip return 403
   - Requires AWS credentials or pre-signed URLs not available
2. **FigShare full dataset download impractically slow**
   - Download speed ~22 MB/minute for 12.36 GB ≈ 97 hours
   - Partial download corrupted at ~453 MB
3. **No alternative public source identified**
   - Kaggle contains only India subset (1530 images, D40 only)
   - No verified mirrors contain non-India data

## Country Audit Results: N/A (NO DATA ACQUIRED)

| Country | Expected Images | Actual Images | Status |
|---------|----------------|---------------|--------|
| Japan | ~1,023 MB | 0 | NOT ACQUIRED |
| Czech Republic | ~245 MB | 0 | NOT ACQUIRED |
| Norway | ~9.9 GB | 0 | NOT ACQUIRED |
| United States | ~424 MB | 0 | NOT ACQUIRED |
| China (Drone) | ~153 MB | 0 | NOT ACQUIRED |
| China (MotorBike) | ~183 MB | 0 | NOT ACQUIRED |
| India (to be EXCLUDED) | ~502 MB | 0 | NOT ACQUIRED |

## Recommendation

Dataset B cannot be acquired with current access permissions and bandwidth.
Experiment 2 cannot proceed without Dataset B due to H1 negative-diversity requirement.