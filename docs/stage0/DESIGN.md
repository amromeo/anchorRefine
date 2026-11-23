# Stage 0 run specification

The approved endpoint amendment is recorded in commit 6456011. The benchmark covers every C2 Index with N ≤ 5,000, including CRP. The input inventory is in archive/c2/testsets.csv. No new fit outcomes were available when these rules were written.

## Build and input check

Build reference refineR 2.0.0 from the verified CRAN tarball. Install a second copy in a different R library from the extracted upstream source in vendor/refineR, then install anchorRefine against that copy. The public Stage 0 entry points are anchorRefine::findRI (passthrough mode) and anchorRefine::getRI. The fitting code, defaults and returned fit objects come from the vendored installation. The package requires refineR version 2.0.0.

Use Linux amd64, R 4.5.0 and the Rocker image identified in the preparation workflow. Pin additional dependency sources in stage0/dependencies.tsv and compare their SHA-256 digests before installation. Record the build commit, session, compiled file hashes and overall bundle hash. Commit that freeze and the benchmark runner before any fit. Check source hashes, bundle identity and installed file hashes at both ends of each shard.

Read the routine CSV files through the C2 data.table reader. Require RIbench's R-serialized MD5 for every routine vector, the archived SHA-256 for every independent 40-anchor panel, and the member SHA-256 for every archived R fit. Verify the model class, parameters and Index against the full-precision historical RDS. Order all sets by numeric Index and distribute round-robin across 20 shards. For every Index, run both engines and both repetitions on the same physical runner. Preserve all rows when an algorithm returns an error.

## Fitting and comparisons

Each shard starts four fresh Rscript sessions, two per repetition. They receive the same ordered datasets and use separate reference and vendored library paths plus a shared frozen dependency library. Use one numerical thread, C.UTF-8, UTC and sequential future evaluation in each R process. Reset R's Mersenne-Twister / Inversion / Rejection RNG to seed 123 immediately before each fit. The upstream findRI call receives only the data vector, as in C2. Its defaults are BoxCox, no bootstrap, seed 123. Only the routine vector enters the fit.

For all requested percentiles save the entire raw fit, the native getRI return including its default uncertainty margins, and RIbench's historical getRI(truncNormal = FALSE) output. Compare serialized XDR bytes (version 2) of the complete returns, warnings, messages and status in all four pairings: CRAN versus pass-through in each repetition, and repeat 1 versus repeat 2 for each engine. No returned fit or limit field is excluded. Seconds elapsed, process identifiers, library paths and host provenance are measured outside the returns.

For the independent C2 audit, use the full-precision archived performance RDS as the historical endpoint reference. Check reconstruction from C2's saved parameters separately, using the same endpoint tolerance. Compare the new pass-through historical limits to the saved reference. The tolerance is inclusive: 0.001 times the archived width at each endpoint. For CRP use the 95th percentile and width from zero. For the other nine analytes use the 2.5th and 97.5th percentiles and their difference. Record absolute and width-normalized differences, fit status, model parameter deltas, and the native-versus-historical difference on the same new fit. A mismatch, nonpositive width, invalid result, incomplete cohort or missing audit fails its comparison. No averaging over endpoints or substitution of a new reference.

An exact reproduction claim requires 2,880/2,880 passing same-machine comparisons and repeat checks. A Stage 0 pass also requires 2,880/2,880 passing cross-machine audits, complete input checks and an intact freeze. Review every exception by Index. Stop after the Stage 0 report for the user's decision.

## Frozen execution

Preparation run [45241449225](https://github.com/amromeo/anchorRefine/actions/runs/45241449225) built the two installations and verified all 2,880 routine vectors, independent anchor hashes and archived models. Its binaries and verified case files are preserved in stage0/frozen/bundle.tar.gz. Both paths use the same dependencies. The workflow verifies the bundle, its individual files and the source manifests before and after fitting. The two earlier preparation attempts stopped before any fit: the image lacked the curl command, then the version check encountered CRAN's hyphenated version notation. The successful build uses the preserved dependency tarballs and checks the exact Version field.

Start the committed Stage 0 workflow with `gh workflow run stage0.yml -R amromeo/anchorRefine --ref main`. Each shard invokes stage0/worker.R with its bundle path, engine, repetition, shard and output directory. It then invokes stage0/audit.R. The reporter verifies artifact and result file hashes, cohort membership and all four comparison pairs per Index before it summarizes the study.
