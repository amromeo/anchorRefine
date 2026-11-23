# Stage 1 anchor check

[PROTOCOL.md](../PROTOCOL.md) fixes the decision rules. The historical RIbench extraction is primary. Native refineR limits are secondary. Both use the same test of the four fitted parameters against 40 rounded independent anchors. A kept estimate retains the original limit.

The [small C2 archive](../archive/c2/) and [50,000-sample C2 archive](large/README.md) contain the refineR fits and the original anchors-only and anchoredRI results. Both cohorts have complete archived fits. For the improved Task E fitter, the [frozen export](task-e/manifest.json) covers the entire small cohort and 144 of 1,440 large datasets. Only the complete cohort enters the Task E comparison. The raw improved-fitter estimates and estimates released by its own safeguard have separate method labels.

The [Actions workflow](../.github/workflows/stage1.yml) checks SHA-256 manifests before and after execution. It runs the four null simulations first, then evaluates and audits the small cohort. After the small report passes, it regenerates the large routine vectors to verify their archived identities, then evaluates and audits the large cohort. Each cohort uses two isolated R processes on one host and a third process on a distinct hosted runner. The image and installed libraries are pinned to Stage 0.

Each cohort's primary run produces the following files.

| File | Contents |
|---|---|
| checks.csv | Per-Index parameters, input hashes, decisions and p-values for both PIT seeds, archive reconstruction differences and diagnostics |
| estimates.csv | Per-endpoint truth, estimate and signed RIbench z for both extractions and all available comparators, plus the refineR values released by each seed |
| results.rds | Full-precision R objects for the exact repeat comparison |
| host.json, r-pid.txt | Runner identity and isolated R process ID |
| audit/ | Same-host and separate-host checks, with recorded differences |
| analysis/ | Report and compressed tables of rates, accuracy, endpoint results, boundary counts and paired loss differences |

To reproduce a report from a downloaded primary run, install the pinned NumPy version and run `python stage1/report.py --small PATH_TO_SMALL_PRIMARY --large PATH_TO_LARGE_PRIMARY --out OUTPUT`. Each input path contains checks.csv and estimates.csv. An individual cohort can also be reported alone.
