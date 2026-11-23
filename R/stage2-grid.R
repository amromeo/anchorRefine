# Derived from testParam by Tatjana Ammer in refineR 2.0.0, GPL (>= 3).
# Stage 2 retains refineR's histogram cost and adaptive grid optimizer.

stage2_initial_nodes <- function(bounds, center, k, starts) {
    if (length(bounds) != 2L || any(!is.finite(bounds)) || bounds[1L] >= bounds[2L]) {
        stop("grid: invalid initial bounds", call. = FALSE)
    }
    if (starts && bounds[1L] < center && center < bounds[2L]) {
        # Supply the bounds themselves to preserve their exact values at j=k.
        fractions <- (seq_len(k - 1L) / k)^2
        nodes <- c(bounds[1L], center - (center - bounds[1L]) * rev(fractions),
                   center, center + (bounds[2L] - center) * fractions, bounds[2L])
    } else {
        nodes <- seq(bounds[1L], bounds[2L], length.out = 2L * k + 1L)
    }
    if (any(!is.finite(nodes)) || any(diff(nodes) <= 0)) {
        stop("grid: collapsed or nonfinite initial nodes", call. = FALSE)
    }
    nodes
}

stage2_project_nodes <- function(nodes, bounds) {
    if (any(!is.finite(nodes))) stop("grid: nonfinite adaptive node", call. = FALSE)
    sort(unique(pmax(bounds[1L], pmin(bounds[2L], nodes))), method = "quick")
}

stage2_test_param <- function(lambdaVec, bestParam, Data, HistData, startValues,
                              NIter, alpha = 0.01, alphaMcb = 0.1, ctx) {
    if (!ctx$starts && !ctx$regions) {
        return(refineR:::testParam(lambdaVec, bestParam, Data, HistData, startValues,
                                   NIter, alpha, alphaMcb))
    }

    quartiles <- unname(ctx$quartiles)
    if (length(quartiles) != 3L || any(!is.finite(quartiles)) || quartiles[1L] <= 0) {
        stop("proposal: missing quartiles or nonpositive first quartile", call. = FALSE)
    }
    h <- 0.002
    lookup <- list(h = h, val = stats::pnorm(seq(-5.2, 5.2 + h, by = h)))
    for (i in seq_along(lambdaVec)) {
        transformed <- refineR::BoxCox(quartiles, lambdaVec[i])
        m <- transformed[2L]
        s <- (transformed[3L] - transformed[1L]) / 1.3489795003921634
        if (any(!is.finite(transformed)) || !is.finite(s) || s <= 0) {
            stop("proposal: unusable transformed anchor location or scale", call. = FALSE)
        }
        if (ctx$regions) {
            mu_bounds <- m + c(-1.5, 1.5) * s
            sigma_bounds <- c(s / 2, 2 * s)
            if (sigma_bounds[1L] <= 0) stop("grid: nonpositive sigma bound", call. = FALSE)
        } else {
            mu_bounds <- startValues$muEst[i, 2:3]
            sigma_bounds <- startValues$sigmaEst[i, 2:3]
        }
        mu <- stage2_initial_nodes(mu_bounds, m, 4L, ctx$starts)
        sigma <- stage2_initial_nodes(sigma_bounds, s, 6L, ctx$starts)

        tried_mu <- tried_sigma <- NULL
        best_cost <- 1e9
        best_mu <- best_sigma <- NA_real_
        for (iter in seq_len(NIter)) {
            if (iter > 1L) {
                if (is.na(best_mu) || is.na(best_sigma)) break
                mu <- refineR:::optimizeGrid(best_mu, tried_mu, iter, sigmLimit = FALSE)
                sigma <- refineR:::optimizeGrid(best_sigma, tried_sigma, iter, sigmLimit = TRUE)
                if (ctx$regions) {
                    mu <- stage2_project_nodes(mu, mu_bounds)
                    sigma <- stage2_project_nodes(sigma, sigma_bounds)
                    if (all(mu %in% tried_mu) && all(sigma %in% tried_sigma)) break
                }
            }
            tested <- refineR:::calculateCostHist(lambdaVec[i], mu, sigma, HistData,
                                                   alpha, alphaMcb, lookup)
            tried_mu <- sort(unique(c(tried_mu, mu)), method = "quick")
            tried_sigma <- sort(unique(c(tried_sigma, sigma)), method = "quick")
            if (tested[5L] < best_cost) {
                best_mu <- tested[2L]
                best_sigma <- tested[3L]
                best_cost <- tested[5L]
            }
            if (tested[5L] < bestParam[5L]) bestParam <- tested
        }
    }
    bestParam
}
