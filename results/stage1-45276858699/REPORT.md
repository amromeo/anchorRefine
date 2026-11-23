# Stage 1 review

Forty independent, screened healthy anchors were tested against each of 4,320 archived refineR fits. The primary comparisons use the historical C2 reference limits. Both those limits and native refineR limits are available for every fit, including declined fits. The check gives one decision per fit.

| Primary result | N ≤ 5,000 | N = 50,000 |
|---|---:|---:|
| Declined at p < 0.01 | 437/2,880 (15.2%) | 149/1,440 (10.3%) |
| Caught among E > 1 | 216/411 (52.6%) | 57/94 (60.6%) |
| Caught among E > 5 | 34/42 (81.0%) | 2/2 (100.0%) |
| Declined among E < 0.25 | 19/1,180 (1.6%) | 16/881 (1.8%) |
| Decision changed with alternate PIT seed | 33/2,880 (1.1%) | 12/1,440 (0.8%) |

E is the largest absolute signed RIbench z error among a dataset’s requested endpoints. CRP has one requested endpoint. At greater than 20% pathology, the check caught 202 of 389 small-cohort results with E > 1 (51.9%) and 55 of 92 large-cohort results (59.8%).

With native refineR limits, fewer baseline results crossed E > 5. The same decisions caught 17 of 18 small-cohort results and 1 of 1 large-cohort result. Only two large-cohort results crossed that threshold even with the historical limits.

| Mean capped absolute z | N ≤ 5,000 | N = 50,000 |
|---|---:|---:|
| refineR, all datasets | 0.394 | 0.232 |
| refineR, kept datasets | 0.287 | 0.169 |
| Anchors only, same kept datasets | 0.282 | 0.288 |
| anchoredRI C2 old fitter, same kept datasets | 0.252 | 0.404 |
| anchoredRI Task E improved fitter, raw estimates on the same kept datasets | 0.247 | Incomplete export |
| Anchor check, all datasets with loss 5 for a withheld result | 1.003 | 0.669 |

The check selects which estimates to release. Each released endpoint was identical to its ungated refineR value. The loss caps each endpoint error at 5 and averages within each dataset. The full comparison includes each method’s own coverage and the separate Task E safeguard row. Its frozen export covered all 2,880 small datasets and 144 of the 1,440 large datasets.

On the 2,443 kept small-cohort datasets, anchors-only and both anchoredRI fitters had lower mean capped error than refineR. On the 1,291 kept large-cohort datasets, refineR had lower mean capped error than either available comparator. Assigning the prespecified loss of 5 to a declined result raised the all-dataset loss above ungated refineR in both cohorts.

## Calibration and reproducibility

All 16 null checks passed across four designs, two PIT seeds and two nominal rejection rates. At the nominal 1% level the observed rejection rates ranged from 0.943% to 1.049%. The grid-of-ten simulation generated 100,000 panels in which every recorded anchor had the same rounded value. Both PIT seeds passed calibration there. Calibration is conditional on the fixed healthy model being correct. [Simulation counts](calibration/calibration.csv) · [Independent numerical calculation](calibration/calibration-numerics.csv)

The small-cohort audit finished before large-cohort execution began. All 4,320 routine identities, anchor panels, and archived fits were verified. All fits and tests were evaluable. Both cohorts passed the exact same-host repeat and the audit on a separate runner. The largest cross-machine difference in a p-value or finite endpoint was zero. An independent readback matched all 24,624 historical endpoint estimates and corresponding signed z scores across refineR, anchors-only and C2 anchoredRI exactly. [Small audit](small/audit-summary.json) · [Large audit](large/audit-summary.json) · [50,000-sample routine identities](artifacts/large-inputs.zip)

The first run stopped in the audit reader on a scientific-notation sample size in the RIbench inventory. Its data and logs are preserved. The corrected run reproduced the first run’s calibration tables and small-cohort numeric outputs byte for byte. [Initial run record](../stage1-45276328667/) · [Execution record](../../PROTOCOL.md#stage-1-execution-record)

## Data and detailed results

- [Full report](analysis/REPORT.md) with the historical and native analyses, pathological-fraction strata and comparator accuracy. Its five downloadable tables include uncertainty intervals, endpoint-level errors, individual sample sizes and scenarios.
- [Small-cohort decisions](small/checks.csv.gz) and [endpoint estimates](small/estimates.csv.gz), with both PIT seeds and both extractions.
- [Large-cohort decisions](large/checks.csv.gz) and [endpoint estimates](large/estimates.csv.gz), with both PIT seeds and both extractions.
- [Archive readback](postread/) comparing historical signed z and estimated limits with the full-precision C2 performance R objects.
- [Original Actions artifacts](artifacts/), [GitHub digests](actions-artifacts.json), [complete job logs](actions-logs.zip) and [SHA-256 manifest](SHA256SUMS).
- [Approved protocol](../../PROTOCOL.md) · [Frozen run source](https://github.com/amromeo/anchorRefine/commit/ec7ab5400b61ff732dec34aa6460d96bbc623ea0) · [GitHub Actions run](https://github.com/amromeo/anchorRefine/actions/runs/45276858699)
