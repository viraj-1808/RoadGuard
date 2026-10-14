# Phase 1 Repository Audit - 2026-10-10

## Git Status
```
On branch chore/viraj-model-training
Your branch is ahead of 'origin/chore/viraj-model-training' by 1 commit.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   experiments/evaluation/exp1_frozen_dataset_a_test/predictions.json
	modified:   experiments/evaluation/exp2_frozen_dataset_a_test/eval/predictions.json

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	cache/
	experiments/optimization/
	experiments/results/
	inspect_checkpoints.py
	inspect_state_tmp.py
	launch_microtrial.py
	run_microtrial.bat
	scan_images.py
	scripts/optimization/
	validation/manual/output/test2/

no changes added to commit (use "git add" and/or "git commit -a")
```

## Git Branches
```
* chore/viraj-model-training 09b6d3f [ahead 1] final_training_decision_report: CONTINUE_EXP2_TRAINING decision with analysis artifacts
  main                       312d4f4 Merge branch 'main' of https://github.com/viraj-1808/RoadGuard
```

## Recent Git Log (Last 5 Commits)
```
09b6d3f final_training_decision_report: CONTINUE_EXP2_TRAINING decision with analysis artifacts
290d011 cleanup: organize repository structure, fix stale references, update gitignore
53cb8e2 restructure: organize repository scripts and configs
6e7fc9c chore: checkpoint repository before cleanup
312d4f4 Merge branch 'main' of https://github.com/viraj-1808/RoadGuard
```

## Current HEAD
```
09b6d3f56ace636e39190f0ce61ca4045767a263
```

## Uncommitted Changes Summary
**Modified Files (2 files, 2 insertions(+), 2 deletions(-)):**
- `experiments/evaluation/exp1_frozen_dataset_a_test/predictions.json` - 1 line changed
- `experiments/evaluation/exp2_frozen_dataset_a_test/eval/predictions.json` - 1 line changed

**Untracked Files/Directories:**
- `cache/`
- `experiments/optimization/`
- `experiments/results/`
- `inspect_checkpoints.py`
- `inspect_state_tmp.py`
- `launch_microtrial.py`
- `run_microtrial.bat`
- `scan_images.py`
- `scripts/optimization/`
- `validation/manual/output/test2/`

---

## Directory Trees

### runs/
```
runs/
└── detect/
    ├── experiments/
    │   └── training/
    │       ├── yol11s_dataset_v2_split_v2/     # Full training run with weights, results, test_eval, test_final
    │       ├── yol11s_experiment2/              # Experiment 2 training (70 epochs, best.pt + epoch checkpoints)
    │       ├── yol11s_microtrial_w2_pf2/        # Micro-trial with workers=2, prefetch=2
    │       └── yol11s_smoke_test/               # Smoke test run
    ├── runs/
    │   └── detect/
    │       └── experiments/
    │           ├── evaluation/
    │           │   └── experiment2_frozen_test/
    │           └── training/
    │               └── yol11s_dataset_v2_split_v2/
    ├── val/                                     # Validation run 1
    ├── val-2/                                   # Validation run 2
    ├── val-3/                                   # Validation run 3
    ├── val-4/                                   # Validation run 4
    ├── val-5/                                   # Validation run 5 (with prediction_boxes.json)
    └── validation/
        └── manual/
            └── output/
                └── experiment2_best/            # Manual validation output
```

### experiments/
```
experiments/
├── dataset/
│   └── raw_hf_rdd2022/
│       └── data/
│           └── images/
│               └── train/
│                   └── shard_006/              # Large dataset (Norway images)
├── evaluation/
│   ├── exp1_frozen_dataset_a_test/
│   │   └── predictions.json
│   └── exp2_frozen_dataset_a_test/
│       └── eval/
│           └── predictions.json
├── optimization/                                # Untracked
└── results/                                     # Untracked (this audit output)
```

### validation/
```
validation/
└── manual/
    ├── input/                                   # 39 input images (road001-road039)
    ├── output/                                  # Annotated outputs + reports
    │   ├── INFERENCE_VALIDATION_REPORT.md
    │   ├── predictions.json
    │   ├── road001-road015_annotated.*
    │   └── test2/                               # Untracked second test run
    │       ├── INFERENCE_VALIDATION_REPORT.md
    │       ├── predictions.json
    │       └── road001-road039_annotated.*
    └── test_output/                             # Large batch: 200+ annotated India images
        ├── predictions.json
        └── India_XXXXXX_annotated.jpg (200+ files)
```

### configs/
```
configs/
├── data/
└── training/
    ├── baseline_training_plan.json
    └── baseline_training_plan.md
```

### docs/
```
docs/
├── API_CONTRACTS.md
├── ARCHITECTURE.md
├── CLASS_MAPPING.md
├── DATA_PIPELINE.md
├── DATA_PIPELINE_UPDATES.md
├── DATABASE_SCHEMA.md
├── DATASET_AUDIT.md
├── DATASET_AUDIT_SUMMARY.md
├── DECISION_LOG.md
├── DEPLOYMENT.md
├── ENGINEERING_LOG.md
├── EVENT_SCHEMAS.md
├── INFERENCE_ARCHITECTURE.md
├── MODEL_EVALUATION.md
├── MODEL_TRAINING.md
├── PROJECT.md
├── RESEARCH_REGISTER.md
├── RESEARCH_REGISTER_ADDITIONS.md
├── SECURITY_ARCHITECTURE.md
└── TEAM_WORKSTREAMS.md
```

### scripts/
```
scripts/
├── __init__.py
├── analysis/                                    # 30+ analysis scripts
│   ├── analyze_*.py (correlation, similarity, ground_truth, image_correlation, manifest parts 1-10, official_metrics, predictions, results, split, strata, xml)
│   ├── audit_*.py (h11_evidence_scope, missed_pair_evidence)
│   ├── convert_to_yolo.py
│   ├── corrected_error_analysis.py
│   ├── dataset_analysis.py
│   ├── debug_strata.py
│   ├── error_analysis_dataset_a_val.py
│   ├── generate_dataset_a_val_predictions.py
│   ├── generate_error_analysis_sheet.py
│   ├── rdd2022_*.py (india_analysis, provenance_analysis, visualization)
│   ├── render_missed_pair_contact_sheets.py
│   ├── transform_rdd2022_annotations.py
│   ├── validate_transformation.py
│   ├── validate_yolo_conversion.py
│   └── verify_near_duplicates.py
├── benchmark/
│   └── benchmark_batch_size.py
├── download/                                    # 7 download scripts for RDD2022
├── evaluation/
│   └── eval_run.py
├── experiment2/                                 # Experiment 2 pipeline
│   ├── audit_leakage.py
│   ├── build_splits.py
│   ├── convert_arrow_to_yolo.py
│   ├── country_index.py
│   ├── exclude_india.py
│   ├── validate_yolo.py
│   └── _fixtures/test_splits.py
├── inspection/                                  # 4 inspection scripts
├── optimization/                                # 6 optimization scripts
├── utils/                                       # 2 utility scripts
└── validation/                                  # 15+ validation scripts + pipeline
    ├── check_*.py (all_strata, china_mb, component, counts, leakage, strata, v3, xml, geometry)
    └── pipeline/
        ├── step1_verify.py
        ├── step2_verify.py
        ├── step3_verify.py
        ├── step4_verify.py
        └── step5_verify.py
```

### weights/
```
weights/
├── yolo11s.pt
└── yolo26n.pt
```