# The interpolation, local ASH window and smoothing are derived from
# Tatjana Ammer's findMainPeak in refineR 2.0.0 (GPL >= 3). The ASH and
# peak detection are called directly from that version. The anchor election
# and tracking rule are modifications by the anchorRefine project (GPL-3).

stage2_empty_election <- function(reason, K) {
    list(ok = FALSE, reason = reason, K = K, index = NA_integer_,
         winner = NA_integer_, peak_x = NA_real_, bounds = c(NA_real_, NA_real_),
         closed_right = NA, target = NA_real_, anchor_median = NA_real_,
         quantiles = c(NA_real_, NA_real_), votes = NA_integer_,
         runner_up = NA_integer_, counts = integer(), edges = numeric(),
         peak_indices = integer(), coordinates = numeric(),
         assignments = rep(NA_integer_, 40L))
}

stage2_valid_density <- function(dens) {
    is.numeric(dens$x) && is.numeric(dens$y) && length(dens$x) >= 3L &&
        length(dens$x) == length(dens$y) && all(is.finite(dens$x)) &&
        all(is.finite(dens$y)) && all(dens$y >= 0) && all(diff(dens$x) > 0) &&
        is.numeric(dens$ab) && length(dens$ab) == 2L &&
        all(is.finite(dens$ab)) && dens$ab[1L] <= dens$x[1L] &&
        dens$x[length(dens$x)] <= dens$ab[2L]
}

stage2_grid_indices <- function(indices, n) {
    length(indices) == 0L || (is.numeric(indices) && all(is.finite(indices)) &&
        all(indices == trunc(indices)) && all(indices >= 1L & indices <= n))
}

stage2_valid_anchor_grid <- function(anchors, h) {
    if (!is.numeric(h) || length(h) != 1L || !is.finite(h) || h / 2 <= 0)
        return(FALSE)
    indices <- anchors / h
    if (any(!is.finite(indices))) return(FALSE)
    # Simulated measurements use h * round(x/h). The RIbench archives use
    # round(x, digits); its doubles may differ by one ULP from that product.
    on_grid <- anchors == h * round(indices)
    digits <- round(-log10(h))
    if (h == 10^(-digits))
        on_grid <- on_grid | anchors == round(anchors, digits)
    all(on_grid)
}

stage2_rethreshold <- function(election, K) {
    election$K <- K
    if (length(K) != 1L || !is.numeric(K) || !K %in% c(24, 28)) {
        election$ok <- FALSE
        election$reason <- "invalid_K"
        return(election)
    }
    if (!length(election$counts)) return(election)
    reason <- if (is.na(election$winner)) {
        "tied_vote"
    } else if (election$votes < K) {
        "insufficient_votes"
    } else if (election$votes - election$runner_up < 8L) {
        "insufficient_lead"
    } else if (election$peak_x < election$quantiles[1L] ||
               election$peak_x > election$quantiles[2L]) {
        "peak_outside_anchor_quantiles"
    } else {
        "clear"
    }
    election$ok <- reason == "clear"
    election$reason <- reason
    election
}

stage2_elect_peak <- function(dens, peaks, valleys, anchors, h, K) {
    fail <- function(reason) stage2_empty_election(reason, K)
    if (!is.numeric(anchors) || length(anchors) != 40L ||
        any(!is.finite(anchors)) || any(anchors < 0))
        return(fail("invalid_anchor_panel"))
    if (!stage2_valid_anchor_grid(anchors, h))
        return(fail("invalid_rounding_grid"))
    if (!stage2_valid_density(dens)) return(fail("invalid_density"))
    if (!length(peaks)) return(fail("no_detected_peak"))
    if (!stage2_grid_indices(peaks, length(dens$x)) ||
        !stage2_grid_indices(valleys, length(dens$x)) || anyDuplicated(peaks))
        return(fail("invalid_extrema"))
    peaks <- sort(as.integer(peaks))
    valleys <- sort(as.integer(valleys))
    interior <- numeric(length(peaks) - 1L)
    for (i in seq_along(interior)) {
        between <- valleys[valleys > peaks[i] & valleys < peaks[i + 1L]]
        if (!length(between)) return(fail("missing_intervening_valley"))
        interior[i] <- dens$x[between[which.min(dens$y[between])]]
    }
    edges <- c(dens$ab[1L], interior, dens$ab[2L])
    if (any(diff(edges) <= 0)) return(fail("zero_width_basin"))

    lower <- pmax(0, anchors - h / 2)
    upper <- anchors + h / 2
    basin <- findInterval(lower, edges)
    inside <- which(basin >= 1L & basin <= length(peaks) & upper > lower)
    whole <- inside[upper[inside] <= edges[basin[inside] + 1L]]
    assignments <- rep(NA_integer_, 40L)
    assignments[whole] <- basin[whole]
    counts <- tabulate(assignments, nbins = length(peaks))
    leaders <- which(counts == max(counts))
    election <- stage2_empty_election("undecided", K)
    election$counts <- counts
    election$votes <- max(counts)
    election$runner_up <- if (length(counts) == 1L) 0L else sort(counts, decreasing = TRUE)[2L]
    election$edges <- edges
    election$peak_indices <- peaks
    election$coordinates <- dens$x[peaks]
    election$assignments <- assignments
    election$anchor_median <- stats::median(anchors)
    election$quantiles <- stats::quantile(anchors, c(0.1, 0.9), type = 7, names = FALSE)
    if (length(leaders) == 1L) {
        winner <- leaders[1L]
        election$winner <- winner
        election$index <- peaks[winner]
        election$peak_x <- dens$x[peaks[winner]]
        election$bounds <- edges[c(winner, winner + 1L)]
        election$closed_right <- winner == length(peaks)
        election$target <- stats::median(anchors[which(assignments == winner)])
    }
    stage2_rethreshold(election, K)
}

stage2_peak_stop <- function(reason) stop(paste0("stage2_peak: ", reason), call. = FALSE)

stage2_peak_grid <- function(x, ab, nbin, m) {
    dens <- tryCatch(refineR:::ashDensity(x = x, ab = ab, nbin = nbin, m = m),
                     error = function(e) stage2_peak_stop("ash_density_error"))
    if (!stage2_valid_density(dens)) stage2_peak_stop("invalid_density")
    extrema <- tryCatch(refineR:::findPeaksAndValleys(dens),
                        error = function(e) stage2_peak_stop("peak_detection_error"))
    if (!length(extrema$peaks)) stage2_peak_stop("no_detected_peak")
    if (!stage2_grid_indices(extrema$peaks, length(dens$x)))
        stage2_peak_stop("invalid_extrema")
    list(density = dens, peaks = extrema$peaks, valleys = extrema$valleys)
}

stage2_first_election <- function(x, ab, mStart, anchors, h, K) {
    tryCatch({
        grid <- stage2_peak_grid(x, ab, 512L, mStart)
        stage2_elect_peak(grid$density, grid$peaks, grid$valleys, anchors, h, K)
    }, error = function(e) {
        stage2_empty_election(sub("^stage2_peak: ", "", conditionMessage(e)), K)
    })
}

stage2_tracking_coordinates <- function(election, lambda) {
    bounds <- election$bounds
    target <- election$target
    if (!is.null(lambda)) {
        if (length(lambda) != 1L || !is.finite(lambda)) stage2_peak_stop("invalid_lambda")
        # At zero upstream gives the positive-domain limit, including -Inf
        # for logs. Raw ASH windows can extend below measurement support.
        bounds <- refineR::BoxCox(pmax(0, bounds), lambda)
        target <- refineR::BoxCox(target, lambda)
    }
    if (!is.finite(target)) stage2_peak_stop("nonfinite_target")
    if (anyNA(bounds) || bounds[1L] >= bounds[2L]) stage2_peak_stop("empty_mapped_basin")
    list(bounds = bounds, target = target)
}

stage2_track_peak <- function(grid, coords, closed_right) {
    peaks <- grid$peaks
    x <- grid$density$x[peaks]
    right <- if (closed_right) x <= coords$bounds[2L] else x < coords$bounds[2L]
    eligible <- peaks[x >= coords$bounds[1L] & right]
    if (!length(eligible)) stage2_peak_stop("no_peak_in_basin")
    distance <- abs(grid$density$x[eligible] - coords$target)
    eligible[order(distance, -grid$density$y[eligible], eligible)[1L]]
}

stage2_peak_mode <- function(dens, index) {
    i <- min(length(dens$x) - 1L, max(2L, index))
    bins <- i + (-1L:1L)
    mode <- sum(dens$x[bins] * dens$y[bins]) / sum(dens$y[bins])
    if (!is.finite(mode)) stage2_peak_stop("nonfinite_interpolated_mode")
    list(index = i, mode = mode)
}

stage2_guided_peak <- function(x, ab, mStart, election, lambda = NULL, initial = FALSE) {
    if (!isTRUE(election$ok)) stage2_peak_stop("unclear_election")
    coords <- stage2_tracking_coordinates(election, lambda)
    coarse <- stage2_peak_grid(x, ab, 512L, mStart)
    if (initial) {
        index <- election$index
        if (!is.null(lambda) || !index %in% coarse$peaks ||
            coarse$density$x[index] != election$peak_x)
            stage2_peak_stop("initial_grid_mismatch")
    } else {
        index <- stage2_track_peak(coarse, coords, election$closed_right)
    }
    d <- coarse$density
    peak <- stage2_peak_mode(d, index)
    threshold <- 0.35 * d$y[peak$index]
    left <- max(ab[1L], d$x[d$x < peak$mode & d$y <= threshold])
    right <- min(ab[2L], d$x[d$x > peak$mode & d$y <= threshold])
    fine <- stage2_peak_grid(x, c(left, right), 256L, ceiling(mStart / 1.5))
    final <- stage2_track_peak(fine, coords, election$closed_right)
    peak <- stage2_peak_mode(fine$density, final)
    list(peakInd = peak$index, modEst = peak$mode, Dens = fine$density,
         coarse = index, fine = final)
}
