# Stage 0 reproduction report

**Passed.** The native same-machine comparison and its repeats agreed on 2,880 of 2,880 datasets. The C2 historical audit passed on 2,880 of 2,880 datasets.

Each dataset underwent four fits (CRAN and pass-through, twice), for 11,520 fits. Each group of four ran in fresh R sessions on the same host. The benchmark used 20 runner jobs. Equality covers the complete fitted object, native and historical interval data frames, and captured conditions. Elapsed time and host metadata were recorded separately.

| Routine N | Planned | Completed | Missing | All four exact comparisons passed | C2 audit passed |
|---:|---:|---:|---:|---:|---:|
| 1,000 | 1,440 | 1,440 | 0 | 1,440 | 1,440 |
| 5,000 | 1,440 | 1,440 | 0 | 1,440 | 1,440 |

Fit failures in the first pass-through run: 0 datasets. Datasets with unavailable native point limits: 0. All four runs together recorded 0 warnings and 0 errors. The log also retains 1,548 messages.

The audit compared 5,472 endpoints with C2. The archived limit came from the full-precision RIbench performance RDS. Both historical calculations used RIbench 1.0.2 with truncNormal = FALSE. The tolerance was 0.1% of archived interval width per endpoint. The 288 CRP datasets each contributed their 95th percentile and used the archived upper limit as width.

| Endpoint | Audited | Within tolerance including C2 reconstruction | Largest absolute difference / width |
|---|---:|---:|---:|
| Lower | 2,592 | 2,592 | 9.13548e-12% |
| Upper | 2,880 | 2,880 | 7.6269e-12% |

Maximum observed difference: 9.13548e-12% of archived width (Index 130, Hb, lower). 4,758 historical endpoint differences were zero.

Re-extracting limits from the archived C2 fits gave a maximum discrepancy of 0% of archived width from the saved C2 endpoints.

On the same new fit, native refineR and the historical extraction differed by more than 0.1% of archived width at 150 of 5,472 comparable endpoints. The maximum was 7.30059%. The native extractor corrects for Box–Cox support. C2 used untruncated normal quantiles.

The runner CPU models were AMD EPYC 7763 64-Core Processor, AMD EPYC 9V45 96-Core Processor, AMD EPYC 9V74 80-Core Processor, INTEL(R) XEON(R) PLATINUM 8573C, Intel(R) Xeon(R) 6973P-C, Intel(R) Xeon(R) 6975P-C. The new environment and the archived C2 session both used R 4.5.0. The archived session file identifies the C2 environment. The C2 workflow imported its refineR fits from the preceding small-N run.

| Environment | Platform and numerical libraries |
|---|---|
| Stage 0 | Platform: x86_64-pc-linux-gnu · Running under: Ubuntu 24.04.2 LTS · BLAS:   /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3 · LAPACK: /usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.26.so;  LAPACK version 3.12.0 |
| Archived C2 session | Platform: x86_64-pc-linux-gnu · Running under: Ubuntu 26.04.1 LTS · BLAS:   /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3 · LAPACK: /usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.32.so;  LAPACK version 3.12.0 |

The fit workflow ran at commit `8e8c7c4a249af8052b9a794f9480ef0188121e74`. All 2,880 routine and anchor hashes passed before fitting. Each shard verified its sources, libraries and inputs before and after fitting. [Workflow run](https://github.com/amromeo/anchorRefine/actions/runs/45241996440) · [Input and build freeze](../../stage0/frozen/) · [Frozen rules](../../docs/stage0/DESIGN.md)

[Same-machine comparisons](same-machine.csv.gz) · [C2 endpoint comparisons](historical-audit.csv.gz) · [Parameter changes and timings](parameter-differences.csv.gz) · [Warnings and errors](conditions.csv.gz) · [Full R objects, logs and runner records](shards/)

The study stops here for review before Stage 1.
