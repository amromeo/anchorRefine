# Stage 3 confirmation data for Task G

Use the published confirmation results directory as the working directory. The two compressed CSVs contain all 7,488 datasets, including failed fits and declined intervals. The same integer `j` identifies the dataset in both tables and in the saved R object. Development and confirmation each number datasets from 1, so keep the phase with the ID when combining studies.

| File | One row per | Contents |
| --- | --- | --- |
| [Fits](evidence/fits.csv.gz) | `j, arm` | 52,416 fitted-model records. Includes native and historical endpoints before checking, status, parameters, Stage 2 fallback, input hashes, seeds, simulation cell and scoring truth. |
| [Anchor-check decisions](evidence/checks.csv.gz) | `j, arm, panel, seed_kind` | 209,664 decisions. Includes the actual PIT seed, check status, reason, likelihood-ratio statistic, p-value and released native and historical limits. |
| [Dataset index](task-g-index.csv) | `j` | Raw shard ZIP path, primary RDS member and one-based position in its `cases` list. Includes N, original Stage 2 fallback status and ordered input hashes. |
| [Manifest](task-g-manifest.json) | Export and shard | Source and run IDs, counts, SHA-256 of the tables and each original primary RDS member. The archive's [checksums](SHA256SUMS) cover the ZIPs. |

The five scientific arms are `baseline` (unchanged refineR 2.0.0), `stage2` (frozen peak choice, K = 24), `w1` (primary), `t0.25` (post-fit comparator) and `anchorsOnly` (archived C2 estimator). The `w0` and `t0` rows are technical identity controls. For the main release, join a fit to its decision where `panel == "guidance"` and `seed_kind == "primary"`. The guidance panel is the one supplied to the fitting arms. The diagnostic panel is an independent sample of 40 screened anchors. The `alternate` seed repeats PIT randomization for the same panel. Join by IDs because export order follows the shard assignment.

`fit_status` records whether the fit returned. Check `status` takes the values `keep`, `decline`, `check_failed` and `fit_failed`. A declined fit retains its pre-check parameters and limits in the fits table. A released endpoint is present only for a kept result with finite endpoints for that extraction. The anchors-only comparator releases each successful original interval under its C2 rule. Its four rows record that release with an empty statistic and p-value. Each of its two extraction columns contains the same original interval.

For refineR-derived fits, capitalized `Mu`, `Sigma`, `Lambda` and `Shift` are fitted healthy-model parameters. Lowercase `mu`, `sigma` and `lambda` describe the simulation family. For anchors-only use `ao_transform`, `ao_location`, `ao_spread` and `ao_shift`. Its stored R object also contains `transform`, `mu`, `sd`, `shift`, `limits` and the candidate diagnostics. `mu` and `sd` use the chosen identity, log or shifted-log scale. `sd` is the sample standard deviation used to form the two endpoints. Screening truth, z errors and results from the independent panel are available for scoring.

## Read one saved fit

Download the shard ZIP named in the [index](task-g-index.csv) to its listed `artifacts/` path. This R example restores the complete fitted object for dataset 1, extracts its primary decision and checks the stored hashes. R's `digest` package uses serialization version 2 here. File hashes in the manifest use SHA-256 of the file bytes.

```r
j <- 1L
chosen_arm <- "w1"
index <- read.csv("task-g-index.csv", stringsAsFactors = FALSE)
i <- index[index$j == j, , drop = FALSE]
stopifnot(nrow(i) == 1L)
dest <- tempfile()
dir.create(dest)
member <- unzip(i$archive, files = i$member, exdir = dest)
shard <- readRDS(member)
case <- shard$cases[[i$rds_position]]
sha <- function(x) digest::digest(x, algo = "sha256", serializeVersion = 2L)
stopifnot(case$j == j, identical(sha(case$routine), i$routine_hash),
          identical(sha(case$panels$guidance), i$anchor_hash),
          identical(sha(case$panels$diagnostic), i$diagnostic_hash))
entry <- case$arms[[chosen_arm]]
fit <- entry$search$fit
if (entry$uses_routine) fit$Data <- case$routine
if (!is.null(fit)) stopifnot(identical(sha(fit), entry$full_fit_hash))
decision <- subset(shard$checks, j == case$j & arm == chosen_arm &
                   panel == "guidance" & seed_kind == "primary")
stopifnot(nrow(decision) == 1L)
```

The RDS stores the exact ordered routine vector once per dataset and the two panels in draw order. Fits that use the routine vector preserve a `Data` slot for restoration. The runner read each primary RDS back and verified every restored object hash and input hash before publication. `entry$search` carries the original fit status and search details, and `entry$conditions` contains the captured scoring conditions. For a failed fit, retain its status and available object. The RDS also contains `shard$fits` and `shard$checks` for the same datasets in R's native types. Numeric assay increments, seeds and input hashes in the fits table support alignment to a separate combined-method implementation.
