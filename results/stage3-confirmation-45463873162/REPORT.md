# Stage 3 synthetic confirmation

The primary arm used w = 1 and the post-fit comparator used t = 0.25 throughout the 7,488 fresh simulations. The primary arm passed before checking and passed after checking. The post-fit comparator passed before checking and passed after checking. Both weights came from development. RIbench awaits review.

## Prespecified comparisons with unchanged refineR

A negative difference favors the Stage 3 arm. Each endpoint contributes its absolute native healthy-scale z error capped at 5. A missing interval contributes 5 on its own side. Above 20% pathology the paired mean difference must be strictly negative. At or below 20% it must be at most 0.02. Each comparison also requires at most as many implausible intervals (uncapped mean absolute endpoint error above 5) and at most as many nonreturns. Before-check and checked comparisons use matching refineR releases. The decision uses unrounded point estimates. The 95% intervals use 2,000 paired bootstrap resamples of factorial cells.

| N | Pathology | Arm | Mode | Assigned | Loss difference [95% interval] | Implausible, arm / refineR | Nonreturns, arm / refineR | All criteria met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=5000 | ≤20% | w1 | pre | 1728 | -0.0299 [-0.0387, -0.0221] | 0 / 0 | 0 / 0 | Yes |
| <=5000 | ≤20% | w1 | checked | 1728 | -0.1662 [-0.2156, -0.1215] | 0 / 0 | 33 / 86 | Yes |
| <=5000 | ≤20% | t0.25 | pre | 1728 | -0.0179 [-0.0214, -0.0145] | 0 / 0 | 0 / 0 | Yes |
| <=5000 | ≤20% | t0.25 | checked | 1728 | -0.1709 [-0.2170, -0.1297] | 0 / 0 | 28 / 86 | Yes |
| <=5000 | >20% | w1 | pre | 3888 | -0.1958 [-0.2424, -0.1581] | 0 / 0 | 0 / 1 | Yes |
| <=5000 | >20% | w1 | checked | 3888 | -0.4797 [-0.5568, -0.4124] | 0 / 0 | 692 / 1068 | Yes |
| <=5000 | >20% | t0.25 | pre | 3888 | -0.2229 [-0.2701, -0.1855] | 0 / 0 | 0 / 1 | Yes |
| <=5000 | >20% | t0.25 | checked | 3888 | -0.7517 [-0.8323, -0.6751] | 0 / 0 | 479 / 1068 | Yes |
| 50000 | ≤20% | w1 | pre | 576 | -0.0017 [-0.0034, -0.0002] | 0 / 0 | 0 / 0 | Yes |
| 50000 | ≤20% | w1 | checked | 576 | -0.0098 [-0.0275, -0.0003] | 0 / 0 | 5 / 6 | Yes |
| 50000 | ≤20% | t0.25 | pre | 576 | +0.0051 [-0.0004, +0.0108] | 0 / 0 | 0 / 0 | Yes |
| 50000 | ≤20% | t0.25 | checked | 576 | -0.0374 [-0.0799, -0.0038] | 0 / 0 | 1 / 6 | Yes |
| 50000 | >20% | w1 | pre | 1296 | -0.2466 [-0.3856, -0.1311] | 0 / 0 | 0 / 0 | Yes |
| 50000 | >20% | w1 | checked | 1296 | -0.4317 [-0.6641, -0.2346] | 0 / 0 | 152 / 266 | Yes |
| 50000 | >20% | t0.25 | pre | 1296 | -0.2919 [-0.4288, -0.1809] | 0 / 0 | 0 / 0 | Yes |
| 50000 | >20% | t0.25 | checked | 1296 | -0.9180 [-1.1551, -0.7161] | 0 / 0 | 29 / 266 | Yes |

[Formal comparisons at full precision](confirmation-gates.csv)

## Each simulation sample size

| N | Pathology | Arm | Mode | Assigned | Loss difference [95% interval] | Implausible, arm / refineR | Nonreturns, arm / refineR | All criteria met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | ≤20% | w1 | pre | 576 | -0.0382 [-0.0536, -0.0254] | 0 / 0 | 0 / 0 | Yes |
| 1000 | ≤20% | w1 | checked | 576 | -0.2336 [-0.3350, -0.1434] | 0 / 0 | 14 / 39 | Yes |
| 1000 | ≤20% | t0.25 | pre | 576 | -0.0285 [-0.0345, -0.0224] | 0 / 0 | 0 / 0 | Yes |
| 1000 | ≤20% | t0.25 | checked | 576 | -0.2339 [-0.3361, -0.1474] | 0 / 0 | 13 / 39 | Yes |
| 1000 | >20% | w1 | pre | 1296 | -0.2147 [-0.2835, -0.1569] | 0 / 0 | 0 / 0 | Yes |
| 1000 | >20% | w1 | checked | 1296 | -0.6266 [-0.7449, -0.5210] | 0 / 0 | 245 / 409 | Yes |
| 1000 | >20% | t0.25 | pre | 1296 | -0.2144 [-0.2763, -0.1626] | 0 / 0 | 0 / 0 | Yes |
| 1000 | >20% | t0.25 | checked | 1296 | -0.7394 [-0.8531, -0.6257] | 0 / 0 | 214 / 409 | Yes |
| 1500 | ≤20% | w1 | pre | 576 | -0.0430 [-0.0635, -0.0252] | 0 / 0 | 0 / 0 | Yes |
| 1500 | ≤20% | w1 | checked | 576 | -0.2328 [-0.3274, -0.1414] | 0 / 0 | 11 / 36 | Yes |
| 1500 | ≤20% | t0.25 | pre | 576 | -0.0157 [-0.0213, -0.0098] | 0 / 0 | 0 / 0 | Yes |
| 1500 | ≤20% | t0.25 | checked | 576 | -0.2034 [-0.2874, -0.1284] | 0 / 0 | 12 / 36 | Yes |
| 1500 | >20% | w1 | pre | 1296 | -0.1867 [-0.2580, -0.1294] | 0 / 0 | 0 / 1 | Yes |
| 1500 | >20% | w1 | checked | 1296 | -0.4387 [-0.5552, -0.3374] | 0 / 0 | 238 / 351 | Yes |
| 1500 | >20% | t0.25 | pre | 1296 | -0.2201 [-0.2962, -0.1573] | 0 / 0 | 0 / 1 | Yes |
| 1500 | >20% | t0.25 | checked | 1296 | -0.7219 [-0.8537, -0.5969] | 0 / 0 | 163 / 351 | Yes |
| 5000 | ≤20% | w1 | pre | 576 | -0.0085 [-0.0132, -0.0042] | 0 / 0 | 0 / 0 | Yes |
| 5000 | ≤20% | w1 | checked | 576 | -0.0320 [-0.0655, -0.0071] | 0 / 0 | 8 / 11 | Yes |
| 5000 | ≤20% | t0.25 | pre | 576 | -0.0096 [-0.0144, -0.0046] | 0 / 0 | 0 / 0 | Yes |
| 5000 | ≤20% | t0.25 | checked | 576 | -0.0755 [-0.1189, -0.0341] | 0 / 0 | 3 / 11 | Yes |
| 5000 | >20% | w1 | pre | 1296 | -0.1860 [-0.2794, -0.1122] | 0 / 0 | 0 / 0 | Yes |
| 5000 | >20% | w1 | checked | 1296 | -0.3740 [-0.5269, -0.2488] | 0 / 0 | 209 / 308 | Yes |
| 5000 | >20% | t0.25 | pre | 1296 | -0.2341 [-0.3271, -0.1586] | 0 / 0 | 0 / 0 | Yes |
| 5000 | >20% | t0.25 | checked | 1296 | -0.7939 [-0.9566, -0.6350] | 0 / 0 | 102 / 308 | Yes |
| 50000 | ≤20% | w1 | pre | 576 | -0.0017 [-0.0034, -0.0002] | 0 / 0 | 0 / 0 | Yes |
| 50000 | ≤20% | w1 | checked | 576 | -0.0098 [-0.0275, -0.0003] | 0 / 0 | 5 / 6 | Yes |
| 50000 | ≤20% | t0.25 | pre | 576 | +0.0051 [-0.0004, +0.0108] | 0 / 0 | 0 / 0 | Yes |
| 50000 | ≤20% | t0.25 | checked | 576 | -0.0374 [-0.0799, -0.0038] | 0 / 0 | 1 / 6 | Yes |
| 50000 | >20% | w1 | pre | 1296 | -0.2466 [-0.3856, -0.1311] | 0 / 0 | 0 / 0 | Yes |
| 50000 | >20% | w1 | checked | 1296 | -0.4317 [-0.6641, -0.2346] | 0 / 0 | 152 / 266 | Yes |
| 50000 | >20% | t0.25 | pre | 1296 | -0.2919 [-0.4288, -0.1809] | 0 / 0 | 0 / 0 | Yes |
| 50000 | >20% | t0.25 | checked | 1296 | -0.9180 [-1.1551, -0.7161] | 0 / 0 | 29 / 266 | Yes |

[Each N at full precision](confirmation-gates-by-n.csv)

## Accuracy and coverage

The guidance panel and primary randomized-PIT seed determine the checked release. Anchors-only retains its C2 reporting rule.

| Arm | Mode | Assigned | Returned | Mean loss | Mean among returned | Implausible | Fit failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 7488 | 7487 | 0.4394 | 0.4388 | 0 | 1 |
| Unchanged refineR | checked | 7488 | 6062 | 1.1328 | 0.2231 | 0 | 1 |
| Stage 2 | pre | 7488 | 7488 | 0.3379 | 0.3379 | 0 | 0 |
| Stage 2 | checked | 7488 | 6319 | 0.9693 | 0.2236 | 0 | 0 |
| w1 | pre | 7488 | 7488 | 0.2880 | 0.2880 | 0 | 0 |
| w1 | checked | 7488 | 6606 | 0.7699 | 0.2051 | 0 | 0 |
| t0.25 | pre | 7488 | 7488 | 0.2694 | 0.2694 | 0 | 0 |
| t0.25 | checked | 7488 | 6951 | 0.5413 | 0.1968 | 0 | 0 |
| Anchors-only | pre | 7488 | 7488 | 0.2550 | 0.2550 | 1 | 0 |
| Anchors-only | checked | 7488 | 7488 | 0.2550 | 0.2550 | 1 | 0 |

## Results when Stage 2 fell back

Membership uses the original Stage 2 fallback flag on every dataset, including unsuccessful updates. The table compares each Stage 3 arm to Stage 2 before and after the guidance-panel check. A subset's contribution to the pooled pre-check difference is its mean difference multiplied by its share of all datasets at that N. An empty subset contributes zero.

| N | Stage 2 parent | Assigned | Arm | Pre loss | Stage 2 pre loss | Pre difference | Contribution | Checked difference | Checked returned, arm / Stage 2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=5000 | Fallback | 2344 | w1 | 0.4632 | 0.5586 | -0.0954 | -0.0398 | -0.3493 | 1872 / 1709 |
| <=5000 | Fallback | 2344 | t0.25 | 0.4325 | 0.5586 | -0.1262 | -0.0527 | -0.5196 | 1952 / 1709 |
| <=5000 | Non-fallback | 3272 | w1 | 0.2248 | 0.2684 | -0.0435 | -0.0254 | -0.1926 | 3019 / 2903 |
| <=5000 | Non-fallback | 3272 | t0.25 | 0.2210 | 0.2684 | -0.0474 | -0.0276 | -0.3963 | 3157 / 2903 |
| 1000 | Fallback | 1073 | w1 | 0.4421 | 0.5600 | -0.1179 | -0.0676 | -0.4777 | 866 / 763 |
| 1000 | Fallback | 1073 | t0.25 | 0.4357 | 0.5600 | -0.1243 | -0.0713 | -0.5477 | 881 / 763 |
| 1000 | Non-fallback | 799 | w1 | 0.2416 | 0.3130 | -0.0714 | -0.0305 | -0.3310 | 747 / 698 |
| 1000 | Non-fallback | 799 | t0.25 | 0.2576 | 0.3130 | -0.0554 | -0.0236 | -0.4202 | 764 / 698 |
| 1500 | Fallback | 852 | w1 | 0.4787 | 0.5665 | -0.0877 | -0.0399 | -0.3074 | 678 / 626 |
| 1500 | Fallback | 852 | t0.25 | 0.4394 | 0.5665 | -0.1271 | -0.0578 | -0.5143 | 714 / 626 |
| 1500 | Non-fallback | 1020 | w1 | 0.2362 | 0.2927 | -0.0565 | -0.0308 | -0.2264 | 945 / 904 |
| 1500 | Non-fallback | 1020 | t0.25 | 0.2421 | 0.2927 | -0.0506 | -0.0275 | -0.3968 | 983 / 904 |
| 5000 | Fallback | 419 | w1 | 0.4855 | 0.5391 | -0.0536 | -0.0120 | -0.1054 | 328 / 320 |
| 5000 | Fallback | 419 | t0.25 | 0.4101 | 0.5391 | -0.1290 | -0.0289 | -0.4585 | 357 / 320 |
| 5000 | Non-fallback | 1453 | w1 | 0.2077 | 0.2268 | -0.0191 | -0.0149 | -0.0928 | 1327 / 1301 |
| 5000 | Non-fallback | 1453 | t0.25 | 0.1861 | 0.2268 | -0.0407 | -0.0316 | -0.3828 | 1410 / 1301 |
| 50000 | Fallback | 52 | w1 | 0.2453 | 0.2659 | -0.0205 | -0.0006 | -0.1891 | 44 / 42 |
| 50000 | Fallback | 52 | t0.25 | 0.2192 | 0.2659 | -0.0466 | -0.0013 | -0.5555 | 48 / 42 |
| 50000 | Non-fallback | 1820 | w1 | 0.1770 | 0.1808 | -0.0038 | -0.0037 | -0.0188 | 1671 / 1665 |
| 50000 | Non-fallback | 1820 | t0.25 | 0.1477 | 0.1808 | -0.0331 | -0.0322 | -0.3634 | 1794 / 1665 |

All N and pathology combinations, including high-pathology shoulder/overlap and separated disease, are available with both extractions, paired intervals and coverage. The parent counts include empty subsets. Fractions and panel capture use their own displayed denominators. [Parent counts](parent-counts.csv) · [Parent comparisons](parent-comparisons.csv) · [Panel capture by parent](panel-rates.csv)

## Fits where both updates were available

| Stage 2 parent subset | Arm | Mode | Assigned | Returned | Mean loss |
| --- | --- | --- | --- | --- | --- |
| yes | w1 | pre | 7488 | 7488 | 0.2880 |
| yes | w1 | checked | 7488 | 6606 | 0.7699 |
| yes | t0.25 | pre | 7488 | 7488 | 0.2694 |
| yes | t0.25 | checked | 7488 | 6951 | 0.5413 |
| parent_fallback | w1 | pre | 2396 | 2396 | 0.4585 |
| parent_fallback | w1 | checked | 2396 | 1916 | 1.1836 |
| parent_fallback | t0.25 | pre | 2396 | 2396 | 0.4278 |
| parent_fallback | t0.25 | checked | 2396 | 2000 | 1.0090 |
| parent_nonfallback | w1 | pre | 5092 | 5092 | 0.2078 |
| parent_nonfallback | w1 | checked | 5092 | 4690 | 0.5752 |
| parent_nonfallback | t0.25 | pre | 5092 | 5092 | 0.1948 |
| parent_nonfallback | t0.25 | checked | 5092 | 4951 | 0.3212 |

## High-pathology comparisons at N = 50,000

Gap closed is Stage 2 loss minus arm loss. Remaining gap is arm loss minus anchors-only loss. These are the observed gaps on the independent synthetic datasets. The previous RIbench gap was 0.0540.

| Pathology subset | Mode | Assigned | Arm | Stage 2 | Arm loss | Anchors-only | Gap closed | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high | pre | 1296 | w1 | 0.2311 | 0.2257 | 0.2552 | +0.0054 | -0.0294 |
| high | pre | 1296 | t0.25 | 0.2311 | 0.1804 | 0.2552 | +0.0507 | -0.0747 |
| high | checked | 1296 | w1 | 0.8017 | 0.7720 | 0.2552 | +0.0297 | +0.5168 |
| high | checked | 1296 | t0.25 | 0.8017 | 0.2857 | 0.2552 | +0.5160 | +0.0305 |
| focus | pre | 864 | w1 | 0.2883 | 0.2858 | 0.2563 | +0.0025 | +0.0295 |
| focus | pre | 864 | t0.25 | 0.2883 | 0.2100 | 0.2563 | +0.0783 | -0.0463 |
| focus | checked | 864 | w1 | 1.0914 | 1.0629 | 0.2563 | +0.0285 | +0.8065 |
| focus | checked | 864 | t0.25 | 1.0914 | 0.3648 | 0.2563 | +0.7266 | +0.1085 |
| separated_high | pre | 432 | w1 | 0.1168 | 0.1056 | 0.2529 | +0.0112 | -0.1472 |
| separated_high | pre | 432 | t0.25 | 0.1168 | 0.1212 | 0.2529 | -0.0044 | -0.1316 |
| separated_high | checked | 432 | w1 | 0.2223 | 0.1902 | 0.2529 | +0.0321 | -0.0626 |
| separated_high | checked | 432 | t0.25 | 0.2223 | 0.1276 | 0.2529 | +0.0948 | -0.1253 |

## Guidance and fresh-panel checks

E is the larger absolute endpoint z error. Declines are shown among evaluable checks. Capture and good-result loss use all classifiable valid fits in each category.

| Stage 2 parent | Arm | Panel | Declined | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- | --- |
| All | Unchanged refineR | guidance | 1425/7487 | 626/715 | 1/1 | 81/3176 |
| All | Unchanged refineR | diagnostic | 1457/7487 | 622/715 | 1/1 | 97/3176 |
| All | Stage 2 | guidance | 1169/7488 | 350/455 | 1/1 | 85/3304 |
| All | Stage 2 | diagnostic | 1197/7488 | 345/455 | 1/1 | 99/3304 |
| All | w1 | guidance | 882/7488 | 229/267 | 1/1 | 97/3637 |
| All | w1 | diagnostic | 977/7488 | 235/267 | 1/1 | 98/3637 |
| All | t0.25 | guidance | 537/7488 | 268/370 | 0/0 | 46/3977 |
| All | t0.25 | diagnostic | 822/7488 | 278/370 | 0/0 | 105/3977 |
| fallback | Unchanged refineR | guidance | 645/2396 | 290/321 | 1/1 | 34/775 |
| fallback | Unchanged refineR | diagnostic | 654/2396 | 286/321 | 1/1 | 37/775 |
| fallback | Stage 2 | guidance | 645/2396 | 290/321 | 1/1 | 34/775 |
| fallback | Stage 2 | diagnostic | 654/2396 | 286/321 | 1/1 | 37/775 |
| fallback | w1 | guidance | 480/2396 | 222/232 | 1/1 | 40/923 |
| fallback | w1 | diagnostic | 517/2396 | 224/232 | 1/1 | 38/923 |
| fallback | t0.25 | guidance | 396/2396 | 252/288 | 0/0 | 24/1010 |
| fallback | t0.25 | diagnostic | 479/2396 | 254/288 | 0/0 | 37/1010 |
| nonfallback | Unchanged refineR | guidance | 780/5091 | 336/394 | 0/0 | 47/2401 |
| nonfallback | Unchanged refineR | diagnostic | 803/5091 | 336/394 | 0/0 | 60/2401 |
| nonfallback | Stage 2 | guidance | 524/5092 | 60/134 | 0/0 | 51/2529 |
| nonfallback | Stage 2 | diagnostic | 543/5092 | 59/134 | 0/0 | 62/2529 |
| nonfallback | w1 | guidance | 402/5092 | 7/35 | 0/0 | 57/2714 |
| nonfallback | w1 | diagnostic | 460/5092 | 11/35 | 0/0 | 60/2714 |
| nonfallback | t0.25 | guidance | 141/5092 | 16/82 | 0/0 | 22/2967 |
| nonfallback | t0.25 | diagnostic | 343/5092 | 24/82 | 0/0 | 68/2967 |

The case-level exports retain both PIT seeds, the guidance and fresh panels, both extractors and every fit failure. The two zero-weight labels audit identity with Stage 2. The five scientific arms are unchanged refineR, Stage 2, w1, t0.25 and anchors-only. [Task G fit objects and join keys](TASK-G.md) · [Per-dataset fits](evidence/fits.csv.gz) · [Per-dataset checks](evidence/checks.csv.gz)

## Reproducibility

All 96 same-host repetitions and 96 separate-host shard comparisons passed. The maximum cross-host endpoint difference was 0 of interval width. The maximum absolute difference between PIT probabilities was 0. [Technical audit](evidence/audit.json) · [Fit branches and failure reasons](branches.csv) · [Historical and native paired results](paired-loss.csv) · [Endpoint errors](endpoints.csv) · [Healthy center and spread by elected basin](curve.csv) · [Coverage](coverage.csv) · [PIT-seed and panel disagreement](decision-pairs.csv)

## Observations from development

Unit sensitivity was already present in the refineR-based Stage 2 fit. A change of measurement units moved at least one back-converted endpoint by more than 0.1% of interval width on 36 of 720 Stage 2 datasets, 35 for the primary arm and 36 for the post-fit arm. In development, t = 0.5 reduced small-N control error but increased control error by 0.0431 at N = 50,000. Studying a blend weight that varies with N would require new development and confirmation samples. [Stage 3 development](../stage3-development/REVIEW.md)
