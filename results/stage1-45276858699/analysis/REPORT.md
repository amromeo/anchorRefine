# Stage 1 rounded-anchor results

The anchor check keeps the original refineR limits when the randomized PIT likelihood-ratio test gives p ≥ 0.01. Each set uses one decision for both extraction formulas. The primary seed is 38000000 + Index. Estimates are paired with comparators by test set.

## N ≤ 5,000

The primary check declined 437/2,880 (15.2%), 95% CI 11.9% to 18.7% evaluable fits. There were 0 invalid baseline fits, 0 check failures on valid fits, and 0 declines for a zero-probability measurement interval.

Changing the PIT seed to 39000000 + Index reversed 33/2,880 (1.1%), 95% CI 0.7% to 1.7% decisions among sets evaluable twice (33/2,880 (1.1%) of all planned). 16 changed from keep to decline and 17 from decline to keep. The second seed declined 436/2,880 (15.1%) evaluable fits.

### C2 historical limits (primary)

Bad-result capture and good-result loss use the largest absolute endpoint z deviation (E). CRP contributes its upper endpoint. The denominators below include every classifiable valid baseline result in the indicated class, including any failed checks.

| Pathological fraction | Declined / evaluable | Caught E > 1 | Caught E > 5 | Declined E < 0.25 | Kept / planned | Kept mean capped absolute z |
|---|---:|---:|---:|---:|---:|---:|
| All | 437/2,880 (15.2%) | 216/411 (52.6%) | 34/42 (81.0%) | 19/1,180 (1.6%) | 2,443/2,880 | 0.287 |
| ≤20% | 122/1,440 (8.5%) | 14/22 (63.6%) | 2/2 (100.0%) | 15/916 (1.6%) | 1,318/1,440 | 0.166 |
| >20% | 315/1,440 (21.9%) | 202/389 (51.9%) | 32/40 (80.0%) | 4/264 (1.5%) | 1,125/1,440 | 0.430 |

| Method | Returned / planned | Scored | Mean absolute z | Mean capped absolute z | E 95th percentile | Capped loss with 5 for no result | Capped mean on gate-kept sets |
|---|---:|---:|---:|---:|---:|---:|---:|
| refineR alone | 2,880/2,880 | 2,880 | 0.955 | 0.394 | 2.074 | 0.394 | 0.287 |
| refineR with anchor check | 2,443/2,880 | 2,443 | 0.406 | 0.287 | 1.275 | 1.003 | 0.287 |
| Anchors only | 2,880/2,880 | 2,880 | 0.290 | 0.290 | 0.866 | 0.290 | 0.282 |
| anchoredRI (C2 old fitter) | 2,880/2,880 | 2,880 | 0.439 | 0.294 | 1.700 | 0.294 | 0.252 |
| anchoredRI (Task E raw) | 2,880/2,880 | 2,880 | 0.438 | 0.289 | 1.611 | 0.289 | 0.247 |
| anchoredRI (Task E reported) | 2,406/2,880 | 2,406 | 0.187 | 0.187 | 0.730 | 0.979 | 0.181 |

### Native refineR limits (secondary)

Bad-result capture and good-result loss use the largest absolute endpoint z deviation (E). CRP contributes its upper endpoint. The denominators below include every classifiable valid baseline result in the indicated class, including any failed checks.

| Pathological fraction | Declined / evaluable | Caught E > 1 | Caught E > 5 | Declined E < 0.25 | Kept / planned | Kept mean capped absolute z |
|---|---:|---:|---:|---:|---:|---:|
| All | 437/2,880 (15.2%) | 216/411 (52.6%) | 17/18 (94.4%) | 19/1,180 (1.6%) | 2,443/2,880 | 0.283 |
| ≤20% | 122/1,440 (8.5%) | 14/22 (63.6%) | 0/0 (–) | 15/916 (1.6%) | 1,318/1,440 | 0.166 |
| >20% | 315/1,440 (21.9%) | 202/389 (51.9%) | 17/18 (94.4%) | 4/264 (1.5%) | 1,125/1,440 | 0.421 |

| Method | Returned / planned | Scored | Mean absolute z | Mean capped absolute z | E 95th percentile | Capped loss with 5 for no result | Capped mean on gate-kept sets |
|---|---:|---:|---:|---:|---:|---:|---:|
| refineR alone | 2,880/2,880 | 2,880 | 0.413 | 0.385 | 2.020 | 0.385 | 0.283 |
| refineR with anchor check | 2,443/2,880 | 2,443 | 0.283 | 0.283 | 1.274 | 0.999 | 0.283 |
| Anchors only | 2,880/2,880 | 2,880 | 0.290 | 0.290 | 0.866 | 0.290 | 0.282 |
| anchoredRI (C2 old fitter) | 2,880/2,880 | 2,880 | 0.439 | 0.294 | 1.700 | 0.294 | 0.252 |
| anchoredRI (Task E raw) | 2,880/2,880 | 2,880 | 0.438 | 0.289 | 1.611 | 0.289 | 0.247 |
| anchoredRI (Task E reported) | 2,406/2,880 | 2,406 | 0.187 | 0.187 | 0.730 | 0.979 | 0.181 |

## N = 50,000

The primary check declined 149/1,440 (10.3%), 95% CI 6.7% to 14.9% evaluable fits. There were 0 invalid baseline fits, 0 check failures on valid fits, and 0 declines for a zero-probability measurement interval.

Changing the PIT seed to 39000000 + Index reversed 12/1,440 (0.8%), 95% CI 0.4% to 1.3% decisions among sets evaluable twice (12/1,440 (0.8%) of all planned). 5 changed from keep to decline and 7 from decline to keep. The second seed declined 147/1,440 (10.2%) evaluable fits.

### C2 historical limits (primary)

Bad-result capture and good-result loss use the largest absolute endpoint z deviation (E). CRP contributes its upper endpoint. The denominators below include every classifiable valid baseline result in the indicated class, including any failed checks.

| Pathological fraction | Declined / evaluable | Caught E > 1 | Caught E > 5 | Declined E < 0.25 | Kept / planned | Kept mean capped absolute z |
|---|---:|---:|---:|---:|---:|---:|
| All | 149/1,440 (10.3%) | 57/94 (60.6%) | 2/2 (100.0%) | 16/881 (1.8%) | 1,291/1,440 | 0.169 |
| ≤20% | 43/720 (6.0%) | 2/2 (100.0%) | 0/0 (–) | 11/624 (1.8%) | 677/720 | 0.076 |
| >20% | 106/720 (14.7%) | 55/92 (59.8%) | 2/2 (100.0%) | 5/257 (1.9%) | 614/720 | 0.272 |

| Method | Returned / planned | Scored | Mean absolute z | Mean capped absolute z | E 95th percentile | Capped loss with 5 for no result | Capped mean on gate-kept sets |
|---|---:|---:|---:|---:|---:|---:|---:|
| refineR alone | 1,440/1,440 | 1,440 | 0.310 | 0.232 | 1.135 | 0.232 | 0.169 |
| refineR with anchor check | 1,291/1,440 | 1,291 | 0.169 | 0.169 | 0.781 | 0.669 | 0.169 |
| Anchors only | 1,440/1,440 | 1,440 | 0.296 | 0.296 | 0.869 | 0.296 | 0.288 |
| anchoredRI (C2 old fitter) | 1,440/1,440 | 1,440 | 0.957 | 0.438 | 3.752 | 0.438 | 0.404 |

### Native refineR limits (secondary)

Bad-result capture and good-result loss use the largest absolute endpoint z deviation (E). CRP contributes its upper endpoint. The denominators below include every classifiable valid baseline result in the indicated class, including any failed checks.

| Pathological fraction | Declined / evaluable | Caught E > 1 | Caught E > 5 | Declined E < 0.25 | Kept / planned | Kept mean capped absolute z |
|---|---:|---:|---:|---:|---:|---:|
| All | 149/1,440 (10.3%) | 57/94 (60.6%) | 1/1 (100.0%) | 16/881 (1.8%) | 1,291/1,440 | 0.169 |
| ≤20% | 43/720 (6.0%) | 2/2 (100.0%) | 0/0 (–) | 11/624 (1.8%) | 677/720 | 0.076 |
| >20% | 106/720 (14.7%) | 55/92 (59.8%) | 1/1 (100.0%) | 5/257 (1.9%) | 614/720 | 0.271 |

| Method | Returned / planned | Scored | Mean absolute z | Mean capped absolute z | E 95th percentile | Capped loss with 5 for no result | Capped mean on gate-kept sets |
|---|---:|---:|---:|---:|---:|---:|---:|
| refineR alone | 1,440/1,440 | 1,440 | 0.230 | 0.230 | 1.135 | 0.230 | 0.169 |
| refineR with anchor check | 1,291/1,440 | 1,291 | 0.169 | 0.169 | 0.781 | 0.669 | 0.169 |
| Anchors only | 1,440/1,440 | 1,440 | 0.296 | 0.296 | 0.869 | 0.296 | 0.288 |
| anchoredRI (C2 old fitter) | 1,440/1,440 | 1,440 | 0.957 | 0.438 | 3.752 | 0.438 | 0.404 |

## Reading the tables

The capped loss clips each requested endpoint at 5, then averages within each dataset. The historical RIbench exclusion-based score drops datasets whose uncapped mean |z| exceeds 5. The files report both. The failure-penalized sensitivity assigns 5 to every unscored, failed or withheld result. The gate changes which results are returned, so the kept subset has the same refineR accuracy as ungated refineR on those same indices.

All accuracy means weight datasets equally, including one-sided CRP. Signed bias uses truth minus estimate on the healthy z scale. Measurements with infinite z retain their severity and capped loss. A missing z leaves a returned result unscored. Full paired comparisons use verified matched inputs. The native analysis changes the refineR endpoint formula only. Comparator limits and both PIT decisions remain the same under both analyses.

The 95% descriptive intervals use 2,000 paired cluster bootstrap resamples. Within each summary stratum the observed (Analyte, Scenario) groups are sampled with replacement as intact clusters using NumPy PCG64 seed 37000000. Undefined bootstrap ratios are omitted and their valid replicate count is shown. Intervals require at least two informative parent groups. Scenario-balanced estimates weight contributing groups equally. Strata overlap and their counts must not be added.

| File | Contents |
|---|---|
| [rates.csv.gz](rates.csv.gz) | Declines, failures, structural declines, both capture denominators, good losses, coverage, severity rates and seed reversals with uncertainty |
| [accuracy.csv.gz](accuracy.csv.gz) | Own available and gate-kept populations, returned and scored denominators, loss, E quantiles, historical score and failure sensitivity |
| [endpoints.csv.gz](endpoints.csv.gz) | Signed bias and mean, median and capped endpoint errors |
| [paired-loss.csv.gz](paired-loss.csv.gz) | Paired differences in mean capped loss and bootstrap intervals for common-scored, separately returned and failure-penalized populations |
| [boundary-counts.csv.gz](boundary-counts.csv.gz) | Counts exactly at each strict threshold for intervals and individual endpoints |

Each file includes overall, pathological-fraction, individual N, analyte, and Scenario rows. The raw and reported Task E rows, when present, distinguish its selected fits from outputs released by its original safeguard. The C2 old-fitter row is the historical anchoredRI comparator.
