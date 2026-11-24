# Stage 2 development review of the K = 24 ablations

**I recommend using unchanged refineR whenever the anchors and refineR choose the same first peak.** At N = 50,000 and ≤20% pathology, the two methods chose the same peak in 285 of 288 datasets. In those 285, the full K = 24 search increased mean capped error by 0.0289. The other three elections were unclear and fell back to refineR. Above 20% pathology, choosing a different peak identified the cases with the largest gains at both sample sizes.

The proposed rule would compare the two detected peak indices on the same first raw-scale, 512-bin density, before interpolation. If the K = 24 election is clear and both indices agree, use the complete upstream refineR fit with its original routine seed. If the indices differ, use the full K = 24 search. An unclear election or failed guided search would follow the existing fallback rule. Apply the Stage 1 check to the resulting fit. This is a proposal for review. Confirmation remains unopened. Only the previously specified development arms were run or scored.

## What changed when each component acted alone?

Each entry is the paired change in **pre-check mean capped absolute endpoint z error** from unchanged refineR, using native limits. Negative values favor the indicated method. Each dataset contributes the average of its two absolute endpoint errors, each capped at 5. A missing interval contributes 5. The full K = 24 column is the original development candidate.

| Routine N | Pathology | Datasets | Peak choice only | Starting values only | Search regions only | Full K = 24 |
|---:|---|---:|---:|---:|---:|---:|
| 1,500 | >20% | 432 | −0.1511 | −0.0005 | −0.1772 | −0.1493 |
| 1,500 | ≤20% | 288 | +0.0026 | +0.0004 | +0.0164 | +0.0156 |
| 50,000 | >20% | 432 | −0.3441 | −0.0023 | −0.2910 | −0.3310 |
| 50,000 | ≤20% | 288 | +0.0000 | +0.0001 | +0.0526 | +0.0286 |

At N = 50,000 and ≤20% pathology, search regions alone increased loss by 0.0526 against a 0.02 margin. Peak choice alone gave the same mean loss as unchanged refineR there. Starting values alone changed the mean by at most 0.0023 in any of the four strata.

Above 20% pathology, peak choice alone reduced mean loss by 0.7555 for separated disease on the left and 0.6668 for separated disease on the right. The reduction was 0.0618 for bilateral separated disease. For the two shoulder patterns and centered overlap, the absolute change was at most 0.0014. All three healthy families benefited on average in this stratum, by 0.2259 for the linear model, 0.2916 for the lognormal model and 0.2252 for the power model (λ = 0.5). [All three ablations by disease pattern and healthy family, with secondary historical limits](REPORT.md) · [All 72 combinations of pathology, N, disease pattern and healthy family](fully-crossed.csv) · [Marginal and pooled groups](marginal-and-pooled.csv) · [Paired differences and 95% intervals](paired-loss.csv)

## Where did the full K = 24 search help?

Above 20% pathology, 36 datasets at N = 1,500 and 63 at N = 50,000 had a clear anchor choice that differed from refineR's first peak. On those datasets the full K = 24 search reduced loss by **1.7400** and **2.3716**, respectively. Where the two choices agreed, full K = 24 changed loss by −0.0081 at N = 1,500 and +0.0177 at N = 50,000. In the lower-pathology stratum the changes on same-peak datasets were +0.0260 and +0.0289.

Across all 1,440 datasets, there were 1,048 same-peak elections, 100 different-peak elections and 292 unclear elections. Of the 100 differing choices, 99 occurred above 20% pathology. The proposed rule uses only the peak choices observable at fit time. These conditional comparisons describe the original development fits and do not establish the amended rule's performance. If approved, the next step is to freeze the amendment and rerun development once before opening confirmation. [Counts and estimates by first peak](peak-diagnostic.csv)

## When did the full candidate fall back?

Full K = 24 returned to unchanged refineR on **331/1,440 datasets (23.0%)**. For 292 datasets the initial election failed. A further 39 had a clear election, but the first search for regions found no eligible peak in the elected basin. All 331 fallback fits returned an interval.

| Group | Fallbacks / assigned | Rate | Too few votes | Tied vote | Outside anchor 10th–90th percentiles | No peak in basin during first search |
|---|---:|---:|---:|---:|---:|---:|
| All | 331/1,440 | 23.0% | 273 | 17 | 2 | 39 |
| N = 1,500, >20% | 187/432 | 43.3% | 158 | 9 | 1 | 19 |
| N = 1,500, ≤20% | 119/288 | 41.3% | 106 | 8 | 0 | 5 |
| N = 50,000, >20% | 21/432 | 4.9% | 6 | 0 | 1 | 14 |
| N = 50,000, ≤20% | 4/288 | 1.4% | 3 | 0 | 0 | 1 |
| Linear | 125/480 | 26.0% | 113 | 4 | 0 | 8 |
| Lognormal | 91/480 | 19.0% | 65 | 3 | 1 | 22 |
| Power (λ = 0.5) | 115/480 | 24.0% | 95 | 10 | 1 | 9 |
| Bilateral separated | 30/240 | 12.5% | 11 | 0 | 0 | 19 |
| Left separated | 71/240 | 29.6% | 66 | 3 | 0 | 2 |
| Left shoulder | 69/240 | 28.8% | 59 | 3 | 2 | 5 |
| Centered overlap | 51/240 | 21.3% | 43 | 5 | 0 | 3 |
| Right separated | 32/240 | 13.3% | 28 | 2 | 0 | 2 |
| Right shoulder | 78/240 | 32.5% | 66 | 4 | 0 | 8 |

Sample-size and pathology rows partition the development data. Family and disease rows each give a separate breakdown of the same data. [Fallbacks and reasons for all 72 combinations](fully-crossed.csv) · [Fallback step for each dataset](fallback-cases.csv)

## How often did changing the 40-anchor panel reverse the decision?

With the primary randomized PIT seed, the two panels disagreed on **148/1,439 (10.3%)** evaluable unchanged refineR fits and **155/1,440 (10.8%)** full K = 24 fits. One unchanged refineR fit failed before checking. Among the 1,439 evaluable by both methods, 41 datasets showed disagreement only for K = 24 and 34 only for refineR. The paired excess for K = 24 was **0.49 percentage points** (95% factorial-cell bootstrap interval **−0.63 to +1.60**). The alternate seed gave 10.6% and 10.9%, a paired difference of +0.28 points. Switching panels reversed about one decision in ten even when neither panel helped fit the interval. The comparison cannot separate the effect of reusing anchors from differences in the fitted distributions. [Panel transitions and both seeds](REPORT.md#disagreement-between-the-two-40-anchor-panels) · [Paired panel differences](paired-panel-noise.csv)

## Accuracy after the Stage 1 check

These paired differences compare each arm with refineR **after the same primary guidance-panel check**. A decline or failure contributes loss 5 on either side. Peak choice alone reduced loss in both high-pathology strata. Its differences in the lower-pathology strata were +0.0185 and zero.

| Routine N | Pathology | Peak choice only | Starting values only | Search regions only | Full K = 24 |
|---:|---|---:|---:|---:|---:|
| 1,500 | >20% | −0.2729 | +0.0624 | −0.2056 | −0.2603 |
| 1,500 | ≤20% | +0.0185 | −0.0153 | +0.1871 | +0.0437 |
| 50,000 | >20% | −0.5732 | +0.0090 | −0.3647 | −0.5035 |
| 50,000 | ≤20% | 0.0000 | −0.0163 | +0.1117 | +0.0604 |

For each arm the accompanying table gives losses across all assigned datasets and among kept results, the share declined, the share of bad and severe results caught, and the share of good results lost. It gives denominators for both panels and both randomized PIT seeds. [Definitions and validation](POSTCHECK.md) · [Post-check results](ablation-postcheck-summary.csv)

## Data and reproducibility

The review used the existing simulated development data and panels for all 1,440 datasets. The three ablations added 4,320 fits and 17,280 check records across two panels and two PIT seeds. The 2,880 original comparator fits and 11,520 original check records matched the archived inputs. Across all 48 shards, repeated same-host runs matched exactly and the separate-host audit found zero differences in the recorded parameters, endpoints, signed errors and check probabilities. An independent calculation from the archived endpoints reproduced all 3,528 paired loss estimates and 208 first-peak estimates. The 49 original Actions artifacts matched GitHub's byte counts and SHA-256 digests. [Review decision record](../../stage2/ABLATION-PLAN.md) · [Actions run](https://github.com/amromeo/anchorRefine/actions/runs/45293475762) · [Audit](evidence/audit.json) · [Fits](evidence/fits.csv.gz) · [Checks](evidence/checks.csv.gz) · [Original artifacts](artifacts/) · [Logs](actions-logs.zip) · [Checksums](SHA256SUMS)
