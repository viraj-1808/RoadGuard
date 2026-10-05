# Experiment 2 Decision — FINAL (ACQUISITION FAILED)

## Gate Outcome: OUTCOME C — ACQUISITION FAILED

Dataset B (RDD2022 non-India subset) **cannot be acquired**.
Therefore Experiment 2 is **BLOCKED**.

---

## 1. Exact Dataset B
**Could not be acquired.**
- **Source**: RDD2022 (CRDDC'2022) via S3 bucket `bigdatacup` or FigShare
- **Attempted URLs**: All country-specific ZIPs from https://bigdatacup.s3.ap-northeast-1.amazonaws.com/2022/CRDDC2022/RDD2022/Country_Specific_Data_CRDDC2022/
- **Result**: 403 Forbidden on all 6 URLs
- **FigShare attempt**: Download speed ~22 MB/min for 12.36 GB (~97 hours); partial download corrupted at ~453 MB

## 2. Why It Was Being Considered
- Primary candidate from dataset research (perfect 4-class match, CC BY 4.0 license, geographic diversity, includes negatives)
- Directly addresses H1 (zero negatives in current artifact) and H2 (only 30 transverse-crack instances)

## 3. H1 Addressed? UNKNOWN (NO DATA)
Could not verify negative-diversity improvement without acquiring data.
Methodology was sound (46% negatives expected in full RDD2022).

## 4. H2 Addressed? UNKNOWN (NO DATA)
Could not verify transverse-crack increase without acquiring data.
Methodology was sound (~1,500 transverse instances expected).

## 5. Taxonomy Compatible? YES (THEORETICAL)
- D00→0, D10→1, D20→2: HIGH confidence
- D40→3: MEDIUM confidence (D40 = "Other Corruption" including pothole, rutting, bump, separation)
- Caveat: Class 3 is D40-corruption detector, not pure pothole (same as baseline)

## 6. Leakage Exists? N/A (NO DATA)
Could not perform overlap audit without acquiring data.
Proposed mitigation: Exclude India subset and verify with SHA256 hashes.

## 7. Acquisition Practical? NO
- S3 bucket requires AWS credentials/pre-signed URLs (not available)
- FigShare download impractically slow (~97 hours at 22 MB/min)
- No alternative public source identified

## 8. Experiment 2 Should Use It? **NO — ACQUISITION FAILED**
Conditions for use cannot be met:
1. India subset cannot be excluded (cannot download)
2. SHA256 hash verification impossible (no files)
3. Image similarity analysis impossible (no files)
4. Transverse class semantic verification impossible (no files)
5. D40 semantics documentation possible but irrelevant without data

## 9. Exact Proposed Experiment 2 Configuration
**NOT APPLICABLE — ACQUISITION FAILED**

## 10. What Remains Uncertain
Everything — no data acquired.

## Conclusion
**EXPERIMENT 2 BLOCKED — Dataset B provenance/acquisition/compatibility insufficient.**

Without Dataset B, H1 (negative-diversity deficiency) cannot be addressed because:
- Current artifact has 100% pothole coverage (0% negatives)
- No negative/background images exist in current training data
- Model cannot learn to distinguish potholes from non-pothole regions

No training should be initiated. The overnight analysis remains valid, but Experiment 2 cannot proceed.