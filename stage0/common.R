# Arguments and installed libraries are explicit in each fresh Rscript process.
use_libraries <- function(bundle, engine) {
    lib <- normalizePath(file.path(bundle, engine))
    deps <- normalizePath(file.path(bundle, "deps"))
    .libPaths(c(lib, deps, .Library), include.site = FALSE)
    stopifnot(getRversion() == "4.5.0", packageVersion("refineR") == "2.0.0",
              normalizePath(find.package("refineR")) == file.path(lib, "refineR"))
    if (engine == "vendored") {
        stopifnot(normalizePath(find.package("anchorRefine")) == file.path(lib, "anchorRefine"))
    }
    data.table::setDTthreads(1)
    RNGkind("Mersenne-Twister", "Inversion", "Rejection")
}

percentiles <- function(analyte) {
    if (analyte == "CRP") 0.95 else c(0.025, 0.975)
}

shard_path <- function(bundle, shard) {
    file.path(bundle, "inputs", sprintf("shard-%02d.rds", as.integer(shard)))
}

write_table <- function(rows, path) {
    # CSV writers may print fewer than 17 significant decimal digits.
    # Preserve round-trip precision for every double exported for review.
    for (field in names(rows)) {
        x <- rows[[field]]
        if (is.double(x)) {
            rows[[field]] <- ifelse(is.na(x), NA_character_, sprintf("%.17g", x))
        }
    }
    write.csv(rows, path, na = "", row.names = FALSE)
}
