# anchorRefine

anchorRefine fits a healthy reference distribution to routine laboratory measurements. Stage 0 provides refineR's original fit and reference limits. Stage 1 checks that fit against 40 independently screened healthy patients. A kept fit retains its original reference limits.

Stage 0 passed on all 2,880 RIbench datasets with N ≤ 5,000. The pass-through matched CRAN exactly on the same machine in both repetitions. All 5,472 historical endpoints met the C2 tolerance. [Stage 0 report](results/stage0-45241996440/REPORT.md) · [Readback and interpretation](results/stage0-45241996440/READBACK.md)

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
