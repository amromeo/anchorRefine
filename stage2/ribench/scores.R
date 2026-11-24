# Stage 2 uses CRAN refineR 2.0.0 and RIbench 1.0.2 endpoint extraction.
# Signed scores follow computePerfMeas in RIbench/R/evaluateResults.R.

stage2_ribench_read_limits <- function(fit, extraction, probs) {
    warnings <- messages <- character()
    error <- NA_character_
    limits <- tryCatch(withCallingHandlers({
        tab <- if (extraction == "native") {
            refineR::getRI(fit, RIperc = probs)
        } else {
            RIbench::getRI(fit, RIperc = probs, truncNormal = FALSE)
        }
        if (!is.data.frame(tab) || !identical(as.numeric(tab$Percentile), probs) ||
            !is.numeric(tab$PointEst) || length(tab$PointEst) != length(probs) ||
            any(tab$PointEst < 0, na.rm = TRUE)) {
            stop("Malformed RIbench limit extraction")
        }
        as.numeric(tab$PointEst)
    }, warning = function(w) {
        warnings <<- c(warnings, conditionMessage(w))
        invokeRestart("muffleWarning")
    }, message = function(m) {
        messages <<- c(messages, conditionMessage(m))
        invokeRestart("muffleMessage")
    }), error = function(e) {
        error <<- conditionMessage(e)
        rep(NA_real_, length(probs))
    })
    list(limits = limits, conditions = list(error = error, warnings = warnings, messages = messages))
}

stage2_ribench_scores <- function(fit, valid, definition) {
    stopifnot(is.data.frame(definition), nrow(definition) == 1L,
              is.logical(valid), length(valid) == 1L, !is.na(valid))
    crp <- as.character(definition$Analyte) == "CRP"
    probs <- if (crp) 0.95 else c(0.025, 0.975)
    shift <- definition$nonp_shift
    lambda <- definition$nonp_lambda
    mu <- definition$nonp_mu
    sigma <- definition$nonp_sigma
    stopifnot(all(is.finite(c(shift, lambda, mu, sigma))), sigma > 0)
    standardize <- function(limit) {
        (RIbench:::BoxCox(limit - shift, lambda) - mu) / sigma
    }
    truth <- standardize(c(definition$GT_LRL, definition$GT_URL))
    stopifnot(is.finite(truth[2L]), crp || is.finite(truth[1L]))
    summary <- conditions <- list()
    for (ext in c("native", "historical")) {
        limits <- rep(NA_real_, 2L)
        if (valid) {
            result <- stage2_ribench_read_limits(fit, ext, probs)
            limits[if (crp) 2L else 1:2] <- result$limits
            conditions[[ext]] <- result$conditions
        }
        # RIbench computes z(truth) - z(estimate) using the archived *rounded
        # truths*. It adds 1e-20 in the original units before subtracting
        # shift. For LDH, 100 + 1e-20 is exactly 100 in double precision.
        corrected <- limits
        below <- !is.na(corrected) & corrected <= shift
        corrected[below] <- shift + 1e-20
        # Any zero URL in the analyte group selects RIbench's zero-only URL
        # branch, even at positive shift. Carry both possible results so the
        # aggregate can resolve the branch exactly after all shards arrive.
        upper <- limits[2L]
        zero_branch <- if (!is.na(upper) && upper == 0) 1e-20 else upper
        z_upper_if_group_zero <- truth[2L] - standardize(zero_branch)
        z <- truth - standardize(corrected)
        if (!is.na(upper) && upper == 0) z[2L] <- z_upper_if_group_zero
        finite <- is.finite(limits)
        finite_requested <- finite[2L] && (crp || finite[1L])
        data <- list(lower = limits[1L], upper = upper, z_lower = z[1L],
                     z_upper = z[2L], z_upper_if_group_zero = z_upper_if_group_zero,
                     out_lower = if (finite[1L]) limits[1L] <= shift else NA,
                     out_upper = if (finite[2L]) upper <= shift else NA,
                     ordered = if (!crp && finite_requested) limits[1L] < upper else NA,
                     nonfinite = !finite_requested)
        names(data) <- paste(ext, names(data), sep = "_")
        summary <- c(summary, data)
    }
    list(summary = summary, conditions = conditions)
}

# Resolve the grouped URL branch on an entire stage cohort. The lower score
# is row-separable because both official extractors produce nonnegative
# limits, and the zero-only lower branch is used only when shift is zero.
stage2_ribench_group_scores <- function(rows) {
    definitions <- RIbench::loadTestsetDefinition()
    ensure_cohort <- function(n) ifelse(n <= 5000, "small", "large")
    stopifnot(all(rows$N <= 5000 | rows$N == 50000), !anyDuplicated(rows[c("Index", "arm")]))
    cohort <- ensure_cohort(rows$N)
    for (ii in split(seq_len(nrow(rows)), list(cohort, rows$arm), drop = TRUE)) {
        planned <- if (cohort[ii[1L]] == "small") definitions$N <= 5000 else definitions$N == 50000
        stopifnot(setequal(rows$Index[ii], definitions$Index[planned]))
        for (idx in split(ii, rows$Analyte[ii], drop = TRUE)) {
            for (ext in c("native", "historical")) {
                if (any(rows[[paste0(ext, "_upper")]][idx] == 0, na.rm = TRUE)) {
                    rows[[paste0(ext, "_z_upper")]][idx] <-
                        rows[[paste0(ext, "_z_upper_if_group_zero")]][idx]
                }
            }
        }
    }
    rows
}
