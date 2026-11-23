# RIbench, small-N first

Protocol: PROTOCOL.md. The workflow runs 2,880 datasets with N=1,000 or 5,000. It has no job for N=50,000 or 500,000.

From anchoredRI/, install the pinned dependencies with Rscript tools/ribench/install.R. Generate data with Rscript tools/ribench/generate.R /absolute/workingDir. Run Rscript tools/ribench/probe.R after copying one generated Hb file into tools/ribench/probe/Data/Hb/ to avoid repeating the full generator sequence. The probe must save a data.frame named fit with Percentile, PointEst, Runtime columns.

Run Rscript tools/ribench/run.R /absolute/workingDir <shard> 60 for shards 1 through 60. Each shard has 48 datasets. Each shard must use its own working directory because RIbench uses shared progress filenames. Merge the Results/ subdirectories and the shard CSV/TXT files afterward. Rscript tools/ribench/score.R /absolute/mergedDir scores the completed subset and exports per-analyte performance, including separate lambda=0.432 CSVs.

The GitHub Actions workflow handles generation, isolated shards, artifact merging and scoring. Artifacts retain native Rdata results, diagnostics, per-fit timings, shard wall times and versions. Timings should distinguish generation time, fitting time summed across methods, and overall elapsed time including queueing/installation. Subset scores cannot be described as the full RIbench published score.
