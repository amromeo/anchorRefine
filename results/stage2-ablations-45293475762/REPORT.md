# K24 development ablations

The same 1,440 development datasets and 40 guidance anchors per dataset were used for all arms. Unchanged refineR and full K24 use the archived fits and panel decisions from the original development run. Each ablation activates one component of the original K24 search and uses the same clarity requirement.

## Accuracy before the check

Each difference subtracts the unchanged refineR loss from the indicated arm’s loss. Negative values favor that arm. Each dataset contributes the mean of its two absolute endpoint z errors, capped at 5 per endpoint. A missing interval contributes 5. Fallback cases count in their assigned arm. The four primary strata pool rounding increments and replicates.

### Native refineR limits (primary)

| N | Pathology | Datasets | refineR loss | Full K24 Δ | Peak only Δ | Starting values only Δ | Search regions only Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1,500 | >20% | 432 | 0.7744 | -0.1493 | -0.1511 | -0.0005 | -0.1772 |
| 1,500 | <=20% | 288 | 0.2083 | +0.0156 | +0.0026 | +0.0004 | +0.0164 |
| 50,000 | >20% | 432 | 0.5669 | -0.3310 | -0.3441 | -0.0023 | -0.2910 |
| 50,000 | <=20% | 288 | 0.0768 | +0.0286 | +0.0000 | +0.0001 | +0.0526 |


### Historical C2 limits (secondary)

| N | Pathology | Datasets | refineR loss | Full K24 Δ | Peak only Δ | Starting values only Δ | Search regions only Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1,500 | >20% | 432 | 0.7823 | -0.1522 | -0.1511 | -0.0021 | -0.1778 |
| 1,500 | <=20% | 288 | 0.2109 | +0.0159 | +0.0028 | +0.0002 | +0.0151 |
| 50,000 | >20% | 432 | 0.5669 | -0.3310 | -0.3441 | -0.0023 | -0.2898 |
| 50,000 | <=20% | 288 | 0.0768 | +0.0286 | +0.0000 | +0.0001 | +0.0527 |

### Healthy families and disease patterns

These native-limit differences pool both routine sample sizes. The downloadable paired loss table also gives each healthy family × disease pattern × N × pathology combination with its interval.

| Family or disease pattern | Pathology | Datasets | Full K24 Δ | Peak only Δ | Starting values only Δ | Search regions only Δ |
| --- | --- | --- | --- | --- | --- | --- |
| linear | >20% | 288 | -0.2202 | -0.2259 | +0.0015 | -0.2038 |
| linear | <=20% | 192 | +0.0151 | -0.0000 | +0.0006 | +0.0252 |
| lognormal | >20% | 288 | -0.2813 | -0.2916 | -0.0046 | -0.2689 |
| lognormal | <=20% | 192 | +0.0241 | +0.0039 | -0.0000 | +0.0496 |
| power_0.5 | >20% | 288 | -0.2190 | -0.2252 | -0.0011 | -0.2297 |
| power_0.5 | <=20% | 192 | +0.0271 | +0.0000 | +0.0002 | +0.0287 |
| bilateral_separated | >20% | 144 | -0.0725 | -0.0618 | -0.0094 | -0.0855 |
| bilateral_separated | <=20% | 96 | +0.0382 | +0.0007 | -0.0003 | +0.0555 |
| left_separated | >20% | 144 | -0.7514 | -0.7555 | -0.0106 | -0.7550 |
| left_separated | <=20% | 96 | +0.0207 | +0.0000 | +0.0042 | +0.0271 |
| left_shoulder | >20% | 144 | +0.0241 | +0.0000 | +0.0027 | +0.0236 |
| left_shoulder | <=20% | 96 | +0.0163 | +0.0029 | +0.0034 | +0.0274 |
| overlapping | >20% | 144 | -0.0026 | -0.0001 | +0.0041 | -0.0070 |
| overlapping | <=20% | 96 | +0.0277 | +0.0000 | -0.0039 | +0.0348 |
| right_separated | >20% | 144 | -0.6537 | -0.6668 | +0.0071 | -0.5983 |
| right_separated | <=20% | 96 | +0.0209 | +0.0042 | +0.0017 | +0.0381 |
| right_shoulder | >20% | 144 | +0.0152 | -0.0014 | -0.0022 | +0.0176 |
| right_shoulder | <=20% | 96 | +0.0089 | +0.0000 | -0.0034 | +0.0241 |

## When the search fell back to refineR

A failed initial election stops guidance immediately. A later search failure follows a clear election. A pass1_regions no_peak_in_basin failure means the search then found no eligible peak in the retained basin while defining first-pass regions.

| Full K24 step | Recorded reason | Share of all K24 fallbacks | Share of assigned datasets |
| --- | --- | --- | --- |
| initial_election | insufficient_votes | 273/331 (82.5%) | 273/1,440 (19.0%) |
| initial_election | peak_outside_anchor_quantiles | 2/331 (0.6%) | 2/1,440 (0.1%) |
| initial_election | tied_vote | 17/331 (5.1%) | 17/1,440 (1.2%) |
| pass1_regions | pass1_regions stage2_peak: no_peak_in_basin | 39/331 (11.8%) | 39/1,440 (2.7%) |


| Arm | Fallbacks | Fallback fits that also failed |
| --- | --- | --- |
| Full K24 | 331/1,440 (23.0%) | 0 |
| Peak only | 331/1,440 (23.0%) | 0 |
| Starting values only | 293/1,440 (20.3%) | 1 |
| Search regions only | 292/1,440 (20.3%) | 0 |

## First coarse peak

The native differences below compare each unchanged arm with pass-through on the same cases. The groups use the actual upstream raw coarse peak and the elected anchor peak. An unclear election forms a third group. These conditional means describe existing fits.

| First coarse peak | N | Pathology | Datasets | Full K24 Δ | Peak only Δ | Starting values only Δ | Search regions only Δ |
| --- | --- | --- | --- | --- | --- | --- | --- |
| same | 1,500 | >20% | 228 | -0.0081 | -0.0098 | -0.0060 | -0.0260 |
| same | 1,500 | <=20% | 173 | +0.0260 | +0.0043 | +0.0007 | +0.0262 |
| same | 50,000 | >20% | 362 | +0.0177 | +0.0001 | -0.0008 | +0.0396 |
| same | 50,000 | <=20% | 285 | +0.0289 | +0.0000 | +0.0001 | +0.0532 |
| different | 1,500 | >20% | 36 | -1.7400 | -1.7512 | +0.0328 | -1.9614 |
| different | 1,500 | <=20% | 1 | +0.0000 | +0.0000 | -0.0000 | +0.1858 |
| different | 50,000 | >20% | 63 | -2.3716 | -2.3603 | -0.0113 | -2.2230 |
| different | 50,000 | <=20% | 0 | — | — | — | — |
| no_clear_election | 1,500 | >20% | 168 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| no_clear_election | 1,500 | <=20% | 114 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| no_clear_election | 50,000 | >20% | 7 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| no_clear_election | 50,000 | <=20% | 3 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |

## Disagreement between the two 40-anchor panels

For each fixed fit, the table compares the decision from its original guidance panel with the decision from its fresh independent panel. Unchanged refineR uses neither panel to fit its interval. The original full K24 fit used the guidance panel. A switch in either direction counts as disagreement.

| PIT seed | Fit | Evaluable IDs | Disagreement | Keep → decline | Decline → keep | Excluded from denominator |
| --- | --- | --- | --- | --- | --- | --- |
| primary | Unchanged refineR | own | 148/1,439 (10.3%) | 71 | 77 | 1 |
| primary | Unchanged refineR | common | 148/1,439 (10.3%) | 71 | 77 | 1 |
| primary | Full K24 | own | 155/1,440 (10.8%) | 79 | 76 | 0 |
| primary | Full K24 | common | 155/1,439 (10.8%) | 79 | 76 | 1 |
| alternate | Unchanged refineR | own | 153/1,439 (10.6%) | 72 | 81 | 1 |
| alternate | Unchanged refineR | common | 153/1,439 (10.6%) | 72 | 81 | 1 |
| alternate | Full K24 | own | 157/1,440 (10.9%) | 82 | 75 | 0 |
| alternate | Full K24 | common | 157/1,439 (10.9%) | 82 | 75 | 1 |


| PIT seed | Common IDs | Only K24 disagreed | Only refineR disagreed | K24 − refineR (percentage points) | 95% interval (points) |
| --- | --- | --- | --- | --- | --- |
| primary | 1439 | 41 | 34 | +0.49 | [-0.625, +1.603] |
| alternate | 1439 | 38 | 34 | +0.28 | [-0.835, +1.458] |

With the primary PIT seed, changing panels reversed 148/1,439 (10.3%) of evaluable unchanged refineR decisions and 155/1,440 (10.8%) of full K24 decisions. On the 1,439 common datasets the difference was +0.49 percentage points. 

The baseline measures how often two independent healthy panels give different decisions for a fit made without either panel. The K24 comparison also reflects its different fitted distributions and its use of the original panel in the search. These data do not isolate the effect of reuse from the change in fitted distributions.

## Data tables

- Per-dataset paired differences in all-set loss, the two arm means, nonreturns, fit failures and implausible counts are summarized for every marginal and cross of pathology, sample size, disease pattern and healthy family. Implausibility requires an uncapped mean absolute endpoint z error above 5. [Individual paired losses](case-loss.csv) · [Grouped paired losses](paired-loss.csv)
- The first coarse peak comparison is available by sample size and pathology with both endpoint extractions. [Peak diagnostic](peak-diagnostic.csv)
- Every fallback has a case identifier, stage, complete recorded reason, final fit status and design factors. [Cases](fallback-cases.csv) · [Counts by step](fallback-steps.csv) · [Fallback rates](fallback-rates.csv)
- Panel tables give own and common evaluable populations, directional transitions, paired differences and cluster intervals for both PIT seeds. [Panel disagreement](panel-noise.csv) · [Paired differences](paired-panel-noise.csv)

The 95% percentile intervals resample complete factorial cells, keeping all replicates in the selected stratum together. Each stratum uses 2,000 draws and PCG64 seed 37000000. Paired differences use identical case weights for both estimators. The tables count undefined replicates and omit intervals for fewer than two informative cells. Component contrasts evaluate each component in isolation. Combining components can change the peak and grid jointly, so these contrasts need not add to the full K24 effect.
