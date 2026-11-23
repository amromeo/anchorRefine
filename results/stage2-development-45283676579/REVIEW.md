# Stage 2 development review

**Selected K = 24.** In the 864 development datasets above 20% pathology, the worse of the two sample-size differences in pre-check capped mean absolute z was −0.1493 for K = 24 and −0.1208 for K = 28. The prespecified rule chooses the smaller difference. The 576 lower-pathology controls did not enter selection. Confirmation remains unopened.

## Did K = 24 meet the development gates?

The fitted intervals improved on unchanged refineR in both high-pathology strata. At 20% pathology or below, the increase in error was within the 0.02 margin at N = 1,500 and exceeded it at N = 50,000. The checked release improved on checked refineR in both high-pathology strata and missed the low-pathology gate at both sample sizes.

| Pathological fraction | N | Candidate − baseline loss before check | Candidate − baseline loss after the same check | Candidate / baseline nonreturns after check |
|---|---:|---:|---:|---:|
| >20% | 1,500 | −0.1493 | −0.2603 | 112 / 136 |
| >20% | 50,000 | −0.3310 | −0.5035 | 50 / 95 |
| ≤20% | 1,500 | +0.0156 | +0.0437 | 20 / 18 |
| ≤20% | 50,000 | +0.0286 | +0.0604 | 8 / 6 |

These are native-limit results. Each of the two high-pathology rows includes 432 datasets and each control row includes 288. A negative difference favors K = 24. The all-dataset score assigns loss 5 to a fit failure or withheld interval. The selected fitter returned all 1,440 intervals before the check, including 331 upstream fallbacks. The baseline had one fit failure. Neither method returned an interval meeting the prespecified implausibility definition. [Gate counts and paired confidence intervals](gates.csv)

Disease location affected the gain. Pooling the two routine sample sizes above 20% pathology, the pre-check difference was −0.751 for separated disease on the left, −0.654 on the right, and −0.072 for separated disease on both sides. In the overlapping scenarios, it was +0.024 for the left shoulder, +0.015 for the right shoulder and −0.003 for disease centered on the healthy peak. Each pattern contributed 144 datasets. [Paired differences by disease pattern](paired-loss.csv)

## Reuse of the 40 guidance anchors

| K = 24, primary PIT seed | Guidance panel | Fresh diagnostic panel |
|---|---:|---:|
| All fits declined | 190/1,440 (13.2%) | 193/1,440 (13.4%) |
| Bad results caught, E > 1 | 72/92 (78.3%) | 74/92 (80.4%) |
| Severe results caught, E > 5 | No eligible fits | No eligible fits |
| Good results declined, E < 0.25 | 16/747 (2.1%) | 8/747 (1.1%) |

E is the larger absolute endpoint z error. Switching from the guidance panel to the fresh panel changed 155 of 1,440 decisions (10.8%). For comparison, the same switch changed 148 of 1,439 evaluable decisions (10.3%) for unchanged refineR, whose fit used neither panel. Panel disagreement includes sampling variation between two groups of 40 and PIT randomization. The diagnostic panel never determined release. [Both seeds and all arms](REPORT.md) · [Paired decisions](decision-pairs.csv)

## Reproducibility and source

Each of the 48 shards ran in two isolated R sessions on the same host and again on a different host. Same-host outputs matched byte for byte. The separate-host audit found zero differences in the recorded probabilities, fitted parameters, endpoints and signed scores. All 49 original Actions artifacts were preserved and checked against GitHub’s SHA-256 digests. [Audit](evidence/audit.json) · [Case fits](evidence/fits.csv.gz) · [Panel decisions](evidence/checks.csv.gz) · [Original artifacts](artifacts/) · [Job logs](actions-logs.zip)

The development freeze covers the three healthy families, their two SD-based rounding increments, the separate seed for each panel, both full candidates and the selection rule. The report includes both reference-limit extractions and the descriptive comparison of a checked candidate with ungated refineR. [Approved amendments](../../PROTOCOL.md#stage-2-approved-development-protocol) · [Design manifest](../../stage2/development-design.csv) · [Source freeze](https://github.com/amromeo/anchorRefine/commit/1c914bc3448a50f5327e522525cb448bfe836cea) · [Actions run](https://github.com/amromeo/anchorRefine/actions/runs/45283676579) · [K selection](selection.json)
