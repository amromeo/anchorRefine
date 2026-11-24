# Refit the frozen peak-only K24 rule on development. The selected entry
# point sees the routine data, guidance panel, rounding increment and fitter
# seed. The archived comparison is read separately and supplies no fit.
# Rscript --vanilla stage2/reproduce-selected.R BUNDLE SHARD N_SHARDS OUT
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
source("stage2/ablation-peak.R")
stopifnot(identical(stage2_selected_rule, "peak"))

shard <- as.integer(args[2L])
n_shards <- as.integer(args[3L])
out <- args[4L]
stopifnot(identical(n_shards, 48L), shard %in% seq_len(n_shards))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

# Load the previously frozen scoring and serialization helpers. Parsing the
# original driver avoids executing any of its retrospective benchmark loops.
needed <- c("sha", "probs", "extractors", "panel_names", "capture_conditions", "raw_limits",
            "evaluate_model", "collapse_int", "one", "election_fields")
frozen <- new.env(parent = environment())
for (expr in parse("stage2/run.R", keep.source = FALSE)) {
    if (is.call(expr) && identical(expr[[1L]], as.name("<-")) && is.symbol(expr[[2L]]) &&
        as.character(expr[[2L]]) %in% needed) {
        stopifnot(!exists(as.character(expr[[2L]]), frozen, inherits = FALSE))
        eval(expr, frozen)
    }
}
stopifnot(setequal(ls(frozen), needed))
sha <- frozen$sha
one <- frozen$one

canonical <- function(x) {
    row.names(x) <- NULL
    x
}

reference_dir <- "results/stage2-ablations-45293475762"
manifest_file <- file.path(reference_dir, "SHA256SUMS")
stopifnot(identical(digest::digest(file = manifest_file, algo = "sha256"),
                    "119eda01b5b0f29c346e1cdb3a81f941a190319cadad9b8b83c33b8601d4997e"))
manifest <- read.table(manifest_file, col.names = c("hash", "file"), colClasses = "character")
archive_name <- sprintf("artifacts/ablation-%d.zip", shard)
archive <- file.path(reference_dir, archive_name)
expected <- manifest$hash[manifest$file == archive_name]
stopifnot(length(expected) == 1L, identical(digest::digest(file = archive, algo = "sha256"), expected))
load_reference <- function() {
    temp <- tempfile("ablation-reference-")
    dir.create(temp)
    on.exit(unlink(temp, recursive = TRUE))
    member <- sprintf("primary-%d/results.rds", shard)
    utils::unzip(archive, files = member, exdir = temp)
    readRDS(file.path(temp, member))
}
reference <- load_reference()
planned <- stage2_design()
design <- read.csv("stage2/development-design.csv", stringsAsFactors = FALSE,
                   colClasses = vapply(planned, typeof, character(1)))
stopifnot(identical(names(design), names(planned)), identical(design$j, seq_len(1440L)))
design <- design[seq.int(shard, 1440L, by = n_shards), , drop = FALSE]
stopifnot(identical(design$j, vapply(reference$cases, function(case) case$j, integer(1))),
          !anyDuplicated(reference$fits[c("j", "arm")]),
          !anyDuplicated(reference$checks[c("j", "arm", "panel", "seed_kind")]))
ref_fits <- reference$fits[reference$fits$arm == stage2_selected_rule, , drop = FALSE]
ref_checks <- reference$checks[reference$checks$arm == stage2_selected_rule, , drop = FALSE]
stopifnot(identical(ref_fits$j, design$j), nrow(ref_checks) == 4L * nrow(design))

fresh_case <- function(row) {
    sample <- stage2_generate(row)
    panels <- list(guidance = sample$anchors, diagnostic = sample$diagnostic)
    stopifnot(length(sample$x) == row$N, all(is.finite(sample$x)), all(sample$x >= 0),
              identical(sample$h, row$h), all(lengths(panels) == 40L))

    # No prepared archive, baseline or cached fitted model is passed. If an
    # election or guided search fails, stage2_selected_fit fits refineR anew.
    captured <- frozen$capture_conditions(stage2_selected_fit(sample$x, panels$guidance, sample$h,
                                                               row$fitter_seed))
    if (!is.na(captured$error)) stop("Selected-rule execution failed for j=", row$j, ": ", captured$error)
    result <- captured$value
    fit <- result$fit
    valid <- identical(result$status, "ResultFound")
    stopifnot(valid || identical(result$status, "fit_failed"), identical(stage2_valid_fit(fit), valid))
    if (!is.null(fit)) stopifnot(identical(fit$Data, sample$x))
    evaluated <- frozen$evaluate_model(fit, valid, panels, row)
    initial <- stage2_development_peak(sample$x, panels$guidance, sample$h, row$fitter_seed,
                                      result$election)
    hash <- if (is.null(fit)) NA_character_ else sha(fit)
    fit_row <- canonical(cbind(row, data.frame(cell_id = (row$j - 1L) %/% 4L + 1L,
        routine_hash = sha(sample$x), anchor_hash = sha(panels$guidance),
        diagnostic_hash = sha(panels$diagnostic), arm = "selected", K = 24L, fit_hash = hash,
        fit_status = result$status, fallback = result$fallback, reason = one(result$reason, NA_character_),
        guidance_used = !result$fallback && valid, fit_upstream_status = one(fit$Status, NA_character_),
        Mu = one(fit$Mu), Sigma = one(fit$Sigma), Lambda = one(fit$Lambda), Shift = one(fit$Shift),
        P = one(fit$P), Cost = one(fit$Cost), rf = one(fit$rf)), frozen$election_fields(result),
        evaluated$summary, initial))
    check_rows <- canonical(data.frame(j = row$j, arm = "selected", evaluated$checks))
    if (!is.null(result$fit)) result$fit$Data <- NULL
    record <- list(j = row$j, routine_hash = fit_row$routine_hash, panels = panels, search = result,
        full_fit_hash = hash, scoring = evaluated$conditions, initial_peak_diagnostic = initial,
        search_conditions = captured[c("error", "warnings", "messages")])
    fit_row$rule <- stage2_selected_rule
    fit_row$source_arm <- stage2_selected_rule
    fit_row$result_hash <- sha(list(record = record, fits = fit_row, checks = check_rows))
    list(fits = fit_row, checks = check_rows, record = record)
}

# Distinguish category/branch or missingness changes from finite numeric
# roundoff throughout the stored fitted object, election and peak trace.
same_structure <- function(a, b) {
    if (!identical(typeof(a), typeof(b)) || length(a) != length(b) ||
        !identical(attributes(a), attributes(b))) return(FALSE)
    if (is.list(a)) {
        a <- unclass(a)
        b <- unclass(b)
        return(all(vapply(seq_along(a), function(i) same_structure(a[[i]], b[[i]]), logical(1))))
    }
    if (!is.double(a)) return(identical(a, b))
    finite <- is.finite(a)
    identical(finite, is.finite(b)) && identical(a[!finite], b[!finite])
}

compare_archive <- function(case, i) {
    f <- case$fits
    rec <- case$record
    old <- reference$cases[[i]]
    old_fit <- canonical(ref_fits[i, , drop = FALSE])
    expected <- old$arms[[stage2_selected_rule]]
    stopifnot(identical(old$j, f$j), identical(old_fit$j, f$j),
              identical(expected$full_fit_hash, old_fit$fit_hash))
    old_checks <- canonical(ref_checks[ref_checks$j == f$j, , drop = FALSE])
    stopifnot(nrow(old_checks) == 4L)
    new_fit <- f
    new_fit$arm <- stage2_selected_rule
    comparable <- setdiff(names(old_fit), c("result_hash", "original_result_hash"))
    stopifnot(setequal(comparable, setdiff(names(f), c("result_hash", "rule", "source_arm"))))
    new_checks <- case$checks
    new_checks$arm <- stage2_selected_rule
    input_fields <- c("routine_hash", "anchor_hash", "diagnostic_hash")
    data.frame(j = f$j, rule = stage2_selected_rule, source_arm = stage2_selected_rule,
        routine_hash = f$routine_hash, anchor_hash = f$anchor_hash, diagnostic_hash = f$diagnostic_hash,
        fit_hash = f$fit_hash, archived_fit_hash = old_fit$fit_hash,
        fit_status = f$fit_status, archived_fit_status = old_fit$fit_status,
        archived_result_hash = old_fit$result_hash, selected_result_hash = f$result_hash,
        inputs_exact = identical(f[input_fields], old_fit[input_fields]) &&
            identical(rec$panels, old$panels) && identical(rec$routine_hash, old$routine_hash),
        exact_fit = identical(f$fit_hash, old_fit$fit_hash),
        exact_search = identical(rec$search, expected$search),
        search_structure = same_structure(rec$search, expected$search),
        exact_fit_row = identical(new_fit[comparable], old_fit[comparable]),
        exact_checks = identical(new_checks, old_checks),
        exact_scoring = identical(rec$scoring, expected$scoring),
        exact_diagnostic = identical(rec$initial_peak_diagnostic, old$initial_peak_diagnostic))
}

cases <- matches <- vector("list", nrow(design))
for (i in seq_len(nrow(design))) {
    cases[[i]] <- fresh_case(design[i, , drop = FALSE])
    matches[[i]] <- compare_archive(cases[[i]], i)
    cat("Completed selected-rule development reproduction for j =", design$j[i], "\n")
    flush.console()
}
fits <- canonical(do.call(rbind, lapply(cases, "[[", "fits")))
checks <- canonical(do.call(rbind, lapply(cases, "[[", "checks")))
matches <- canonical(do.call(rbind, matches))
stopifnot(identical(fits$j, design$j), identical(matches$j, design$j), nrow(checks) == 4L * nrow(design),
          !anyDuplicated(checks[c("j", "arm", "panel", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
write_table(matches, file.path(out, "matches.csv"))
saveRDS(list(fits = fits, checks = checks, matches = matches, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = FALSE)
