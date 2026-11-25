# Stage 3 RIbench, N ≤ 5,000

Both frozen arms ran on 2,880 paired RIbench datasets. The primary (w = 1) met the pre-check criteria and met the checked criteria. The post-fit (t = 0.25) met the pre-check criteria and met the checked criteria.

## Prespecified gates

The difference is arm minus unchanged refineR in mean capped absolute endpoint z error. Both sides use native limits. Checked comparisons use each fit’s own guidance-panel decision under the primary PIT seed. Every failed, withheld or unscorable interval contributes 5. Above 20% pathology the difference must be strictly negative. At or below 20% the margin is +0.02. Each comparison must also have no extra implausible intervals or nonreturns. The table gives arm and refineR counts in that order. The formal decision uses the unrounded point estimates.


| Pathology | Arm | Release | Assigned | Loss difference [95% interval] | Implausible | Nonreturns | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <=20% | Primary (w = 1) | pre | 1440 | -0.0258 [-0.0378, -0.0157] | 0 / 0 | 0 / 0 | Met |
| <=20% | Primary (w = 1) | checked | 1440 | -0.2744 [-0.3739, -0.1862] | 0 / 0 | 42 / 122 | Met |
| <=20% | Post-fit (t = 0.25) | pre | 1440 | -0.0151 [-0.0218, -0.0095] | 0 / 0 | 0 / 0 | Met |
| <=20% | Post-fit (t = 0.25) | checked | 1440 | -0.2571 [-0.3565, -0.1766] | 0 / 0 | 46 / 122 | Met |
| >20% | Primary (w = 1) | pre | 1440 | -0.1941 [-0.2812, -0.1208] | 2 / 4 | 0 / 0 | Met |
| >20% | Primary (w = 1) | checked | 1440 | -0.6452 [-0.8614, -0.4580] | 0 / 0 | 135 / 315 | Met |
| >20% | Post-fit (t = 0.25) | pre | 1440 | -0.1228 [-0.1465, -0.0999] | 1 / 4 | 0 / 0 | Met |
| >20% | Post-fit (t = 0.25) | checked | 1440 | -0.6009 [-0.7094, -0.4941] | 0 / 0 | 133 / 315 | Met |


Implausibility means uncapped mean absolute error across requested endpoints above 5. The severe endpoint flag uses the largest absolute endpoint error. For CRP the only requested endpoint is the 95th percentile. [Formal comparisons](gates.csv) · [Separate N comparisons](gates-by-n.csv.gz) · [Native and historical contrasts](paired-loss.csv.gz)

## Error and coverage


| Arm | Release | Returned | Fit failures | Implausible | All-set loss | Returned/scored loss |
| --- | --- | --- | --- | --- | --- | --- |
| Unchanged refineR | pre | 2880 | 0 | 4 | 0.3847 | 0.3847 |
| Unchanged refineR | checked | 2443 | 0 | 0 | 0.9989 | 0.2831 |
| Stage 2 | pre | 2880 | 0 | 4 | 0.3840 | 0.3840 |
| Stage 2 | checked | 2452 | 0 | 0 | 0.9850 | 0.2842 |
| Primary (w = 1) | pre | 2880 | 0 | 2 | 0.2748 | 0.2748 |
| Primary (w = 1) | checked | 2703 | 0 | 0 | 0.5390 | 0.2469 |
| Post-fit (t = 0.25) | pre | 2880 | 0 | 1 | 0.3158 | 0.3158 |
| Post-fit (t = 0.25) | checked | 2701 | 0 | 0 | 0.5699 | 0.2763 |
| Anchors only | pre | 2880 | 0 | 0 | 0.2899 | 0.2899 |
| Anchors only | checked | 2880 | 0 | 0 | 0.2899 | 0.2899 |


## Baseline Stage 2 fallback

Subgroup membership is fixed by the Stage 2 fit on that dataset. The weighted contribution is the within-subgroup difference multiplied by that subgroup’s share of the cohort. The fallback and non-fallback contributions sum to the pooled change from Stage 2.


| Stage 2 subgroup | Datasets | Arm | Release | Stage 2 loss | Arm loss | Change from Stage 2 [95% interval] | Contribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fallback | 377 | Primary (w = 1) | pre | 0.6428 | 0.3982 | -0.2447 [-0.3878, -0.0913] | -0.0320 |
| nonfallback | 2503 | Primary (w = 1) | pre | 0.3450 | 0.2562 | -0.0888 [-0.1176, -0.0644] | -0.0772 |
| fallback | 377 | Primary (w = 1) | checked | 1.7699 | 0.8636 | -0.9062 [-1.2429, -0.5272] | -0.1186 |
| nonfallback | 2503 | Primary (w = 1) | checked | 0.8668 | 0.4902 | -0.3767 [-0.4547, -0.3000] | -0.3274 |
| fallback | 377 | Post-fit (t = 0.25) | pre | 0.6428 | 0.5184 | -0.1244 [-0.1607, -0.0865] | -0.0163 |
| nonfallback | 2503 | Post-fit (t = 0.25) | pre | 0.3450 | 0.2853 | -0.0597 [-0.0710, -0.0504] | -0.0519 |
| fallback | 377 | Post-fit (t = 0.25) | checked | 1.7699 | 1.1404 | -0.6295 [-0.8375, -0.4151] | -0.0824 |
| nonfallback | 2503 | Post-fit (t = 0.25) | checked | 0.8668 | 0.4839 | -0.3829 [-0.4490, -0.3176] | -0.3328 |


[Parent subgroups by N and pathology](parent-contributions.csv.gz) · [Search branches and reasons](branches.csv.gz) · [Both updates available and common scored results](paired-loss.csv.gz)

## RIbench overlap and pathological fraction

RIbench assigns low, medium or high overlap separately to its left and right pathological components. These are the original specification labels, including on zero-pathology controls. The tables retain left, right and ordered pair labels. Pre-check entries below use native limits and all assigned datasets.


| Designed overlap | Level | Datasets | Stage 2 loss | Primary loss | Primary Δ [95% interval] | Post-fit loss | Post-fit Δ [95% interval] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| overlapPatholLeft | high | 960 | 0.4327 | 0.3054 | -0.1273 [-0.1768, -0.0865] | 0.3512 | -0.0815 [-0.0975, -0.0669] |
| overlapPatholLeft | low | 960 | 0.3434 | 0.2515 | -0.0920 [-0.1428, -0.0502] | 0.2889 | -0.0546 [-0.0692, -0.0424] |
| overlapPatholLeft | medium | 960 | 0.3759 | 0.2675 | -0.1084 [-0.1561, -0.0665] | 0.3073 | -0.0686 [-0.0840, -0.0543] |
| overlapPatholRight | high | 960 | 0.4089 | 0.3129 | -0.0960 [-0.1362, -0.0608] | 0.3282 | -0.0808 [-0.0936, -0.0684] |
| overlapPatholRight | low | 960 | 0.3508 | 0.2474 | -0.1034 [-0.1511, -0.0626] | 0.2960 | -0.0548 [-0.0685, -0.0426] |
| overlapPatholRight | medium | 960 | 0.3922 | 0.2641 | -0.1282 [-0.1849, -0.0787] | 0.3232 | -0.0691 [-0.0841, -0.0551] |



| Pathological fraction | Level | Datasets | Stage 2 loss | Primary loss | Primary Δ [95% interval] | Post-fit loss | Post-fit Δ [95% interval] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fraction | 0 | 360 | 0.1772 | 0.1446 | -0.0326 [-0.0467, -0.0216] | 0.1707 | -0.0065 [-0.0160, +0.0009] |
| fraction | 0.05 | 360 | 0.1774 | 0.1475 | -0.0299 [-0.0435, -0.0164] | 0.1655 | -0.0120 [-0.0195, -0.0049] |
| fraction | 0.1 | 360 | 0.1802 | 0.1591 | -0.0211 [-0.0297, -0.0131] | 0.1589 | -0.0213 [-0.0286, -0.0147] |
| fraction | 0.2 | 360 | 0.2379 | 0.2086 | -0.0293 [-0.0487, -0.0119] | 0.2075 | -0.0304 [-0.0384, -0.0227] |
| fraction | 0.3 | 360 | 0.3192 | 0.2596 | -0.0596 [-0.0909, -0.0333] | 0.2669 | -0.0523 [-0.0631, -0.0426] |
| fraction | 0.4 | 360 | 0.4560 | 0.3197 | -0.1363 [-0.2083, -0.0722] | 0.3644 | -0.0916 [-0.1126, -0.0732] |
| fraction | 0.5 | 360 | 0.6052 | 0.3945 | -0.2107 [-0.3280, -0.1219] | 0.4693 | -0.1360 [-0.1618, -0.1114] |
| fraction | 0.6 | 360 | 0.9188 | 0.5647 | -0.3541 [-0.4971, -0.2305] | 0.7231 | -0.1958 [-0.2390, -0.1530] |


[All pairwise overlaps and fractional strata](paired-loss.csv.gz) · [Official case labels](overlap.csv.gz)

## Same-dataset comparisons

Unchanged refineR, frozen Stage 2 and anchors-only used the same ordered inputs. The anchoredRI comparators are the archived Task E arm B and the improved anchoredRI baseline. Raw comparisons use their fitted intervals. Checked comparisons use the intervals they originally reported after their own safeguards. The archived C2 anchors-only reporting rule releases a successful fit. All pairing uses RIbench Index plus ordered routine and anchor hashes. The final two columns restrict both methods to cases where both returned scorable results.


| Arm | Release | Comparator | Matched | Arm returned | Comparator returned | Arm loss | Comparator loss | Arm − comparator [95% interval] | Common scored | Common Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primary (w = 1) | pre | Stage 2 | 2880 | 2880 | 2880 | 0.2748 | 0.3840 | -0.1092 [-0.1552, -0.0698] | 2880 | -0.1092 |
| Primary (w = 1) | pre | Anchors only | 2880 | 2880 | 2880 | 0.2748 | 0.2899 | -0.0151 [-0.0873, +0.0495] | 2880 | -0.0151 |
| Primary (w = 1) | pre | anchoredRI Arm B (Task E) | 2880 | 2880 | 2880 | 0.2748 | 0.2231 | +0.0516 [-0.0331, +0.1201] | 2880 | +0.0516 |
| Primary (w = 1) | pre | Improved anchoredRI baseline | 2880 | 2880 | 2880 | 0.2748 | 0.2886 | -0.0138 [-0.0705, +0.0493] | 2880 | -0.0138 |
| Primary (w = 1) | checked | Stage 2 | 2880 | 2703 | 2452 | 0.5390 | 0.9850 | -0.4460 [-0.5638, -0.3351] | 2452 | -0.0522 |
| Primary (w = 1) | checked | Anchors only | 2880 | 2703 | 2880 | 0.5390 | 0.2899 | +0.2491 [+0.1316, +0.3797] | 2703 | -0.0392 |
| Primary (w = 1) | checked | anchoredRI Arm B (Task E) | 2880 | 2703 | 2781 | 0.5390 | 0.3725 | +0.1666 [-0.0191, +0.3247] | 2629 | +0.0418 |
| Primary (w = 1) | checked | Improved anchoredRI baseline | 2880 | 2703 | 2406 | 0.5390 | 0.9793 | -0.4402 [-0.9769, -0.0035] | 2314 | +0.0575 |
| Post-fit (t = 0.25) | pre | Stage 2 | 2880 | 2880 | 2880 | 0.3158 | 0.3840 | -0.0682 [-0.0810, -0.0562] | 2880 | -0.0682 |
| Post-fit (t = 0.25) | pre | Anchors only | 2880 | 2880 | 2880 | 0.3158 | 0.2899 | +0.0259 [-0.0551, +0.1101] | 2880 | +0.0259 |
| Post-fit (t = 0.25) | pre | anchoredRI Arm B (Task E) | 2880 | 2880 | 2880 | 0.3158 | 0.2231 | +0.0926 [+0.0001, +0.1852] | 2880 | +0.0926 |
| Post-fit (t = 0.25) | pre | Improved anchoredRI baseline | 2880 | 2880 | 2880 | 0.3158 | 0.2886 | +0.0272 [-0.0466, +0.1156] | 2880 | +0.0272 |
| Post-fit (t = 0.25) | checked | Stage 2 | 2880 | 2701 | 2452 | 0.5699 | 0.9850 | -0.4152 [-0.4848, -0.3457] | 2452 | -0.0413 |
| Post-fit (t = 0.25) | checked | Anchors only | 2880 | 2701 | 2880 | 0.5699 | 0.2899 | +0.2800 [+0.1527, +0.4186] | 2701 | -0.0106 |
| Post-fit (t = 0.25) | checked | anchoredRI Arm B (Task E) | 2880 | 2701 | 2781 | 0.5699 | 0.3725 | +0.1974 [+0.0271, +0.3627] | 2617 | +0.0712 |
| Post-fit (t = 0.25) | checked | Improved anchoredRI baseline | 2880 | 2701 | 2406 | 0.5699 | 0.9793 | -0.4094 [-0.9183, +0.0378] | 2291 | +0.0836 |


## Gap to anchors-only

The gap closed is Stage 2 loss minus arm loss. The remaining gap is arm loss minus anchors-only loss. Both use the same datasets. On the large cohort the above-20% rows address the prespecified target of 720 datasets.


| Pathology | Arm | Release | Assigned | Stage 2 | Arm | Anchors-only | Gap closed | Remaining gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <=20% | Primary (w = 1) | pre | 1440 | 0.1932 | 0.1650 | 0.2918 | +0.0282 | -0.1269 |
| <=20% | Primary (w = 1) | checked | 1440 | 0.5796 | 0.3010 | 0.2918 | +0.2786 | +0.0092 |
| <=20% | Post-fit (t = 0.25) | pre | 1440 | 0.1932 | 0.1757 | 0.2918 | +0.0175 | -0.1161 |
| <=20% | Post-fit (t = 0.25) | checked | 1440 | 0.5796 | 0.3183 | 0.2918 | +0.2613 | +0.0265 |
| >20% | Primary (w = 1) | pre | 1440 | 0.5748 | 0.3846 | 0.2880 | +0.1902 | +0.0966 |
| >20% | Primary (w = 1) | checked | 1440 | 1.3905 | 0.7771 | 0.2880 | +0.6134 | +0.4891 |
| >20% | Post-fit (t = 0.25) | pre | 1440 | 0.5748 | 0.4559 | 0.2880 | +0.1189 | +0.1679 |
| >20% | Post-fit (t = 0.25) | checked | 1440 | 1.3905 | 0.8214 | 0.2880 | +0.5691 | +0.5334 |


[Gap estimates, intervals and subgroups](gap.csv.gz) · [Comparator sources](../../stage2/ribench/comparators/README.md)

## Guidance-panel checks

RIbench has one independent panel of 40 screened anchors per dataset. Both PIT seeds use the same rounded panel. The primary seed determines release. E is the largest absolute error of the requested endpoints before checking.


| Arm | PIT seed | Declined / evaluable | E > 1 caught | E > 5 caught | E < 0.25 declined |
| --- | --- | --- | --- | --- | --- |
| Unchanged refineR | primary | 437 / 2880 | 216 / 411 | 17 / 18 | 19 / 1180 |
| Unchanged refineR | alternate | 436 / 2880 | 218 / 411 | 17 / 18 | 17 / 1180 |
| Stage 2 | primary | 428 / 2880 | 216 / 414 | 16 / 17 | 16 / 1170 |
| Stage 2 | alternate | 425 / 2880 | 217 / 414 | 16 / 17 | 14 / 1170 |
| Primary (w = 1) | primary | 177 / 2880 | 60 / 184 | 4 / 4 | 11 / 1314 |
| Primary (w = 1) | alternate | 177 / 2880 | 62 / 184 | 4 / 4 | 8 / 1314 |
| Post-fit (t = 0.25) | primary | 179 / 2880 | 83 / 296 | 5 / 5 | 4 / 1330 |
| Post-fit (t = 0.25) | alternate | 184 / 2880 | 83 / 296 | 5 / 5 | 3 / 1330 |



| Arm | PIT-seed reversals | Evaluable under both | Share |
| --- | --- | --- | --- |
| Unchanged refineR | 33 | 2880 | 0.0115 |
| Stage 2 | 27 | 2880 | 0.0094 |
| Primary (w = 1) | 14 | 2880 | 0.0049 |
| Post-fit (t = 0.25) | 13 | 2880 | 0.0045 |


## Audit and Task G export

The technical audit covered all 2,880 primary datasets. The verified repeated set contained 288 datasets. The maximum separate-host endpoint difference was 0 of reference width, and the maximum PIT probability difference was 0. Descriptive 95% intervals use 2,000 matched bootstrap resamples of (analyte, scenario) clusters with PCG64 seed 37000000. Intervals require at least two informative clusters.

[Technical audit](evidence/audit.json) · [Fit records](evidence/fits.csv.gz) · [Decisions](evidence/checks.csv.gz) · [Task G guide](TASK-G.md) · [Error and coverage](accuracy.csv.gz) · [Endpoint errors](endpoints.csv.gz) · [Healthy curve error by elected basin](curve.csv.gz) · [Capture and good-result loss](rates.csv.gz) · [PIT-seed reversals](seed-changes.csv.gz)
