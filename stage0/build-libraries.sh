#!/usr/bin/env bash
set -euo pipefail
# Run at the repository root. The destination is outside the source tree.
destination=$(realpath -m "${1:?usage: build-libraries.sh DIRECTORY}")
mkdir -p "$destination"/{sources,deps,cran,vendored}
export MAKEFLAGS=-j2
export R_LIBS_USER="$destination/deps"
Rscript --vanilla -e 'stopifnot(getRversion() == "4.5.0")'
while IFS=$'\t' read -r package version digest url; do
    name="${package}_${version}.tar.gz"
    file="$destination/sources/$name"
    if [[ ! -f "$file" ]]; then
        curl -fsSL --retry 3 "$url" -o "$file" ||
            curl -fsSL --retry 3 "https://cran.r-project.org/src/contrib/Archive/$package/$name" -o "$file"
    fi
    echo "$digest  $file" | sha256sum --check --status
    R CMD INSTALL --library="$destination/deps" "$file"
done < <(tail -n +2 stage0/dependencies.tsv)
R CMD INSTALL --library="$destination/deps" vendor/RIbench_1.0.2.tar.gz
R CMD INSTALL --library="$destination/cran" vendor/refineR_2.0.0.tar.gz
R CMD INSTALL --library="$destination/vendored" vendor/refineR
R_LIBS_USER="$destination/vendored:$destination/deps" R CMD INSTALL --library="$destination/vendored" .
