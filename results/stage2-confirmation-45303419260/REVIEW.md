# Stage 2 confirmation review

**The K = 24 peak-choice-only fit met all four native-limit confirmation gates. Its checked release also met all four gates against checked refineR.** The study included 2,880 independent simulated datasets across 360 factorial cells. Both methods returned an interval before checking on every dataset. Neither had an implausible interval. The candidate used its fallback on 645 datasets (22.4%). In 582 cases the anchors did not identify a clear peak. In 63 the search lost the selected peak. All 645 returned the unchanged refineR fit.

## Why peak choice alone was selected

On development datasets where the anchors and refineR chose different peaks, full K = 24 had lower mean capped error than the peak-only arm at N = 50,000 but higher error at N = 1,500. The fixed selection rule required lower error at both. The selected rule uses the original peak-only arm everywhere and keeps its existing fallback. Every one of its 1,440 development fits and 5,760 checks reproduced before confirmation opened. [Decision and absolute development means](../../PROTOCOL.md#stage-2-candidate-decision-after-the-development-ablations) · [Development reproduction](../stage2-selected-development-45299765250/REPORT.md)

## Accuracy on fresh data

Each difference subtracts the matched refineR loss from the candidate loss using native reference limits. Negative values favor the candidate. Each dataset contributes the average of two absolute endpoint z errors capped at 5. After checking, a decline costs 5 on either side. The intervals are 95% paired percentile intervals clustered by factorial cell. The prespecified gates use the point estimates.

| Routine N | Pathology | Datasets | Before check, difference [95% interval] | After same check, difference [95% interval] | After-check nonreturns, candidate / refineR |
|---:|---|---:|---:|---:|---:|
| 1,500 | >20% | 864 | -0.1682 [-0.2588, -0.0918] | -0.3067 [-0.4692, -0.1638] | 231 / 287 |
| 1,500 | ≤20% | 576 | -0.0011 [-0.00273, -0.00001] | -0.0088 [-0.02582, -0.00001] | 36 / 37 |
| 50,000 | >20% | 864 | -0.3580 [-0.5501, -0.1884] | -0.6153 [-0.9442, -0.3276] | 80 / 189 |
| 50,000 | ≤20% | 576 | -0.00001 [-0.00003, 0] | -0.00001 [-0.00003, 0] | 11 / 11 |

Above 20% pathology the largest improvements were for separated disease on the left (change in pre-check loss -0.7440) and right (-0.8019). Bilateral separated disease gave -0.0333. The absolute changes for the two shoulders and centered overlap were all below 0.001. The high-pathology averages thus depend on where the pathological values fall relative to the healthy peak. The frozen candidate and peak-only ablation matched exactly across all 2,880 datasets. [All three ablations, raw losses and historical limits](REPORT.md) · [Gates](gates.csv) · [Paired losses by subgroup](paired-loss.csv.gz)

## What the check caught

E is the larger of the two absolute endpoint z errors on the pre-check native interval. Each row uses the primary randomized PIT seed on that panel. Only the guidance panel determines release.

| Panel on selected fit | All declines | Bad results caught (E > 1) | Severe results caught (E > 5) | Good results declined (E < 0.25) |
|---|---:|---:|---:|---:|
| Guidance | 358/2,880 (12.4%) | 123/155 (79.4%) | No eligible fits | 35/1,603 (2.2%) |
| Fresh diagnostic | 363/2,880 (12.6%) | 122/155 (78.7%) | No eligible fits | 27/1,603 (1.7%) |

Switching panels changed 339/2,880 candidate decisions (11.8%) and 331/2,880 refineR decisions (11.5%). The paired difference was +0.28 percentage points (95% interval +0.03 to +0.52). [Both panels and both seeds](panel-rates.csv.gz) · [Paired panel decisions](paired-panel-noise.csv.gz)

## Reproducibility

All 48 same-machine repetitions matched byte for byte. Across 48 independent-machine comparisons, the largest endpoint difference was 0 times the interval width and the largest absolute p-value difference was 0. In the first Actions attempt, job 15 timed out downloading the repository before fitting. GitHub retained the other 47 jobs. A failed-job retry at the same commit ran job 15 and the aggregate audit. An independent calculation from the 48 primary shard archives reproduced the gate decisions, paired intervals, panel metrics, fallback counts and disease-pattern comparisons. This completes the simulated confirmation study. RIbench remains pending review. [Audit](evidence/audit.json) · [Original archives](artifacts/) · [Job logs](actions-logs.zip) · [Confirmation run](https://github.com/amromeo/anchorRefine/actions/runs/45303419260)
