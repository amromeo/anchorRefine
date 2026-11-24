# Stage 2 confirmation

The frozen K24 peak-only fitter **met** its prespecified native-limit criteria against unchanged refineR. Its checked release **met** the criteria against refineR after both received the same check. The study used 2,880 fresh simulated routine datasets and eight independent replicates in each of 360 design cells. The frozen candidate and peak-only ablation had identical fits, limits and check decisions in all 2,880 cases.

## Candidate versus refineR

Each dataset contributes the average of the two absolute healthy-scale endpoint z errors after clipping each at 5. An unavailable interval contributes 5. A negative difference favors the candidate. The healthy Box–Cox support correction is included in the native limits used for the success criteria.

### Before checking

| N | Pathology | Datasets | Candidate loss | refineR loss | Δ [95% interval] | Implausible, candidate / refineR | Nonreturns, candidate / refineR | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,500 | >20% | 864 | 0.6015 | 0.7697 | -0.1682 [-0.259, -0.092] | 0 / 0 | 0 / 0 | met |
| 1,500 | <=20% | 576 | 0.2065 | 0.2076 | -0.0011 [-0.003, -0.000] | 0 / 0 | 0 / 0 | met |
| 50,000 | >20% | 864 | 0.2087 | 0.5667 | -0.3580 [-0.550, -0.188] | 0 / 0 | 0 / 0 | met |
| 50,000 | <=20% | 576 | 0.0778 | 0.0778 | -0.0000 [-0.000, +0.000] | 0 / 0 | 0 / 0 | met |


### Released after the primary guidance-panel check

| N | Pathology | Datasets | Candidate loss | refineR loss | Δ [95% interval] | Implausible, candidate / refineR | Nonreturns, candidate / refineR | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,500 | >20% | 864 | 1.5437 | 1.8504 | -0.3067 [-0.469, -0.164] | 0 / 0 | 231 / 287 | met |
| 1,500 | <=20% | 576 | 0.4859 | 0.4947 | -0.0088 [-0.026, -0.000] | 0 / 0 | 36 / 37 | met |
| 50,000 | >20% | 864 | 0.6282 | 1.2435 | -0.6153 [-0.944, -0.328] | 0 / 0 | 80 / 189 | met |
| 50,000 | <=20% | 576 | 0.1710 | 0.1710 | -0.0000 [-0.000, +0.000] | 0 / 0 | 11 / 11 | met |

Above 20% pathology the loss difference must be strictly negative. At 20% or below the maximum permitted excess is 0.02. Both strata also require candidate implausible and nonreturn counts no greater than refineR. An implausible returned interval has uncapped mean absolute endpoint z error above 5. A missing or declined interval carries the full loss penalty. The gate decisions use the point estimates.

## Individual components

Each native-limit difference compares the indicated arm with unchanged refineR on identical datasets. The checked columns apply the primary check to both arms. The three component arms describe how the fixed search operations behaved in confirmation.

| N | Pathology | Peak pre | Peak checked | Starts pre | Starts checked | Regions pre | Regions checked |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1,500 | >20% | -0.1682 | -0.3067 | -0.0034 | -0.0343 | -0.1650 | -0.2402 |
| 1,500 | <=20% | -0.0011 | -0.0088 | +0.0036 | +0.0264 | +0.0162 | +0.0889 |
| 50,000 | >20% | -0.3580 | -0.6153 | +0.0005 | -0.0047 | -0.3133 | -0.4492 |
| 50,000 | <=20% | -0.0000 | -0.0000 | -0.0006 | -0.0002 | +0.0365 | +0.1098 |

## Coverage and error among returned intervals

Overall means below give each dataset equal weight. The kept-set means use each arm's own finite returned intervals. The paired common-returned table additionally compares the methods on the same jointly available cases.

| Arm | Mode | Returned | Returned capped loss | All-set loss | Implausible | E > 5 | Nonfinite | Outside support | Unordered | Fit failures | Fallbacks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 2,880/2,880 (100.0%) | 0.4580 | 0.4580 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Unchanged refineR | checked | 2,356/2,880 (81.8%) | 0.1853 | 1.0613 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Frozen candidate (peak only) | pre | 2,880/2,880 (100.0%) | 0.2999 | 0.2999 | 0 | 0 | 0 | 0 | 0 | 0 | 645 |
| Frozen candidate (peak only) | checked | 2,522/2,880 (87.6%) | 0.1843 | 0.7829 | 0 | 0 | 0 | 0 | 0 | 0 | 645 |
| Peak only | pre | 2,880/2,880 (100.0%) | 0.2999 | 0.2999 | 0 | 0 | 0 | 0 | 0 | 0 | 645 |
| Peak only | checked | 2,522/2,880 (87.6%) | 0.1843 | 0.7829 | 0 | 0 | 0 | 0 | 0 | 0 | 645 |
| Starting values only | pre | 2,880/2,880 (100.0%) | 0.4577 | 0.4577 | 0 | 0 | 0 | 0 | 0 | 0 | 582 |
| Starting values only | checked | 2,360/2,880 (81.9%) | 0.1856 | 1.0548 | 0 | 0 | 0 | 0 | 0 | 0 | 582 |
| Search regions only | pre | 2,880/2,880 (100.0%) | 0.3250 | 0.3250 | 0 | 0 | 0 | 0 | 0 | 0 | 582 |
| Search regions only | checked | 2,468/2,880 (85.7%) | 0.2088 | 0.8942 | 0 | 0 | 0 | 0 | 0 | 0 | 582 |

## Disease distribution

The following native paired differences pool both routine sample sizes. The fully crossed tables give disease, healthy family, pathology and sample size together.

| Disease pattern | Pathology | Datasets | Pre-check Δ | Checked Δ |
| --- | --- | --- | --- | --- |
| bilateral_separated | >20% | 288 | -0.0333 | -0.0634 |
| bilateral_separated | <=20% | 192 | -0.0017 | -0.0248 |
| left_separated | >20% | 288 | -0.7440 | -1.2862 |
| left_separated | <=20% | 192 | +0.0000 | +0.0000 |
| left_shoulder | >20% | 288 | +0.0007 | +0.0162 |
| left_shoulder | <=20% | 192 | -0.0000 | -0.0000 |
| overlapping | >20% | 288 | -0.0001 | -0.0001 |
| overlapping | <=20% | 192 | +0.0000 | +0.0000 |
| right_separated | >20% | 288 | -0.8019 | -1.4158 |
| right_separated | <=20% | 192 | -0.0014 | -0.0014 |
| right_shoulder | >20% | 288 | -0.0000 | -0.0168 |
| right_shoulder | <=20% | 192 | -0.0002 | -0.0002 |

## Guidance and fresh-panel checks

A fit is declined at p < 0.01. E is the larger absolute endpoint z error of the corresponding pre-check native fit. The capture and good-loss fractions below count every classifiable valid fit in that error category. The fresh panel was drawn independently of fitting. Actual release uses the guidance panel and primary randomized PIT seed.

| Arm | Panel | PIT seed | Evaluable declined | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | guidance | primary | 524/2,880 (18.2%) | 289/317 (91.2%) | 0/0 | 36/1,497 (2.4%) |
| Unchanged refineR | guidance | alternate | 522/2,880 (18.1%) | 288/317 (90.9%) | 0/0 | 33/1,497 (2.2%) |
| Unchanged refineR | diagnostic | primary | 521/2,880 (18.1%) | 287/317 (90.5%) | 0/0 | 24/1,497 (1.6%) |
| Unchanged refineR | diagnostic | alternate | 523/2,880 (18.2%) | 288/317 (90.9%) | 0/0 | 24/1,497 (1.6%) |
| Frozen candidate (peak only) | guidance | primary | 358/2,880 (12.4%) | 123/155 (79.4%) | 0/0 | 35/1,603 (2.2%) |
| Frozen candidate (peak only) | guidance | alternate | 356/2,880 (12.4%) | 122/155 (78.7%) | 0/0 | 32/1,603 (2.0%) |
| Frozen candidate (peak only) | diagnostic | primary | 363/2,880 (12.6%) | 122/155 (78.7%) | 0/0 | 27/1,603 (1.7%) |
| Frozen candidate (peak only) | diagnostic | alternate | 367/2,880 (12.7%) | 125/155 (80.6%) | 0/0 | 27/1,603 (1.7%) |


| PIT seed | refineR panel switches | Candidate panel switches | Common evaluable | Only candidate switched | Only refineR switched | Paired excess in points [95% interval] |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 331/2,880 (11.5%) | 339/2,880 (11.8%) | 2880 | 10 | 2 | +0.28 [+0.035, +0.521] |
| alternate | 335/2,880 (11.6%) | 345/2,880 (12.0%) | 2880 | 12 | 2 | +0.35 [+0.104, +0.625] |

Panel disagreement includes changes in both the 40 measurements and the randomized PIT draw. The paired excess uses only datasets evaluable under both panels in both arms. A fresh panel can change the decision even when a fit was made independently of both panels.

## Descriptive endpoint and release comparisons

The historical C2 extraction uses the same fitted parameters and check decisions. The native checked-candidate versus ungated-refineR comparison includes the cost of withholding an interval on the candidate side.

| N | Pathology | Historical pre Δ | Historical checked Δ | Native checked vs ungated Δ |
| --- | --- | --- | --- | --- |
| 1,500 | >20% | -0.1671 | -0.3063 | +0.7740 |
| 1,500 | <=20% | -0.0011 | -0.0088 | +0.2783 |
| 50,000 | >20% | -0.3578 | -0.6151 | +0.0615 |
| 50,000 | <=20% | -0.0000 | -0.0000 | +0.0932 |

## Reproducibility and files

All 14,400 fits and 57,600 check records passed the technical audit. The same-host repeats matched across 48 shards. The distinct-host comparison covered 48 shards. Maximum differences were 0 of reference width for endpoints and 0 for p-values. [Audit](evidence/audit.json)

The 95% descriptive intervals use 2,000 paired percentile resamples of factorial cells with PCG64 seed 37000000. All replicates in a sampled cell keep their common weight. Tables include valid and undefined replicate counts. An interval requires at least two informative cells.

- All four primary strata include raw counts for each numerical gate. [Gate details](gates.csv)
- Paired contrasts cover all marginal and joint groups of N, pathology, disease and healthy family, exact fractions and rounding, and all 360 factorial cells. [Paired loss](paired-loss.csv.gz) · [Common returned](common-returned.csv.gz) · [Cells](factorial-cells.csv.gz)
- Each arm has before- and after-check accuracy, coverage, endpoint bias and error, and fallback counts by recorded reason. [Accuracy](accuracy.csv.gz) · [Coverage](coverage.csv.gz) · [Endpoints](endpoints.csv.gz) · [Fallbacks](fallback.csv.gz)
- Both panels and both seeds have denominator-specific decline, bad capture, good loss, and failures, with separate endpoint-level analyses. [Panel rates](panel-rates.csv.gz) · [Decision reversals](decision-pairs.csv.gz) · [Paired panel disagreement](paired-panel-noise.csv.gz)
- Each fit and each panel decision is available by dataset. [Fits](evidence/fits.csv.gz) · [Checks](evidence/checks.csv.gz)
