# Screened observations are measured on the original scale. Fixed bin edges can
# be transformed once per lambda and reused for every candidate Mu and Sigma.
stage3_anchor_prepare <- function(anchors, h, lambda, shift) {
    valid_scalar <- function(x) is.numeric(x) && length(x) == 1L && is.finite(x)
    if (!is.numeric(anchors) || length(anchors) != 40L || any(!is.finite(anchors)) ||
        !valid_scalar(lambda) || lambda < 0 || !valid_scalar(shift)) {
        return(list(status = "invalid_panel_or_transformation"))
    }
    if (is.null(h)) h <- 0
    if (!valid_scalar(h) || h < 0 || (h > 0 && h / 2 == 0)) {
        return(list(status = "invalid_increment"))
    }

    v <- as.numeric(anchors) - shift
    # This is the same log branch used by refineR::BoxCox and Stage 1.
    if (lambda < 1e-20) lambda <- 0
    boundary <- if (lambda == 0) -Inf else -1 / lambda
    transform_log <- function(log_v) {
        if (lambda == 0) log_v else expm1(lambda * log_v) / lambda
    }

    if (h == 0) {
        if (any(v <= 0)) return(list(status = "structural_zero"))
        log_v <- log(v)
        return(list(status = "ok", exact = TRUE, boundary = boundary,
                    y = transform_log(log_v), log_jacobian = (lambda - 1) * log_v))
    }
    upper <- v + h / 2
    if (any(upper <= 0)) return(list(status = "structural_zero"))
    lower <- pmax(0, v - h / 2)
    if (any(!is.finite(upper))) return(list(status = "unresolved_cell"))
    log_upper <- log(upper)
    log_lower <- log(lower)
    ylo <- transform_log(log_lower)
    yhi <- transform_log(log_upper)

    # Keep a separate accurately calculated width in transformed coordinates
    # for narrow bins, even when the computed transformed edges coincide.
    raw_width <- pmin(h, upper)
    relative_width <- raw_width / upper
    log_edge_ratio <- log_lower - log_upper
    narrow <- relative_width < 0.5
    log_edge_ratio[narrow] <- log1p(-relative_width[narrow])
    if (lambda == 0) {
        log_width <- log(-log_edge_ratio)
    } else {
        log_width <- lambda * log_upper + log(-expm1(lambda * log_edge_ratio)) - log(lambda)
    }
    # At this threshold the midpoint Jacobian approximation differs by less
    # than machine precision. It also covers a relative width that underflowed.
    very_narrow <- relative_width < .Machine$double.eps
    log_width[very_narrow] <- log(raw_width[very_narrow]) + (lambda - 1) * log_upper[very_narrow]
    list(status = "ok", exact = FALSE, boundary = boundary, lower = ylo, upper = yhi,
         log_width = log_width)
}

# Integrate the normalized normal density over the transformed (support-clipped)
# bin. Scaling by its maximum keeps the quadrature finite in either tail.
stage3_anchor_integral <- function(left, right, log_width, log_normalizer) {
    if (!is.finite(log_normalizer) || is.na(left) || is.na(right)) return(NA_real_)
    if (left == -Inf && is.finite(right)) {
        return(pnorm(right, log.p = TRUE) - log_normalizer)
    }
    if (!all(is.finite(c(left, right, log_width)))) return(NA_real_)
    width <- exp(log_width)
    if (!is.finite(width)) return(NA_real_)
    mode <- min(right, max(0, left))
    relative_density <- function(f) {
        displacement <- if (left >= 0) {
            f * width
        } else if (right <= 0) {
            (f - 1) * width
        } else {
            left + f * width
        }
        exp(-displacement * (mode + displacement / 2))
    }
    mass <- tryCatch(stats::integrate(relative_density, 0, 1, rel.tol = 1e-12,
                abs.tol = 0, subdivisions = 200L)$value, error = function(e) NA_real_)
    if (!is.finite(mass) || mass <= 0) return(NA_real_)
    log_width + dnorm(mode, log = TRUE) - log_normalizer + log(mass)
}

# Rows correspond to anchors in their original order. Columns correspond to
# paired (mu, sigma) trials. Returned values average natural log mass/density.
stage3_anchor_scores <- function(prepared, mu, sigma) {
    n <- max(length(mu), length(sigma))
    if (!n) return(numeric())
    stopifnot(length(mu) %in% c(1L, n), length(sigma) %in% c(1L, n))
    values <- rep(NA_real_, n)
    if (prepared$status != "ok") {
        if (prepared$status == "structural_zero") values[] <- -Inf
        return(values)
    }
    mu <- rep_len(mu, n)
    sigma <- rep_len(sigma, n)
    valid <- which(is.finite(mu) & is.finite(sigma) & sigma > 0)
    if (!length(valid)) return(values)
    mu <- mu[valid]
    sigma <- sigma[valid]
    log_norm <- pnorm((prepared$boundary - mu) / sigma, lower.tail = FALSE, log.p = TRUE)
    standardize <- function(y) {
        sweep(outer(y, mu, "-"), 2L, sigma, "/")
    }
    if (prepared$exact) {
        z <- standardize(prepared$y)
        log_density <- dnorm(z, log = TRUE) + prepared$log_jacobian
        score <- colMeans(log_density) - log(sigma) - log_norm
    } else {
        left <- standardize(prepared$lower)
        right <- standardize(prepared$upper)
        # Reflection maps a right-tail difference to the more stable lower
        # tail. Subtract before dividing by the common support normalization.
        reflect <- left > -right
        reflect[is.na(reflect)] <- FALSE
        lo <- left
        hi <- right
        lo[reflect] <- -right[reflect]
        hi[reflect] <- -left[reflect]
        log_hi <- pnorm(hi, log.p = TRUE)
        log_ratio <- pnorm(lo, log.p = TRUE) - log_hi
        log_prob <- sweep(log_hi + log(-expm1(pmin(0, log_ratio))), 2L, log_norm, "-")
        unstable <- !is.finite(log_prob) | log_prob > 1e-12 |
                    (is.finite(log_ratio) & log_ratio > -1e-8)
        for (cell in which(unstable)) {
            i <- (cell - 1L) %% nrow(log_prob) + 1L
            j <- (cell - 1L) %/% nrow(log_prob) + 1L
            log_prob[cell] <- stage3_anchor_integral(left[cell], right[cell],
                prepared$log_width[i] - log(sigma[j]), log_norm[j])
        }
        log_prob[is.finite(log_prob) & log_prob > 1e-12] <- NA_real_
        score <- colMeans(pmin(log_prob, 0))
    }
    # Structural zeros leave the function before this point. A nonfinite
    # numerical score marks an unresolved trial, including overflow in z².
    score[!is.finite(score)] <- NA_real_
    values[valid] <- score
    values
}

stage3_loglik <- function(fit, anchors, h) {
    prepared <- stage3_anchor_prepare(anchors, h, fit$Lambda, fit$Shift)
    stage3_anchor_scores(prepared, fit$Mu, fit$Sigma)
}

# Estimate the underlying (before truncation) normal parameters at the parent's
# fixed transformation. The search coordinates scale automatically with units.
stage3_post_estimate <- function(parent, anchors, h) {
    invalid <- function(reason) list(ok = FALSE, reason = reason, Mu = NA_real_,
                         Sigma = NA_real_, u = NA_real_, v = NA_real_, loglik = NA_real_)
    fit <- parent$fit
    if (!stage2_valid_fit(fit)) return(invalid("invalid_parent_fit"))
    prepared <- stage3_anchor_prepare(anchors, h, fit$Lambda, fit$Shift)
    if (prepared$status != "ok") return(invalid(prepared$status))
    if (length(unique(anchors)) < 2L) return(invalid("single_occupied_cell"))
    v_bound <- log(16)
    best_at <- function(us, vs) {
        trials <- expand.grid(u = unique(us), v = unique(vs), KEEP.OUT.ATTRS = FALSE)
        trials$Mu <- fit$Mu + fit$Sigma * trials$u
        trials$Sigma <- fit$Sigma * exp(trials$v)
        trials$loglik <- stage3_anchor_scores(prepared, trials$Mu, trials$Sigma)
        trials <- trials[is.finite(trials$loglik), , drop = FALSE]
        if (!nrow(trials)) return(NULL)
        # Candidate ordering also defines an exact tie on the final grid.
        ord <- with(trials, order(-loglik, u^2 + v^2, u, v))
        trials[ord[1L], , drop = FALSE]
    }
    best <- best_at(-12:12, seq(-v_bound, v_bound, length.out = 17L))
    if (is.null(best)) return(invalid("no_finite_anchor_score"))
    du <- 1
    dv <- v_bound / 8
    for (iter in seq_len(20L)) {
        du <- du / 2
        dv <- dv / 2
        us <- pmax(-12, pmin(12, best$u + (-1:1) * du))
        vs <- pmax(-v_bound, pmin(v_bound, best$v + (-1:1) * dv))
        best <- best_at(us, vs)
    }
    ans <- c(list(ok = TRUE, reason = "estimated"), as.list(best))
    if (abs(ans$u) == 12 || abs(ans$v) == v_bound) {
        ans$ok <- FALSE
        ans$reason <- "anchor_optimum_at_boundary"
    }
    ans
}

stage3_post <- function(parent, anchors, h, t, estimate = NULL) {
    if (length(t) != 1L || !is.finite(t) || t < 0 || t > 1) stop("Invalid post-fit weight")
    if (t == 0) return(parent)
    result <- parent
    result$inherited_fallback <- isTRUE(parent$fallback)
    result$inherited_reason <- parent$reason
    result$additional_fallback <- FALSE
    result$parent_histogram <- parent$fit[c("P", "rf", "Cost")]
    if (is.null(estimate)) estimate <- stage3_post_estimate(parent, anchors, h)
    result$post_estimate <- estimate
    if (!stage2_valid_fit(parent$fit)) {
        result$reason <- "invalid_parent_fit"
        return(result)
    }
    if (!estimate$ok) {
        result$fallback <- TRUE
        result$additional_fallback <- TRUE
        result$reason <- estimate$reason
        return(result)
    }
    fit <- parent$fit
    fit$Mu <- (1 - t) * fit$Mu + t * estimate$Mu
    fit$Sigma <- fit$Sigma * exp(t * log(estimate$Sigma / fit$Sigma))
    if (!stage2_valid_fit(fit)) {
        result$fallback <- TRUE
        result$additional_fallback <- TRUE
        result$reason <- "invalid_blended_parameters"
        return(result)
    }
    result$fit <- fit
    result$reason <- "post_adjusted"
    result
}
