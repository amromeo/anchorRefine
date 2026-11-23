#!/usr/bin/env bash
set -euo pipefail
bash stage2/verify-freeze.sh "$@"
sha256sum --quiet --check stage2/ablation-sources.sha256
(cd results/stage2-development-45283676579 && sha256sum --quiet --check SHA256SUMS)
