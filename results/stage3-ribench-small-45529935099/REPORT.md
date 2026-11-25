# Interrupted small-cohort RIbench environment check

The Ubuntu source-validation job passed. During worker startup, 46 jobs reached a validation command that called Python in the frozen R container. The container had no Python executable. These workers stopped during library and source verification, before running any fits. The remaining jobs were cancelled. The run uploaded zero artifacts and produced no cohort estimates or audit disposition. [Run 45529935099](https://github.com/amromeo/anchorRefine/actions/runs/45529935099) · [Frozen source](https://github.com/amromeo/anchorRefine/commit/a15ec4facdbf2d32462998390ca879aeeed0c137)

The archive contains metadata for all 50 jobs and 49 available job logs. [Original metadata and logs](actions-logs.zip)
