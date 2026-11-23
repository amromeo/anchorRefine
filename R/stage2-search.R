# Stage 2 is derived from refineR 2.0.0, GPL (>= 3), by Tatjana Ammer,
# Matthias Beck, Christopher M Rank and Andre Schuetzenmeister.
# The unchanged routine histogram and its cost remain in the upstream package.

stage2_rng <- function() get0(".Random.seed", envir = .GlobalEnv, inherits = FALSE)

stage2_restore_rng <- function(state) {
    if (!is.null(state)) {
        assign(".Random.seed", state, envir = .GlobalEnv)
    } else if (exists(".Random.seed", envir = .GlobalEnv, inherits = FALSE)) {
        rm(".Random.seed", envir = .GlobalEnv)
    }
}

# Use the same two future seed calls as refineR::findRI(NBootstrap=0).
stage2_job <- function(seed, work) {
    seeds <- future.apply::future_lapply(1L, function(i) .Random.seed,
                  future.chunk.size = Inf, future.seed = seed)
    future.apply::future_lapply(1L, function(i) work(), future.seed = seeds,
                               future.packages = c("ash", "refineR"))[[1L]]
}

stage2_routine <- function(x) {
    stopifnot(is.numeric(x))
    x <- x[!is.na(x)]
    x <- x[x >= 0]
    stopifnot(length(x) > 10L)
    x
}

# Upstream defineSearchRegions jitters rounded data in the working copy.
# length(x) after duplication also sets the ASH smoother downstream.
stage2_working_data <- function(x, roundingBase) {
    if (length(x) > 100000) {
        if (!is.na(roundingBase)) {
            x <- x + stats::runif(length(x), -0.5 * roundingBase, 0.5 * roundingBase - 1e-20)
        }
        qData <- as.numeric(stats::quantile(x, seq(0, 1, length.out = 50000), type = 7))
    } else if (!is.na(roundingBase)) {
        x <- rep(x, times = floor(100000 / length(x)))
        qData <- x + stats::runif(length(x), -0.5 * roundingBase, 0.5 * roundingBase - 1e-20)
    } else {
        qData <- as.numeric(stats::quantile(x, seq(0, 1, length.out = 50000), type = 7))
    }
    list(qData = qData, n = length(x))
}

# Bounds of the *first* coarse ASH in upstream estimateAB, before trimming.
stage2_first_window <- function(x) {
    q <- as.numeric(stats::quantile(x, c(0, 0.01, 0.95, 0.99, 0.999), na.rm = TRUE))
    opt <- q[c(2L, 4L)]
    span <- diff(opt)
    opt[1L] <- max(opt[1L] - 0.1 * span, q[1L], 1e-20)
    opt[2L] <- min(opt[2L] + 0.1 * span, q[5L])
    det <- q[c(2L, 4L)]
    det[1L] <- max(det[1L], 1e-20)
    det[1L] <- det[1L] - 0.01 * diff(det)
    if (!all(is.finite(c(opt, det))) || opt[2L] <= opt[1L] || opt[2L] <= det[1L]) {
        stop("election: empty upstream first window", call. = FALSE)
    }
    ab <- c(max(det[1L], 1e-20), min(opt[2L], det[2L]))
    ab[1L] <- ab[1L] - 0.01 * diff(ab)
    ab
}

stage2_prepare <- function(x, anchors, h, seed = 123) {
    state <- stage2_rng()
    on.exit(stage2_restore_rng(state))
    first <- tryCatch(stage2_job(seed, function() {
        raw <- stage2_routine(x)
        data <- rep(raw, times = ceiling(250 / length(raw))) - 0
        work <- stage2_working_data(data, refineR:::findRoundingBase(data))
        stage2_first_election(work$qData, stage2_first_window(work$qData), 24, anchors, h, 24L)
    }), error = function(e) stage2_empty_election(paste("prepare", conditionMessage(e)), 24L))
    second <- stage2_rethreshold(first, 28L)
    list(K24 = first, K28 = second, x = x, anchors = anchors, h = h, seed = seed)
}

stage2_trace <- function() {
    data.frame(phase = character(), pass = integer(), lambda = double(),
               coarse = integer(), fine = integer(), stringsAsFactors = FALSE)
}

stage2_track <- function(x, ab, mStart, ctx, lambda = NULL, initial = FALSE) {
    peak <- stage2_guided_peak(x, ab, mStart, ctx$election, lambda = lambda, initial = initial)
    ctx$trace <- rbind(ctx$trace, data.frame(phase = if (is.null(lambda)) "raw" else "transformed",
        pass = ctx$pass, lambda = if (is.null(lambda)) NA_real_ else lambda,
        coarse = as.integer(peak$coarse), fine = as.integer(peak$fine), stringsAsFactors = FALSE))
    peak
}

# Only the peak picker is replaced in this private copy. estimateAB's own
# iterative expansion and clipping of both raw intervals remain unchanged.
stage2_estimate_ab <- function(x, ctx) {
    select_window <- refineR:::estimateAB
    scope <- new.env(parent = environment(select_window))
    scope$findMainPeak <- function(x, ab, mStart, withHeight = FALSE, prevPeak = NULL) {
        initial <- !ctx$first_peak_seen
        ctx$first_peak_seen <- TRUE
        stage2_track(x, ab, mStart, ctx, initial = initial)
    }
    environment(select_window) <- scope
    select_window(x)
}

# The lambda is passed explicitly to the peak picker. The width equations
# below are those of Tatjana Ammer in refineR::defineSearchRegions.
stage2_regions <- function(x, lambdaVec, roundingBase, abEst, ctx) {
    if (!ctx$peak) return(refineR:::defineSearchRegions(x, lambdaVec, roundingBase, abEst))
    work <- stage2_working_data(x, roundingBase)
    qData <- work$qData
    if (is.null(abEst)) abEst <- stage2_estimate_ab(qData, ctx)
    qData <- qData[qData >= abEst$abSearchReg[1L] & qData <= abEst$abSearchReg[2L]]
    muEst <- sigmaEst <- matrix(nrow = length(lambdaVec), ncol = 3L)
    densM <- min(48, max(24, ceiling(50 - (1/10) * work$n / 1000)))
    for (i in seq_along(lambdaVec)) {
        lambda <- lambdaVec[i]
        transformed <- suppressWarnings(refineR::BoxCox(qData, lambda))
        transformed <- transformed[is.finite(transformed)]
        abTr <- range(transformed)
        span <- diff(abTr)
        abTr <- c(abTr[1L] - 0.1 * span, abTr[2L] + 0.1 * span)
        main <- stage2_track(transformed, abTr, densM, ctx, lambda)
        dens <- main$Dens
        mode <- main$modEst
        steps <- seq(0.5, 0.95, by = 0.05)
        levels <- steps * dens$y[main$peakInd]
        fractions <- widthsL <- widthsR <- NULL
        for (j in seq_along(levels)) {
            left <- which(dens$x < mode & dens$y <= levels[j])
            right <- which(dens$x > mode & dens$y <= levels[j])
            if (length(left) && length(right)) {
                widthsL <- c(widthsL, mode - max(dens$x[left]))
                widthsR <- c(widthsR, min(dens$x[right]) - mode)
                fractions <- c(fractions, steps[j])
            }
        }
        if (!length(fractions)) {
            # Hard-bound arms supply their own parameter intervals.
            if (ctx$regions) next
            stop("regions: no usable routine peak widths", call. = FALSE)
        }
        centers <- apply(cbind(mode - widthsL, mode + widthsR), 1L, mean)
        muRange <- range(centers, mode)
        muEst[i, ] <- c(lambda, muRange[1L] - 0.5 * diff(muRange),
                                  muRange[2L] + 0.5 * diff(muRange))
        scales <- pmin(widthsL, widthsR) / sqrt((-2) * log(fractions))
        sigRange <- range(scales)
        sigmaEst[i, ] <- c(lambda, max(0, sigRange[1L] - 2.5 * diff(sigRange)),
                                     sigRange[2L] + diff(sigRange))
    }
    list(abEst = abEst, muEst = muEst, sigmaEst = sigmaEst)
}

stage2_valid_fit <- function(fit) {
    if (!inherits(fit, "RWDRI")) return(FALSE)
    parameters <- unlist(fit[c("Mu", "Sigma", "Lambda", "Shift")], use.names = FALSE)
    length(parameters) == 4L && all(is.finite(parameters)) && fit$Sigma > 0 &&
        (is.null(fit$Status) || identical(as.character(fit$Status), "ResultFound"))
}

stage2_guided <- function(x, anchors, seed, arm, election) {
    stage2_job(seed, function() {
        ctx <- new.env(parent = emptyenv())
        ctx$peak <- arm %in% c("peak", "full")
        ctx$starts <- arm %in% c("start", "full")
        ctx$regions <- arm %in% c("region", "full")
        ctx$election <- election
        ctx$first_peak_seen <- FALSE
        ctx$trace <- stage2_trace()
        step <- "initialization"
        tryCatch({
            raw <- stage2_routine(x)
            data <- rep(raw, times = ceiling(250 / length(raw))) - 0
            rb <- refineR:::findRoundingBase(data)
            ctx$quartiles <- stats::quantile(anchors, c(0.25, 0.5, 0.75), names = FALSE, type = 7)
            lambda <- (1/12 * (0:12))^1.8170595
            best <- c(NA, NA, NA, NA, 1e9, NA)
            ab <- NULL
            for (pass in 1:2) {
                ctx$pass <- pass
                step <- paste0("pass", pass, "_regions")
                regions <- stage2_regions(data, lambda, rb, ab, ctx)
                if (pass == 1L) {
                    step <- "histogram"
                    ab <- regions$abEst
                    hist <- refineR:::generateHistData(data, ab$abHist, rb)
                }
                step <- paste0("pass", pass, "_grid")
                best <- stage2_test_param(lambda, best, data, hist, regions, 7, 0.01, 0.1, ctx)
                if (pass == 1L) {
                    if (!is.finite(best[1L])) stop("no winning first-pass lambda")
                    idx <- min(length(lambda)-2, max(3, which.min(abs(best[1L]-lambda))))
                    lambda <- unlist(lapply((idx-2):(idx+1), function(j) {
                        seq(lambda[j], lambda[j+1], length.out = 5)[2:4]
                    }), use.names = FALSE)
                }
            }
            fit <- list(Data = raw, Method = "refineR", PkgVersion = utils::packageVersion("refineR"),
                        Model = "BoxCox", NBootstrap = 0, Lambda = best[1L], Mu = best[2L],
                        Sigma = best[3L], P = best[4L], Shift = 0, Cost = best[5L],
                        abOr = hist$abOr, roundingBase = rb, rf = best[6L])
            class(fit) <- "RWDRI"
            if (!stage2_valid_fit(fit)) stop("invalid guided model")
            list(fit = fit, reason = "guided", trace = ctx$trace)
        }, error = function(e) list(fit = NULL, reason = paste(step, conditionMessage(e)),
                                    trace = ctx$trace))
    })
}

stage2_baseline <- function(x, seed) {
    error <- NULL
    fit <- tryCatch(refineR::findRI(Data = x, model = "BoxCox", NBootstrap = 0, seed = seed),
        error = function(e) { error <<- conditionMessage(e); NULL })
    status <- if (stage2_valid_fit(fit)) "ResultFound" else "fit_failed"
    list(fit = fit, status = status, fallback = FALSE, reason = if (is.null(error)) "baseline" else error,
         baseline_status = status, election = NULL, peak_trace = stage2_trace())
}

stage2_fit <- function(x, anchors, h, seed = 123, K = 24L,
                       arm = c("full", "baseline", "peak", "start", "region"),
                       prepared = NULL, baseline = NULL) {
    arm <- match.arg(arm)
    if (arm == "baseline") return(stage2_baseline(x, seed))
    if (!(length(K) == 1L && K %in% c(24L, 28L))) stop("K must be 24 or 28")
    if (is.null(prepared)) prepared <- stage2_prepare(x, anchors, h, seed)
    if (!identical(prepared$x, x) || !identical(prepared$anchors, anchors) ||
        !identical(prepared$h, h) || !identical(as.numeric(prepared$seed), as.numeric(seed))) {
        stop("prepared election belongs to different inputs", call. = FALSE)
    }
    election <- prepared[[paste0("K", K)]]
    state <- stage2_rng()
    trace <- stage2_trace()
    reason <- election$reason
    if (isTRUE(election$ok)) {
        attempt <- tryCatch(stage2_guided(x, anchors, seed, arm, election),
            error = function(e) list(fit = NULL, reason = paste("guided", conditionMessage(e)), trace = trace))
        trace <- attempt$trace
        reason <- attempt$reason
        if (stage2_valid_fit(attempt$fit)) {
            return(list(fit = attempt$fit, status = "ResultFound", fallback = FALSE, reason = reason,
                        baseline_status = NA_character_, election = election, peak_trace = trace))
        }
    }
    stage2_restore_rng(state)
    if (is.null(baseline)) baseline <- stage2_baseline(x, seed)
    baseline$fallback <- TRUE
    baseline$baseline_status <- baseline$status
    baseline$reason <- reason
    baseline$election <- election
    baseline$peak_trace <- trace
    baseline
}

# Evaluate a selection pair on the very same first density; K influences only
# clarity. A passing K28 and K24 use identical search operations and fallback.
stage2_fit_pair <- function(x, anchors, h, seed = 123) {
    state <- stage2_rng()
    baseline <- stage2_baseline(x, seed)
    after_baseline <- stage2_rng()
    on.exit(stage2_restore_rng(after_baseline))
    stage2_restore_rng(state)
    prepared <- stage2_prepare(x, anchors, h, seed)
    k24 <- stage2_fit(x, anchors, h, seed, 24L, "full", prepared, baseline)
    if (isTRUE(prepared$K28$ok)) {
        stopifnot(isTRUE(prepared$K24$ok))
        k28 <- k24
        k28$election <- prepared$K28
    } else {
        stage2_restore_rng(state)
        k28 <- stage2_fit(x, anchors, h, seed, 28L, "full", prepared, baseline)
    }
    list(baseline = baseline, K24 = k24, K28 = k28)
}
