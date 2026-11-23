# Stage 0 readback

The 20 runner jobs completed in 56 minutes 33 seconds of wall time from dispatch to completion. Each of the four fits for a given Index ran on the same host. The run included 11,520 fits across 2,880 distinct datasets.

A second R 4.5.0 installation read the stored R objects and independently checked the decisions. Base R object comparison with bitwise numeric and missing-value checks confirmed all 11,520 same-machine flags. Recalculation from the full-precision C2 RDS confirmed all 5,472 historical endpoint flags. To repeat this check from the repository root, run the following command.

```sh
Rscript --vanilla results/stage0-45241996440/readback.R results/stage0-45241996440
```

All 1,548 informational messages were the upstream small-sample notice. In the source files, 387 nominal N = 1,000 datasets contained 998 or 999 measurements. Each triggered the same notice in all four fits. Both sizes and all ten analytes have complete coverage.

The native and historical extraction formulas differed by more than 0.1% of archived width at 150 endpoints across 111 datasets. For example, the same GGT model at Index 3120 gave a native lower limit of 2.806 U/L and a historical lower limit of zero. The difference was 7.30% of the archived width. C2 and the new pass-through run both returned zero using the historical formula.

The 2,880 archived model files also matched the SHA-256 digests of the corresponding files from the original fitting run. All 60 original session files were identical and recorded Ubuntu 26.04.1 with OpenBLAS 0.3.32. Stage 0 used Ubuntu 24.04.2 with OpenBLAS 0.3.26. Both used R 4.5.0. [Original fitting run](https://github.com/amromeo/amromeo.github.io/actions/runs/45091086783) · [Archived session](archived-fit-session.txt) · [Provenance](archived-fit-origin.json)

The raw shard ZIPs and all report tables are stored in this directory. Verify them by running `sha256sum --check SHA256SUMS` from here. The pre-run checksums and decision rules are recorded at commit `8e8c7c4a249af8052b9a794f9480ef0188121e74`.
