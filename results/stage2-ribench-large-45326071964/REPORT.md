# Stage 2 RIbench at N = 50,000

The frozen K24 peak-only fitter **met** the pre-check criteria for this cohort. Its checked release **met** the criteria against refineR receiving the same check. The audit covered all 1,440 routine datasets. Native support-corrected limits determine these decisions. Each interval contributes its mean absolute endpoint z error with each endpoint capped at 5. CRP contributes its 95th-percentile upper limit only. An unavailable or unscored interval contributes 5.

## Candidate versus unchanged refineR


| Mode | Pathology | Sets | Candidate loss | refineR loss | Δ [95% interval] | Implausible, candidate / refineR | Nonreturns, candidate / refineR | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | >20% | 720 | 0.3610 | 0.3653 | -0.0044 [-0.012, +0.000] | 0 / 0 | 0 / 0 | met |
| pre | <=20% | 720 | 0.0965 | 0.0946 | +0.0019 [+0.000, +0.005] | 0 / 0 | 0 / 0 | met |
| checked | >20% | 720 | 0.9535 | 0.9672 | -0.0137 [-0.034, +0.000] | 0 / 0 | 104 / 106 | met |
| checked | <=20% | 720 | 0.3707 | 0.3701 | +0.0006 [-0.020, +0.022] | 0 / 0 | 43 / 43 | met |

The high-pathology gate requires a strictly lower mean loss. At 20% pathology or below, the permitted increase is 0.02. Both gates also require no increase in the number of implausible intervals or nonreturns. The implausibility definition uses the uncapped mean absolute endpoint z above 5. Each gate uses paired point estimates.

## Components and reported intervals

The frozen candidate equals the independently labeled peak-only arm on every case. The other arms use anchor-guided starting values or search regions, respectively.

| Arm | Mode | Returned | Returned/scored loss | All-set loss | Implausible | E > 5 | Nonfinite | Outside support | Unordered | Fit failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 1,440/1,440 (100.0%) | 0.2300 | 0.2300 | 0 | 1 | 0 | 0 | 0 | 0 |
| Unchanged refineR | checked | 1,291/1,440 (89.7%) | 0.1687 | 0.6686 | 0 | 0 | 0 | 0 | 0 | 0 |
| Frozen K24 peak-only candidate | pre | 1,440/1,440 (100.0%) | 0.2287 | 0.2287 | 0 | 1 | 0 | 0 | 0 | 0 |
| Frozen K24 peak-only candidate | checked | 1,293/1,440 (89.8%) | 0.1689 | 0.6621 | 0 | 0 | 0 | 0 | 0 | 0 |
| Peak only | pre | 1,440/1,440 (100.0%) | 0.2287 | 0.2287 | 0 | 1 | 0 | 0 | 0 | 0 |
| Peak only | checked | 1,293/1,440 (89.8%) | 0.1689 | 0.6621 | 0 | 0 | 0 | 0 | 0 | 0 |
| Starting values only | pre | 1,440/1,440 (100.0%) | 0.2305 | 0.2305 | 0 | 0 | 0 | 0 | 0 | 0 |
| Starting values only | checked | 1,292/1,440 (89.7%) | 0.1690 | 0.6655 | 0 | 0 | 0 | 0 | 0 | 0 |
| Search regions only | pre | 1,440/1,440 (100.0%) | 0.2779 | 0.2779 | 0 | 1 | 0 | 0 | 0 | 0 |
| Search regions only | checked | 1,215/1,440 (84.4%) | 0.2029 | 0.9524 | 0 | 0 | 0 | 0 | 0 | 0 |


| Pathology | Arm | Native pre Δ | Native checked Δ | Native checked vs ungated Δ | Historical pre Δ | Historical checked Δ |
| --- | --- | --- | --- | --- | --- | --- |
| >20% | Frozen K24 peak-only candidate | -0.0044 | -0.0137 | +0.5882 | -0.0044 | -0.0137 |
| >20% | Starting values only | +0.0008 | +0.0000 | +0.6019 | +0.0013 | +0.0000 |
| >20% | Search regions only | +0.0189 | +0.2232 | +0.8250 | +0.0224 | +0.2233 |
| <=20% | Frozen K24 peak-only candidate | +0.0019 | +0.0006 | +0.2761 | +0.0019 | +0.0006 |
| <=20% | Starting values only | +0.0003 | -0.0062 | +0.2693 | +0.0003 | -0.0062 |
| <=20% | Search regions only | +0.0769 | +0.3444 | +0.6199 | +0.0825 | +0.3444 |

## Peak choice and fallback

Different peaks means that the anchor election and refineR chose different detected indices on the initial raw density. The all-assigned rate uses every dataset. The clear-comparison rate uses just clear elections with an upstream peak for comparison. An unclear election and an unavailable comparison are counted separately. Fallback uses all assigned datasets.

| Group | Value | Same | Different / assigned | Different / clear | Unclear | Unavailable | Fallback / assigned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | All | 1406 | 7/1,440 (0.5%) | 7/1,413 (0.5%) | 27 | 0 | 57/1,440 (4.0%) |
| analyte | AST | 144 | 0/144 (0.0%) | 0/144 (0.0%) | 0 | 0 | 10/144 (6.9%) |
| analyte | CRP | 142 | 2/144 (1.4%) | 2/144 (1.4%) | 0 | 0 | 0/144 (0.0%) |
| analyte | Ca | 144 | 0/144 (0.0%) | 0/144 (0.0%) | 0 | 0 | 0/144 (0.0%) |
| analyte | FT4 | 142 | 0/144 (0.0%) | 0/142 (0.0%) | 2 | 0 | 2/144 (1.4%) |
| analyte | GGT | 138 | 5/144 (3.5%) | 5/143 (3.5%) | 1 | 0 | 14/144 (9.7%) |
| analyte | Hb | 142 | 0/144 (0.0%) | 0/142 (0.0%) | 2 | 0 | 2/144 (1.4%) |
| analyte | IgE | 144 | 0/144 (0.0%) | 0/144 (0.0%) | 0 | 0 | 0/144 (0.0%) |
| analyte | LACT | 144 | 0/144 (0.0%) | 0/144 (0.0%) | 0 | 0 | 6/144 (4.2%) |
| analyte | LDH | 144 | 0/144 (0.0%) | 0/144 (0.0%) | 0 | 0 | 1/144 (0.7%) |
| analyte | TSH | 122 | 0/144 (0.0%) | 0/122 (0.0%) | 22 | 0 | 22/144 (15.3%) |
| N | 50000 | 1406 | 7/1,440 (0.5%) | 7/1,413 (0.5%) | 27 | 0 | 57/1,440 (4.0%) |
| fraction | 0 | 176 | 0/180 (0.0%) | 0/176 (0.0%) | 4 | 0 | 5/180 (2.8%) |
| fraction | 0.05 | 180 | 0/180 (0.0%) | 0/180 (0.0%) | 0 | 0 | 0/180 (0.0%) |
| fraction | 0.1 | 180 | 0/180 (0.0%) | 0/180 (0.0%) | 0 | 0 | 0/180 (0.0%) |
| fraction | 0.2 | 178 | 0/180 (0.0%) | 0/178 (0.0%) | 2 | 0 | 2/180 (1.1%) |
| fraction | 0.3 | 180 | 0/180 (0.0%) | 0/180 (0.0%) | 0 | 0 | 0/180 (0.0%) |
| fraction | 0.4 | 175 | 0/180 (0.0%) | 0/175 (0.0%) | 5 | 0 | 5/180 (2.8%) |
| fraction | 0.5 | 173 | 0/180 (0.0%) | 0/173 (0.0%) | 7 | 0 | 8/180 (4.4%) |
| fraction | 0.6 | 164 | 7/180 (3.9%) | 7/171 (4.1%) | 9 | 0 | 37/180 (20.6%) |

The joint table includes every observed analyte × N × pathological fraction combination, its assigned and clear denominators, and cluster intervals. [Peak choice and fallback](peak-fallback.csv.gz) · [Fallback reasons](fallback.csv.gz)

## Archival comparisons on the same datasets

Raw comparisons use ungated Stage 2 and the comparator’s raw estimates. Checked comparisons use the primary Stage 2 release and the intervals originally reported by each comparator. The published safeguards and original comparator limits apply with both Stage 2 extractions. Each paired comparison verifies the routine and anchor identities. Missing archive coverage is excluded from the paired population and counted separately from a withheld or failed estimate.

| Comparator | Version | Matched / planned | Candidate returned | Comparator returned | Candidate loss | Comparator loss | Δ [95% interval] | Common scored | Candidate on common | Comparator on common |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchoredRI Arm B (Task E) | raw | 1,440/1,440 (100.0%) | 1440 | 1440 | 0.2287 | 0.3751 | -0.1464 [-0.407, +0.056] | 1440 | 0.2287 | 0.3751 |
| anchoredRI Arm B (Task E) | reported | 1,440/1,440 (100.0%) | 1293 | 1135 | 0.6621 | 1.1620 | -0.4999 [-1.204, +0.098] | 1043 | 0.1681 | 0.1238 |
| Improved anchoredRI baseline | raw | 1,440/1,440 (100.0%) | 1440 | 1440 | 0.2287 | 0.4280 | -0.1992 [-0.328, -0.060] | 1440 | 0.2287 | 0.4280 |
| Improved anchoredRI baseline | reported | 1,440/1,440 (100.0%) | 1293 | 1066 | 0.6621 | 1.4249 | -0.7628 [-1.413, -0.167] | 994 | 0.1696 | 0.1651 |
| Anchors only | raw | 1,440/1,440 (100.0%) | 1440 | 1440 | 0.2287 | 0.2961 | -0.0674 [-0.156, +0.015] | 1440 | 0.2287 | 0.2961 |
| Anchors only | reported | 1,440/1,440 (100.0%) | 1293 | 1440 | 0.6621 | 0.2961 | 0.3660 [+0.149, +0.610] | 1293 | 0.1689 | 0.2885 |

## Anchor check

A primary p-value below 0.01 declines the fit. Capture and good-result loss use every classifiable valid fit in the indicated group. E is the largest absolute endpoint z. The alternate seed uses the same rounded measurements and a fresh PIT randomization. Both decisions apply to both extractions.

| Arm | Extraction | Evaluable fits declined | E > 1 caught | E > 5 caught | E < 0.25 declined | Seed reversals |
| --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | native | 149/1,440 (10.3%) | 57/94 (60.6%) | 1/1 (100.0%) | 16/881 (1.8%) | 12/1,440 (0.8%) |
| Unchanged refineR | historical | 149/1,440 (10.3%) | 57/94 (60.6%) | 2/2 (100.0%) | 16/881 (1.8%) | 12/1,440 (0.8%) |
| Frozen K24 peak-only candidate | native | 147/1,440 (10.2%) | 56/93 (60.2%) | 1/1 (100.0%) | 15/882 (1.7%) | 11/1,440 (0.8%) |
| Frozen K24 peak-only candidate | historical | 147/1,440 (10.2%) | 56/93 (60.2%) | 2/2 (100.0%) | 15/882 (1.7%) | 11/1,440 (0.8%) |

## Reproducibility and evidence

All 7,200 fits and 14,400 check records passed the technical audit. Same-host reruns matched across 48 shards. The independent-host audit covered 48 shards. The largest endpoint difference was 0 of reference width and the largest p-value difference was 0. [Audit](evidence/audit.json)

Descriptive 95% intervals resample RIbench (Analyte, Scenario) clusters intact. Each stratum uses 2,000 paired percentile bootstrap draws with PCG64 seed 37000000. Paired differences use common cluster weights. Undefined replicates are excluded and intervals require two informative clusters. The data tables identify all case and endpoint denominators.

- [Prespecified gate details](gates.csv) · [Paired loss and common-returned differences](paired-loss.csv.gz) · [Descriptive paired comparators](comparators.csv.gz)
- [Before-check and after-check accuracy](accuracy.csv.gz) · [Signed endpoint errors](endpoints.csv.gz) · [Check rates, capture and coverage](rates.csv.gz) · [Threshold ties](boundary-counts.csv.gz) · [Seed reversals](seed-changes.csv.gz)
- [Case fits](evidence/fits.csv.gz) · [Check records](evidence/checks.csv.gz)
