# Experiment 2 — Dataset B Build Runbook

**Scope:** building the Experiment 2 training corpus (Dataset A train + non-India Dataset B)
from a complete RDD2022 download, and proving it fit for training.

**This runbook builds the dataset. It does not train.** Training is authorised only after
`experiments/analysis/overnight/experiment2_dataset_b/PRE_TRAINING_GATE_CHECKLIST.md` shows
all 13 gates passing.

## Read-only inputs (never modified by any step)

| Path | Role |
|---|---|
| `experiments/dataset/raw_hf_rdd2022/` | Dataset B source, HuggingFace Arrow `DatasetDict`. **Read-only.** |
| `experiments/dataset/yolo_rdd2022_india/` | Dataset A, the frozen Experiment 1 baseline data. **Read-only.** |
| `runs/detect/experiments/training/yol11s_dataset_v2_split_v2/` | The frozen Experiment 1 run. **Read-only.** |

## Write targets

| Path | Owner step |
|---|---|
| `experiments/analysis/overnight/experiment2_dataset_b/` | 1, 2, 4 (val record), 5, 6 |
| `experiments/dataset/experiment2/` | 3 (images, labels, manifests), 4 (`split_manifest.json`, `data.yaml`) |

---

## Order of operations

The six scripts are a chain, not a set. Each consumes artifacts the previous one produced.
**Do not run them out of order or in parallel.** Every step hard-fails loudly rather than
degrading quietly, so a nonzero exit always means "stop, do not proceed".

```
download  ──▶ 1 country_index  ──▶ 2 exclude_india  ──▶ 3 convert_arrow_to_yolo
                                                                    │
                              6 validate_yolo  ◀── 5 audit_leakage ◀──┤
                                    │                                 │
                                    └────────── 4 build_splits ◀───────┘
                                                   │
                                                   ▼
                                              data.yaml
```

Steps 5 and 6 are read-only audits of the result and are order-independent of each other;
run both after step 4. `data.yaml` is written by step 4 and by nothing else.

### Environment

Run everything from the repository root with the same interpreter that produced the
Experiment 1 run.

```powershell
cd "C:\Users\viraj\Code_files\Github\RoadGuard AI"
```

Dependencies by step:

| Step | Needs |
|---|---|
| 1, 3 | `datasets` (HuggingFace), `PIL` |
| 2 | standard library only |
| 4 | standard library only |
| 5 | `PIL`, `numpy` (no `torch`, no `ultralytics`, no `datasets`) |
| 6 | `PIL`, `numpy`, `pyarrow` |

Step 6's `pyarrow` dependency is only for the Arrow reconciliation; the script degrades
gracefully (and reports `status: skipped_or_unavailable`) if the Arrow root is missing, and
`--no-arrow` disables it outright.

---

## Step 1 — `country_index.py`

**Purpose.** Build the authoritative record of which images Dataset B contains and which
split each belongs to, from the **complete Arrow metadata** via
`datasets.load_from_disk`. It deliberately does *not* walk the on-disk image/label shards —
the Arrow metadata is treated as the source of truth. Country is parsed from the `file_name`
(prefix rules, with the three-part Chinese filenames handled explicitly).

It then verifies the tallies against hard-coded expected values and **exits nonzero on any
mismatch**, including the presence of an unexpected country.

Expected values verified at runtime:

| Quantity | Expected |
|---|---|
| Grand total | 38,385 |
| train / validation / test | 26,869 / 5,758 / 5,758 |
| Japan | 10,506 |
| Norway | 8,161 |
| India | 7,706 |
| United States | 4,805 |
| China | 4,378 |
| Czech | 2,829 |

**Inputs:** `experiments/dataset/raw_hf_rdd2022/` (Arrow `DatasetDict`).
**Outputs:** `experiments/analysis/overnight/experiment2_dataset_b/country_index.json`.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--hf-root` | `experiments/dataset/raw_hf_rdd2022` | Arrow `DatasetDict` directory. |
| `--out-dir` | `.../overnight/experiment2_dataset_b` | Where `country_index.json` lands. |

**Exact command**

```powershell
python scripts/experiment2/country_index.py
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Index written, every expected total matched, `ALL CHECKS PASSED`. |
| `1` | `hf-root` missing, or any total mismatch / unexpected country. |

**Expected runtime:** ~1–5 minutes. The cost is dominated by loading the Arrow tables; no
image is decoded.

**If it fails:** a mismatch here means the download is incomplete or corrupt. Do not pass
`--allow-missing` downstream to work around it. Re-run the download and re-run this step.

---

## Step 2 — `exclude_india.py`

**Purpose.** Emit the authoritative India-exclusion decision record. It reads
`country_index.json` (not the shards) and partitions every entry into India vs non-India by
country.

Two invariants, both hard:

- **Hard assert:** no entry classified as non-India may carry `country == "India"`.
- **Exhaustive partition:** `india_count + non_india_count == total_entries`.

It then verifies the India count equals 7,706.

**Inputs:** `country_index.json` (step 1).
**Outputs:** `india_excluded.json` and `non_india_allowlist.json`, both in
`experiments/analysis/overnight/experiment2_dataset_b/`.

`non_india_allowlist.json` is a sorted list of `{file_name, split, country}` and is the sole
input contract for step 3.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--index` | `.../experiment2_dataset_b/country_index.json` | Step 1 output. |
| `--out-dir` | `.../experiment2_dataset_b` | Output directory. |

**Exact command**

```powershell
python scripts/experiment2/exclude_india.py
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Hard assert passed, India count is 7,706, both files written. |
| `1` | Index missing; a non-India entry carries `country == "India"`; the partition is not exhaustive; or the India count is not 7,706. |

**Expected runtime:** under 10 seconds.

---

## Step 3 — `convert_arrow_to_yolo.py`  ← the long step

**Purpose.** Materialise the non-India Dataset B images and labels into YOLO layout under
`experiments/dataset/experiment2/`:

```
experiments/dataset/experiment2/images/<train|val|test>/<name>.jpg
experiments/dataset/experiment2/labels/<train|val|test>/<name>.txt
```

Note the source RDD2022 shards use `valid` for the validation split; the output uses `val`.
Country is **not** re-derived here — the allowlist already carries it.

Label resolution, in priority order, per image:

1. `repo_txt` — the on-disk `data/labels/<split>/shard_*/*.txt` in the source repo.
2. `arrow_synthesized` — the Arrow `objects.bbox` (COCO absolute pixel xywh) normalised by
   the **actual** image width/height read from the JPEG with PIL. Used only when no on-disk
   label file exists.

**Negatives are preserved.** An image with zero target objects is still copied and receives
an **empty label file**. Negatives are a deliberate part of the Experiment 2 design and are
never dropped. Their presence is what fixes the Experiment 1 pothole over-specialisation.

**Every row is validated before it is written:** class in `{0,1,2,3}`, `0 <= cx,cy <= 1`,
`0 < w <= 1`, `0 < h <= 1`, all four corners inside `[0,1]`. Boxes exceeding the image are
clipped on their corners and the clip is recorded; unrecoverable boxes are rejected into a
report rather than silently discarded. A label file is committed only if its fully rendered
text independently re-parses and re-validates.

**Inputs:** `experiments/dataset/raw_hf_rdd2022/` (Arrow + on-disk shards),
`non_india_allowlist.json` (step 2).
**Outputs** in `experiments/dataset/experiment2/`: `provenance_manifest.csv` (one row per
converted image), `TAXONOMY_NOTE.md` (the D40 semantic caveat), `rejection_report.csv`,
`clipping_report.csv`.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--hf-root` | `experiments/dataset/raw_hf_rdd2022` | Arrow + shard source. |
| `--allowlist` | `.../non_india_allowlist.json` | Step 2 output. |
| `--out-root` | `experiments/dataset/experiment2` | Destination. |
| `--dry-run` | off | Validate and report, write nothing. |
| `--limit N` | `0` (no limit) | Process only the first N allowlist entries. |
| `--allow-missing` | off | Do not hard-fail on an allowlisted source image that cannot be found. **Only for a partial download.** |

**Exact command**

```powershell
python scripts/experiment2/convert_arrow_to_yolo.py
```

Recommended first pass on a small sample, then a full dry run, then the real run:

```powershell
python scripts/experiment2/convert_arrow_to_yolo.py --dry-run --limit 200
python scripts/experiment2/convert_arrow_to_yolo.py --dry-run
python scripts/experiment2/convert_arrow_to_yolo.py
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Conversion complete. Any `missing_image` entries are tolerated only because `--allow-missing` was passed; they are listed in `rejection_report.csv` and excluded from the manifest. |
| `1` | Allowlist unreadable; `hf-root` missing; Arrow metadata load failed; or a **blocking** failure — `unreadable_image`, `no_label_source`, `write_failed`, or any `missing_image` **without** `--allow-missing`. |

**Expected runtime: this is the long step — roughly 1–4 hours** for the full ~30.7k images.
It copies every image, computes a sha256 of each, and writes then re-verifies every label
file. Progress is printed every 2,000 images.

**`--allow-missing` is a diagnostic tool, not a shortcut.** A conversion run that used it
produces a *partial* Dataset B. That build can be inspected and audited, but it must never
be trained on and must never be recorded as gates G1/G2 passing. See the gate checklist.

---

## Step 4 — `build_splits.py`

**Purpose.** Build the Experiment 2 train/val split and emit `data.yaml`. This is the step
that defines the ablation.

- **TRAIN** = Dataset A `train` (1,071 frozen India images, **copied read-only from the
  source**, never moved) **PLUS** the non-India Dataset B train pool.
  Dataset A `val` and `test` are **excluded**; the script hard-fails if any of their
  filenames reach the train pool.
- **VAL** = a deterministic hold-out carved **only** out of the non-India Dataset B train
  pool, `--seed 42`, `--val-frac 0.11` (~11%), **stratified by country** so all five non-India
  countries are represented proportionally. Stratification is applied jointly on
  `(country, is_negative)`, which preserves the negative-image ratio *inside every country*
  rather than only overall.
- **TEST is NOT created.** The frozen 230-image India test set stays where it is and is
  referenced from `data.yaml` as an external path.

After selection, the val files are moved from `images/train` to `images/val`, then removed
from train. The move is idempotent and self-healing: a re-run reconciles the filesystem to
the selected split even after an interrupted previous run.

**Invariants, each a hard failure with nonzero exit**

- no filename appears in both train and val;
- no image sha256 appears in both train and val;
- no Dataset A val/test filename enters the train pool;
- val contains *only* Dataset B pool members;
- the Dataset A inventory matches 1,071 / 229 / 230;
- no India image is present in the Dataset B pool (a broken exclusion).

**Inputs:** `provenance_manifest.csv` + images/labels under
`experiments/dataset/experiment2/` (step 3); `experiments/dataset/yolo_rdd2022_india/`
(read-only, step 3 must not have touched it).
**Outputs:** `experiments/dataset/experiment2/split_manifest.json`,
`experiments/analysis/overnight/experiment2_dataset_b/val_holdout_manifest.json`, and
`experiments/dataset/experiment2/data.yaml` — **written last**, only after every invariant
has passed.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--dataset-a` | `experiments/dataset/yolo_rdd2022_india` | Frozen Dataset A root, read-only. |
| `--exp2-root` | `experiments/dataset/experiment2` | Converted dataset root. |
| `--out-dir` | `.../experiment2_dataset_b` | Where `val_holdout_manifest.json` lands. |
| `--val-frac` | `0.11` | Fraction of the Dataset B train pool held out for val. |
| `--seed` | `42` | Seed for the deterministic stratified hold-out. |
| `--expected-a-train` | `1071` | Asserted Dataset A train size; `0` disables. |
| `--expected-a-val` | `229` | Asserted Dataset A val size; `0` disables. |
| `--expected-a-test` | `230` | Asserted Dataset A test size; `0` disables. |
| `--dry-run` | off | Compute and report, verify the *projected* post-split state, write nothing. |

**Exact command**

```powershell
python scripts/experiment2/build_splits.py --dry-run
python scripts/experiment2/build_splits.py
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | Split written, all hard-fail checks clean, `data.yaml` emitted. |
| `1` | `--val-frac` out of range; Dataset A or Experiment 2 root missing; Dataset A inventory size mismatch; empty Dataset B pool; an India image in the pool; a pool file missing from both pools; or any of the train/val / contamination / val-provenance invariants violated. |

**Expected runtime:** ~20–60 minutes. It sha256s the whole pool to verify disjointness.

**`data.yaml` discipline.** `data.yaml` is written by this step and only by this step, and only
after every earlier step has succeeded and every invariant has held. If a `data.yaml` exists
on disk, it is either from a fully successful run of this step or it is stale — in both cases
it is not evidence that the current dataset is valid. Re-run the chain if in doubt.

---

## Step 5 — `audit_leakage.py`  (Phase 10)

**Purpose.** The leakage audit, checks **A–F**, over the frozen Experiment 1 test set, the
Dataset A splits, and the Experiment 2 splits. Strictly **read-only**: it never deletes,
moves or edits an image or label.

| Check | What it asserts |
|---|---|
| A | Dataset A train ∩ frozen test, exact sha256, must be empty. |
| B | Dataset B ∩ frozen test, exact sha256, must be empty; plus the `India_` filename-prefix audit. |
| C | Every Dataset A train / Dataset B content collision is enumerated and classified. |
| D | Experiment 2 train ∩ val, exact sha256 **and** filename, must be empty. |
| E | Near-duplicate audit: 64-bit dHash screen at Hamming ≤ 5, each candidate confirmed by exact decoded RGB pixel-array equality. |
| F | Source-level split leakage — documented residual risk (the upstream RDD_SPLIT is a random per-image split, not country-grouped, so frames from one source video can cross splits), with the confirmed near-dup crossing count for exp2 train/val reported alongside. |

**`REMOVAL_REQUIRED`.** If any Experiment 2 image is byte-identical to a frozen test image,
the offending file pairs are recorded in the `REMOVAL_REQUIRED` array of the JSON report, a
loud banner is printed, and the process exits nonzero. The script **does not delete
anything** — a human removes the files and re-runs. This is the single most important gate
in the chain (G4, G11).

**Inputs:** `experiments/dataset/yolo_rdd2022_india/` (read-only),
`experiments/dataset/experiment2/` (read-only).
**Outputs:** `experiments/analysis/overnight/experiment2_dataset_b/experiment2_leakage_report.md`
and `experiment2_leakage_report.json`.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--dataset-a` | `experiments/dataset/yolo_rdd2022_india` | Frozen Dataset A root, read-only. |
| `--exp2-root` | `experiments/dataset/experiment2` | Experiment 2 root, read-only. |
| `--out-dir` | `.../experiment2_dataset_b` | Output directory for the two reports. |
| `--workers` | `16` | Thread-pool size for hashing and dHashing (I/O bound). |
| `--hamming-threshold` | `5` | dHash distance that flags a near-duplicate candidate. |
| `--skip-near-dup` | off | Skip check E for a fast hash-only pass. **Not sufficient for gate G11.** |
| `--no-cache` | off | Disable the sha256 cache. |
| `--cache-path` | `<exp2-root>/_hash_cache.json` | Override the cache location. |
| `--expected-a-train` / `--expected-a-val` / `--expected-a-test` | `1071` / `229` / `230` | Asserted Dataset A sizes; `0` disables. |

**Exact command**

```powershell
python scripts/experiment2/audit_leakage.py
```

A fast pre-check while iterating (not a gate pass):

```powershell
python scripts/experiment2/audit_leakage.py --skip-near-dup
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | All hard checks clean, `REMOVAL_REQUIRED` empty, `LEAKAGE AUDIT PASSED`. |
| `1` | `REMOVAL_REQUIRED` is non-empty (Dataset B leaked into the frozen test set), or any of checks A–D failed. |
| `2` | Dataset A or the Experiment 2 root not found, or a Dataset A size assertion failed. |

**Expected runtime:** ~30–90 minutes, dominated by sha256 over ~32.8k images and the dHash
screen in check E. Substantially faster on a re-run thanks to the hash cache.

---

## Step 6 — `validate_yolo.py`  (Phase 11)

**Purpose.** End-to-end validation of the Experiment 2 conversion. Read-only with respect to
every dataset directory; writes only its two reports.

Checks performed:

1. **Pairing** — every image under `images/{train,val}` has a matching `.txt` label and every
   label has an image. Orphans are reported in both directions.
2. **Negatives** — empty label files are present-and-valid, and counted.
3. **Row grammar** — exactly 5 tokens, class id in `{0,1,2,3}`, parseable floats,
   `0 <= cx,cy <= 1`, `0 < w <= 1`, `0 < h <= 1`, all four corners inside `[0,1]`.
4. **Degenerate boxes** — no zero-area or negative-area box.
5. **Dimensions** — image sizes readable via PIL and matching the `width`/`height` recorded
   in `provenance_manifest.csv`.
6. **Reconciliation** — three sources reconciled: (a) label files on disk, (b)
   `provenance_manifest.csv` `n_objects`/classes, (c) the Arrow source totals.
7. **Statistics** — per-split and per-country images, images-per-class, objects-per-class,
   negatives and negative percentage.

**The Arrow reconciliation reads the `.arrow` files directly via `pyarrow`** — it does not go
through `datasets`/`load_from_disk` and does not decode images. This is the independent
cross-check that the on-disk YOLO labels and the source-of-truth Arrow objects agree. If the
Arrow root is absent the script degrades gracefully and records
`arrow.status: skipped_or_unavailable`; the reconciliation then rests on two sources only.
Do not accept a two-source reconciliation as a full G10 pass — run it against the complete
Arrow store.

**Inputs:** `experiments/dataset/experiment2/` (read-only),
`experiments/dataset/raw_hf_rdd2022/` (read-only, Arrow reconciliation source 3).
**Outputs:** `experiments/analysis/overnight/experiment2_dataset_b/experiment2_conversion_validation.json`
and `experiment2_conversion_report.md`.

**CLI flags**

| Flag | Default | Meaning |
|---|---|---|
| `--exp2-root` | `experiments/dataset/experiment2` | Experiment 2 root, read-only. |
| `--arrow-root` | `experiments/dataset/raw_hf_rdd2022` | Arrow store, reconciliation source 3, read-only. |
| `--out-dir` | `.../experiment2_dataset_b` | Output directory for the two reports. |
| `--workers` | `16` | Thread-pool size for PIL dimension reads. |
| `--no-arrow` | off | Skip the Arrow reconciliation source entirely. |
| `--strict-reconciliation` | off | Treat any three-source disagreement as a hard failure. |

**Exact command**

```powershell
python scripts/experiment2/validate_yolo.py
```

**Exit codes**

| Code | Meaning |
|---|---|
| `0` | No hard-check failure. `CONVERSION VALIDATION PASSED`. |
| `1` | Any hard failure: image without a label, label without an image, unreadable image or label, invalid label row, degenerate box, dimension mismatch, `n_objects` disagreement — or, with `--strict-reconciliation`, any three-source disagreement. |
| `2` | Experiment 2 root not found. |

**Expected runtime:** ~15–40 minutes. PIL dimension reads over ~31.8k images dominate; the
Arrow read is comparatively cheap.

---

## Full chain, as run

```powershell
cd "C:\Users\viraj\Code_files\Github\RoadGuard AI"

python scripts/experiment2/country_index.py
python scripts/experiment2/exclude_india.py
python scripts/experiment2/convert_arrow_to_yolo.py
python scripts/experiment2/build_splits.py
python scripts/experiment2/audit_leakage.py
python scripts/experiment2/validate_yolo.py
```

Total expected wall clock for a complete cold run: **roughly 3–7 hours**, dominated by step 3.

---

## Known behaviours that are expected, not bugs

These three will look like failures on first encounter. They are not. Read this section
before concluding that anything is wrong.

### (a) `build_splits.py` copies Dataset A train under its original `India_*` filename

`build_splits.py` copies the 1,071 Dataset A train images into the Experiment 2 train
directory **verbatim, under their original filenames**, which all begin with `India_`. This is
intentional: Dataset A train is a deliberate component of the Experiment 2 training set (it
becomes ~3.4% of it), the source is read-only, and renaming would break traceability to the
frozen baseline.

The consequence is that check **B** of the leakage audit sees `India_`-prefixed filenames
under `experiments/dataset/experiment2/`. It does **not** report that as a single opaque
count. It splits them into two buckets:

| Bucket | Definition | Consequence |
|---|---|---|
| `india_prefixed_designed_carry_over` | the file's sha256 matches a Dataset A **train** image | **Informational only.** Expected to be ~1,071. |
| `india_prefixed_unexpected` | `India_`-prefixed but sha256 does **not** match any Dataset A train image | **Hard failure.** Would mean an India image survived the exclusion somewhere unexpected. |

Only the *unexpected* bucket fails the check. A non-zero `india_prefixed_filenames` total
with an all-carry-over breakdown is the correct, passing result. Check the split, not the
total.

### (b) Check C reports colliding pairs, and most are expected

Check **C** compares Dataset A train against Dataset B and enumerates **every** colliding
pair rather than just counting them, classifying each as:

| Classification | Meaning | Consequence |
|---|---|---|
| `expected_dataset_a_carry_over` | the Experiment 2 filename still carries the `India_` prefix | **Informational only.** |
| `unexpected_cross_dataset_duplicate` | a genuine cross-dataset duplicate, not the carry-over | **Hard failure.** |

Same underlying cause as (a): the carry-over copies the Dataset A train images, so their
sha256 values necessarily collide with Dataset A train. Only `unexpected_pair_count == 0`
is required. `duplicate_pair_count` and `duplicate_sha256_count` are expected to be non-zero.

### (c) No class 4 should ever appear

The redistribution's own class-4 "other" bucket was **already dropped upstream**, before this
pipeline ever sees the data. The locked taxonomy maps only four codes — `D00 → 0`,
`D10 → 1`, `D20 → 2`, `D40 → 3` — and `CLASS_NAMES` has keys `0..3` only.

Therefore **class 4 should never appear in any label file, and class 4 is not a valid class
for this experiment.** If a class 4 ever does appear it is a genuine anomaly, and the
converter will reject it rather than write it: the row fails with reason
`unknown_class_id:4` and lands in `rejection_report.csv`. A non-empty
`rejection_report.csv` is not automatically a problem — it is the designed landing place for
these and for any other unrecoverable row — but **any `unknown_class_id` row must be
investigated, not ignored.** Zero `unknown_class_id` rejections is the expected state.

A separate, expected non-empty artifact is `clipping_report.csv`: boxes that extended past
the image edge were clipped to the image bounds and recorded. That is correct behaviour, and
the report exists so the clipping is auditable rather than silent.

---

## Resuming

**Every step is idempotent.** Re-running the chain is the normal way to recover from an
interruption, and the correct way to pick up where a partial run left off. No step needs to be
restarted from scratch, and no step needs manual cleanup of its predecessor's output.

| Step | Resume behaviour |
|---|---|
| 1 | Overwrites `country_index.json` in place. Pure re-derivation from Arrow. |
| 2 | Overwrites both JSON files in place. |
| 3 | Reads the existing `provenance_manifest.csv` first. An image already present in the output whose sha256 is already in the manifest is **skipped**, not re-copied. Images and labels are staged as `.part` files and committed with `os.replace`, so a crash can never leave a half-written label visible. Manifest rows are keyed on `(source_split, source_image_id)` and updated in place rather than appended, so re-running does not duplicate rows. |
| 4 | Fully self-healing. Re-running recomputes the deterministic selection (same `--seed`, same `--val-frac` → same val set), then reconciles the filesystem to it: a file in the wrong directory is moved back, a duplicate is deduplicated, and a file missing from both directories is a hard failure naming it. |
| 5 | Overwrites both reports. Hash cache makes the re-run largely free. |
| 6 | Overwrites both reports. No persistent state. |

Re-running step 3 after a crash therefore resumes rather than restarts, and re-running step 4
after a crash is the normal recovery path — no need to delete `experiments/dataset/experiment2/`
first.

### Hash caching in the leakage audit

Step 5 keeps a sha256 cache at `experiments/dataset/experiment2/_hash_cache.json`. It is keyed
on

```
<repo-relative path>|<mtime_ns>|<size>
```

so a file whose content changes — any change at all, including a same-size rewrite — produces
a different key and is re-hashed. Stale entries cannot be served. The report records
`hash_cache.path`, `hits`, `misses`, and `key_format`.

Use `--no-cache` to force a full re-hash from scratch (e.g. if you suspect the filesystem or
the cache file itself), or `--cache-path` to relocate it. The first run of step 5 is the slow
one; every subsequent run reuses the cache.

---

## Where the evidence lands

Every gate in `PRE_TRAINING_GATE_CHECKLIST.md` points at one of these artifacts. After a full
chain run, `experiments/analysis/overnight/experiment2_dataset_b/` should contain:

```
country_index.json                    step 1
india_excluded.json                   step 2
non_india_allowlist.json              step 2
val_holdout_manifest.json             step 4
experiment2_leakage_report.json/.md   step 5
experiment2_conversion_validation.json  step 6
experiment2_conversion_report.md      step 6
```

and `experiments/dataset/experiment2/` should contain:

```
images/{train,val,test}/              step 3, then reconciled by step 4
labels/{train,val,test}/              step 3, then reconciled by step 4
provenance_manifest.csv               step 3
TAXONOMY_NOTE.md                      step 3
rejection_report.csv                  step 3
clipping_report.csv                   step 3
split_manifest.json                   step 4
data.yaml                             step 4  (last, and only if every prior step passed)
```

**Training is not authorised until all 13 gates in the pre-training checklist are `PASS`.**


