#!/usr/bin/env bash
set -euo pipefail

# The selected-source verifier covers the upstream tarball, original search
# code, Stage 1 checker, fitter selection and the pinned installed libraries.
sha256sum --quiet --check stage2/ribench/SHA256SUMS
bash stage2/verify-selected.sh "$@"
(cd stage1/large && sha256sum --quiet --check SHA256SUMS)
(cd results/stage0-45241996440 && sha256sum --quiet --check SHA256SUMS)
(cd results/stage1-45276858699 && sha256sum --quiet --check SHA256SUMS)
