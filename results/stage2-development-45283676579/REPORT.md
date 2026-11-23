# Stage 2 development results

**K = 24 was selected** from 1,440 independent development datasets. The selection used the worse of the two sample-size differences in pre-check capped loss above 20% pathology. A lower difference favors the guided fit. An exact tie selects K = 28.

## Candidate selection


| K | Difference at N = 1,500 | Difference at N = 50,000 | Worse difference |
| --- | --- | --- | --- |
| 24 | -0.149277 | -0.331044 | -0.149277 |
| 28 | -0.120848 | -0.333219 | -0.120848 |

## Native fits and checked releases

Each formal comparison uses the corresponding refineR baseline. The release uses the original 40 anchors and the primary PIT seed. Each returned interval contributes the average of its two absolute endpoint errors capped at 5. A missing interval contributes 5. Implausible intervals have an uncapped mean absolute endpoint error above 5. The gates apply separately to each sample size and pathology group.


| Arm | N | Pathology | Mode | Arm loss | Baseline loss | Difference [95% CI] | Implausible, arm / baseline | Nonreturns, arm / baseline | All gates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K24 | 1500 | >20% | pre | 0.6251 | 0.7744 | -0.1493 [-0.2379, -0.0721] | 0 / 0 | 0 / 1 | met |
| K24 | 1500 | >20% | checked | 1.5004 | 1.7607 | -0.2603 [-0.4342, -0.1022] | 0 / 0 | 112 / 136 | met |
| K24 | 1500 | <=20% | pre | 0.2239 | 0.2083 | 0.0156 [0.0034, 0.0296] | 0 / 0 | 0 / 0 | met |
| K24 | 1500 | <=20% | checked | 0.5373 | 0.4937 | 0.0437 [-0.0361, 0.1241] | 0 / 0 | 20 / 18 | missed |
| K24 | 50000 | >20% | pre | 0.2358 | 0.5669 | -0.3310 [-0.5186, -0.1647] | 0 / 0 | 0 / 0 | met |
| K24 | 50000 | >20% | checked | 0.7486 | 1.2521 | -0.5035 [-0.8077, -0.2218] | 0 / 0 | 50 / 95 | met |
| K24 | 50000 | <=20% | pre | 0.1054 | 0.0768 | 0.0286 [0.0204, 0.0373] | 0 / 0 | 0 / 0 | missed |
| K24 | 50000 | <=20% | checked | 0.2388 | 0.1784 | 0.0604 [-0.0281, 0.1619] | 0 / 0 | 8 / 6 | missed |
| K28 | 1500 | >20% | pre | 0.6535 | 0.7744 | -0.1208 [-0.2017, -0.0530] | 0 / 0 | 1 / 1 | met |
| K28 | 1500 | >20% | checked | 1.5440 | 1.7607 | -0.2167 [-0.3842, -0.0713] | 0 / 0 | 116 / 136 | met |
| K28 | 1500 | <=20% | pre | 0.2234 | 0.2083 | 0.0151 [0.0035, 0.0282] | 0 / 0 | 0 / 0 | met |
| K28 | 1500 | <=20% | checked | 0.5370 | 0.4937 | 0.0433 [-0.0370, 0.1239] | 0 / 0 | 20 / 18 | missed |
| K28 | 50000 | >20% | pre | 0.2336 | 0.5669 | -0.3332 [-0.5195, -0.1668] | 0 / 0 | 0 / 0 | met |
| K28 | 50000 | >20% | checked | 0.7371 | 1.2521 | -0.5150 [-0.8170, -0.2377] | 0 / 0 | 49 / 95 | met |
| K28 | 50000 | <=20% | pre | 0.1054 | 0.0768 | 0.0286 [0.0204, 0.0373] | 0 / 0 | 0 / 0 | missed |
| K28 | 50000 | <=20% | checked | 0.2388 | 0.1784 | 0.0604 [-0.0281, 0.1619] | 0 / 0 | 8 / 6 | missed |

**Pre-check fitter.** K24 missed the full set of development gates.

**Checked release.** K24 missed the full set of development gates.

## Returned intervals

Accuracy of returned intervals uses only finite endpoint pairs. Coverage and all-set loss use all assigned datasets, including fallback and fit failures.


| Arm | Mode | Returned | Returned capped loss | All-set loss | E > 5 | Outside support | Unordered | Nonfinite | Fallback | Fit failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | pre | 1439/1440 | 0.4562 | 0.4594 | 0 | 0 | 0 | 1 | 0 | 1 |
| baseline | checked | 1185/1440 | 0.1857 | 1.0382 | 0 | 0 | 0 | 0 | 0 | 1 |
| K24 | pre | 1440/1440 | 0.3241 | 0.3241 | 0 | 0 | 0 | 0 | 331 | 0 |
| K24 | checked | 1250/1440 | 0.1961 | 0.8299 | 0 | 0 | 0 | 0 | 331 | 0 |
| K28 | pre | 1439/1440 | 0.3287 | 0.3319 | 0 | 0 | 0 | 1 | 380 | 1 |
| K28 | checked | 1247/1440 | 0.1956 | 0.8395 | 0 | 0 | 0 | 0 | 380 | 1 |

## Original and independent anchor panels

Each fraction is the number declined divided by the number of valid pre-check fits in the error group. E is the larger absolute endpoint error. The diagnostic panel was sampled independently of fitting. Only the guidance panel determines the release.


| Arm | Panel | PIT seed | All declined | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | guidance | primary | 254/1440 (17.6%) | 142/157 (90.4%) | 0/0 | 17/760 (2.2%) |
| baseline | guidance | alternate | 254/1440 (17.6%) | 141/157 (89.8%) | 0/0 | 17/760 (2.2%) |
| baseline | diagnostic | primary | 248/1440 (17.2%) | 140/157 (89.2%) | 0/0 | 11/760 (1.4%) |
| baseline | diagnostic | alternate | 245/1440 (17.0%) | 141/157 (89.8%) | 0/0 | 10/760 (1.3%) |
| K24 | guidance | primary | 190/1440 (13.2%) | 72/92 (78.3%) | 0/0 | 16/747 (2.1%) |
| K24 | guidance | alternate | 189/1440 (13.1%) | 71/92 (77.2%) | 0/0 | 16/747 (2.1%) |
| K24 | diagnostic | primary | 193/1440 (13.4%) | 74/92 (80.4%) | 0/0 | 8/747 (1.1%) |
| K24 | diagnostic | alternate | 196/1440 (13.6%) | 75/92 (81.5%) | 0/0 | 9/747 (1.2%) |
| K28 | guidance | primary | 192/1440 (13.3%) | 74/94 (78.7%) | 0/0 | 16/749 (2.1%) |
| K28 | guidance | alternate | 191/1440 (13.3%) | 73/94 (77.7%) | 0/0 | 16/749 (2.1%) |
| K28 | diagnostic | primary | 195/1440 (13.5%) | 77/94 (81.9%) | 0/0 | 9/749 (1.2%) |
| K28 | diagnostic | alternate | 198/1440 (13.8%) | 78/94 (83.0%) | 0/0 | 10/749 (1.3%) |


| Arm | First check | Second check | Paired decisions changed | Keep → decline | Decline → keep |
| --- | --- | --- | --- | --- | --- |
| baseline | guidance primary | guidance alternate | 10/1439 (0.7%) | 5 | 5 |
| baseline | diagnostic primary | diagnostic alternate | 9/1439 (0.6%) | 3 | 6 |
| baseline | guidance primary | diagnostic primary | 148/1439 (10.3%) | 71 | 77 |
| baseline | guidance alternate | diagnostic alternate | 153/1439 (10.6%) | 72 | 81 |
| K24 | guidance primary | guidance alternate | 9/1440 (0.6%) | 4 | 5 |
| K24 | diagnostic primary | diagnostic alternate | 7/1440 (0.5%) | 5 | 2 |
| K24 | guidance primary | diagnostic primary | 155/1440 (10.8%) | 79 | 76 |
| K24 | guidance alternate | diagnostic alternate | 157/1440 (10.9%) | 82 | 75 |
| K28 | guidance primary | guidance alternate | 9/1439 (0.6%) | 4 | 5 |
| K28 | diagnostic primary | diagnostic alternate | 7/1439 (0.5%) | 5 | 2 |
| K28 | guidance primary | diagnostic primary | 153/1439 (10.6%) | 78 | 75 |
| K28 | guidance alternate | diagnostic alternate | 155/1439 (10.8%) | 81 | 74 |

## Disease overlapping the healthy center


| Arm | Pathology | Mode | Returned | All-set loss | Implausible |
| --- | --- | --- | --- | --- | --- |
| baseline | >20% | pre | 144/144 | 0.3455 | 0 |
| baseline | >20% | checked | 133/144 | 0.6972 | 0 |
| baseline | <=20% | pre | 96/96 | 0.1372 | 0 |
| baseline | <=20% | checked | 91/96 | 0.3844 | 0 |
| K24 | >20% | pre | 144/144 | 0.3429 | 0 |
| K24 | >20% | checked | 130/144 | 0.7929 | 0 |
| K24 | <=20% | pre | 96/96 | 0.1649 | 0 |
| K24 | <=20% | checked | 92/96 | 0.3611 | 0 |
| K28 | >20% | pre | 144/144 | 0.3453 | 0 |
| K28 | >20% | checked | 130/144 | 0.7953 | 0 |
| K28 | <=20% | pre | 96/96 | 0.1654 | 0 |
| K28 | <=20% | checked | 92/96 | 0.3617 | 0 |

## Descriptive comparisons

Checked candidate versus ungated refineR is reported separately from the like-for-like success comparisons. Historical C2 extraction is secondary.


| Arm | Pathology | Native checked vs ungated | Historical pre vs pre | Historical checked vs checked |
| --- | --- | --- | --- | --- |
| K24 | >20% | 0.4539 | -0.2416 | -0.3830 |
| K24 | <=20% | 0.2455 | 0.0222 | 0.0517 |
| K28 | >20% | 0.4699 | -0.2285 | -0.3670 |
| K28 | <=20% | 0.2453 | 0.0220 | 0.0515 |

The CSV tables include all arms, both extractions, sample sizes, pathology groups, healthy families, disease patterns and rounding increments. Panel rates include denominators for all eligible valid fits and for evaluable checks. Rate and paired-difference intervals use 2,000 percentile bootstrap draws, resampling factorial cells with replicates together (PCG64 seed 37000000). The gate judgments use point estimates. This development report selects the candidate for independent confirmation.
