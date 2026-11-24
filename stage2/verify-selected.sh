#!/usr/bin/env bash
set -euo pipefail

# The selected-rule lock covers the current protocol. The earlier lock keeps
# the protocol hash from the original development run at commit 1c914bc.
sha256sum --quiet --check stage2/selected-sources.sha256
sha256sum --quiet --check sources/SHA256SUMS
awk '$2 != "PROTOCOL.md"' stage2/SHA256SUMS | sha256sum --quiet --check -
sha256sum --quiet --check stage2/ablation-sources.sha256
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
(cd results/stage2-development-45283676579 && sha256sum --quiet --check SHA256SUMS)
(cd results/stage2-ablations-45293475762 && sha256sum --quiet --check SHA256SUMS)
if [[ $# -eq 1 ]]; then
    installed_manifest="$(pwd)/stage0/frozen/installed-files.sha256"
    (cd "$1" && sha256sum --quiet --check "$installed_manifest")
fi
