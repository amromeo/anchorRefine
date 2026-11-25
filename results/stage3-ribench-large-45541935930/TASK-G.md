# RIbench fits and decisions for Task G

Work from the published results directory for either cohort. The original RIbench `Index` is the dataset identifier and `j` is its Task G alias. The small cohort contains 2,880 distinct indices at N = 1,000 or 5,000. The large cohort contains 1,440 at N = 50,000. RIbench strata use nominal `N`. Some routine vectors have a different length, recorded as `routine_n`. Indices keep their original values within and across cohorts. Include the phase when combining these data with synthetic studies.

| File | Key | Contents |
| --- | --- | --- |
| [Fits](evidence/fits.csv.gz) | `j, arm` | Fitted parameters, original status and branch, both pre-check extractions, requested limits, z scores, seeds and input hashes. Small has 20,160 fit rows and large has 10,080. |
| [Anchor-check decisions](evidence/checks.csv.gz) | `j, arm, panel, seed_kind` | PIT seed, status, reason, likelihood-ratio statistic, p-value and released native and historical limits. Small has 40,320 decision rows and large has 20,160. |
| [Dataset index](task-g-index.csv) | `Index` | Primary shard ZIP and RDS member, one-based case position, analyte, nominal N, actual routine vector length (routine_n), scenario, pathological fraction, Stage 2 fallback status and input hashes. |
| [Export manifest](task-g-manifest.json) | Export and shard | GitHub run and source commit, arm names, counts, public file hashes and SHA-256 of each primary RDS member. Original ZIP hashes appear in [the archive manifest](SHA256SUMS). |
| [Arm B estimates and original releases](task-g-arm-b.csv.gz) | `Index` | Paired Task E raw and reported limits and z scores, native source statuses and ordered input hashes. |
| [Original Arm B fit and safeguard record](task-g-arm-b-original.csv.gz) | `Index` | Published Task E fields and decision on each RIbench dataset. The [source manifest](task-g-comparator-provenance.json) gives immutable upstream revisions and SHA-256 digests. |

The scientific arms fitted here are `baseline` (unchanged refineR), `stage2` (frozen peak choice), `w1` (weighted search), `t0.25` (post-fit comparator), and `anchorsOnly` (C2 estimator applied to the same anchors). The `w0` and `t0` labels are technical identity controls. The two check rows per arm refer to the same screened panel of 40 observations, drawn with seed 17000000 + Index. Both use `panel == "guidance"`. The primary release uses `seed_kind == "primary"`, with seed 38000000 + Index. The alternate uses 39000000 + Index. Join by keys because file order follows the shard assignment.

`Mu`, `Sigma`, `Lambda` and `Shift` are the refineR-derived healthy-model parameters. `fit_status` is the fitting outcome. Check `status` can be `keep`, `decline`, `fit_failed` or `check_failed`. Retain technical failures and declines when computing all-dataset coverage. The pre-check table preserves the available model and limits even when the check declines the interval. In the checks table, released endpoints require a kept decision and a usable extraction. CRP uses only its 95th-percentile upper limit, with no lower limit requested. All other analytes use the 2.5th and 97.5th percentiles.

For anchors-only, use `ao_transform`, `ao_location`, `ao_spread` and `ao_shift`. The saved object contains `transform`, `mu`, `sd`, `shift`, `limits` and candidate diagnostics. The two PIT labels record the original C2 reporting rule. They have no likelihood-ratio statistic or PIT p-value. Native and historical fields carry the same C2 estimate. For CRP use the exported CRP upper endpoint. The generic two-sided limits inside the saved C2 object use the estimator’s original 1.96 convention.

RIbench can change its upper z-score calculation for an entire method/analyte group when a reported upper estimate is zero. The public fits table applies this rule across the complete cohort, separately for each extraction. Its `native_z_upper_before_group` and `historical_z_upper_before_group` fields preserve the original shard z scores. The `*_group_has_zero_upper` fields identify the applicable group. The shard's R fits table reflects the per-case calculation. All fitted parameters, raw endpoints and anchor-check decisions are preserved in both locations.

Task E arm B is an external comparison. Join the two Arm B files to the five scientific arms on `Index` and verify both ordered input hashes in the paired estimates file. Its `reported_status` and decision fields are products of its original safeguard. The small cohort also supplies `task-g-arm-b-component.csv.gz` with the previously archived full-precision screened component coordinates and fit digest. Its original diagnostics carry the available `lrt_p`, flags, and decision. For the large cohort, the original records include the fitter revision, transform, component count, original LRT statistic, p-value, flags, and reason. Task G can use those decisions directly.

The parent path is recorded in `parent_fallback`. Use `weighted_search_entered`, `weighted_search_path`, `extra_fallback` and `parent_retained` to distinguish a successful weighted update, a scored incumbent and an update failure. A primary fit can use its anchors on the unguided path.

## Restore one fitted object

Download the ZIP specified by the [index](task-g-index.csv) and place it under its listed `artifacts/` path. The same example works in either cohort. R's `digest` package checks object hashes using serialization version 2.

```r
index <- read.csv("task-g-index.csv", stringsAsFactors = FALSE)
i <- index[1L, , drop = FALSE]
chosen_arm <- "w1"
dest <- tempfile()
dir.create(dest)
member <- unzip(i$archive, files = i$member, exdir = dest)
shard <- readRDS(member)
case <- shard$cases[[i$rds_position]]
sha <- function(x) digest::digest(x, algo = "sha256", serializeVersion = 2L)
stopifnot(case$Index == i$Index, case$j == i$j, length(case$routine) == i$routine_n,
          identical(sha(case$routine), i$routine_hash),
          identical(sha(case$panels$guidance), i$anchor_hash))
entry <- case$arms[[chosen_arm]]
fit <- entry$search$fit
if (entry$uses_routine) fit$Data <- case$routine
if (!is.null(fit)) stopifnot(identical(sha(fit), entry$full_fit_hash))
decision <- subset(shard$checks, Index == case$Index & arm == chosen_arm &
                   panel == "guidance" & seed_kind == "primary")
stopifnot(nrow(decision) == 1L)
```

Each original primary RDS stores the ordered routine vector once per dataset, its panel in draw order, fit objects and search diagnostics, and the fit and check tables in R-native types. The per-case record digest is `case_hash` in the fits table. The primary worker reads back every serialized case, verifies the input and case hashes, reattaches the `Data` slot where present, and verifies all seven original model hashes.
