# Cancelled Stage 3 development run

The initial development run was cancelled at the user's request before the methods amendment. Its results are excluded from weight selection. The source commit was `dc82857d600de43080f499873f1639658b456a3f`. [GitHub Actions run](https://github.com/amromeo/anchorRefine/actions/runs/45409118727) · [Source](https://github.com/amromeo/anchorRefine/commit/dc82857d600de43080f499873f1639658b456a3f)

The eligibility job succeeded. Twenty of the 96 fitting jobs started. All 20 uploaded a partial original ZIP when cancelled. The remaining 76 fitting jobs and the aggregate job received no runner. The [job archive](actions-logs.zip) contains the 21 available job logs and all 98 job metadata records.

The 60 archived session logs record 287 completed primary cases, 273 same-host repeat cases and 283 separate-host cases. They identify 567 distinct development dataset IDs completed in at least one role and 32 completed in all three. Every running shard was interrupted before its final results write. The preserved evidence consists of progress messages, session identities, source hashes and toolchain information. GitHub Actions produced no fit, score, check or weight-selection table for this cancelled run. [Per-session progress](progress.csv) · [Logged case IDs](completed-cases.csv)

A separate local workspace replay completed one of the original-rule development cases on R 4.5.0. Its 14 fit rows, checks, diagnostics and runtime provenance are preserved independently and excluded from selection. [Local R 4.5.0 technical replay](local-technical-replay/README.md)
