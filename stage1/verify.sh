#!/usr/bin/env bash
set -euo pipefail
sha256sum --quiet --check sources/SHA256SUMS
sha256sum --quiet --check stage1/SHA256SUMS
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
if [[ $# == 1 ]]; then
    (cd "$1" && sha256sum --quiet --check "$GITHUB_WORKSPACE/stage0/frozen/installed-files.sha256")
fi
