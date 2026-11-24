#!/usr/bin/env bash
set -euo pipefail

sha256sum --quiet --check stage3/SHA256SUMS
sha256sum --quiet --check sources/SHA256SUMS
# The current protocol is in the Stage 3 manifest. The historical manifests
# retain the protocol as it stood at the Stage 2 freezes.
for manifest in stage2/SHA256SUMS stage2/selected-sources.sha256; do
    awk '$2 != "PROTOCOL.md"' "$manifest" | sha256sum --quiet --check -
done
sha256sum --quiet --check stage2/ablation-sources.sha256
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
if [[ $# -eq 1 ]]; then
    installed_manifest="$(pwd)/stage0/frozen/installed-files.sha256"
    (cd "$1" && sha256sum --quiet --check "$installed_manifest")
fi
