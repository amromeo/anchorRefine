# Stage 3 development

The selected inside-fit weight is **w = 1**. The selected post-fit weight is **t = 0.25**. All 3,744 independent development datasets enter the selection. Confirmation remains unopened.

## Control eligibility and high-pathology target

Entries are paired differences in pre-check native loss from the frozen Stage 2 fit, with 5 for missing fits. A positive difference increases loss. Eligibility requires all four control differences to be at most 0.02. Among eligible weights, the smallest worst difference on high-pathology shoulder and overlapping disease wins, with ties given to the smaller weight. These judgments use full precision.

| Arm | Weight | Control 1,000 | Control 1,500 | Control 5,000 | Control 50,000 | Eligible | Focus 1,000 | Focus 1,500 | Focus 5,000 | Focus 50,000 | Worst focus | Selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | +0.00000 | +0.00000 | +0.00000 | +0.00000 | Yes | +0.00000 | +0.00000 | +0.00000 | +0.00000 | +0.00000 |  |
| primary | 1 | -0.06675 | -0.04142 | -0.01055 | -0.00116 | Yes | -0.05368 | -0.03628 | -0.01024 | -0.00180 | -0.00180 | Yes |
| primary | 10 | -0.06092 | -0.03579 | +0.02130 | +0.01363 | No | -0.11988 | -0.07715 | -0.05372 | -0.00880 | -0.00880 |  |
| primary | 100 | -0.02708 | +0.00253 | +0.08331 | +0.09751 | No | -0.13619 | -0.09801 | -0.08054 | -0.06203 | -0.06203 |  |
| primary | 1000 | -0.01405 | +0.01452 | +0.09720 | +0.11819 | No | -0.13203 | -0.09416 | -0.07986 | -0.06179 | -0.06179 |  |
| primary | 10000 | -0.01234 | +0.01535 | +0.09977 | +0.12010 | No | -0.13049 | -0.09406 | -0.07854 | -0.06059 | -0.06059 |  |
| postfit | 0 | +0.00000 | +0.00000 | +0.00000 | +0.00000 | Yes | +0.00000 | +0.00000 | +0.00000 | +0.00000 | +0.00000 |  |
| postfit | 0.25 | -0.03095 | -0.02268 | -0.00418 | +0.00514 | Yes | -0.07292 | -0.07624 | -0.07703 | -0.07979 | -0.07292 | Yes |
| postfit | 0.5 | -0.03821 | -0.01979 | +0.01998 | +0.04312 | No | -0.12276 | -0.12379 | -0.12347 | -0.12679 | -0.12276 |  |
| postfit | 0.75 | -0.02263 | +0.00318 | +0.06079 | +0.08948 | No | -0.13482 | -0.12381 | -0.11934 | -0.11563 | -0.11563 |  |
| postfit | 1 | +0.01109 | +0.04234 | +0.10925 | +0.13914 | No | -0.10534 | -0.08351 | -0.07791 | -0.06796 | -0.06796 |  |

[Unrounded selection values, including high separated disease](selection.csv)

## Influence before full development

Center is the native median and spread is half the distance between the 15.87th and 84.13th percentiles, after mapping each quantile to the parent Stage 2 transformation. Shifts are candidate minus parent, divided by parent Sigma. Unchanged fits contribute zero. Parent fallback status is fixed before any weighted search.

### All fixtures

| N | w | Measured / assigned | Center signed | Center absolute | Spread signed | Spread absolute | Searches entered | Fits changed | Update failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,000 | 0 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 1,000 | 1 | 24 / 24 | 0.00000 | 0.02959 | 0.00000 | 0.02486 | 24 | 18 | 0 |
| 1,000 | 10 | 24 / 24 | 0.04330 | 0.10077 | 0.00215 | 0.10334 | 24 | 24 | 0 |
| 1,000 | 100 | 24 / 24 | -0.01329 | 0.18304 | 0.04168 | 0.16712 | 24 | 24 | 0 |
| 1,000 | 1000 | 24 / 24 | -0.02169 | 0.19685 | 0.05840 | 0.17403 | 24 | 24 | 0 |
| 1,000 | 10000 | 24 / 24 | -0.02169 | 0.19767 | 0.05840 | 0.17571 | 24 | 24 | 0 |
| 1,500 | 0 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 1,500 | 1 | 24 / 24 | 0.00000 | 0.00262 | 0.00000 | 0.00155 | 24 | 14 | 0 |
| 1,500 | 10 | 24 / 24 | 0.01102 | 0.07803 | 0.00298 | 0.08301 | 24 | 23 | 0 |
| 1,500 | 100 | 24 / 24 | 0.07141 | 0.15851 | -0.03605 | 0.11966 | 24 | 24 | 0 |
| 1,500 | 1000 | 24 / 24 | 0.08201 | 0.18432 | -0.03328 | 0.12149 | 24 | 24 | 0 |
| 1,500 | 10000 | 24 / 24 | 0.08324 | 0.18169 | -0.03235 | 0.12149 | 24 | 24 | 0 |
| 5,000 | 0 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 5,000 | 1 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 24 | 6 | 0 |
| 5,000 | 10 | 24 / 24 | 0.00000 | 0.02884 | -0.00000 | 0.01220 | 24 | 20 | 0 |
| 5,000 | 100 | 24 / 24 | -0.00117 | 0.08191 | -0.07310 | 0.12921 | 24 | 24 | 0 |
| 5,000 | 1000 | 24 / 24 | -0.00831 | 0.11716 | -0.08510 | 0.12294 | 24 | 24 | 0 |
| 5,000 | 10000 | 24 / 24 | -0.01172 | 0.12768 | -0.07940 | 0.12294 | 24 | 24 | 0 |
| 50,000 | 0 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 50,000 | 1 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 24 | 7 | 0 |
| 50,000 | 10 | 24 / 24 | 0.00000 | 0.00066 | 0.00000 | 0.00082 | 24 | 16 | 0 |
| 50,000 | 100 | 24 / 24 | -0.03260 | 0.06859 | -0.06525 | 0.06895 | 24 | 24 | 0 |
| 50,000 | 1000 | 24 / 24 | -0.04320 | 0.06830 | -0.04942 | 0.06131 | 24 | 24 | 0 |
| 50,000 | 10000 | 24 / 24 | -0.04285 | 0.06830 | -0.05024 | 0.06179 | 24 | 24 | 0 |

### Stage 2 non-fallback fixtures

| N | w | Measured / assigned | Center signed | Center absolute | Spread signed | Spread absolute | Searches entered | Fits changed | Update failures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1,000 | 0 | 7 / 7 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 1,000 | 1 | 7 / 7 | -0.02449 | 0.03470 | 0.01575 | 0.02747 | 7 | 7 | 0 |
| 1,000 | 10 | 7 / 7 | 0.17669 | 0.19773 | -0.11769 | 0.14688 | 7 | 7 | 0 |
| 1,000 | 100 | 7 / 7 | 0.20140 | 0.20140 | -0.14002 | 0.16058 | 7 | 7 | 0 |
| 1,000 | 1000 | 7 / 7 | 0.20387 | 0.20387 | -0.14507 | 0.17366 | 7 | 7 | 0 |
| 1,000 | 10000 | 7 / 7 | 0.20634 | 0.20634 | -0.14756 | 0.17475 | 7 | 7 | 0 |
| 1,500 | 0 | 11 / 11 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 1,500 | 1 | 11 / 11 | 0.00000 | 0.00936 | 0.00000 | 0.00372 | 11 | 7 | 0 |
| 1,500 | 10 | 11 / 11 | 0.12785 | 0.15052 | 0.07363 | 0.16505 | 11 | 11 | 0 |
| 1,500 | 100 | 11 / 11 | 0.17583 | 0.20726 | 0.09965 | 0.17950 | 11 | 11 | 0 |
| 1,500 | 1000 | 11 / 11 | 0.22029 | 0.22029 | 0.08873 | 0.19097 | 11 | 11 | 0 |
| 1,500 | 10000 | 11 / 11 | 0.22572 | 0.22572 | 0.08481 | 0.19723 | 11 | 11 | 0 |
| 5,000 | 0 | 18 / 18 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 5,000 | 1 | 18 / 18 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 18 | 6 | 0 |
| 5,000 | 10 | 18 / 18 | 0.00000 | 0.03011 | 0.00000 | 0.01220 | 18 | 15 | 0 |
| 5,000 | 100 | 18 / 18 | -0.00117 | 0.09714 | -0.03891 | 0.13967 | 18 | 18 | 0 |
| 5,000 | 1000 | 18 / 18 | 0.01283 | 0.11716 | -0.03118 | 0.13619 | 18 | 18 | 0 |
| 5,000 | 10000 | 18 / 18 | 0.00923 | 0.12768 | -0.03286 | 0.13446 | 18 | 18 | 0 |
| 50,000 | 0 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0 | 0 | 0 |
| 50,000 | 1 | 24 / 24 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 24 | 7 | 0 |
| 50,000 | 10 | 24 / 24 | 0.00000 | 0.00066 | 0.00000 | 0.00082 | 24 | 16 | 0 |
| 50,000 | 100 | 24 / 24 | -0.03260 | 0.06859 | -0.06525 | 0.06895 | 24 | 24 | 0 |
| 50,000 | 1000 | 24 / 24 | -0.04320 | 0.06830 | -0.04942 | 0.06131 | 24 | 24 | 0 |
| 50,000 | 10000 | 24 / 24 | -0.04285 | 0.06830 | -0.05024 | 0.06179 | 24 | 24 | 0 |

### Searches on Stage 2 fallback fixtures

| N | Fallback fixtures | Positive-weight searches attempted / entered | Changed fits | Incumbent selected | Update failures |
| --- | --- | --- | --- | --- | --- |
| 1,000 | 17 | 85 / 85 | 79 | 6 | 0 |
| 1,500 | 13 | 65 / 65 | 58 | 7 | 0 |
| 5,000 | 6 | 30 / 30 | 23 | 7 | 0 |
| 50,000 | 0 | 0 / 0 | 0 | 0 | 0 |

[All fixtures](influence.csv) · [Stage 2 non-fallback](influence-nonfallback.csv) · [Stage 2 fallback](influence-fallback.csv)

## Accuracy and coverage

The primary release uses the original guidance panel and primary PIT seed. Mean loss counts each endpoint's absolute healthy-scale z error capped at five, and each nonreturn contributes five. Returned accuracy excludes nonreturns. The anchors-only row uses the C2 reporting rule.

| Arm | Mode | Returned / 3,744 | All-set loss | Returned loss | Implausible | Fallbacks | Fit failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 3743 | 0.4576 | 0.4564 | 0 | 0 | 1 |
| Unchanged refineR | checked | 2990 | 1.1848 | 0.2227 | 0 | 0 | 1 |
| Stage 2 | pre | 3744 | 0.3528 | 0.3528 | 0 | 1175 | 0 |
| Stage 2 | checked | 3127 | 1.0104 | 0.2232 | 0 | 1175 | 0 |
| w1 | pre | 3744 | 0.2964 | 0.2964 | 0 | 1175 | 0 |
| w1 | checked | 3291 | 0.7843 | 0.2040 | 0 | 1175 | 0 |
| t0.25 | pre | 3744 | 0.2804 | 0.2804 | 0 | 1175 | 0 |
| t0.25 | checked | 3463 | 0.5594 | 0.1990 | 0 | 1175 | 0 |
| Anchors-only | pre | 3744 | 0.2601 | 0.2601 | 0 | 0 | 0 |
| Anchors-only | checked | 3744 | 0.2601 | 0.2601 | 0 | 0 | 0 |

## Comparisons with unchanged refineR by N

These synthetic development comparisons describe the selected weights. A fit passes above 20% pathology only with a lower mean loss. At or below 20%, the margin is 0.02. Each stratum also requires no extra nonreturns or implausible intervals. Both release methods receive the same check. An interval is implausible when its uncapped mean absolute endpoint error exceeds five.

| N | Pathology | Arm | Mode | Difference [95% interval] | Implausible, arm / refineR | Nonreturns, arm / refineR | Met |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | control | w1 | pre | -0.0660 [-0.1025, -0.0370] | 0 / 0 | 0 / 0 | Yes |
| 1000 | control | w1 | checked | -0.3836 [-0.5312, -0.2446] | 0 / 0 | 10 / 31 | Yes |
| 1000 | control | t0.25 | pre | -0.0302 [-0.0393, -0.0217] | 0 / 0 | 0 / 0 | Yes |
| 1000 | control | t0.25 | checked | -0.3685 [-0.5091, -0.2391] | 0 / 0 | 9 / 31 | Yes |
| 1000 | high | w1 | pre | -0.2210 [-0.2918, -0.1586] | 0 / 0 | 0 / 1 | Yes |
| 1000 | high | w1 | checked | -0.6437 [-0.7851, -0.5084] | 0 / 0 | 132 / 216 | Yes |
| 1000 | high | t0.25 | pre | -0.2248 [-0.2923, -0.1697] | 0 / 0 | 0 / 1 | Yes |
| 1000 | high | t0.25 | checked | -0.8058 [-0.9718, -0.6483] | 0 / 0 | 109 / 216 | Yes |
| 1500 | control | w1 | pre | -0.0408 [-0.0598, -0.0239] | 0 / 0 | 0 / 0 | Yes |
| 1500 | control | w1 | checked | -0.2868 [-0.4131, -0.1655] | 0 / 0 | 9 / 25 | Yes |
| 1500 | control | t0.25 | pre | -0.0221 [-0.0296, -0.0148] | 0 / 0 | 0 / 0 | Yes |
| 1500 | control | t0.25 | checked | -0.3734 [-0.5319, -0.2322] | 0 / 0 | 3 / 25 | Yes |
| 1500 | high | w1 | pre | -0.1985 [-0.2767, -0.1337] | 0 / 0 | 0 / 0 | Yes |
| 1500 | high | w1 | checked | -0.5213 [-0.6639, -0.3928] | 0 / 0 | 128 / 196 | Yes |
| 1500 | high | t0.25 | pre | -0.2212 [-0.2958, -0.1594] | 0 / 0 | 0 / 0 | Yes |
| 1500 | high | t0.25 | checked | -0.7553 [-0.9203, -0.5928] | 0 / 0 | 97 / 196 | Yes |
| 5000 | control | w1 | pre | -0.0105 [-0.0170, -0.0048] | 0 / 0 | 0 / 0 | Yes |
| 5000 | control | w1 | checked | -0.0584 [-0.1253, -0.0069] | 0 / 0 | 5 / 8 | Yes |
| 5000 | control | t0.25 | pre | -0.0041 [-0.0097, +0.0019] | 0 / 0 | 0 / 0 | Yes |
| 5000 | control | t0.25 | checked | -0.1197 [-0.2088, -0.0483] | 0 / 0 | 1 / 8 | Yes |
| 5000 | high | w1 | pre | -0.2102 [-0.3152, -0.1269] | 0 / 0 | 0 / 0 | Yes |
| 5000 | high | w1 | checked | -0.4067 [-0.5803, -0.2528] | 0 / 0 | 93 / 147 | Yes |
| 5000 | high | t0.25 | pre | -0.2612 [-0.3630, -0.1791] | 0 / 0 | 0 / 0 | Yes |
| 5000 | high | t0.25 | checked | -0.8002 [-0.9951, -0.6199] | 0 / 0 | 43 / 147 | Yes |
| 50000 | control | w1 | pre | -0.0012 [-0.0025, -0.0001] | 0 / 0 | 0 / 0 | Yes |
| 50000 | control | w1 | checked | -0.0012 [-0.0025, -0.0001] | 0 / 0 | 0 / 0 | Yes |
| 50000 | control | t0.25 | pre | +0.0051 [-0.0016, +0.0119] | 0 / 0 | 0 / 0 | Yes |
| 50000 | control | t0.25 | checked | +0.0051 [-0.0016, +0.0119] | 0 / 0 | 0 / 0 | Yes |
| 50000 | high | w1 | pre | -0.2488 [-0.3875, -0.1334] | 0 / 0 | 0 / 0 | Yes |
| 50000 | high | w1 | checked | -0.4177 [-0.6552, -0.2142] | 0 / 0 | 76 / 131 | Yes |
| 50000 | high | t0.25 | pre | -0.2940 [-0.4300, -0.1817] | 0 / 0 | 0 / 0 | Yes |
| 50000 | high | t0.25 | checked | -0.8714 [-1.1228, -0.6593] | 0 / 0 | 19 / 131 | Yes |

## Guidance and fresh-panel checks

E is the larger absolute endpoint z error before checking. Each capture or loss denominator includes all classifiable valid fits in that group. Only guidance-panel decisions determine release.

| Arm | Panel | Declined | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- |
| Unchanged refineR | guidance | 753/3743 | 334/380 | 0/0 | 40/1554 |
| Unchanged refineR | diagnostic | 767/3743 | 335/380 | 0/0 | 54/1554 |
| Stage 2 | guidance | 617/3744 | 193/246 | 0/0 | 42/1633 |
| Stage 2 | diagnostic | 632/3744 | 194/246 | 0/0 | 54/1633 |
| w1 | guidance | 453/3744 | 124/137 | 2/2 | 41/1806 |
| w1 | diagnostic | 525/3744 | 127/137 | 2/2 | 56/1806 |
| t0.25 | guidance | 281/3744 | 150/202 | 0/0 | 22/1947 |
| t0.25 | diagnostic | 448/3744 | 156/202 | 0/0 | 55/1947 |

## Both selected updates available

| Stage 2 parent subset | Arm | Assigned | Returned | Pre-check loss |
| --- | --- | --- | --- | --- |
| yes | w1 | 3743 | 3743 | 0.2956 |
| yes | t0.25 | 3743 | 3743 | 0.2798 |
| parent_nonfallback | w1 | 2569 | 2569 | 0.2071 |
| parent_nonfallback | t0.25 | 2569 | 2569 | 0.1963 |
| parent_fallback | w1 | 1174 | 1174 | 0.4892 |
| parent_fallback | t0.25 | 1174 | 1174 | 0.4623 |

Paired intervals use 2,000 percentile bootstrap resamples of factorial cells, preserving their replicates, with PCG64 seed 37000000. Synthetic ground truth is available only to scoring. The technical audit covers every planned case and all primary, repeated and independent-host results.

All 96 same-host shard repeats and 96 separate-host comparisons passed. The maximum cross-host endpoint difference was 0 of reference width. The maximum absolute PIT probability difference was 0.

[Paired losses and jointly returned results](paired-loss.csv) · [Accuracy](accuracy.csv) · [Endpoint errors](endpoints.csv) · [Center and spread bias](curve.csv) · [Fallback and peak decisions](branches.csv) · [Panel capture](panel-rates.csv) · [PIT-seed and panel disagreement](decision-pairs.csv) · [Unit, width and N sensitivity](sensitivity-summary.csv) · [Technical audit](evidence/audit.json) · [Case-level fits](evidence/fits.csv.gz) · [Case-level checks](evidence/checks.csv.gz)
