# Interrupted amended Stage 3 influence check

Run [45411770454](https://github.com/amromeo/anchorRefine/actions/runs/45411770454) was cancelled after a local replay exposed a misspelled function name in the first-pass verification on Stage 2 fallback cases. This was the first influence attempt with the amended fallback method. [Source commit](https://github.com/amromeo/anchorRefine/commit/869d5e84e0834c389fde51e43f9ecf614ac84c6c)

The source and eligibility job succeeded. Twenty fitting workers received runners, and all twenty skipped the paired-fit step after cancellation. GitHub lists 26 jobs and 0 uploaded artifacts. The archive contains original metadata for all jobs and 21 available runner logs. The cancelled attempt produced no fixture-level fit table or aggregate influence report and contributed no results to weight selection. [GitHub metadata and logs](actions-logs.zip)

The local R 4.5.0 replay that prompted cancellation stopped on fixture 1 during the positive-weight verification. [Original local log](local-fixture-1.log.gz)
