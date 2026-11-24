# RIbench comparison inputs

Each of 4,320 datasets has one row for each method in `comparators.csv.gz`. `Index`, `routine_hash`, and `anchor_hash` pair the routine sample and the 40 independently screened anchors with anchorRefine. Both hashes are R serialized-vector SHA-256 digests. The table also retains RIbench’s original `HashCode`, the anchor seed, analyte, sample size, scenario and pathological fraction.

| Method ID | Estimator | Returned raw, small / large | Returned after its original reporting rule, small / large |
| --- | --- | --- | --- |
| `taskE_armB` | Task E round 3 multistart, up to five components | 2,880 / 1,440 | 2,781 / 1,135 |
| `anchoredRI_improved` | Improved round 3 baseline, up to three components | 2,880 / 1,440 | 2,406 / 1,066 |
| `anchorsOnly` | C2 anchors-only estimator, using the same 40 observations | 2,880 / 1,440 | 2,880 / 1,440 |

Both anchoredRI models select the lowest-BIC eligible identity, log or shifted-log fit and take reference limits from the screened component. Their original safeguard can withhold the limits after a disagreement test or lower-limit flag. The C2 anchors-only estimator chooses among identity, log and shifted log by BIC. It uses the sample standard deviation for limits and reports all fits. [Small Task E run](https://github.com/amromeo/amromeo.github.io/actions/runs/45257620744) · [Large Task E run](https://github.com/amromeo/amromeo.github.io/actions/runs/45298562883) · [C2 small run](https://github.com/amromeo/amromeo.github.io/actions/runs/45096614442) · [C2 large run](https://github.com/amromeo/amromeo.github.io/actions/runs/45101564181)

`lower`, `upper`, `z_lower` and `z_upper` describe each raw estimate. Columns prefixed `reported_` describe the estimate released under that method’s original rules. Raw and reported statuses distinguish a returned interval from a decline. Limits are the 2.5th and 97.5th percentiles, except for CRP, which uses one 95th-percentile upper limit. Blank lower limits for CRP are intentional. The comparator’s own limits apply in both the native and historical refineR analyses.

The published export at revision `8bcd49c3c7977c50982524b9dbc48d16bdfa5914` supplies the improved baseline for both sample sizes and the full-precision large Arm B fits. For small Arm B we recovered every selected component at full precision from the 2,880 accepted fit objects across 120 Actions artifacts. Every archive matched GitHub’s SHA-256 digest. Each fit matched the publication’s per-dataset SHA-256, routine hash, and anchor hash. We verified its selected component count, transform and BIC, the limits against the published diagnostics, and the original safeguard decision. `small-armB-selected.csv.gz` preserves the component coordinates and fit digest for each Index. This permits full-precision reconstruction after Actions artifacts expire. [Baseline export](https://github.com/amromeo/amromeo.github.io/blob/8bcd49c3c7977c50982524b9dbc48d16bdfa5914/anchoredRI/tools/boxcox/anchorRefine-comparator/README.md) · [Large fit export](https://github.com/amromeo/amromeo.github.io/blob/8bcd49c3c7977c50982524b9dbc48d16bdfa5914/anchoredRI/tools/boxcox/accuracy/large/results/armB-fits.csv) · [Small accepted batches](https://github.com/amromeo/amromeo.github.io/blob/8bcd49c3c7977c50982524b9dbc48d16bdfa5914/anchoredRI/tools/boxcox/accuracy/results/runtime-provenance.csv)

The original RIbench 1.0.2 function `computePerfMeas` supplies signed endpoint z deviations on the known healthy scale. We score each full cohort by analyte and method, separately for raw and reported limits, using the same group-level support rules as Stage 1. Small-cohort improved baseline and both anchors-only cohorts reproduced every Stage 1 native comparator endpoint and z value exactly.

## Rebuild

From the repository root, use Python 3.11+ and R 4.5.0 with the frozen Stage 0 libraries on the R library path. In the example, `cache` is a local directory. The optional `--zips` argument to the preparation script points to original small Actions ZIPs named by artifact in `sources.json`. It enables a fresh extraction and exact comparison of all 2,880 saved small Arm B model records.

```sh
python3 stage2/ribench/comparators/prepare.py cache
Rscript --vanilla stage2/ribench/comparators/build.R cache cache/comparators.csv
gzip -n -c cache/comparators.csv > cache/comparators.csv.gz
cmp cache/comparators.csv.gz stage2/ribench/comparators/comparators.csv.gz
```

The source manifest records immutable upstream paths, Git blob IDs, SHA-256 digests and the local Stage 1 inputs. Preparation and scoring read previously fitted models and estimates.
