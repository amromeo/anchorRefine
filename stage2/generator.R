# Stage 2 development simulation, protocol c2d02a8. Sourcing draws no data.
# H is the native, unrounded, shift-zero healthy distribution.

stage2_from_z <- function(z, lambda, mu, sigma) {
  if (lambda == 0) return(exp(mu + sigma * z))
  a <- (-1 / lambda - mu) / sigma
  # Under H, the unconditioned normal survival probability is Q(a) * Q(z).
  log_survival <- pnorm(a, lower.tail = FALSE, log.p = TRUE) +
    pnorm(z, lower.tail = FALSE, log.p = TRUE)
  latent <- qnorm(log_survival, lower.tail = FALSE, log.p = TRUE)
  (lambda * sigma * pmax(0, latent - a))^(1 / lambda)
}

stage2_healthy_z <- function(x, lambda, mu, sigma) {
  z <- rep(NA_real_, length(x))
  z[!is.na(x) & x <= 0] <- -Inf
  z[!is.na(x) & x == Inf] <- Inf
  positive <- which(is.finite(x) & x > 0)
  if (!length(positive)) return(z)
  log_x <- log(x[positive])
  if (lambda == 0) {
    z[positive] <- (log_x - mu) / sigma
    return(z)
  }

  a <- (-1 / lambda - mu) / sigma
  log_normalizer <- pnorm(a, lower.tail = FALSE, log.p = TRUE)
  log_gap <- lambda * log_x - log(lambda * sigma)
  gap <- exp(log_gap)
  latent <- a + gap
  score <- numeric(length(positive))
  # Very near the Box-Cox boundary, a + gap can round to a. Integrate
  # the standard normal density over that short interval about its midpoint.
  near <- gap * (1 + abs(a)) < 1e-4
  if (any(near)) {
    midpoint <- a + gap[near] / 2
    log_p <- log_gap[near] + dnorm(midpoint, log = TRUE) - log_normalizer +
      log1p((midpoint^2 - 1) * gap[near]^2 / 24)
    score[near] <- qnorm(log_p, log.p = TRUE)
  }
  lower <- !near & latent < 0
  if (any(lower)) {
    log_cdf <- pnorm(latent[lower], log.p = TRUE)
    log_p <- log_cdf + log(-expm1(pnorm(a, log.p = TRUE) - log_cdf)) -
      log_normalizer
    score[lower] <- qnorm(log_p, log.p = TRUE)
  }
  upper <- !near & !lower
  if (any(upper)) {
    log_q <- pnorm(latent[upper], lower.tail = FALSE, log.p = TRUE) - log_normalizer
    score[upper] <- qnorm(log_q, lower.tail = FALSE, log.p = TRUE)
  }
  z[positive] <- score
  z
}

stage2_healthy_cdf <- function(x, lambda, mu, sigma) {
  pnorm(stage2_healthy_z(x, lambda, mu, sigma))
}

stage2_healthy_sd <- function(lambda, mu, sigma) {
  if (lambda == 0) return(exp(mu + sigma^2 / 2) * sqrt(expm1(sigma^2)))
  # Raw moments of a standard normal conditioned above a. For orders
  # n >= 2, m[n] = a^(n-1) * m[1] + (n-1) * m[n-2].
  a <- (-1 / lambda - mu) / sigma
  m1 <- exp(dnorm(a, log = TRUE) - pnorm(a, lower.tail = FALSE, log.p = TRUE))
  m2 <- 1 + a * m1
  if (lambda == 1) return(sigma * sqrt(m2 - m1^2))
  stopifnot(lambda == 0.5)
  # X = (1 + lambda * mu + lambda * sigma * Z)^2. Drop its constant
  # term before calculating the variance of its linear and quadratic terms.
  linear <- 2 * (1 + lambda * mu) * lambda * sigma
  quadratic <- (lambda * sigma)^2
  m3 <- a^2 * m1 + 2 * m1
  m4 <- a^3 * m1 + 3 * m2
  sqrt(linear^2 * (m2 - m1^2) +
       2 * linear * quadratic * (m3 - m1 * m2) +
       quadratic^2 * (m4 - m2^2))
}

stage2_design <- function() {
  fam <- data.frame(family = c("lognormal", "linear", "power_0.5"),
                    lambda = c(0, 1, 0.5), mu = c(log(10), 12, 4),
                    sigma = c(0.35, 1, 0.75))
  fam$healthy_sd <- mapply(stage2_healthy_sd, fam$lambda, fam$mu, fam$sigma)
  truth <- mapply(function(lambda, mu, sigma) {
    stage2_from_z(qnorm(c(0.025, 0.975)), lambda, mu, sigma)
  }, fam$lambda, fam$mu, fam$sigma)
  fam$truth_lower <- truth[1, ]
  fam$truth_upper <- truth[2, ]
  disease_names <- c("left_separated", "right_separated", "left_shoulder",
                     "right_shoulder", "bilateral_separated", "overlapping")

  # expand.grid varies its first argument fastest.
  grid <- expand.grid(replicate = 1:4, rounding_fraction = c(0.05, 0.25),
                      disease = disease_names,
                      fraction = c(0.25, 0.45, 0.60, 0.10, 0.20),
                      N = c(1500L, 50000L), family_id = seq_len(nrow(fam)),
                      KEEP.OUT.ATTRS = FALSE, stringsAsFactors = FALSE)
  j <- seq_len(nrow(grid))
  f <- fam[grid$family_id, ]
  h <- f$healthy_sd * grid$rounding_fraction
  base <- 62000000L + 10L * j
  data.frame(j, family = f$family, lambda = f$lambda, mu = f$mu,
             sigma = f$sigma, N = grid$N, fraction = grid$fraction,
             disease = grid$disease, rounding_fraction = grid$rounding_fraction,
             h, precision = h, replicate = grid$replicate, healthy_sd = f$healthy_sd,
             truth_lower = f$truth_lower, truth_upper = f$truth_upper,
             routine_seed = base, anchor_seed = base + 1L,
             diagnostic_seed = base + 2L, fitter_seed = base + 3L,
             pit_primary_seed = base + 4L, pit_alternate_seed = base + 5L,
             diagnostic_primary_seed = base + 6L, diagnostic_alternate_seed = base + 7L)
}

stage2_write_design <- function(path) {
  design <- stage2_design()
  # Seventeen significant digits preserve the exact doubles used for rounding.
  for (key in names(design)) {
    if (is.double(design[[key]])) design[[key]] <- sprintf("%.17g", design[[key]])
  }
  write.table(design, file = path, sep = ",", row.names = FALSE, quote = FALSE)
}

stage2_generate <- function(row) {
  stopifnot(is.data.frame(row), nrow(row) == 1L, row$j %in% seq_len(1440L),
            row$routine_seed == 62000000L + 10L * row$j,
            row$anchor_seed == row$routine_seed + 1L,
            row$diagnostic_seed == row$routine_seed + 2L)
  n_disease <- as.integer(round(row$N * row$fraction))
  stopifnot(abs(row$N * row$fraction - n_disease) < 1e-8)
  measure <- function(z) {
    value <- stage2_from_z(z, row$lambda, row$mu, row$sigma)
    row$h * round(value / row$h)
  }
  set.seed(row$routine_seed, kind = "Mersenne-Twister",
           normal.kind = "Inversion", sample.kind = "Rejection")
  healthy <- rnorm(row$N - n_disease)
  disease <- switch(as.character(row$disease),
                    left_separated = rnorm(n_disease, -3, 0.7),
                    right_separated = rnorm(n_disease, 3, 0.7),
                    left_shoulder = rnorm(n_disease, -0.65, 0.9),
                    right_shoulder = rnorm(n_disease, 0.65, 0.9),
                    bilateral_separated = c(rnorm(n_disease %/% 2L, -3, 0.7),
                                            rnorm(n_disease - n_disease %/% 2L, 3, 0.7)),
                    overlapping = rnorm(n_disease, 0, 1.6),
                    stop("Unrecognized development disease distribution"))
  x <- measure(c(healthy, disease))[sample.int(row$N)]
  set.seed(row$anchor_seed)
  anchors <- measure(rnorm(40L))
  set.seed(row$diagnostic_seed)
  diagnostic <- measure(rnorm(40L))
  list(x = x, anchors = anchors, diagnostic = diagnostic, h = row$h,
       truth = c(lower = row$truth_lower, upper = row$truth_upper),
       healthy_sd = row$healthy_sd)
}
