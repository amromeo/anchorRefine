# Stage 2 RIbench at N ≤ 5,000

The frozen K24 peak-only fitter **met** the pre-check criteria for this cohort. Its checked release **missed** the criteria against refineR receiving the same check. The audit covered all 2,880 routine datasets. Native support-corrected limits determine these decisions. Each interval contributes its mean absolute endpoint z error with each endpoint capped at 5. CRP contributes its 95th-percentile upper limit only. An unavailable or unscored interval contributes 5.

## Candidate versus unchanged refineR


| Mode | Pathology | Sets | Candidate loss | refineR loss | Δ [95% interval] | Implausible, candidate / refineR | Nonreturns, candidate / refineR | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pre | >20% | 1440 | 0.5748 | 0.5787 | -0.0039 [-0.009, +0.001] | 4 / 4 | 0 / 0 | met |
| pre | <=20% | 1440 | 0.1932 | 0.1907 | +0.0025 [+0.000, +0.005] | 0 / 0 | 0 / 0 | met |
| checked | >20% | 1440 | 1.3905 | 1.4223 | -0.0318 [-0.073, +0.004] | 0 / 0 | 305 / 315 | met |
| checked | <=20% | 1440 | 0.5796 | 0.5754 | +0.0042 [-0.012, +0.022] | 0 / 0 | 123 / 122 | missed |

The high-pathology gate requires a strictly lower mean loss. At 20% pathology or below, the permitted increase is 0.02. Both gates also require no increase in the number of implausible intervals or nonreturns. The implausibility definition uses the uncapped mean absolute endpoint z above 5. Each gate uses paired point estimates.

## Components and reported intervals

The frozen candidate equals the independently labeled peak-only arm on every case. The other arms use anchor-guided starting values or search regions, respectively.

| Arm | Mode | Returned | Returned/scored loss | All-set loss | Implausible | E > 5 | Nonfinite | Outside support | Unordered | Fit failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 2,880/2,880 (100.0%) | 0.3847 | 0.3847 | 4 | 18 | 0 | 3 | 0 | 0 |
| Unchanged refineR | checked | 2,443/2,880 (84.8%) | 0.2831 | 0.9989 | 0 | 1 | 0 | 0 | 0 | 0 |
| Frozen K24 peak-only candidate | pre | 2,880/2,880 (100.0%) | 0.3840 | 0.3840 | 4 | 17 | 0 | 3 | 0 | 0 |
| Frozen K24 peak-only candidate | checked | 2,452/2,880 (85.1%) | 0.2842 | 0.9850 | 0 | 1 | 0 | 0 | 0 | 0 |
| Peak only | pre | 2,880/2,880 (100.0%) | 0.3840 | 0.3840 | 4 | 17 | 0 | 3 | 0 | 0 |
| Peak only | checked | 2,452/2,880 (85.1%) | 0.2842 | 0.9850 | 0 | 1 | 0 | 0 | 0 | 0 |
| Starting values only | pre | 2,880/2,880 (100.0%) | 0.3863 | 0.3863 | 4 | 18 | 0 | 3 | 0 | 0 |
| Starting values only | checked | 2,430/2,880 (84.4%) | 0.2836 | 1.0205 | 0 | 2 | 0 | 0 | 0 | 0 |
| Search regions only | pre | 2,880/2,880 (100.0%) | 0.3895 | 0.3895 | 4 | 20 | 0 | 3 | 0 | 0 |
| Search regions only | checked | 2,407/2,880 (83.6%) | 0.2910 | 1.0644 | 0 | 0 | 0 | 0 | 0 | 0 |


| Pathology | Arm | Native pre Δ | Native checked Δ | Native checked vs ungated Δ | Historical pre Δ | Historical checked Δ |
| --- | --- | --- | --- | --- | --- | --- |
| >20% | Frozen K24 peak-only candidate | -0.0039 | -0.0318 | +0.8117 | -0.0037 | -0.0322 |
| >20% | Starting values only | +0.0009 | +0.0314 | +0.8750 | +0.0012 | +0.0327 |
| >20% | Search regions only | -0.0118 | +0.0083 | +0.8519 | -0.0104 | +0.0075 |
| <=20% | Frozen K24 peak-only candidate | +0.0025 | +0.0042 | +0.3889 | +0.0025 | +0.0042 |
| <=20% | Starting values only | +0.0023 | +0.0118 | +0.3965 | +0.0023 | +0.0119 |
| <=20% | Search regions only | +0.0214 | +0.1228 | +0.5075 | +0.0211 | +0.1228 |

## Peak choice and fallback

Different peaks means that the anchor election and refineR chose different detected indices on the initial raw density. The all-assigned rate uses every dataset. The clear-comparison rate uses just clear elections with an upstream peak for comparison. An unclear election and an unavailable comparison are counted separately. Fallback uses all assigned datasets.

| Group | Value | Same | Different / assigned | Different / clear | Unclear | Unavailable | Fallback / assigned |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all | All | 2537 | 15/2,880 (0.5%) | 15/2,552 (0.6%) | 328 | 0 | 377/2,880 (13.1%) |
| analyte | AST | 244 | 1/288 (0.3%) | 1/245 (0.4%) | 43 | 0 | 58/288 (20.1%) |
| analyte | CRP | 284 | 4/288 (1.4%) | 4/288 (1.4%) | 0 | 0 | 0/288 (0.0%) |
| analyte | Ca | 253 | 3/288 (1.0%) | 3/256 (1.2%) | 32 | 0 | 35/288 (12.2%) |
| analyte | FT4 | 254 | 1/288 (0.3%) | 1/255 (0.4%) | 33 | 0 | 33/288 (11.5%) |
| analyte | GGT | 225 | 3/288 (1.0%) | 3/228 (1.3%) | 60 | 0 | 77/288 (26.7%) |
| analyte | Hb | 231 | 3/288 (1.0%) | 3/234 (1.3%) | 54 | 0 | 60/288 (20.8%) |
| analyte | IgE | 283 | 0/288 (0.0%) | 0/283 (0.0%) | 5 | 0 | 5/288 (1.7%) |
| analyte | LACT | 260 | 0/288 (0.0%) | 0/260 (0.0%) | 28 | 0 | 34/288 (11.8%) |
| analyte | LDH | 257 | 0/288 (0.0%) | 0/257 (0.0%) | 31 | 0 | 32/288 (11.1%) |
| analyte | TSH | 246 | 0/288 (0.0%) | 0/246 (0.0%) | 42 | 0 | 43/288 (14.9%) |
| N | 1000 | 1181 | 8/1,440 (0.6%) | 8/1,189 (0.7%) | 251 | 0 | 271/1,440 (18.8%) |
| N | 5000 | 1356 | 7/1,440 (0.5%) | 7/1,363 (0.5%) | 77 | 0 | 106/1,440 (7.4%) |
| fraction | 0 | 239 | 1/360 (0.3%) | 1/240 (0.4%) | 120 | 0 | 122/360 (33.9%) |
| fraction | 0.05 | 326 | 0/360 (0.0%) | 0/326 (0.0%) | 34 | 0 | 35/360 (9.7%) |
| fraction | 0.1 | 341 | 2/360 (0.6%) | 2/343 (0.6%) | 17 | 0 | 19/360 (5.3%) |
| fraction | 0.2 | 341 | 1/360 (0.3%) | 1/342 (0.3%) | 18 | 0 | 22/360 (6.1%) |
| fraction | 0.3 | 341 | 0/360 (0.0%) | 0/341 (0.0%) | 19 | 0 | 19/360 (5.3%) |
| fraction | 0.4 | 333 | 0/360 (0.0%) | 0/333 (0.0%) | 27 | 0 | 30/360 (8.3%) |
| fraction | 0.5 | 319 | 0/360 (0.0%) | 0/319 (0.0%) | 41 | 0 | 48/360 (13.3%) |
| fraction | 0.6 | 297 | 11/360 (3.1%) | 11/308 (3.6%) | 52 | 0 | 82/360 (22.8%) |

The joint table includes every observed analyte × N × pathological fraction combination, its assigned and clear denominators, and cluster intervals. [Peak choice and fallback](peak-fallback.csv.gz) · [Fallback reasons](fallback.csv.gz)

## Archival comparisons on the same datasets

Raw comparisons use ungated Stage 2 and the comparator’s raw estimates. Checked comparisons use the primary Stage 2 release and the intervals originally reported by each comparator. The published safeguards and original comparator limits apply with both Stage 2 extractions. Each paired comparison verifies the routine and anchor identities. Missing archive coverage is excluded from the paired population and counted separately from a withheld or failed estimate.

| Comparator | Version | Matched / planned | Candidate returned | Comparator returned | Candidate loss | Comparator loss | Δ [95% interval] | Common scored | Candidate on common | Comparator on common |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchoredRI Arm B (Task E) | raw | 2,880/2,880 (100.0%) | 2880 | 2880 | 0.3840 | 0.2231 | 0.1609 [+0.059, +0.263] | 2880 | 0.3840 | 0.2231 |
| anchoredRI Arm B (Task E) | reported | 2,880/2,880 (100.0%) | 2452 | 2781 | 0.9850 | 0.3725 | 0.6126 [+0.395, +0.840] | 2387 | 0.2844 | 0.2013 |
| Improved anchoredRI baseline | raw | 2,880/2,880 (100.0%) | 2880 | 2880 | 0.3840 | 0.2886 | 0.0954 [+0.017, +0.189] | 2880 | 0.3840 | 0.2886 |
| Improved anchoredRI baseline | reported | 2,880/2,880 (100.0%) | 2452 | 2406 | 0.9850 | 0.9793 | 0.0058 [-0.537, +0.483] | 2127 | 0.2827 | 0.1824 |
| Anchors only | raw | 2,880/2,880 (100.0%) | 2880 | 2880 | 0.3840 | 0.2899 | 0.0941 [+0.003, +0.189] | 2880 | 0.3840 | 0.2899 |
| Anchors only | reported | 2,880/2,880 (100.0%) | 2452 | 2880 | 0.9850 | 0.2899 | 0.6951 [+0.508, +0.900] | 2452 | 0.2842 | 0.2834 |

## Anchor check

A primary p-value below 0.01 declines the fit. Capture and good-result loss use every classifiable valid fit in the indicated group. E is the largest absolute endpoint z. The alternate seed uses the same rounded measurements and a fresh PIT randomization. Both decisions apply to both extractions.

| Arm | Extraction | Evaluable fits declined | E > 1 caught | E > 5 caught | E < 0.25 declined | Seed reversals |
| --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | native | 437/2,880 (15.2%) | 216/411 (52.6%) | 17/18 (94.4%) | 19/1,180 (1.6%) | 33/2,880 (1.1%) |
| Unchanged refineR | historical | 437/2,880 (15.2%) | 216/411 (52.6%) | 34/42 (81.0%) | 19/1,180 (1.6%) | 33/2,880 (1.1%) |
| Frozen K24 peak-only candidate | native | 428/2,880 (14.9%) | 216/414 (52.2%) | 16/17 (94.1%) | 16/1,170 (1.4%) | 27/2,880 (0.9%) |
| Frozen K24 peak-only candidate | historical | 428/2,880 (14.9%) | 216/414 (52.2%) | 34/41 (82.9%) | 16/1,170 (1.4%) | 27/2,880 (0.9%) |

## Reproducibility and evidence

All 14,400 fits and 28,800 check records passed the technical audit. Same-host reruns matched across 48 shards. The independent-host audit covered 48 shards. The largest endpoint difference was 0 of reference width and the largest p-value difference was 0. [Audit](evidence/audit.json)

Descriptive 95% intervals resample RIbench (Analyte, Scenario) clusters intact. Each stratum uses 2,000 paired percentile bootstrap draws with PCG64 seed 37000000. Paired differences use common cluster weights. Undefined replicates are excluded and intervals require two informative clusters. The data tables identify all case and endpoint denominators.

- [Prespecified gate details](gates.csv) · [Paired loss and common-returned differences](paired-loss.csv.gz) · [Descriptive paired comparators](comparators.csv.gz)
- [Before-check and after-check accuracy](accuracy.csv.gz) · [Signed endpoint errors](endpoints.csv.gz) · [Check rates, capture and coverage](rates.csv.gz) · [Threshold ties](boundary-counts.csv.gz) · [Seed reversals](seed-changes.csv.gz)
- [Case fits](evidence/fits.csv.gz) · [Check records](evidence/checks.csv.gz)
