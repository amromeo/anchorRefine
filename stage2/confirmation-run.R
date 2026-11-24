# Run one shard of the frozen 2,880-case confirmation study.
# Rscript --vanilla stage2/confirmation-run.R BUNDLE SHARD N_SHARDS OUT
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 4L)
source("stage0/common.R")
use_libraries(args[1L], "vendored")
stopifnot(packageVersion("RIbench") == "1.0.2")
future::plan(future::sequential)
source("R/anchor-check.R")
source("R/stage2-peaks.R")
source("R/stage2-grid.R")
source("R/stage2-search.R")
source("R/stage2-selected.R")
source("stage2/generator.R")
source("stage2/confirmation-design.R")
source("stage2/confirmation-generator.R")
stopifnot(identical(stage2_selected_rule, "peak"))

shard <- as.integer(args[2L])
n_shards <- as.integer(args[3L])
out <- args[4L]
stopifnot(1L <= shard, shard <= n_shards, n_shards <= 2880L)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

planned <- stage2_confirmation_design()
design <- read.csv("stage2/confirmation-design.csv", stringsAsFactors = FALSE,
                   colClasses = vapply(planned, typeof, character(1)))
stopifnot(identical(names(design), names(planned)), identical(design$j, seq_len(2880L)))
for (key in names(design)) {
    if (is.double(planned[[key]])) {
        stopifnot(isTRUE(all.equal(design[[key]], planned[[key]], tolerance = 5e-15)))
    } else stopifnot(identical(design[[key]], planned[[key]]))
}
design <- design[(design$j - 1L) %% n_shards == shard - 1L, , drop = FALSE]

# Import the immutable development scorer's named functions without invoking
# its top-level benchmark. The shared evaluator computes both extractions,
# both panels and both PIT seeds, plus the released limits and signed errors.
frozen <- new.env(parent = environment())
needed <- c("sha", "probs", "extractors", "panel_names", "capture_conditions", "raw_limits",
            "evaluate_model", "collapse_int", "one", "election_fields", "evaluate_case")
for (expr in parse("stage2/run.R", keep.source = FALSE)) {
    if (is.call(expr) && identical(expr[[1L]], as.name("<-")) && is.symbol(expr[[2L]]) &&
        as.character(expr[[2L]]) %in% needed) {
        name <- as.character(expr[[2L]])
        stopifnot(!exists(name, frozen, inherits = FALSE))
        eval(expr, frozen)
    }
}
stopifnot(setequal(ls(frozen), needed))
frozen$arms <- c("baseline", "candidate", "peak", "start", "region")
frozen$thresholds <- c(baseline = NA_integer_, candidate = 24L, peak = 24L, start = 24L, region = 24L)
frozen$stage2_generate <- stage2_confirmation_generate

# The selected K24 peak-only implementation is the peak ablation itself.
# Execute the chosen production function once; retain both prespecified labels.
# Search inputs contain only the routine measurements, guidance anchors,
# measurement increment and routine-fit seed.
frozen$stage2_fit_pair <- function(x, anchors, h, seed) {
    initial_rng <- stage2_rng()
    baseline <- stage2_baseline(x, seed)
    after_baseline <- stage2_rng()
    on.exit(stage2_restore_rng(after_baseline))
    stage2_restore_rng(initial_rng)
    prepared <- stage2_prepare(x, anchors, h, seed)
    candidate <- stage2_selected_fit(x, anchors, h, seed, prepared = prepared, baseline = baseline)
    results <- list(baseline = baseline, candidate = candidate, peak = candidate)
    for (arm in c("start", "region")) {
        stage2_restore_rng(initial_rng)
        results[[arm]] <- stage2_fit(x, anchors, h, seed, 24L, arm,
                                     prepared = prepared, baseline = baseline)
    }
    results
}

evaluate_confirmation <- function(row) {
    case <- frozen$evaluate_case(row)
    # Development has four replicates per cell; confirmation has eight. The
    # cell identifier is a reporting field and is never passed to the search.
    case$fits$cell_id <- (row$j - 1L) %/% 8L + 1L
    case$fits$result_hash <- NULL
    case$fits$selected_rule <- stage2_selected_rule
    case$record$selected_rule <- stage2_selected_rule
    stopifnot(identical(case$record$arms$candidate, case$record$arms$peak))
    case$fits$result_hash <- frozen$sha(list(record = case$record, fits = case$fits, checks = case$checks))
    case
}
cases <- vector("list", nrow(design))
for (i in seq_len(nrow(design))) {
    cases[[i]] <- evaluate_confirmation(design[i, , drop = FALSE])
    cat("Completed confirmation j =", design$j[i], "\n")
    flush.console()
}
fits <- do.call(rbind, lapply(cases, "[[", "fits"))
checks <- do.call(rbind, lapply(cases, "[[", "checks"))
row.names(fits) <- row.names(checks) <- NULL
stopifnot(nrow(fits) == 5L * nrow(design), nrow(checks) == 4L * nrow(fits),
          !anyDuplicated(fits[c("j", "arm")]), !anyDuplicated(checks[c("j", "arm", "panel", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
saveRDS(list(fits = fits, checks = checks, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = FALSE)
