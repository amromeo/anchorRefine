#!/usr/bin/env bash
set -euo pipefail

sha256sum --quiet --check stage3/confirmation-sources.sha256

# All original fitting methods, helpers and packages must match the accepted
# development freeze. The confirmation manifest covers its new design, orchestration,
# audit, protocol and report, and each historical source manifest remains immutable.
printf '%s  %s\n' 5db4755face4cb67db6e4ac35cd33c859859fbb79cbd4f4d833263a0ee5a8251 stage3/SHA256SUMS | sha256sum --quiet --check -

awk '$2 != "PROTOCOL.md" && $2 !~ /^stage3\/(audit\.py|design\.R|report\.py|run\.R)$/' stage3/SHA256SUMS | sha256sum --quiet --check -
sha256sum --quiet --check sources/SHA256SUMS
for manifest in stage2/SHA256SUMS stage2/selected-sources.sha256; do
    awk '$2 != "PROTOCOL.md"' "$manifest" | sha256sum --quiet --check -
done
sha256sum --quiet --check stage2/ablation-sources.sha256
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
if [[ $# -eq 1 ]]; then
    installed_manifest="$(pwd)/stage0/frozen/installed-files.sha256"
    (cd "$1" && sha256sum --quiet --check "$installed_manifest")
fi
