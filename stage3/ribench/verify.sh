#!/usr/bin/env bash
set -euo pipefail

sha256sum --quiet --check stage3/ribench/SHA256SUMS
# Protocol changes apply only to this benchmark. The numerical methods,
# original inputs, checks and libraries match their accepted upstream freezes.
printf '%s  %s\n' cb5e6896095b7ef51f5d8490b70c63af63b14045b623b0332b4f07bc02186576 stage3/confirmation-sources.sha256 \
    709909e11dcde40ab95fefcf00d1365d8ba03902044f9ad112699d423142f9ae stage2/ribench/SHA256SUMS \
    528b3fc57379c46eec4ac80b246ee3afe9e470bb642fa514e0b3ca5c43d499ff results/stage3-confirmation-45463873162/receipt.json |
    sha256sum --quiet --check -
for manifest in stage3/confirmation-sources.sha256 stage2/ribench/SHA256SUMS stage2/SHA256SUMS stage2/selected-sources.sha256; do
    awk '$2 != "PROTOCOL.md"' "$manifest" | sha256sum --quiet --check -
done
python3 stage3/verify-confirmation-weights.py
sha256sum --quiet --check sources/SHA256SUMS
sha256sum --quiet --check stage2/ablation-sources.sha256
(cd stage0/frozen && sha256sum --quiet --check bundle.sha256)
(cd stage1/large && sha256sum --quiet --check SHA256SUMS)
(cd results/stage0-45241996440 && sha256sum --quiet --check SHA256SUMS)
(cd results/stage1-45276858699 && sha256sum --quiet --check SHA256SUMS)
if [[ $# -eq 1 ]]; then
    installed_manifest="$(pwd)/stage0/frozen/installed-files.sha256"
    (cd "$1" && sha256sum --quiet --check "$installed_manifest")
fi
