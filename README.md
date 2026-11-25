# anchorRefine

anchorRefine fits a healthy reference distribution to routine laboratory measurements. Stage 0 provides refineR's original fit and reference limits. Stage 1 checks that fit against 40 independently screened healthy patients. A kept fit retains its original reference limits.

Stage 0 passed on all 2,880 RIbench datasets with N ≤ 5,000. The pass-through matched CRAN exactly on the same machine in both repetitions. All 5,472 historical endpoints met the C2 tolerance. [Stage 0 report](results/stage0-45241996440/REPORT.md) · [Readback and interpretation](results/stage0-45241996440/READBACK.md)

Stage 1 evaluated 4,320 archived refineR fits. With historical C2 limits, the anchor check caught 34 of 42 severe errors at N ≤ 5,000 and both severe errors at N = 50,000. It declined 1.6% and 1.8% of the fits with every requested endpoint within 0.25 z units of truth. [Stage 1 results and data](results/stage1-45276858699/REPORT.md)

Stage 2 development selected K = 24. The full guided fit improved on refineR above 20% pathology at both sample sizes and missed the lower-pathology margin at N = 50,000. [Development report](results/stage2-development-45283676579/REVIEW.md)

The frozen Stage 2 candidate uses anchors for peak choice only, with K = 24 and the existing fallback. On development datasets where the peaks differed, the full search had lower error than peak choice alone at N = 50,000 and higher error at N = 1,500. The decision rule required lower error at both sizes. The candidate fits an interval with `fit_guided(x, anchors, increment, seed, K = 24L, arm = "peak")`. [Selection and reason](PROTOCOL.md#stage-2-candidate-decision-after-the-development-ablations) · [Development ablations](results/stage2-ablations-45293475762/REVIEW.md)

The selected rule reproduced all 1,440 development fits and 5,760 anchor checks. On 2,880 fresh simulations it met the prespecified criteria at both sample sizes and both pathology levels, before and after checking. The largest gains occurred with separated disease on either side of the healthy peak. [Development reproduction](results/stage2-selected-development-45299765250/REPORT.md) · [Confirmation results](results/stage2-confirmation-45303419260/REVIEW.md)

On the 4,320 RIbench datasets, the peak-choice-only candidate met all four prespecified native-limit comparisons before the anchor check. Above 20% pathology, mean capped error fell by 0.0039 at N ≤ 5,000 and 0.0044 at N = 50,000. The checked release met three of four comparisons. In the small, lower-pathology stratum it withheld 123 intervals and checked refineR withheld 122. [RIbench results](results/stage2-ribench/REVIEW.md) · [Peak choices and fallbacks by analyte, N and pathological fraction](results/stage2-ribench/peak-choice-and-fallback.csv)

Stage 3 synthetic development selected w = 1 for the anchor-weighted search and t = 0.25 for the post-fit comparator. Both passed all prespecified gates on 7,488 independent confirmation datasets. At N ≤ 5,000, Stage 2 fallback datasets accounted for 61.1% of the primary arm’s improvement over Stage 2. On high-pathology shoulder and overlap confirmation datasets at N = 50,000, mean capped errors were 0.2883 for Stage 2, 0.2858 for the primary arm, 0.2100 for the comparator and 0.2563 for anchors-only. [Development and influence](results/stage3-development/REVIEW.md) · [Confirmation results](results/stage3-confirmation/REVIEW.md) · [Confirmation Task G data](results/stage3-confirmation-45463873162/TASK-G.md)

On 4,320 RIbench datasets, both frozen Stage 3 arms passed every prespecified comparison with refineR before and after the anchor check. On the 720 datasets at N = 50,000 with more than 20% pathology, pre-check mean capped error was 0.3610 for Stage 2, 0.3070 for anchors-only, 0.3014 for the weighted search and 0.2904 for the post-fit blend. With declines scored as 5, anchors-only had the lowest checked loss in this stratum. All 432 sampled datasets reproduced exactly on the same and separate hosts. [RIbench results, comparisons and audit](results/stage3-ribench/REVIEW.md) · [Small-cohort Task G data](results/stage3-ribench-small-45530368829/TASK-G.md) · [Large-cohort Task G data](results/stage3-ribench-large-45541935930/TASK-G.md)

anchorRefine is derived from refineR 2.0.0. It is an independent project and is not endorsed by the refineR authors. Matthias Beck, Tatjana Ammer, Christopher M Rank and Andre Schuetzenmeister wrote refineR. This package is licensed under GPL-3. The upstream source and notices are in [vendor/refineR](vendor/refineR).

To install from this checkout, run the following from the repository root in R. The vendored package requires ash, future and future.apply.

```r
install.packages(c("ash", "future", "future.apply"))
install.packages("vendor/refineR", repos = NULL, type = "source")
install.packages(".", repos = NULL, type = "source")

fit <- anchorRefine::findRI(refineR::testcase1, mode = "passthrough")
anchorRefine::getRI(fit)
```

Read the [protocol](PROTOCOL.md), [C2 source review](docs/SOURCE_REVIEW.md) and [Stage 0 run specification](docs/stage0/DESIGN.md) for the study design and the two endpoint calculations.

For a rounded panel, supply the 40 observations in their draw order, the number of recorded decimal places, and a reproducible randomization seed.

```r
decision <- anchorRefine::check_anchors(fit, anchors, decimals = 1L,
                                        seed = 38000000L + Index)
decision[c("status", "p", "reason")]
```

The [Stage 1 workflow](stage1/README.md) describes the inputs and audit files.
