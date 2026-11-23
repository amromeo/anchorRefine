# Run only after committing the Stage 1 design, seeds, and acceptance gates.
source("R/anchor-check.R")
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1L)
out <- args[[1L]]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
RNGkind("Mersenne-Twister", "Inversion", "Rejection")
n <- 40L
total <- 100000L
alphas <- c(0.01, 0.05)
critical <- vapply(alphas, function(a) {
    stats::uniroot(function(t) stage1_null_p(t, n) - a, c(0, 40), tol = 1e-13)$root
}, numeric(1))
write.csv(data.frame(alpha = alphas, critical = critical), file.path(out, "calibration-critical-values.csv"),
          row.names = FALSE)

# Independent integration, conditioning on |Z| with Z^2 ~ chi-square(1).
# Invert the variance deviance on its original, positive variance scale.
alternative_integral <- function(t) {
    limit <- sqrt(t)
    conditional <- function(z) {
        vapply(z, function(s) {
            threshold <- t - s^2
            if (threshold <= 0) return(1)
            g <- function(v) v - n - n * log(v / n) - threshold
            lo <- stats::uniroot(g, c(1e-100, n), tol = 1e-12)$root
            hi <- stats::uniroot(g, c(n, 10 * (t + n)), tol = 1e-12)$root
            stats::pchisq(lo, n - 1L) + stats::pchisq(hi, n - 1L, lower.tail = FALSE)
        }, numeric(1)) * 2 * stats::dnorm(z)
    }
    2 * stats::pnorm(limit, lower.tail = FALSE) +
        stats::integrate(conditional, 0, limit, rel.tol = 1e-12, abs.tol = 1e-12)$value
}
points <- c(0.0001, 0.2, 1, 2, 5, critical, 20, 40, 100)
production <- vapply(points, stage1_null_p, numeric(1))
independent <- vapply(points, alternative_integral, numeric(1))
numeric_tests <- data.frame(statistic = points, p_production = production, p_independent = independent,
                            absolute_difference = abs(production - independent))
numeric_tests$pass <- numeric_tests$absolute_difference <= 1e-10
write.csv(numeric_tests, file.path(out, "calibration-numerics.csv"), row.names = FALSE)
stopifnot(all(numeric_tests$pass), all(vapply(seq_along(alphas), function(j) {
    stage1_null_p(critical[j] - 1e-8) > alphas[j] && stage1_null_p(critical[j] + 1e-8) < alphas[j]
}, logical(1))))

designs <- data.frame(design = c("log_fine", "log_coarse", "truncated_linear", "shifted_extreme_rounding"),
                      Mu = c(1, 0, -1, -2), Sigma = c(0.4, 0.8, 0.8, 0.55),
                      Lambda = c(0, 0, 1, 0.5), Shift = c(0, 0, 0, 2), decimals = c(3, 0, 0, -1))
bases <- c(38000000L, 39000000L)
# Rejection sampling uses Gaussian draws and the inverse Box-Cox transform.
# It is independent of the CDF and tail formulas used to test a panel.
generate_panel <- function(idx, fit, decimals) {
    set.seed(36000000L + idx)
    if (fit$Lambda == 0) {
        return(round(fit$Shift + exp(stats::rnorm(n, fit$Mu, fit$Sigma)), decimals))
    }
    accepted <- numeric()
    while (length(accepted) < n) {
        draw <- stats::rnorm(2L * (n - length(accepted)), fit$Mu, fit$Sigma)
        accepted <- c(accepted, draw[draw > -1 / fit$Lambda])
    }
    raw <- fit$Shift + (1 + fit$Lambda * accepted[seq_len(n)])^(1 / fit$Lambda)
    round(raw, decimals)
}

rows <- list()
for (d in seq_len(nrow(designs))) {
    spec <- designs[d, ]
    fit <- as.list(spec[c("Mu", "Sigma", "Lambda", "Shift")])
    count <- matrix(0L, length(bases), length(alphas))
    changed <- integer(length(alphas))
    constant_panels <- 0L
    decision_checks <- 0L
    for (first in seq.int(1L, total, by = 1000L)) {
        index <- (d - 1L) * total + seq.int(first, min(first + 999L, total))
        panels <- vapply(index, generate_panel, numeric(n), fit = fit, decimals = spec$decimals)
        constant_panels <- constant_panels + sum(colSums(panels != rep(panels[1L, ], each = n)) == 0)
        bins <- stage1_rounding_bins(as.vector(panels), fit, spec$decimals)
        stopifnot(!any(bins$impossible))
        decisions <- vector("list", length(bases))
        for (j in seq_along(bases)) {
            u <- vapply(index, function(k) {
                set.seed(bases[j] + k)
                stats::runif(n)
            }, numeric(n))
            scores <- stage1_randomized_scores(bins, as.vector(u))
            stats <- stage1_statistics(matrix(scores, nrow = n))
            stopifnot(all(is.finite(stats)))
            decisions[[j]] <- outer(stats, critical, ">")
            count[j, ] <- count[j, ] + colSums(decisions[[j]])
            # Confirm batch calculations and classifications against the actual
            # public function, including fresh per-panel RNG initialization.
            selected <- unique(c(1L, vapply(critical, function(k) which.min(abs(stats - k)), integer(1))))
            for (s in selected) {
                check <- stage1_check(panels[, s], fit, spec$decimals, bases[j] + index[s])
                stopifnot(check$status %in% c("keep", "decline"),
                          abs(check$statistic - stats[s]) < 1e-10,
                          identical(unname(check$p < alphas), unname(decisions[[j]][s, ])))
                decision_checks <- decision_checks + 1L
            }
        }
        changed <- changed + colSums(decisions[[1]] != decisions[[2]])
    }
    for (j in seq_along(bases)) {
        lower <- stats::qbinom(0.00005, total, alphas)
        upper <- stats::qbinom(0.99995, total, alphas)
        rows[[length(rows) + 1L]] <- data.frame(spec[rep(1L, length(alphas)), ],
            n = n, panels = total, null_draw_seed_base = 36000000L, pit_seed_base = bases[j],
            first_index = (d - 1L) * total + 1L, last_index = d * total, alpha = alphas,
            declined = count[j, ], declined_share = count[j, ] / total, gate_min = lower, gate_max = upper,
            decisions_changed = changed, constant_panels = constant_panels,
            direct_check_count_both_seeds = decision_checks,
            pass = lower <= count[j, ] & count[j, ] <= upper)
    }
    cat("Calibrated", spec$design, "at both PIT seeds\n")
}
result <- do.call(rbind, rows)
write.csv(result, file.path(out, "calibration.csv"), row.names = FALSE)
stopifnot(nrow(result) == 16L, all(result$pass))
