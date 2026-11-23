#!/usr/bin/env bash
set -euo pipefail
sha256sum --quiet --check sources/SHA256SUMS
sha256sum --quiet --check stage2/SHA256SUMS
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
if [[ $# -eq 1 ]]; then
    manifest="$(pwd)/stage0/frozen/installed-files.sha256"
    (cd "$1" && sha256sum --quiet --check "$manifest")
fi
