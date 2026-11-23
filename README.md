# anchorRefine

anchorRefine fits a healthy reference distribution to routine laboratory measurements. Stage 0 provides refineR's original fit and reference limits. The study protocol describes how later stages will use independently screened healthy patients.

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
