# Evaluate K24's three individual components on one frozen DEVELOPMENT shard.
# Rscript --vanilla stage2/ablation-run.R BUNDLE SHARD N_SHARDS OUT
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
source("stage2/generator.R")
source("stage2/ablation-peak.R")

shard <- as.integer(args[2L])
n_shards <- as.integer(args[3L])
out <- args[4L]
stopifnot(1L <= shard, shard <= n_shards, n_shards <= 1440L)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

original <- "results/stage2-development-45283676579"
manifest <- read.table(file.path(original, "SHA256SUMS"), col.names = c("sha", "file"),
                       colClasses = "character", stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(manifest$file))
checked_file <- function(relative) {
    path <- file.path(original, relative)
    expected <- manifest$sha[match(relative, manifest$file)]
    stopifnot(length(expected) == 1L, !is.na(expected),
              identical(digest::digest(file = path, algo = "sha256"), expected))
    path
}
published <- read.csv(checked_file("evidence/fits.csv.gz"), colClasses = "character",
                      stringsAsFactors = FALSE)
stopifnot(nrow(published) == 4320L, !anyDuplicated(published[c("j", "arm")]))
planned <- stage2_design()
design <- read.csv("stage2/development-design.csv", stringsAsFactors = FALSE,
                   colClasses = vapply(planned, typeof, character(1)))
stopifnot(identical(names(design), names(planned)), identical(design$j, seq_len(1440L)))
design <- design[(design$j - 1L) %% n_shards == shard - 1L, , drop = FALSE]

# Import only the frozen runner's named helpers. This preserves its full-precision
# errors, both extractors, PIT implementation, metadata and serialization without
# executing its top-level three-arm study again.
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
arms <- c("baseline", "K24", "peak", "start", "region")
frozen$arms <- arms
frozen$thresholds <- c(baseline = NA_integer_, K24 = 24L, peak = 24L, start = 24L, region = 24L)
sha <- frozen$sha

canonical <- function(x) {
    row.names(x) <- NULL
    x
}

# The archive stored Data by its digest plus a seed. Reinserting it as the
# original FIRST field reproduces the whole upstream RWDRI object, including
# its class and every fitted parameter. Reject mismatches before reusing it.
restore_search <- function(detail, x) {
    result <- detail$search
    if (!is.null(result$fit)) {
        old <- result$fit
        stopifnot(!"Data" %in% names(old), inherits(old, "RWDRI"))
        fit <- c(list(Data = x), unclass(old))
        class(fit) <- class(old)
        stopifnot(identical(sha(fit), detail$full_fit_hash))
        result$fit <- fit
    } else {
        stopifnot(is.na(detail$full_fit_hash))
    }
    result
}

load_original_shard <- function(s) {
    rel <- sprintf("artifacts/dev-%d.zip", s)
    zip <- checked_file(rel)
    member <- sprintf("primary-%d/results.rds", s)
    path <- tempfile("original-primary-")
    dir.create(path)
    on.exit(unlink(path, recursive = TRUE))
    utils::unzip(zip, files = member, exdir = path)
    old <- readRDS(file.path(path, member))
    js <- vapply(old$cases, function(case) case$j, integer(1))
    stopifnot(identical(js, seq.int(s, 1440L, by = 48L)),
              !anyDuplicated(old$fits[c("j", "arm")]),
              !anyDuplicated(old$checks[c("j", "arm", "panel", "seed_kind")]))
    names(old$cases) <- as.character(js)
    old
}

evaluate_ablation <- function(row, old) {
    j <- row$j
    ref <- old$cases[[as.character(j)]]
    old_fits <- canonical(old$fits[old$fits$j == j, , drop = FALSE])
    old_checks <- canonical(old$checks[old$checks$j == j, , drop = FALSE])
    old_hash <- unique(old_fits$result_hash)
    stopifnot(!is.null(ref), identical(ref$j, j), nrow(old_fits) == 3L, nrow(old_checks) == 12L,
              length(old_hash) == 1L, grepl("^[0-9a-f]{64}$", old_hash))
    # Whole-case hashes were computed before the original RDS concatenated
    # its per-case frames. Check those signed identities against the separate,
    # archived primary evidence export. Recheck the individual fit hashes from
    # the rehydrated full RWDRI objects before the first new search.
    evidence <- published[published$j == as.character(j), ]
    evidence <- evidence[match(old_fits$arm, evidence$arm), ]
    identity <- c("result_hash", "fit_hash", "routine_hash", "anchor_hash", "diagnostic_hash")
    for (field in identity) stopifnot(identical(as.character(old_fits[[field]]), evidence[[field]]))
    old_fits$result_hash <- NULL
    original_design <- canonical(old_fits[old_fits$arm == "baseline", names(row), drop = FALSE])
    stopifnot(identical(original_design, canonical(row)))

    # Keep the original scoring/metadata logic in its own lexical environment.
    # Each per-case callback has access only to this case's archived inputs.
    case_scope <- new.env(parent = frozen)
    evaluator <- frozen$evaluate_case
    environment(evaluator) <- case_scope
    info <- NULL
    case_scope$stage2_generate <- function(row) {
        sample <- stage2_generate(row)
        panels <- list(guidance = sample$anchors, diagnostic = sample$diagnostic)
        stopifnot(identical(sha(sample$x), ref$routine_hash), identical(panels, ref$panels),
                  all(old_fits$routine_hash == ref$routine_hash),
                  all(old_fits$anchor_hash == sha(panels$guidance)),
                  all(old_fits$diagnostic_hash == sha(panels$diagnostic)))
        sample
    }
    case_scope$stage2_fit_pair <- function(x, anchors, h, seed) {
        baseline <- restore_search(ref$arms$baseline, x)
        full <- restore_search(ref$arms$K24, x)
        prepared <- stage2_prepare(x, anchors, h, seed)
        stopifnot(identical(prepared$K24, full$election))
        info <<- stage2_development_peak(x, anchors, h, seed, prepared$K24)
        result <- list(baseline = baseline, K24 = full)
        for (arm in c("peak", "start", "region")) {
            result[[arm]] <- stage2_fit(x, anchors, h, seed, 24L, arm,
                                        prepared = prepared, baseline = baseline)
        }
        result
    }
    case <- evaluator(row)
    case$fits$result_hash <- NULL
    # Re-extract, re-score and re-check the two archived fits. Every baseline
    # and full-model CSV field must equal its binary original on this build.
    comparators <- c("baseline", "K24")
    check_archive <- function(new, archived) {
        a <- canonical(new[new$arm %in% comparators, , drop = FALSE])
        b <- canonical(archived[archived$arm %in% comparators, , drop = FALSE])
        stopifnot(identical(a, b))
    }
    check_archive(case$fits, old_fits)
    check_archive(case$checks, old_checks)
    stopifnot(is.data.frame(info), nrow(info) == 1L,
              all(c("upstream_peak_index", "anchor_initial_index", "same_peak", "initial_peak_count")
                    %in% names(info)))
    diagnostic <- info[rep(1L, nrow(case$fits)), , drop = FALSE]
    case$fits <- canonical(cbind(case$fits, original_result_hash = old_hash, diagnostic))
    case$record$original_result_hash <- old_hash
    case$record$initial_peak_diagnostic <- info
    case$fits$result_hash <- sha(list(record = case$record, fits = case$fits, checks = case$checks))
    case
}

records <- vector("list", nrow(design))
old_shards <- (design$j - 1L) %% 48L + 1L
for (s in unique(old_shards)) {
    old <- load_original_shard(s)
    for (i in which(old_shards == s)) {
        records[[i]] <- evaluate_ablation(design[i, , drop = FALSE], old)
        cat("Completed development ablations j =", design$j[i], "\n")
        flush.console()
    }
}
fits <- canonical(do.call(rbind, lapply(records, "[[", "fits")))
checks <- canonical(do.call(rbind, lapply(records, "[[", "checks")))
stopifnot(nrow(fits) == length(arms) * nrow(design), nrow(checks) == 4L * nrow(fits),
          !anyDuplicated(fits[c("j", "arm")]), !anyDuplicated(checks[c("j", "arm", "panel", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
saveRDS(list(fits = fits, checks = checks, cases = lapply(records, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = FALSE)
