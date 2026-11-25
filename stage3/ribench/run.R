# Evaluate one RIbench shard using the accepted Stage 3 methods.
# Rscript run.R BUNDLE small|large SHARD 48 OUT primary|repeat|other sampled|full [LARGE_CACHE]
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) %in% 7:8)
bundle <- args[1L]
cohort <- match.arg(args[2L], c("small", "large"))
shard <- as.integer(args[3L])
n_shards <- as.integer(args[4L])
out <- args[5L]
role <- match.arg(args[6L], c("primary", "repeat", "other"))
audit_mode <- match.arg(args[7L], c("sampled", "full"))
cache <- if (length(args) == 8L) args[8L] else NULL
stopifnot(n_shards == 48L, shard >= 1L, shard <= n_shards)
source("stage0/common.R")
use_libraries(bundle, "vendored")
invisible(loadNamespace("refineR"))
invisible(loadNamespace("RIbench"))
stopifnot(packageVersion("RIbench") == "1.0.2")
future::plan(future::sequential)
for (file in c("R/anchor-check.R", "R/stage2-peaks.R", "R/stage2-grid.R", "R/stage2-search.R",
               "R/stage2-selected.R", "stage2/ablation-peak.R", "stage2/ribench/design.R",
               "stage2/ribench/inputs.R", "stage2/ribench/scores.R", "stage3/anchors.R",
               "stage3/primary.R", "sources/c2/anchoredRI/tools/anchors-only/estimators.R")) source(file)

# Import functions without executing the previous runners' top-level experiments.
import_helpers <- function(file, keys, into) {
    for (expr in parse(file, keep.source = FALSE)) {
        if (is.call(expr) && identical(expr[[1L]], as.name("<-")) && is.symbol(expr[[2L]]) &&
            as.character(expr[[2L]]) %in% keys) eval(expr, into)
    }
    stopifnot(all(vapply(keys, exists, logical(1), envir = into, inherits = FALSE)))
}
helpers <- new.env(parent = environment())
import_helpers("stage2/run.R", c("sha", "capture_conditions", "one", "collapse_int", "election_fields"), helpers)
import_helpers("stage3/run.R", c("anchor_only", "central_quantiles", "metric_pair", "parent_coordinates",
                                 "data_frame_rows"), helpers)
import_helpers("stage2/ribench/run.R", "evaluate_model", helpers)
arms <- c("baseline", "stage2", "w0", "w1", "t0", "t0.25", "anchorsOnly")
sha <- helpers$sha
one <- helpers$one
combine <- helpers$data_frame_rows

# The C2 percentile wrapper uses its saved 1.96 limits for two-sided intervals.
# For CRP it takes the fitted distribution's 95th percentile (run-stage.R).
ao_env <- new.env(parent = helpers)
ao_env$stage2_ribench_read_limits <- function(fit, extraction, probs) {
    if (length(probs) == 1L) {
        stopifnot(probs == .95)
        z <- fit$mu + stats::qnorm(probs) * fit$sd
        limits <- if (fit$transform == "identity") z else fit$shift + exp(z)
    } else {
        stopifnot(identical(probs, c(.025, .975)))
        limits <- fit$limits
    }
    list(limits = as.numeric(limits),
         conditions = list(error = NA_character_, warnings = character(), messages = character()))
}
ao_env$stage2_ribench_scores <- stage2_ribench_scores
environment(ao_env$stage2_ribench_scores) <- ao_env

evaluate_anchor_only <- function(res, case) {
    valid <- identical(res$status, "ResultFound")
    scored <- ao_env$stage2_ribench_scores(res$fit, valid, case$definition)
    # Anchors-only follows its archived reporting rule, with no PIT test.
    checks <- data.frame(panel = "guidance", seed_kind = c("primary", "alternate"),
        seed = c(case$meta$pit_primary_seed, case$meta$pit_alternate_seed),
        status = if (valid) "keep" else "fit_failed",
        reason = if (valid) "original_reporting_rule" else "fit_failed",
        statistic = NA_real_, p = NA_real_, stringsAsFactors = FALSE)
    for (ext in c("native", "historical")) {
        for (side in c("lower", "upper")) {
            name <- paste(ext, side, sep = "_")
            checks[[paste0("released_", name)]] <- if (valid) scored$summary[[name]] else NA_real_
        }
    }
    list(scores = as.data.frame(scored$summary), checks = checks, conditions = scored$conditions)
}

evaluate_case <- function(case) {
    m <- case$meta
    x <- case$x
    a <- case$a
    h <- m$h
    seed <- m$fitter_seed
    set.seed(seed)
    initial <- stage2_rng()
    conditions <- list()
    run_search <- function(label, expr) {
        ret <- helpers$capture_conditions(expr)
        conditions[[label]] <<- ret[c("error", "warnings", "messages")]
        if (!is.na(ret$error)) stop("Search infrastructure error at Index ", m$Index,
                                     ", arm ", label, ": ", ret$error)
        ret$value
    }
    selected <- function() stage2_selected_fit(x, a, h, seed)
    parent <- run_search("stage2", selected())
    parent_rng <- stage2_rng()
    stage2_restore_rng(initial)
    w0 <- run_search("w0", stage3_primary(x, a, h, seed, parent, w = 0))
    w0_rng <- stage2_rng()
    stage2_restore_rng(initial)
    t0 <- run_search("t0", stage3_post(selected(), a, h, t = 0))
    t0_rng <- stage2_rng()
    rng_exact <- c(w0 = identical(parent_rng, w0_rng), t0 = identical(parent_rng, t0_rng))
    fit_exact <- c(w0 = identical(serialize(w0, NULL, version = 2L), serialize(parent, NULL, version = 2L)),
                   t0 = identical(serialize(t0, NULL, version = 2L), serialize(parent, NULL, version = 2L)))
    stopifnot(all(rng_exact), all(fit_exact))
    stage2_restore_rng(initial)
    w1 <- run_search("w1", stage3_primary_many(x, a, h, seed, parent, 1)[["w1"]])
    stage2_restore_rng(initial)
    baseline <- run_search("baseline", stage2_baseline(x, seed))
    estimate <- run_search("post_anchor_estimate", stage3_post_estimate(parent, a, h))
    post <- run_search("t0.25", stage3_post(parent, a, h, t = .25, estimate = estimate))
    ao <- run_search("anchorsOnly", helpers$anchor_only(a))
    results <- list(baseline = baseline, stage2 = parent, w0 = w0, w1 = w1, t0 = t0,
                    t0.25 = post, anchorsOnly = ao)
    stopifnot(identical(names(results), arms))

    # Truth enters only after all searches finish.
    peak <- stage2_development_peak(x, a, h, seed, parent$election)
    election <- parent$election
    in_basin <- NA
    if (isTRUE(election$ok)) {
        median_truth <- RIbench:::invBoxCox(m$nonp_mu, m$nonp_lambda) + m$nonp_shift
        last <- election$winner == length(election$counts)
        in_basin <- median_truth >= election$bounds[1L] &&
            (median_truth < election$bounds[2L] || (last && median_truth == election$bounds[2L]))
    }
    reference <- helpers$evaluate_model(parent$fit, parent$status == "ResultFound", case)
    zero_evals <- lapply(results[c("w0", "t0")], function(res)
        helpers$evaluate_model(res$fit, res$status == "ResultFound", case))
    score_exact <- vapply(zero_evals, identical, logical(1), y = reference)
    stopifnot(all(score_exact))
    parent_measure <- helpers$parent_coordinates(helpers$central_quantiles(parent), parent)
    parent_valid <- identical(parent$status, "ResultFound")
    parent_fallback <- isTRUE(parent$fallback)
    fits <- checks <- records <- list()
    for (arm in arms) {
        res <- results[[arm]]
        fit <- res$fit
        valid <- identical(res$status, "ResultFound")
        is_ao <- arm == "anchorsOnly"
        is_primary <- arm %in% c("w0", "w1")
        is_post <- arm %in% c("t0", "t0.25")
        is_zero <- arm %in% names(zero_evals)
        stopifnot(res$status %in% c("ResultFound", "fit_failed"), length(res$fallback) == 1L,
                  is.logical(res$fallback), !is.na(res$fallback))
        if (valid && !is_ao) stopifnot(stage2_valid_fit(fit), identical(fit$Data, x))
        hash <- if (is.null(fit)) NA_character_ else sha(fit)
        score <- if (is_ao) evaluate_anchor_only(res, case) else if (is_zero) zero_evals[[arm]] else
            if (arm == "stage2") reference else helpers$evaluate_model(fit, valid, case)

        q <- helpers$central_quantiles(res, is_ao)
        delta <- (helpers$parent_coordinates(q, parent) - parent_measure) /
            if (parent_valid) parent$fit$Sigma else NA_real_
        if (is_zero) stopifnot(all(is.na(delta) | delta == 0))
        # Center/spread use RIbench's unrounded healthy Box-Cox z scale.
        z <- suppressWarnings((RIbench:::BoxCox(q - m$nonp_shift, m$nonp_lambda) - m$nonp_mu) / m$nonp_sigma)
        shape <- helpers$metric_pair(z)
        detail <- res$stage3
        branch <- one(detail$branch, NA_character_)
        attempt <- if (is_primary) !is_zero && parent_valid else NA
        entered <- if (is_primary) !is_zero && isTRUE(detail$entered) else NA
        path <- if (!is_primary) NA_character_ else if (is_zero) "zero" else if (!parent_valid)
            "invalid_parent" else if (parent_fallback) "unguided" else "guided"
        if (arm == "w1") {
            stopifnot(is.logical(detail$entered), length(detail$entered) == 1L,
                      identical(detail$entered, branch %in% c("weighted", "retained_parent", "search_fallback")))
            if (parent_valid) stopifnot(identical(detail$path, path))
        }
        extra <- if (is_post) isTRUE(res$additional_fallback) else
            isTRUE(attempt) && !branch %in% c("weighted", "retained_parent")
        meta <- data.frame(arm, selected_rule = stage2_selected_rule,
            K = if (arm %in% c("baseline", "anchorsOnly")) NA_integer_ else 24L,
            guidance_used = !is_ao && arm != "baseline" && valid && !parent_fallback,
            weight = if (is_primary || is_post) as.numeric(substring(arm, 2L)) else NA_real_,
            fit_hash = hash, fit_status = res$status, fallback = res$fallback,
            reason = one(res$reason, NA_character_), branch, parent_fallback,
            inherited_fallback = (is_primary || is_post) && parent_fallback,
            weighted_search_attempted = attempt, weighted_search_entered = entered,
            weighted_search_path = path, extra_fallback = extra,
            parent_retained = if (arm %in% c("w1", "t0.25") && valid) identical(parent$fit, fit) else NA,
            fit_upstream_status = one(fit$Status, NA_character_), Mu = one(fit$Mu), Sigma = one(fit$Sigma),
            Lambda = one(fit$Lambda), Shift = one(fit$Shift), P = one(fit$P), Cost = one(fit$Cost),
            rf = one(fit$rf), C_H = one(detail$C_H), A = one(detail$A), J = one(detail$J),
            B = one(detail$B), k = one(detail$k), overlap = one(detail$overlap),
            hist_hash = one(detail$hist_hash, NA_character_), loglik_anchor_mu = one(res$post_estimate$Mu),
            loglik_anchor_sigma = one(res$post_estimate$Sigma), ao_transform = one(fit$transform, NA_character_),
            ao_location = if (is_ao) one(fit$mu) else NA_real_, ao_spread = if (is_ao) one(fit$sd) else NA_real_,
            ao_shift = if (is_ao) one(fit$shift) else NA_real_, healthy_median_in_basin = in_basin,
            center_shift = delta[1L], spread_shift = delta[2L],
            healthy_center_z = shape[1L], healthy_spread_z = shape[2L] - 1,
            zero_fit_exact = if (is_zero) fit_exact[[arm]] else NA,
            zero_rng_exact = if (is_zero) rng_exact[[arm]] else NA,
            zero_score_exact = if (is_zero) score_exact[[arm]] else NA, stringsAsFactors = FALSE)
        ids <- data.frame(j = m$Index, phase = "ribench", cohort, stringsAsFactors = FALSE)
        fits[[arm]] <- cbind(m, ids, meta, peak, helpers$election_fields(res), score$scores)
        checks[[arm]] <- data.frame(Index = m$Index, j = m$Index, arm, score$checks, row.names = NULL)
        uses_routine <- !is.null(fit$Data)
        if (uses_routine) {
            stopifnot(identical(fit$Data, x))
            res$fit["Data"] <- list(NULL)
            restored <- res$fit
            restored$Data <- x
            stopifnot(identical(sha(restored), hash))
        }
        records[[arm]] <- list(search = res, full_fit_hash = hash, conditions = score$conditions,
                               uses_routine = uses_routine)
    }
    fit_table <- combine(fits)
    check_table <- combine(checks)
    record <- list(Index = m$Index, j = m$Index, routine_hash = m$routine_hash,
                   panels = list(guidance = a), arms = records, search_conditions = conditions,
                   zero_fit_exact = fit_exact, zero_rng_exact = rng_exact, zero_score_exact = score_exact,
                   initial_rng_hash = sha(initial), parent_rng_hash = sha(parent_rng),
                   w0_rng_hash = sha(w0_rng), t0_rng_hash = sha(t0_rng), routine = x)
    fit_table$case_hash <- sha(record)
    fit_table$result_hash <- sha(list(record, fit_table, check_table))
    list(fits = fit_table, checks = check_table, record = record)
}

dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))
inputs <- stage2_ribench_inputs(bundle, cohort, shard, n_shards, cache)
if (role != "primary" && audit_mode == "sampled") {
    sample <- read.csv("stage3/ribench/audit-sample.csv", stringsAsFactors = FALSE)
    ids <- sample$Index[sample$cohort == cohort]
    inputs <- Filter(function(case) case$meta$Index %in% ids, inputs)
}
cases <- lapply(inputs, function(case) {
    result <- evaluate_case(case)
    cat("Completed RIbench", cohort, "Index", case$meta$Index, "\n")
    flush.console()
    result
})
if (length(cases)) {
    fits <- combine(lapply(cases, "[[", "fits"))
    checks <- combine(lapply(cases, "[[", "checks"))
} else {
    stopifnot(role != "primary", audit_mode == "sampled")
    fits <- data.frame(Index = integer(), j = integer(), arm = character())
    checks <- data.frame(Index = integer(), j = integer(), arm = character(),
                         panel = character(), seed_kind = character())
    writeLines("No sampled datasets assigned to this shard.", file.path(out, "empty.txt"))
}
stopifnot(nrow(fits) == length(arms) * length(cases), nrow(checks) == 2L * nrow(fits),
          !anyDuplicated(fits[c("Index", "arm")]), !anyDuplicated(checks[c("Index","arm","panel","seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
saveRDS(list(fits = fits, checks = checks, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = "gzip")
