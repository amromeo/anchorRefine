# C2 preservation and source review

2026-11-23. This is an input and source inspection, not a Stage 0 result. No new fits, performance comparisons, or anchor tests have run.

## Preserved artifacts

The source project is the `anchoredRI/` directory of `amromeo/amromeo.github.io`, not a separate repository. All access to that repository was read-only.

C2 run: https://github.com/amromeo/amromeo.github.io/actions/runs/45096614442

C2 source commit: `f72ea14fc7978bf2478f54c87548cb6c127fa766` on `anchoredri-ribench-independent`.

The complete combined output and the routine-data artifact are permanently stored here:

| Artifact | ID | Bytes | SHA-256 |
|---|---:|---:|---|
| `archive/c2/ribench-scored-independent.zip` | 14783937282 | 11117261 | `390d5801032b7cc5e64fbc5efbef3ed4c2a2b94e1a6f83e9fe4bdc38ed263d07` |
| `archive/c2/ribench-data-small.zip` | 14784000559 | 11040700 | `a4efc6e89c204d1f48b55adf4438fbf39cd7ef535faf4adfa4be2f86e36e1c27` |

Both digests match GitHub's artifact metadata. The original artifacts expire on December 23, 2026 (30-day retention). GitHub's CLI artifact redirect was denied by the execution network; the connected GitHub download tool succeeded. The ZIP bytes were downloaded from that tool and verified locally.

The combined artifact contains all 2,880 refineR model files, all 2,880 anchoredRI outputs, all 2,880 anchors-only outputs, all 60 custom shard records, the anchor hashes, and the scoring outputs. The companion data artifact contains 2,880 routine-data CSV files plus the test-set definition and generation metadata. The aggregate output subsumes the individual result shards; the shard ZIPs themselves are not retained. Full GitHub artifact listing and run metadata are saved alongside the archives.

The C2 workflow copied refineR fits from run https://github.com/amromeo/amromeo.github.io/actions/runs/45091086783 rather than refitting them. Its source commit is `d0e1eb77a31583c7245e580198009d494542978d`. That earlier workflow's overall conclusion is failure, so its status must not be mistaken for a validation pass. C2 later reused the models and completed successfully. Both run metadata records and relevant source files are preserved; Stage 0 must independently validate the models and data.

## Inventory checks

`archive/c2/model-inventory.csv` records each archived model's Index, member path, SHA-256, parameters and status. Python rdata was used only to inspect serialization and parameter presence; native R readback remains required before use.

- 2,880 models with 2,880 distinct indices, exactly matching the small-N definition.
- 1,440 sets at N = 1,000 and 1,440 at N = 5,000.
- Ten analytes, 288 sets each, including 288 CRP sets.
- Every model records refineR 2.0.0, Model = BoxCox, NBootstrap = 0, Status = ResultFound.
- All four parameters are present and finite in every model. None has negative lambda.
- All 5,760 custom method rows record 40 retained anchors.

These checks establish archive completeness and parameter availability. They do not establish input-vector hash equality, fit reproducibility, or benchmark accuracy.

## Anchor generation and comparators

The C2 generator resets `set.seed(17000000L + Index)` for each set, draws 40 normal observations using the true healthy parameters, inverse-transforms them with RIbench's Box–Cox function, adds the true shift, removes nonfinite/negative draws, and rounds survivors to the analyte's declared decimals. It does not replace discarded draws. No small-N sample lost a draw according to archived records. Preserve the exact generator and R RNG configuration for identity checks; verify every regenerated anchor vector against `anchor-sample-hashes.csv` in R.

The anchors-only estimator compares identity, log and shifted-log models using BIC. It uses MLE variance for likelihood/BIC and sample standard deviation for limits; two-sided limits use exactly 1.96. Its shift search, bounds, convergence flags and tie-breaking are preserved in `sources/c2/anchoredRI/tools/anchors-only/estimators.R`. CRP uses its upper 95th percentile.

The improved comparator is copied unmodified from `study/boxcox` commit `3c921dfaa29f64df3f7ea82e6bf5634be20e8943` into `archive/comparators/`. Coverage is 396 small-N sets (Hb/Ca) and 144 N = 50,000 sets (Hb). This is partial coverage, not the full RIbench comparator. Pair by dataset_id and both input hashes exactly as its upstream README specifies.

The N = 50,000 published-results branch was located at commit `b98c345a3faacaa38666af77035a6b88c5df8639`. Its published results remain available upstream; its raw fits have not been downloaded in this step. The N = 500,000 results are outside the approved stages 0–1 scope.

## Recovered score definitions

RIbench 1.0.2 `R/evaluateResults.R::computePerfMeas` computes signed endpoint deviation as the true endpoint's standardized Box–Cox value minus the estimated endpoint's standardized Box–Cox value, both using the true healthy lambda, shift, mu and sigma. Thus its sign is truth minus estimate. Preserve its special handling of zero and out-of-domain endpoints when reproducing historical scores; separately flag those values as implausible.

Two-sided overall absolute deviation is the mean of the two absolute endpoint deviations. CRP uses only its upper endpoint. RIbench calls an overall absolute deviation above 5 implausible, and its `zzDevAbsCutoff_Ov` sets those rows to NA. It does not winsorize them. Our approved primary loss instead clips each endpoint's absolute deviation at 5 before averaging. Report the historical exclusion-based metric separately and retain the approved clipping-based metric for success decisions. Also retain the protocol's max-endpoint E diagnostics and invalid-result counts.

## Approved Stage 0 endpoint rules

C2's `score.R` explicitly calls RIbench's `computeRIsAll(..., truncNormal=FALSE)`. Its `getRI()` therefore inverse-transforms ordinary normal quantiles and clips negative or invalid limits to zero. refineR 2.0.0's own `getRI()` calls `cdfTruncatedBoxCox()`, which adjusts quantiles for transformation support. A comparison using one extractor for the reference and the other for the candidate would confound a method difference with machine differences.

The user approved the following rules on 2026-11-23, before any Stage 0 fitting.

1. Keep exact same-machine equality against CRAN refineR 2.0.0, including its native `getRI()` limits, on all 2,880 sets.
2. For the C2 cross-machine audit, apply C2's frozen RIbench extraction to both new and archived fits. Keep its endpoint tolerance at 0.1% of the archived interval width. Report the native-versus-historical extraction difference separately, not as a cross-machine discrepancy. Native refineR limits remain the primary limits for anchorRefine's later stages; historical comparisons use explicitly matched extraction.
3. CRP has only a 95th-percentile upper limit. For its C2 audit, define interval width as upper limit minus the fixed lower reporting bound zero, and test only the upper limit. A nonpositive/nonfinite upper limit remains non-auditable. For scoring and capped loss, use only its requested upper endpoint; do not insert an invented second endpoint.

All 2,880 datasets enter both comparisons.

## Stage 1 preparation still required

The C2 anchors are rounded. The initial protocol explicitly requires a discrete-data calibration amendment before testing rounded observations. The continuous PIT statistic and null calibration cannot simply be applied to these values. Prepare and commit the rounded-data likelihood and calibration rules after Stage 0 review, before any Stage 1 tests. Existing archived parameters can be reused once input identity and readback checks pass; parameter availability alone is not sufficient validation.

## Execution status

The reviewed protocol is approved in the conversation. Upstream refineR source is now vendored unchanged, with its original notices and the original source archive. RIbench 1.0.2's source archive is also preserved. File SHA-256 values are in `sources/SHA256SUMS`. These are source/input preservation hashes, not a complete execution freeze: an R runtime, dependency versions, runner source, vector-hash verification and the endpoint clarification are still needed before Stage 0.

This workspace currently lacks R, and system package installation cannot write to the system directories even with an escalated execution request. No automatic approval rejection occurred; the OS denied the package-manager writes. A writable isolated R installation or an anchorRefine-only GitHub Actions environment can provide the runtime. No workflow was added or launched, and no writes were made to amromeo.github.io.
