# Stage 3 RIbench, N = 50,000

Both frozen arms ran on 1,440 paired RIbench datasets. The primary (w = 1) met the pre-check criteria and met the checked criteria. The post-fit (t = 0.25) met the pre-check criteria and met the checked criteria.

## Prespecified gates

The difference is arm minus unchanged refineR in mean capped absolute endpoint z error. Both sides use native limits. Checked comparisons use each fit’s own guidance-panel decision under the primary PIT seed. Every failed, withheld or unscorable interval contributes 5. Above 20% pathology the difference must be strictly negative. At or below 20% the margin is +0.02. Each comparison must also have no extra implausible intervals or nonreturns. The table gives arm and refineR counts in that order. The formal decision uses the unrounded point estimates.


| Pathology | Arm | Release | Assigned | Loss difference [95% interval] | Implausible | Nonreturns | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <=20% | Primary (w = 1) | pre | 720 | -0.0034 [-0.0094, +0.0012] | 0 / 0 | 0 / 0 | Met |
| <=20% | Primary (w = 1) | checked | 720 | -0.1091 [-0.2367, -0.0195] | 0 / 0 | 26 / 43 | Met |
| <=20% | Post-fit (t = 0.25) | pre | 720 | +0.0112 [-0.0015, +0.0217] | 0 / 0 | 0 / 0 | Met |
| <=20% | Post-fit (t = 0.25) | checked | 720 | -0.1502 [-0.2785, -0.0458] | 0 / 0 | 18 / 43 | Met |
| >20% | Primary (w = 1) | pre | 720 | -0.0639 [-0.0981, -0.0344] | 0 / 0 | 0 / 0 | Met |
| >20% | Primary (w = 1) | checked | 720 | -0.2486 [-0.3550, -0.1511] | 0 / 0 | 69 / 106 | Met |
| >20% | Post-fit (t = 0.25) | pre | 720 | -0.0749 [-0.0995, -0.0517] | 0 / 0 | 0 / 0 | Met |
| >20% | Post-fit (t = 0.25) | checked | 720 | -0.4795 [-0.6321, -0.3457] | 0 / 0 | 35 / 106 | Met |


Implausibility means uncapped mean absolute error across requested endpoints above 5. The severe endpoint flag uses the largest absolute endpoint error. For CRP the only requested endpoint is the 95th percentile. [Formal comparisons](gates.csv) · [Separate N comparisons](gates-by-n.csv.gz) · [Native and historical contrasts](paired-loss.csv.gz)

## Error and coverage


| Arm | Release | Returned | Fit failures | Implausible | All-set loss | Returned/scored loss |
| --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 1440 | 0 | 0 | 0.2300 | 0.2300 |
| Unchanged refineR | checked | 1291 | 0 | 0 | 0.6686 | 0.1687 |
| Stage 2 | pre | 1440 | 0 | 0 | 0.2287 | 0.2287 |
| Stage 2 | checked | 1293 | 0 | 0 | 0.6621 | 0.1689 |
| Primary (w = 1) | pre | 1440 | 0 | 0 | 0.1963 | 0.1963 |
| Primary (w = 1) | checked | 1345 | 0 | 0 | 0.4898 | 0.1712 |
| Post-fit (t = 0.25) | pre | 1440 | 0 | 0 | 0.1981 | 0.1981 |
| Post-fit (t = 0.25) | checked | 1387 | 0 | 0 | 0.3537 | 0.1762 |
| Anchors only | pre | 1440 | 0 | 0 | 0.2961 | 0.2961 |
| Anchors only | checked | 1440 | 0 | 0 | 0.2961 | 0.2961 |


## Baseline Stage 2 fallback

Subgroup membership is fixed by the Stage 2 fit on that dataset. The weighted contribution is the within-subgroup difference multiplied by that subgroup’s share of the cohort. The fallback and non-fallback contributions sum to the pooled change from Stage 2.


| Stage 2 subgroup | Datasets | Arm | Release | Stage 2 loss | Arm loss | Change from Stage 2 [95% interval] | Contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fallback | 57 | Primary (w = 1) | pre | 0.8636 | 0.6130 | -0.2505 [-0.5159, -0.0548] | -0.0099 |
| nonfallback | 1383 | Primary (w = 1) | pre | 0.2026 | 0.1791 | -0.0234 [-0.0339, -0.0136] | -0.0225 |
| fallback | 57 | Primary (w = 1) | checked | 2.5628 | 1.9903 | -0.5725 [-1.2919, -0.0438] | -0.0227 |
| nonfallback | 1383 | Primary (w = 1) | checked | 0.5838 | 0.4279 | -0.1558 [-0.2422, -0.0847] | -0.1497 |
| fallback | 57 | Post-fit (t = 0.25) | pre | 0.8636 | 0.6652 | -0.1984 [-0.2569, -0.0825] | -0.0079 |
| nonfallback | 1383 | Post-fit (t = 0.25) | pre | 0.2026 | 0.1789 | -0.0237 [-0.0371, -0.0117] | -0.0228 |
| fallback | 57 | Post-fit (t = 0.25) | checked | 2.5628 | 1.8243 | -0.7385 [-1.2887, -0.0499] | -0.0292 |
| nonfallback | 1383 | Post-fit (t = 0.25) | checked | 0.5838 | 0.2931 | -0.2906 [-0.4044, -0.1951] | -0.2791 |


[Parent subgroups by N and pathology](parent-contributions.csv.gz) · [Search branches and reasons](branches.csv.gz) · [Both updates available and common scored results](paired-loss.csv.gz)

## RIbench overlap and pathological fraction

RIbench assigns low, medium or high overlap separately to its left and right pathological components. These are the original specification labels, including on zero-pathology controls. The tables retain left, right and ordered pair labels. Pre-check entries below use native limits and all assigned datasets.


| Designed overlap | Level | Datasets | Stage 2 loss | Primary loss | Primary Δ [95% interval] | Post-fit loss | Post-fit Δ [95% interval] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| overlapPatholLeft | high | 480 | 0.2683 | 0.2226 | -0.0457 [-0.0652, -0.0262] | 0.2258 | -0.0425 [-0.0614, -0.0242] |
| overlapPatholLeft | low | 480 | 0.1968 | 0.1760 | -0.0208 [-0.0349, -0.0086] | 0.1740 | -0.0227 [-0.0386, -0.0088] |
| overlapPatholLeft | medium | 480 | 0.2211 | 0.1904 | -0.0308 [-0.0495, -0.0149] | 0.1945 | -0.0266 [-0.0419, -0.0124] |
| overlapPatholRight | high | 480 | 0.2715 | 0.2346 | -0.0369 [-0.0586, -0.0194] | 0.2247 | -0.0469 [-0.0617, -0.0325] |
| overlapPatholRight | low | 480 | 0.1939 | 0.1667 | -0.0272 [-0.0460, -0.0118] | 0.1765 | -0.0174 [-0.0331, -0.0038] |
| overlapPatholRight | medium | 480 | 0.2208 | 0.1876 | -0.0331 [-0.0531, -0.0156] | 0.1931 | -0.0276 [-0.0457, -0.0108] |



| Pathological fraction | Level | Datasets | Stage 2 loss | Primary loss | Primary Δ [95% interval] | Post-fit loss | Post-fit Δ [95% interval] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fraction | 0 | 180 | 0.0600 | 0.0498 | -0.0103 [-0.0225, -0.0002] | 0.0938 | +0.0338 [+0.0195, +0.0452] |
| fraction | 0.05 | 180 | 0.0796 | 0.0771 | -0.0025 [-0.0074, +0.0004] | 0.0944 | +0.0149 [+0.0022, +0.0244] |
| fraction | 0.1 | 180 | 0.1044 | 0.1000 | -0.0043 [-0.0111, +0.0008] | 0.1101 | +0.0058 [-0.0071, +0.0163] |
| fraction | 0.2 | 180 | 0.1420 | 0.1380 | -0.0041 [-0.0078, -0.0008] | 0.1247 | -0.0173 [-0.0316, -0.0031] |
| fraction | 0.3 | 180 | 0.2002 | 0.1858 | -0.0144 [-0.0282, -0.0035] | 0.1724 | -0.0278 [-0.0397, -0.0163] |
| fraction | 0.4 | 180 | 0.2856 | 0.2534 | -0.0322 [-0.0539, -0.0136] | 0.2370 | -0.0485 [-0.0676, -0.0310] |
| fraction | 0.5 | 180 | 0.3669 | 0.3197 | -0.0471 [-0.0728, -0.0245] | 0.2909 | -0.0760 [-0.1015, -0.0528] |
| fraction | 0.6 | 180 | 0.5913 | 0.4468 | -0.1445 [-0.2315, -0.0714] | 0.4615 | -0.1298 [-0.1718, -0.0903] |


[All pairwise overlaps and fractional strata](paired-loss.csv.gz) · [Official case labels](overlap.csv.gz)

## Same-dataset comparisons

Unchanged refineR, frozen Stage 2 and anchors-only used the same ordered inputs. The anchoredRI comparators are the archived Task E arm B and the improved anchoredRI baseline. Raw comparisons use their fitted intervals. Checked comparisons use the intervals they originally reported after their own safeguards. The archived C2 anchors-only reporting rule releases a successful fit. All pairing uses RIbench Index plus ordered routine and anchor hashes. The final two columns restrict both methods to cases where both returned scorable results.


| Arm | Release | Comparator | Matched | Arm returned | Comparator returned | Arm loss | Comparator loss | Arm − comparator [95% interval] | Common scored | Common Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primary (w = 1) | pre | Stage 2 | 1440 | 1440 | 1440 | 0.1963 | 0.2287 | -0.0324 [-0.0477, -0.0186] | 1440 | -0.0324 |
| Primary (w = 1) | pre | Anchors only | 1440 | 1440 | 1440 | 0.1963 | 0.2961 | -0.0998 [-0.1837, -0.0252] | 1440 | -0.0998 |
| Primary (w = 1) | pre | anchoredRI Arm B (Task E) | 1440 | 1440 | 1440 | 0.1963 | 0.3751 | -0.1788 [-0.4303, +0.0199] | 1440 | -0.1788 |
| Primary (w = 1) | pre | Improved anchoredRI baseline | 1440 | 1440 | 1440 | 0.1963 | 0.4280 | -0.2317 [-0.3548, -0.0970] | 1440 | -0.2317 |
| Primary (w = 1) | checked | Stage 2 | 1440 | 1345 | 1293 | 0.4898 | 0.6621 | -0.1723 [-0.2574, -0.0998] | 1293 | -0.0094 |
| Primary (w = 1) | checked | Anchors only | 1440 | 1345 | 1440 | 0.4898 | 0.2961 | +0.1936 [+0.0336, +0.3753] | 1345 | -0.1179 |
| Primary (w = 1) | checked | anchoredRI Arm B (Task E) | 1440 | 1345 | 1135 | 0.4898 | 1.1620 | -0.6722 [-1.3551, -0.0854] | 1075 | +0.0406 |
| Primary (w = 1) | checked | Improved anchoredRI baseline | 1440 | 1345 | 1066 | 0.4898 | 1.4249 | -0.9351 [-1.5609, -0.3750] | 1026 | +0.0014 |
| Post-fit (t = 0.25) | pre | Stage 2 | 1440 | 1440 | 1440 | 0.1981 | 0.2287 | -0.0306 [-0.0453, -0.0169] | 1440 | -0.0306 |
| Post-fit (t = 0.25) | pre | Anchors only | 1440 | 1440 | 1440 | 0.1981 | 0.2961 | -0.0980 [-0.1748, -0.0296] | 1440 | -0.0980 |
| Post-fit (t = 0.25) | pre | anchoredRI Arm B (Task E) | 1440 | 1440 | 1440 | 0.1981 | 0.3751 | -0.1770 [-0.4237, +0.0171] | 1440 | -0.1770 |
| Post-fit (t = 0.25) | pre | Improved anchoredRI baseline | 1440 | 1440 | 1440 | 0.1981 | 0.4280 | -0.2298 [-0.3559, -0.0947] | 1440 | -0.2298 |
| Post-fit (t = 0.25) | checked | Stage 2 | 1440 | 1387 | 1293 | 0.3537 | 0.6621 | -0.3084 [-0.4247, -0.2106] | 1293 | -0.0139 |
| Post-fit (t = 0.25) | checked | Anchors only | 1440 | 1387 | 1440 | 0.3537 | 0.2961 | +0.0576 [-0.0818, +0.2036] | 1387 | -0.1177 |
| Post-fit (t = 0.25) | checked | anchoredRI Arm B (Task E) | 1440 | 1387 | 1135 | 0.3537 | 1.1620 | -0.8083 [-1.4973, -0.2313] | 1101 | +0.0425 |
| Post-fit (t = 0.25) | checked | Improved anchoredRI baseline | 1440 | 1387 | 1066 | 0.3537 | 1.4249 | -1.0712 [-1.7016, -0.5082] | 1041 | -0.0005 |


## Gap to anchors-only

The gap closed is Stage 2 loss minus arm loss. The remaining gap is arm loss minus anchors-only loss. Both use the same datasets. On the large cohort the above-20% rows address the prespecified target of 720 datasets.


| Pathology | Arm | Release | Assigned | Stage 2 | Arm | Anchors-only | Gap closed | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=20% | Primary (w = 1) | pre | 720 | 0.0965 | 0.0912 | 0.2853 | +0.0053 | -0.1941 |
| <=20% | Primary (w = 1) | checked | 720 | 0.3707 | 0.2610 | 0.2853 | +0.1097 | -0.0243 |
| <=20% | Post-fit (t = 0.25) | pre | 720 | 0.0965 | 0.1058 | 0.2853 | -0.0093 | -0.1795 |
| <=20% | Post-fit (t = 0.25) | checked | 720 | 0.3707 | 0.2199 | 0.2853 | +0.1509 | -0.0654 |
| >20% | Primary (w = 1) | pre | 720 | 0.3610 | 0.3014 | 0.3070 | +0.0595 | -0.0056 |
| >20% | Primary (w = 1) | checked | 720 | 0.9535 | 0.7185 | 0.3070 | +0.2349 | +0.4116 |
| >20% | Post-fit (t = 0.25) | pre | 720 | 0.3610 | 0.2904 | 0.3070 | +0.0705 | -0.0165 |
| >20% | Post-fit (t = 0.25) | checked | 720 | 0.9535 | 0.4876 | 0.3070 | +0.4659 | +0.1806 |


[Gap estimates, intervals and subgroups](gap.csv.gz) · [Comparator sources](../../stage2/ribench/comparators/README.md)

## Guidance-panel checks

RIbench has one independent panel of 40 screened anchors per dataset. Both PIT seeds use the same rounded panel. The primary seed determines release. E is the largest absolute error of the requested endpoints before checking.


| Arm | PIT seed | Declined / evaluable | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- |
| Unchanged refineR | primary | 149 / 1440 | 57 / 94 | 1 / 1 | 16 / 881 |
| Unchanged refineR | alternate | 147 / 1440 | 57 / 94 | 1 / 1 | 14 / 881 |
| Stage 2 | primary | 147 / 1440 | 56 / 93 | 1 / 1 | 15 / 882 |
| Stage 2 | alternate | 146 / 1440 | 56 / 93 | 1 / 1 | 14 / 882 |
| Primary (w = 1) | primary | 95 / 1440 | 26 / 65 | 0 / 0 | 14 / 901 |
| Primary (w = 1) | alternate | 95 / 1440 | 26 / 65 | 0 / 0 | 13 / 901 |
| Post-fit (t = 0.25) | primary | 53 / 1440 | 23 / 62 | 1 / 1 | 2 / 944 |
| Post-fit (t = 0.25) | alternate | 52 / 1440 | 23 / 62 | 1 / 1 | 1 / 944 |



| Arm | PIT-seed reversals | Evaluable under both | Share |
| --- | --- | --- | --- |
| Unchanged refineR | 12 | 1440 | 0.0083 |
| Stage 2 | 11 | 1440 | 0.0076 |
| Primary (w = 1) | 6 | 1440 | 0.0042 |
| Post-fit (t = 0.25) | 1 | 1440 | 0.0007 |


## Audit and Task G export

The technical audit covered all 1,440 primary datasets. The verified repeated set contained 144 datasets. The maximum separate-host endpoint difference was 0 of reference width, and the maximum PIT probability difference was 0. Descriptive 95% intervals use 2,000 matched bootstrap resamples of (analyte, scenario) clusters with PCG64 seed 37000000. Intervals require at least two informative clusters.

[Technical audit](evidence/audit.json) · [Fit records](evidence/fits.csv.gz) · [Decisions](evidence/checks.csv.gz) · [Task G guide](TASK-G.md) · [Error and coverage](accuracy.csv.gz) · [Endpoint errors](endpoints.csv.gz) · [Healthy curve error by elected basin](curve.csv.gz) · [Capture and good-result loss](rates.csv.gz) · [PIT-seed reversals](seed-changes.csv.gz)
