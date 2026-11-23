# Improved anchoredRI comparator for anchorRefine

[Download the per-dataset CSV](anchoredRI-comparator.csv). Each row gives the local anchoredRI estimate for one dataset, using the round 3 fitter with up to three components. The raw limits come from the lowest-BIC candidate among the eligible identity, log and shifted-log models.

| Coverage at the small-N and grid review | Available | Planned |
| --- | ---: | ---: |
| RIbench N ≤ 5,000 | 2,880 | 2,880 |
| RIbench N = 50,000 | 144 previously fitted Hb datasets | 1,440 |
| Simulation grid, replicates 1 to 20 | 900 | 900 |

The file contains 3,924 unique datasets. The 396 overlapping small-N rows use the accepted Actions fits on the same routine and anchor samples. The 144 previously exported large-N rows remain available. The full large-N comparison awaits approval. Grid rows use keys of the form `s-CC-RR` (case and replicate), the original routine seed and the family-specific screened seed. The design deliberately reuses each screened sample across scenarios in a family and replicate.

## Pairing datasets

Use the unique `dataset_id`, which is `r-<Index>` for RIbench. Verify both input hashes. The 40 independent anchors were drawn with seed `17000000 + Index`. The RIbench routine seed repeats across datasets. The `routine_hash` and `anchor_hash` are SHA-256 digests of the serialized R input vectors using `digest::digest(x, algo="sha256")` under R 4.5.0. The original RIbench `HashCode` is also present as `ribench_hashcode`.

```r
ref <- read.csv("anchoredRI-comparator.csv", na.strings = "", stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(ref$dataset_id), !anyDuplicated(anchorRefine_results$dataset_id))
keys <- c("dataset_id", "routine_hash", "anchor_hash")
overlap <- intersect(anchorRefine_results$dataset_id, ref$dataset_id)
paired <- merge(anchorRefine_results, ref, by = keys, suffixes = c("_anchorRefine", "_anchoredRI"))
stopifnot(setequal(paired$dataset_id, overlap))
```

| Columns | Meaning |
| --- | --- |
| `schema_version`, `method`, `fitter`, `fitter_source_commit`, `max_components` | Comparator schema 1, method anchoredRI, round 3 multistart fitter, exact source revision and a three-component cap. |
| `benchmark`, `stage`, `Index`, `case`, `replicate` | Benchmark and dataset identifiers. The case and replicate fields identify simulation grid cells and replicates. |
| `Analyte`, `N`, `n_routine`, `n_anchor`, `distribution`, `pathological_fraction`, `scenario`, `rounding_step` | Study definition, nominal sample size, actual input counts and recording precision. Pathological fraction is the design fraction in each benchmark. |
| `transform`, `lambda`, `shift`, `components`, `loglik`, `bic`, `convergence_code`, `at_bound` | Selected candidate and fit diagnostics. |
| `lower_probability`, `upper_probability`, `lower`, `upper` | Requested percentiles and raw fitted limits. Use these for comparisons before the safeguard. |
| `routine_min`, `lrt_statistic`, `lrt_p`, `lower_flag`, `declined`, `technical`, `report_status`, `reason` | The original Task E safeguard and its result for this fit. |
| `reported_lower`, `reported_upper` | Limits released by the safeguard. Withheld limits are blank. A one-sided interval also has a blank lower endpoint. |

All finite numeric fields preserve double precision. The exporter rereads the CSV and validates limits, likelihoods and LRT values against the saved fits. [Stage export script](../accuracy/extract.R) · [Accuracy report](../accuracy/results/REPORT.md)
