# Evaluate the frozen peak-only Stage 2 method on a shard of one RIbench cohort.
# Rscript --vanilla stage2/ribench/run.R BUNDLE small|large SHARD N_SHARDS OUT [ROUTINE_CACHE]
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) %in% 5:6)
bundle <- args[1L]
cohort <- match.arg(args[2L], c("small", "large"))
shard <- as.integer(args[3L])
n_shards <- as.integer(args[4L])
out <- args[5L]
cache <- if (length(args) == 6L) args[6L] else NULL
stopifnot(1L <= shard, shard <= n_shards, n_shards <= if (cohort == "small") 2880L else 1440L)
source("stage0/common.R")
use_libraries(bundle, "vendored")
future::plan(future::sequential)
source("R/anchor-check.R")
source("R/stage2-grid.R")
source("R/stage2-peaks.R")
source("R/stage2-search.R")
source("R/stage2-selected.R")
source("stage2/ablation-peak.R")
source("stage2/ribench/design.R")
source("stage2/ribench/inputs.R")
source("stage2/ribench/scores.R")
stopifnot(identical(stage2_selected_rule, "peak"))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

# Reuse the same diagnostic record and condition capture as confirmation,
# without executing the synthetic runner's top-level study.
frozen <- new.env(parent = environment())
needed <- c("capture_conditions", "one", "collapse_int", "election_fields", "sha")
for (expr in parse("stage2/run.R", keep.source = FALSE)) {
    if (is.call(expr) && identical(expr[[1L]], as.name("<-")) && is.symbol(expr[[2L]]) &&
        as.character(expr[[2L]]) %in% needed) {
        name <- as.character(expr[[2L]])
        stopifnot(!exists(name, frozen, inherits = FALSE))
        eval(expr, frozen)
    }
}
stopifnot(setequal(ls(frozen), needed))
capture_conditions <- frozen$capture_conditions
one <- frozen$one
arms <- c("baseline", "candidate", "peak", "start", "region")
thresholds <- c(baseline = NA_integer_, candidate = 24L, peak = 24L, start = 24L, region = 24L)

search_pair <- function(x, anchors, h, seed) {
    # Stage 0's fresh-process invocation sets seed=123 before the unmodified fit.
    set.seed(seed)
    initial_rng <- stage2_rng()
    baseline <- stage2_baseline(x, seed)
    after_baseline <- stage2_rng()
    on.exit(stage2_restore_rng(after_baseline))
    stage2_restore_rng(initial_rng)
    prepared <- stage2_prepare(x, anchors, h, seed)
    diagnostic <- stage2_development_peak(x, anchors, h, seed, prepared$K24)
    candidate <- stage2_selected_fit(x, anchors, h, seed, prepared = prepared, baseline = baseline)
    results <- list(baseline = baseline, candidate = candidate, peak = candidate)
    for (arm in c("start", "region")) {
        stage2_restore_rng(initial_rng)
        results[[arm]] <- stage2_fit(x, anchors, h, seed, 24L, arm, prepared = prepared, baseline = baseline)
    }
    list(arms = results, diagnostic = diagnostic)
}

evaluate_model <- function(fit, valid, case) {
    scored <- stage2_ribench_scores(fit, valid, case$definition)
    summary <- scored$summary
    conditions <- scored$conditions
    checks <- list()
    for (kind in c("primary", "alternate")) {
        seed <- case$meta[[paste0("pit_", kind, "_seed")]]
        if (valid) {
            checked <- capture_conditions(stage1_check(case$a, fit, case$meta$decimals, seed))
            test <- checked$value
            conditions[[paste0("guidance_", kind)]] <- checked[c("error", "warnings", "messages")]
            if (is.null(test)) test <- list(status = "check_failed", reason = "anchor_test_error",
                                             p = NA_real_, statistic = NA_real_)
            stopifnot(test$status %in% c("keep", "decline", "check_failed"))
        } else {
            test <- list(status = "fit_failed", reason = "fit_failed", statistic = NA_real_, p = NA_real_)
        }
        row <- data.frame(panel = "guidance", seed_kind = kind, seed, status = test$status,
                          reason = test$reason, statistic = test$statistic, p = test$p)
        for (extraction in c("native", "historical")) {
            usable <- !summary[[paste0(extraction, "_nonfinite")]]
            for (side in c("lower", "upper")) {
                key <- paste(extraction, side, sep = "_")
                row[[paste0("released_", key)]] <- if (test$status == "keep" && usable) summary[[key]] else NA_real_
            }
        }
        checks[[kind]] <- row
    }
    list(scores = as.data.frame(summary, stringsAsFactors = FALSE),
         checks = do.call(rbind, unname(checks)), conditions = conditions)
}

evaluate_case <- function(case) {
    m <- case$meta
    search <- capture_conditions(search_pair(case$x, case$a, m$h, m$fitter_seed))
    if (!is.na(search$error)) stop("Paired search infrastructure error at Index ", m$Index, ": ", search$error)
    results <- search$value$arms
    diagnostic <- search$value$diagnostic
    stopifnot(identical(names(results), arms), identical(results$candidate, results$peak))
    evaluated <- new.env(parent = emptyenv())
    fit_rows <- check_rows <- details <- setNames(vector("list", length(arms)), arms)
    for (arm in arms) {
        result <- results[[arm]]
        fit <- result$fit
        valid <- identical(result$status, "ResultFound")
        stopifnot(result$status %in% c("ResultFound", "fit_failed"), length(result$fallback) == 1L,
                  !is.na(result$fallback), is.logical(result$fallback))
        if (result$fallback) stopifnot(identical(fit, results$baseline$fit),
                                      identical(result$status, results$baseline$status))
        if (valid) stopifnot(stage2_valid_fit(fit), identical(fit$Data, case$x))
        hash <- if (is.null(fit)) NA_character_ else frozen$sha(fit)
        key <- if (valid) hash else "fit_failed"
        if (!exists(key, evaluated, inherits = FALSE)) assign(key, evaluate_model(fit, valid, case), evaluated)
        ev <- get(key, evaluated, inherits = FALSE)
        meta <- data.frame(arm, K = unname(thresholds[arm]), selected_rule = stage2_selected_rule,
            fit_hash = hash, fit_status = result$status, fallback = result$fallback,
            reason = one(result$reason, NA_character_), guidance_used = arm != "baseline" && !result$fallback && valid,
            fit_upstream_status = one(fit$Status, NA_character_), Mu = one(fit$Mu), Sigma = one(fit$Sigma),
            Lambda = one(fit$Lambda), Shift = one(fit$Shift), P = one(fit$P), Cost = one(fit$Cost), rf = one(fit$rf))
        fit_rows[[arm]] <- cbind(m, meta, frozen$election_fields(result), diagnostic, ev$scores)
        check_rows[[arm]] <- data.frame(Index = m$Index, arm, ev$checks, row.names = NULL)
        if (!is.null(fit$Data)) {
            stopifnot(identical(fit$Data, case$x))
            result$fit$Data <- NULL
        }
        details[[arm]] <- list(search = result, full_fit_hash = hash, scoring = ev$conditions)
    }
    fits <- do.call(rbind, unname(fit_rows))
    checks <- do.call(rbind, unname(check_rows))
    row.names(fits) <- row.names(checks) <- NULL
    record <- list(Index = m$Index, routine_hash = m$routine_hash, panels = list(guidance = case$a),
                   arms = details, initial_peak_diagnostic = diagnostic, selected_rule = stage2_selected_rule,
                   search_conditions = search[c("error", "warnings", "messages")])
    fits$result_hash <- frozen$sha(list(record = record, fits = fits, checks = checks))
    list(fits = fits, checks = checks, record = record)
}

inputs <- stage2_ribench_inputs(bundle, cohort, shard, n_shards, cache)
cases <- vector("list", length(inputs))
for (i in seq_along(inputs)) {
    cases[[i]] <- evaluate_case(inputs[[i]])
    cat("Completed RIbench", cohort, "Index", inputs[[i]]$meta$Index, "\n")
    flush.console()
}
fits <- do.call(rbind, lapply(cases, "[[", "fits"))
checks <- do.call(rbind, lapply(cases, "[[", "checks"))
row.names(fits) <- row.names(checks) <- NULL
stopifnot(nrow(fits) == length(arms) * length(cases), nrow(checks) == 2L * nrow(fits),
          !anyDuplicated(fits[c("Index", "arm")]), !anyDuplicated(checks[c("Index", "arm", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
saveRDS(list(fits = fits, checks = checks, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = FALSE)
