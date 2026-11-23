# CDF and survival function for the healthy model on its valid Box-Cox support.
# Working with both tails avoids subtracting two numbers close to one.
stage1_log_cdf <- function(x, fit) {
    log_cdf <- rep(-Inf, length(x))
    log_surv <- numeric(length(x))
    positive <- x > fit$Shift
    if (!any(positive)) return(list(cdf = log_cdf, survival = log_surv))

    lambda <- fit$Lambda
    log_x <- log(x[positive] - fit$Shift)
    if (abs(lambda) < 1e-20) {
        z <- (log_x - fit$Mu) / fit$Sigma
        log_cdf[positive] <- stats::pnorm(z, log.p = TRUE)
        log_surv[positive] <- stats::pnorm(z, lower.tail = FALSE, log.p = TRUE)
    } else {
        z <- (expm1(lambda * log_x) / lambda - fit$Mu) / fit$Sigma
        boundary <- (-1 / lambda - fit$Mu) / fit$Sigma
        normalization <- stats::pnorm(boundary, lower.tail = FALSE, log.p = TRUE)
        log_q <- pmin(0, stats::pnorm(z, lower.tail = FALSE, log.p = TRUE) - normalization)
        log_f <- log(-expm1(log_q))
        # In the far left tail the untruncated lower probabilities, unlike
        # their complements, still distinguish the two integration limits.
        left <- z <= 0
        if (any(left)) {
            hi <- stats::pnorm(z[left], log.p = TRUE)
            lo <- stats::pnorm(boundary, log.p = TRUE)
            if (is.infinite(lo) && lo < 0) {
                log_f[left] <- hi - normalization
            } else {
                log_f[left] <- hi + log(-expm1(pmin(0, lo - hi))) - normalization
            }
        }
        log_cdf[positive] <- pmin(log_f, 0)
        log_surv[positive] <- log_q
    }
    list(cdf = log_cdf, survival = log_surv)
}

stage1_log_add <- function(a, b) {
    larger <- pmax(a, b)
    smaller <- pmin(a, b)
    result <- larger + log1p(exp(smaller - larger))
    result[which(larger == -Inf)] <- -Inf
    result
}

stage1_rounding_bins <- function(anchors, fit, decimals) {
    half <- 0.5 * 10^(-decimals)
    lower <- anchors - half
    upper <- anchors + half
    list(lower = stage1_log_cdf(lower, fit), upper = stage1_log_cdf(upper, fit),
         impossible = upper <= fit$Shift)
}

# One independent uniform variate per anchor, even for a repeated measurement.
stage1_randomized_scores <- function(bins, uniforms) {
    left <- log1p(-uniforms)
    right <- log(uniforms)
    log_p <- stage1_log_add(left + bins$lower$cdf, right + bins$upper$cdf)
    log_q <- stage1_log_add(left + bins$lower$survival, right + bins$upper$survival)
    use_lower <- log_p <= log(0.5)
    if (anyNA(use_lower)) stop("Nonfinite CDF")
    y <- numeric(length(uniforms))
    y[use_lower] <- stats::qnorm(log_p[use_lower], log.p = TRUE)
    y[!use_lower] <- stats::qnorm(log_q[!use_lower], lower.tail = FALSE, log.p = TRUE)
    y
}

# Columns are independent panels. The variance is the MLE with denominator n.
stage1_statistics <- function(y) {
    n <- nrow(y)
    location <- colMeans(y)
    centered <- sweep(y, 2L, location, "-")
    variance <- colMeans(centered^2)
    statistic <- n * (location^2 + (variance - 1) - log(variance))
    statistic[!is.finite(variance) | variance <= 0] <- NA_real_
    pmax(0, statistic)
}

stage1_deviance <- function(t, n) n * (expm1(t) - t)

stage1_roots <- function(statistic, n) {
    h <- statistic / n
    f <- function(t) stage1_deviance(t, n) - statistic
    # V = n*exp(t). The roots bracket the central interval where the
    # chi-square(1) location term contributes to the survival probability.
    c(stats::uniroot(f, c(-h - 2, 0), tol = 1e-14)$root,
      stats::uniroot(f, c(0, log1p(h) + 2), tol = 1e-14)$root)
}

stage1_null_p <- function(statistic, n = 40L) {
    if (!is.finite(statistic) || statistic < 0) stop("Invalid LRT statistic")
    if (statistic == 0) return(1)
    # For V ~ chi-square(n-1), T = A + n*(exp(t)-1-t), t=log(V/n)
    # and A ~ chi-square(1) independently. Integrate the two outside tails
    # of V analytically. Split the central integral at the density's center
    # and reference quantiles to avoid stepping over a narrow peak.
    bounds <- stage1_roots(statistic, n)
    df <- n - 1L
    left_v <- n * exp(bounds[1L])
    right_v <- n * exp(bounds[2L])
    outside <- stats::pchisq(left_v, df) + stats::pchisq(right_v, df, lower.tail = FALSE)
    knots <- c(0, log(stats::qchisq(c(1e-12, 1e-4, 0.5, 1 - 1e-4, 1 - 1e-12), df) / n))
    cuts <- sort(unique(c(bounds, knots[knots > bounds[1L] & knots < bounds[2L]])))
    shape <- df / 2
    density_constant <- shape * log(n / 2) - lgamma(shape)
    integrand <- function(t) {
        log_density <- density_constant + shape * t - (n / 2) * exp(t)
        threshold <- pmax(0, statistic - stage1_deviance(t, n))
        exp(log_density + stats::pchisq(threshold, 1, lower.tail = FALSE, log.p = TRUE))
    }
    mass <- outside
    error <- 0
    for (j in seq_len(length(cuts) - 1L)) {
        # Quadratic parameterization removes the square-root cusp in
        # P(A>=threshold) at an outer endpoint.
        lo <- cuts[j]
        hi <- cuts[j + 1L]
        if (j == 1L || j == length(cuts) - 1L) {
            edge <- if (j == 1L) lo else hi
            direction <- if (j == 1L) 1 else -1
            f <- function(u) 2 * (hi - lo) * u * integrand(edge + direction * (hi - lo) * u^2)
            piece <- stats::integrate(f, 0, 1, rel.tol = 1e-12, abs.tol = 1e-13)
        } else {
            piece <- stats::integrate(integrand, lo, hi, rel.tol = 1e-12, abs.tol = 1e-13)
        }
        mass <- mass + piece$value
        error <- error + piece$abs.error
    }
    if (!is.finite(mass) || mass < 0 || mass > 1 + 1e-10 || error > 1e-10)
        stop("Null probability did not meet its numerical tolerance")
    min(1, mass)
}

stage1_uniforms <- function(seed, n) {
    had_seed <- exists(".Random.seed", envir = .GlobalEnv, inherits = FALSE)
    if (had_seed) old_seed <- get(".Random.seed", envir = .GlobalEnv, inherits = FALSE)
    old_kind <- RNGkind()
    on.exit({
        do.call(RNGkind, as.list(old_kind))
        if (had_seed) assign(".Random.seed", old_seed, envir = .GlobalEnv)
        else if (exists(".Random.seed", envir = .GlobalEnv, inherits = FALSE))
            rm(".Random.seed", envir = .GlobalEnv)
    })
    set.seed(seed, kind = "Mersenne-Twister", normal.kind = "Inversion", sample.kind = "Rejection")
    stats::runif(n)
}

# The check is conditional on the routine-data model. It never changes the fit.
stage1_check <- function(anchors, fit, decimals, seed) {
    result <- function(status, reason, statistic = NA_real_, p = NA_real_) {
        list(status = status, reason = reason, statistic = statistic, p = p)
    }
    scalar <- function(x) is.numeric(x) && length(x) == 1L && is.finite(x)
    fields <- c("Mu", "Sigma", "Lambda", "Shift")
    if (!is.list(fit) || !all(vapply(fields, function(k) scalar(fit[[k]]), logical(1))) ||
        fit$Sigma <= 0)
        return(result("check_failed", "invalid_model_parameters"))
    if (fit$Lambda < 0 || fit$Shift < 0)
        return(result("check_failed", "unsupported_model"))
    if (!is.numeric(anchors) || length(anchors) != 40L || any(!is.finite(anchors)) ||
        any(anchors < 0))
        return(result("check_failed", "invalid_anchor_panel"))
    if (!scalar(decimals) || decimals != trunc(decimals) || !is.finite(10^(-decimals)) ||
        0.5 * 10^(-decimals) == 0 || any(round(anchors, decimals) != anchors))
        return(result("check_failed", "invalid_rounding_grid"))
    if (!scalar(seed) || seed != trunc(seed) || seed < 0 || seed > .Machine$integer.max)
        return(result("check_failed", "invalid_pit_seed"))
    bins <- stage1_rounding_bins(anchors, fit, decimals)
    if (any(bins$impossible))
        return(result("decline", "structural_incompatibility", Inf, 0))
    flat <- bins$lower$cdf == bins$upper$cdf & bins$lower$survival == bins$upper$survival
    if (anyNA(flat) || any(flat)) return(result("check_failed", "unresolved_bin_probability"))
    y <- tryCatch(stage1_randomized_scores(bins, stage1_uniforms(seed, length(anchors))),
                  error = function(e) rep(NA_real_, length(anchors)))
    if (any(!is.finite(y))) return(result("check_failed", "nonfinite_normal_score"))
    statistic <- stage1_statistics(matrix(y, ncol = 1L))[[1L]]
    if (!is.finite(statistic)) return(result("check_failed", "degenerate_or_nonfinite_statistic"))
    p <- tryCatch(stage1_null_p(statistic), error = function(e) NA_real_)
    if (!is.finite(p)) return(result("check_failed", "null_integration_failed", statistic))
    if (p < 0.01) return(result("decline", "p_below_threshold", statistic, p))
    result("keep", "within_threshold", statistic, p)
}
