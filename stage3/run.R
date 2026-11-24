# Run one audited influence or development shard. Independent roles are separate
# invocations with the same arguments and separate output directories.
# Rscript --vanilla stage3/run.R BUNDLE PHASE SHARD TOTAL OUT
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 5L)
source("stage0/common.R")
use_libraries(args[1L], "vendored")
stopifnot(packageVersion("RIbench") == "1.0.2")
future::plan(future::sequential)
for (file in c("R/anchor-check.R", "R/stage2-peaks.R", "R/stage2-grid.R", "R/stage2-search.R",
               "R/stage2-selected.R", "stage2/generator.R", "stage2/ablation-peak.R",
               "sources/c2/anchoredRI/tools/anchors-only/estimators.R", "stage3/design.R",
               "stage3/anchors.R", "stage3/primary.R", "stage3/diagnostics.R")) source(file)

phase <- args[2L]
shard <- as.integer(args[3L])
n_shards <- as.integer(args[4L])
out <- args[5L]
design <- stage3_manifest(phase)
stopifnot(1L <= shard, shard <= n_shards, n_shards <= nrow(design))
slot <- design$j - 1L
# Rotate each full block so first-replicate diagnostics are shared across hosts.
if (phase == "development") slot <- slot + 5L * (slot %/% n_shards)
design <- design[slot %% n_shards == shard - 1L, , drop = FALSE]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

# Import only helper definitions. The frozen Stage 2 top-level runner never runs.
scorer <- new.env(parent = environment())
helpers <- c("sha", "probs", "extractors", "panel_names", "capture_conditions", "raw_limits",
             "evaluate_model", "collapse_int", "one", "election_fields")
for (expr in parse("stage2/run.R", keep.source = FALSE)) {
    if (is.call(expr) && identical(expr[[1L]], as.name("<-")) && is.symbol(expr[[2L]]) &&
        as.character(expr[[2L]]) %in% helpers) eval(expr, scorer)
}
stopifnot(setequal(ls(scorer), helpers))
sha <- scorer$sha
one <- scorer$one
capture <- scorer$capture_conditions

# For the C2 estimator both endpoint labels use its original 1.96 interval and
# it always releases a successful fit. It has no Stage 1 p-value.
ao_scorer <- new.env(parent = scorer)
ao_scorer$raw_limits <- function(fit, extraction) as.numeric(fit$limits)
ao_scorer$stage2_check <- function(fit, anchors, h, seed) {
    list(status = "keep", reason = "original_reporting_rule", statistic = NA_real_, p = NA_real_)
}
ao_evaluate <- scorer$evaluate_model
environment(ao_evaluate) <- ao_scorer

weights <- c(0, 1, 10, 100, 1000, 10000)
post_weights <- c(0, 0.25, 0.5, 0.75, 1)
primary_labels <- paste0("w", weights)
post_labels <- paste0("t", post_weights)

data_frame_rows <- function(frames) {
    result <- do.call(rbind, unname(frames))
    row.names(result) <- NULL
    result
}

anchor_only <- function(a) {
    f <- ao_auto(a)
    valid <- is.null(f$error) || !nzchar(f$error)
    valid <- valid && identical(length(f$limits), 2L) && all(is.finite(f$limits))
    list(fit = f, status = if (valid) "ResultFound" else "fit_failed", fallback = FALSE,
         reason = if (valid) "original_reporting_rule" else f$error)
}

central_quantiles <- function(result, ao = FALSE) {
    if (result$status != "ResultFound") return(rep(NA_real_, 3L))
    f <- result$fit
    if (ao) {
        transformed <- f$mu + c(-1, 0, 1) * f$sd
        if (f$transform == "identity") return(transformed)
        return(f$shift + exp(transformed))
    }
    refineR:::cdfTruncatedBoxCox(f$Mu, f$Sigma, f$Lambda, f$Shift, pnorm(c(-1, 0, 1)))
}

metric_pair <- function(z) {
    stopifnot(length(z) == 3L)
    c(if (is.finite(z[2L])) z[2L] else NA_real_,
      if (all(is.finite(z[c(1L, 3L)]))) (z[3L] - z[1L]) / 2 else NA_real_)
}

parent_coordinates <- function(q, parent) {
    if (parent$status != "ResultFound") return(c(NA_real_, NA_real_))
    delta <- q - parent$fit$Shift
    delta[!is.finite(delta) | delta <= 0] <- NA_real_
    metric_pair(refineR::BoxCox(delta, parent$fit$Lambda))
}

run_case <- function(row) {
    sample <- stage3_generate(row)
    x <- sample$x
    a <- sample$anchors
    h <- row$h
    seed <- row$fitter_seed
    panels <- list(guidance = a, diagnostic = sample$diagnostic)
    stopifnot(length(x) == row$N, all(is.finite(x)), all(x >= 0), all(lengths(panels) == 40),
              identical(sample$h, h), all(is.finite(unlist(panels, use.names = FALSE))))
    inputs <- data.frame(routine_hash = sha(x), anchor_hash = sha(a),
                         diagnostic_hash = sha(panels$diagnostic))
    conditions <- list()
    run_search <- function(label, expression) {
        ret <- capture(expression)
        conditions[[label]] <<- ret[c("error", "warnings", "messages")]
        if (!is.na(ret$error)) stop("Search error, ", row$phase, ", j=", row$j,
                                     ", arm=", label, ": ", ret$error)
        ret$value
    }
    initial_rng <- stage2_rng()
    selected <- function() stage2_selected_fit(x, a, h, seed)
    parent <- run_search("stage2", selected())
    final_rng <- stage2_rng()
    stage2_restore_rng(initial_rng)
    w0 <- run_search("w0", stage3_primary(x, a, h, seed, parent, w = 0))
    w0_rng <- stage2_rng()
    stage2_restore_rng(initial_rng)
    # Lazy parent expression exercises post_fit's exact Stage 2 zero dispatch.
    t0 <- run_search("t0", stage3_post(selected(), a, h, t = 0))
    t0_rng <- stage2_rng()
    rng_ok <- c(w0 = identical(final_rng, w0_rng), t0 = identical(final_rng, t0_rng))
    exact <- c(w0 = identical(serialize(w0, NULL, version = 2), serialize(parent, NULL, version = 2)),
               t0 = identical(serialize(t0, NULL, version = 2), serialize(parent, NULL, version = 2)))
    stopifnot(all(exact), all(rng_ok))
    stage2_restore_rng(initial_rng)
    positive <- run_search("primary", stage3_primary_many(x, a, h, seed, parent, weights[-1L]))
    primary <- c(list(w0 = w0), positive)
    stopifnot(identical(names(primary), primary_labels))
    result <- c(list(stage2 = parent), primary)
    post <- NULL
    if (phase == "development") {
        stage2_restore_rng(initial_rng)
        baseline <- run_search("baseline", stage2_baseline(x, seed))
        est <- run_search("post_anchor_estimate", stage3_post_estimate(parent, a, h))
        post <- c(list(t0 = t0), setNames(lapply(post_weights[-1L], function(w) {
            stage3_post(parent, a, h, t = w, estimate = est)
        }), post_labels[-1L]))
        result <- c(list(baseline = baseline), result, post,
                    list(anchorsOnly = run_search("anchorsOnly", anchor_only(a))))
    }

    # Raw basin agreement uses the upstream coarse peak before its interpolation.
    peak <- stage2_development_peak(x, a, h, seed, parent$election)
    median_truth <- stage2_from_z(0, row$lambda, row$mu, row$sigma)
    election <- parent$election
    in_basin <- if (isTRUE(election$ok)) {
        last <- election$winner == length(election$counts)
        median_truth >= election$bounds[1L] &&
            (median_truth < election$bounds[2L] || (last && median_truth == election$bounds[2L]))
    } else NA
    diag_primary <- setNames(primary, as.character(weights))
    diag_post <- if (is.null(post)) NULL else setNames(post, as.character(post_weights))
    stage2_restore_rng(initial_rng)
    diagnostics <- stage3_diagnostics(phase, row, x, a, h, seed, parent, diag_primary, post = diag_post)

    # Scoring receives truth after fitting. Always evaluate zero-weight arms
    # afresh to compare their two extractions and all checks with the parent.
    reference <- scorer$evaluate_model(parent$fit, parent$status == "ResultFound", panels, row)
    zero_evals <- list(
        w0 = scorer$evaluate_model(w0$fit, w0$status == "ResultFound", panels, row),
        t0 = scorer$evaluate_model(t0$fit, t0$status == "ResultFound", panels, row))
    zero_score <- vapply(zero_evals, identical, logical(1), y = reference)
    stopifnot(all(zero_score))
    parent_measure <- parent_coordinates(central_quantiles(parent), parent)
    fits <- checks <- records <- list()
    cache <- new.env(parent = emptyenv())
    for (arm in names(result)) {
        res <- result[[arm]]
        fit <- res$fit
        valid <- identical(res$status, "ResultFound")
        ao <- arm == "anchorsOnly"
        is_primary <- arm %in% primary_labels
        is_post <- arm %in% post_labels
        is_zero <- arm %in% names(exact)
        stopifnot(res$status %in% c("ResultFound", "fit_failed"), is.logical(res$fallback),
                  length(res$fallback) == 1L, !is.na(res$fallback))
        if (valid && !ao)
            stopifnot(stage2_valid_fit(fit), identical(fit$Data, x))
        hash <- if (is.null(fit)) NA_character_ else sha(fit)
        key <- if (valid) hash else "unavailable"
        if (ao) {
            score <- ao_evaluate(fit, valid, panels, row)
        } else if (is_zero) {
            score <- zero_evals[[arm]]
        } else if (arm == "stage2") {
            score <- reference
        } else if (exists(key, cache, inherits = FALSE)) {
            score <- get(key, cache, inherits = FALSE)
        } else {
            score <- scorer$evaluate_model(fit, valid, panels, row)
        }
        if (!ao) assign(key, score, cache)
        q <- central_quantiles(res, ao)
        shift <- (parent_coordinates(q, parent) - parent_measure) /
            if (parent$status == "ResultFound") parent$fit$Sigma else NA_real_
        if (is_zero) stopifnot(all(is.na(shift) | shift == 0))
        healthy_shape <- metric_pair(stage2_healthy_z(q, row$lambda, row$mu, row$sigma))
        shape <- res$stage3
        branch <- one(shape$branch, NA_character_)
        # For the primary arm, fallbacks retain the same Stage 2 result.
        # The post-fit arm may adjust a valid inherited fallback.
        inherited <- (is_primary || is_post) && isTRUE(parent$fallback)
        added <- if (is_post) isTRUE(res$additional_fallback) else
            is_primary && isTRUE(res$fallback) && !inherited
        retained <- if (is_primary && !is_zero && valid) identical(parent$fit, fit) else
            if (is_post && !is_zero && valid) identical(parent$fit, fit) else NA
        guidance_used <- !ao && !identical(arm, "baseline") && valid && !isTRUE(parent$fallback)
        meta <- data.frame(arm, guidance_used, weight = if (is_primary || is_post) as.numeric(substring(arm, 2L)) else NA_real_,
            fit_hash = hash, fit_status = res$status, fallback = res$fallback,
            reason = one(res$reason, NA_character_), branch, inherited_fallback = inherited,
            extra_fallback = added, parent_retained = retained,
            fit_upstream_status = one(fit$Status, NA_character_), Mu = one(fit$Mu), Sigma = one(fit$Sigma),
            Lambda = one(fit$Lambda), Shift = one(fit$Shift), P = one(fit$P), Cost = one(fit$Cost),
            rf = one(fit$rf), C_H = one(shape$C_H), A = one(shape$A), J = one(shape$J),
            B = one(shape$B), k = one(shape$k), overlap = one(shape$overlap),
            hist_hash = one(shape$hist_hash, NA_character_), loglik_anchor_mu = one(res$post_estimate$Mu),
            loglik_anchor_sigma = one(res$post_estimate$Sigma), ao_transform = one(fit$transform, NA_character_),
            ao_location = if (ao) one(fit$mu) else NA_real_, ao_spread = if (ao) one(fit$sd) else NA_real_,
            ao_shift = if (ao) one(fit$shift) else NA_real_, healthy_median_in_basin = in_basin,
            center_shift = shift[1L], spread_shift = shift[2L], healthy_center_z = healthy_shape[1L],
            healthy_spread_z = healthy_shape[2L] - 1, zero_fit_exact = if (is_zero) exact[[arm]] else NA,
            zero_rng_exact = if (is_zero) rng_ok[[arm]] else NA,
            zero_score_exact = if (is_zero) zero_score[[arm]] else NA, stringsAsFactors = FALSE)
        fits[[arm]] <- cbind(row, inputs, meta, peak, scorer$election_fields(res), score$summary)
        checks[[arm]] <- data.frame(j = row$j, arm, score$checks, row.names = NULL)
        if (!is.null(res$fit$Data)) {
            stopifnot(identical(res$fit$Data, x))
            res$fit$Data <- NULL
        }
        records[[arm]] <- list(search = res, full_fit_hash = hash, conditions = score$conditions)
    }
    fit_table <- data_frame_rows(fits)
    check_table <- data_frame_rows(checks)
    record <- list(j = row$j, routine_hash = inputs$routine_hash, panels = panels, arms = records,
        search_conditions = conditions, zero_fit_exact = exact, zero_rng_exact = rng_ok,
        zero_score_exact = zero_score, initial_rng_hash = sha(initial_rng),
        parent_rng_hash = sha(final_rng), w0_rng_hash = sha(w0_rng), t0_rng_hash = sha(t0_rng))
    fit_table$result_hash <- sha(list(record, fit_table, check_table))
    list(record = record, fits = fit_table, checks = check_table, diagnostics = diagnostics)
}

cases <- vector("list", nrow(design))
for (i in seq_len(nrow(design))) {
    cases[[i]] <- run_case(design[i, , drop = FALSE])
    cat("Completed", phase, "j =", design$j[i], "(", i, "of", nrow(design), ")\n")
    flush.console()
}
fits <- data_frame_rows(lapply(cases, "[[", "fits"))
checks <- data_frame_rows(lapply(cases, "[[", "checks"))
stopifnot(nrow(fits) == nrow(design) * if (phase == "influence") 7L else 14L,
          nrow(checks) == 4L * nrow(fits), !anyDuplicated(fits[c("j", "arm")]),
          !anyDuplicated(checks[c("j", "arm", "panel", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
for (what in c("identities", "sensitivity")) {
    tbl <- data_frame_rows(lapply(cases, function(case) case$diagnostics[[what]]))
    stopifnot(is.data.frame(tbl), length(names(tbl)) > 0L)
    write_table(tbl, file.path(out, paste0(what, ".csv")))
}
saveRDS(list(fits = fits, checks = checks, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = "gzip")
