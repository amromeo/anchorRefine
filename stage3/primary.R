# The primary arm derives its grid traversal from Tatjana Ammer's testParam
# in refineR 2.0.0 (GPL >= 3). The anchorRefine changes use GPL-3.
# The peak selection, search regions and histogram are those of frozen Stage 2.

stage3_grid_weights <- c(0, 1, 10, 100, 1000, 10000)

stage3_load_engine <- function() {
    if (is.loaded("stage3_hist_profiles")) return(invisible(NULL))
    path <- Sys.getenv("STAGE3_ENGINE", unset = Sys.getenv("STAGE3_ENGINE_SO"))
    if (!nzchar(path) || !file.exists(path)) stop("Missing compiled Stage 3 histogram engine")
    dyn.load(path)
    stopifnot(is.loaded("stage3_hist_profiles"))
}

stage3_lookup <- local({
    step <- 0.002
    list(h = step, val = pnorm(seq(-5.2, 5.2 + step, by = step)))
})

stage3_profile <- function(hist, lambda, mu, sigma) {
    stopifnot(length(lambda) == 1L, length(mu) == length(sigma))
    stage3_load_engine()
    result <- .Call("stage3_hist_profiles", as.double(lambda), as.double(mu),
                    as.double(sigma), hist, stage3_lookup)
    colnames(result) <- c("P", "C_H", "rf", "k")
    result
}

# The interior fine cells and two exterior border entries stay at the same
# locations when testing different rolling-window widths.
stage3_rebin_hist <- function(hist, g) {
    stopifnot(length(g) == 1L, is.finite(g), g > 0)
    fine <- hist$fullHist
    M <- length(fine$counts) - 2L
    width <- min(M, max(1L, round(g * hist$overlapFactor)))
    if (width == hist$overlapFactor) return(hist)
    stopifnot(M >= 1L, length(fine$breaks) == M + 3L)
    starts <- seq_len(M - width + 1L)
    breaks <- fine$breaks[2L:(M + 2L)]
    cumulative <- c(0, cumsum(as.double(fine$counts[2L:(M + 1L)])))
    observed <- cumulative[starts + width] - cumulative[starts]
    hist$counts <- c(fine$counts[1L], observed, fine$counts[M + 2L])
    hist$breakL <- c(fine$breaks[1L], breaks[starts], breaks[M + 1L])
    hist$breakR <- c(breaks[1L], breaks[starts + width], fine$breaks[M + 3L])
    hist$mids <- (hist$breakL + hist$breakR) / 2
    hist$NBins <- max(1L, round(length(starts) / width))
    hist$overlapFactor <- width
    hist
}

stage3_context <- function(election, pass, trace = stage2_trace()) {
    ctx <- new.env(parent = emptyenv())
    ctx$peak <- TRUE
    ctx$starts <- FALSE
    ctx$regions <- FALSE
    ctx$election <- election
    ctx$first_peak_seen <- pass != 1L
    ctx$trace <- trace
    ctx$pass <- as.integer(pass)
    ctx
}

stage3_initial_lambda <- function() (1 / 12 * (0:12))^1.8170595

stage3_refined_lambda <- function(lambda, index) {
    unlist(lapply((index - 2L):(index + 1L), function(j) {
        seq(lambda[j], lambda[j + 1L], length.out = 5L)[2:4]
    }), use.names = FALSE)
}

stage3_first_pass <- function(x, parent) {
    raw <- stage2_routine(x)
    data <- rep(raw, times = ceiling(250 / length(raw))) - 0
    rounding <- refineR:::findRoundingBase(data)
    ctx <- stage3_context(parent$election, 1L)
    regions <- stage2_regions(data, stage3_initial_lambda(), rounding, NULL, ctx)
    hist <- refineR:::generateHistData(data, regions$abEst$abHist, rounding)
    parent_trace <- parent$peak_trace[parent$peak_trace$pass == 1L, , drop = FALSE]
    if (!identical(ctx$trace, parent_trace) || !identical(hist$abOr, parent$fit$abOr) ||
        !identical(rounding, parent$fit$roundingBase))
        stop("Stage 2 first-pass peak trace or histogram window did not replay")
    list(regions = regions, data = data, rounding = rounding, hist = hist, trace = ctx$trace)
}

stage3_histogram <- function(x, seed, parent) {
    if (!stage2_valid_fit(parent$fit) || isTRUE(parent$fallback)) return(NULL)
    state <- stage2_rng()
    on.exit(stage2_restore_rng(state))
    stage2_job(seed, function() stage3_first_pass(x, parent)$hist)
}

# Inspect the original guided path just as it enters its first grid.
# The restart exits that invocation without fitting a second parent.
stage3_parent_histogram <- function(x, anchors, seed, parent) {
    state <- stage2_rng()
    on.exit(stage2_restore_rng(state))
    guided <- stage2_guided
    scope <- new.env(parent = environment(guided))
    scope$stage2_job <- function(seed, work) {
        stage2_job(seed, function() {
            withRestarts(work(), stage3_capture_histogram = function(value) value)
        })
    }
    scope$stage2_test_param <- function(lambdaVec, bestParam, Data, HistData, ...) {
        invokeRestart("stage3_capture_histogram", HistData)
    }
    environment(guided) <- scope
    hist <- guided(x, anchors, seed, "peak", parent$election)
    stopifnot(!is.null(hist$counts), identical(hist$abOr, parent$fit$abOr))
    hist
}

stage3_new_trial_store <- function(hist, anchors, h, reference) {
    store <- new.env(parent = emptyenv())
    store$hist <- hist
    store$B <- length(hist$counts)
    store$anchors <- anchors
    store$increment <- h
    store$reference <- reference
    store$lambdas <- new.env(hash = TRUE, parent = emptyenv())
    store
}

stage3_trial_rows <- function(store, lambda, mu, sigma) {
    lambda_key <- sprintf("%a", lambda)
    info <- store$lambdas[[lambda_key]]
    if (is.null(info)) {
        info <- list(anchors = stage3_anchor_prepare(store$anchors, store$increment, lambda, 0),
                     cache = new.env(hash = TRUE, parent = emptyenv()))
        store$lambdas[[lambda_key]] <- info
    }
    # Keep Mu as the outer loop, exactly as in calculateCostHist.
    means <- rep(mu, each = length(sigma))
    spreads <- rep(sigma, times = length(mu))
    keys <- paste(sprintf("%a", means), sprintf("%a", spreads), sep = "/")
    rows <- mget(keys, envir = info$cache, ifnotfound = list(NULL), inherits = FALSE)
    missing <- which(vapply(rows, is.null, logical(1)))
    if (length(missing)) {
        positions <- missing[!duplicated(keys[missing])]
        m <- means[positions]
        s <- spreads[positions]
        profile <- stage3_profile(store$hist, lambda, m, s)
        eligible <- which(is.finite(profile[, "C_H"]))
        A <- rep(Inf, length(m))
        if (length(eligible)) {
            mean_log_q <- stage3_anchor_scores(info$anchors, m[eligible], s[eligible])
            valid <- is.finite(mean_log_q)
            A[eligible[valid]] <- store$reference - mean_log_q[valid]
        }
        data <- cbind(lambda = lambda, mu = m, sigma = s, profile, A = A)
        for (i in seq_along(positions)) assign(keys[positions[i]], data[i, ], envir = info$cache)
        rows[missing] <- mget(keys[missing], envir = info$cache, inherits = FALSE)
    }
    do.call(rbind, unname(rows))
}

# Per shape, A is constant over P and rf. The kernel profiles those two
# parameters using the native cost; every competing shape receives its own
# A before the grid winner, refinement center or winning lambda is selected.
stage3_search_pass <- function(lambda, regions, store, weight, best = NULL) {
    root_B <- sqrt(store$B)
    for (i in seq_along(lambda)) {
        mu <- seq(regions$muEst[i,2L], regions$muEst[i,3L], length.out = 9L)
        sigma <- seq(regions$sigmaEst[i,2L], regions$sigmaEst[i,3L], length.out = 13L)
        tried_mu <- tried_sigma <- NULL
        lambda_best <- NULL
        for (iteration in seq_len(7L)) {
            # Upstream updates the tried nodes before replacing the current grid.
            tried_mu <- sort(unique(c(tried_mu, mu)), method = "quick")
            tried_sigma <- sort(unique(c(tried_sigma, sigma)), method = "quick")
            if (iteration > 1L) {
                if (is.null(lambda_best)) break
                mu <- refineR:::optimizeGrid(lambda_best[["mu"]], tried_mu,
                                               iteration, sigmLimit = FALSE)
                sigma <- refineR:::optimizeGrid(lambda_best[["sigma"]], tried_sigma,
                                                  iteration, sigmLimit = TRUE)
            }
            rows <- stage3_trial_rows(store, lambda[i], mu, sigma)
            objective <- rows[, "C_H"] / root_B + weight * rows[, "A"]
            if (!any(is.finite(objective))) next
            row <- which.min(replace(objective, !is.finite(objective), Inf))
            score <- objective[row]
            if (is.null(lambda_best) || score < lambda_best[["J"]]) {
                lambda_best <- c(rows[row, ], J = unname(score))
                if (is.null(best) || score < best[["J"]]) best <- lambda_best
            }
        }
    }
    best
}

stage3_details <- function(weight, branch, B = NA_integer_, overlap = NA_integer_,
                           hist_hash = NA_character_, tuple = NULL, parent = NULL) {
    value <- function(x, name) if (is.null(x)) NA_real_ else unname(x[[name]])
    list(weight = weight, branch = branch, B = B, overlap = overlap, hist_hash = hist_hash,
         C_H = value(tuple, "C_H"), A = value(tuple, "A"), J = value(tuple, "J"),
         k = value(tuple, "k"), parent_C_H = value(parent, "C_H"),
         parent_k = value(parent, "k"), parent_P = value(parent, "P"),
         parent_rf = value(parent, "rf"))
}

stage3_primary_many <- function(x, anchors, h, seed, parent, weights = stage3_grid_weights,
                                hist_factor = 1) {
    stopifnot(length(weights) > 0L, !anyDuplicated(weights),
              all(weights %in% stage3_grid_weights))
    output <- setNames(rep(list(parent), length(weights)), paste0("w", weights))
    positive <- which(weights > 0)
    if (!length(positive)) return(output)
    state <- stage2_rng()
    on.exit(stage2_restore_rng(state))
    inactive <- if (!stage2_valid_fit(parent$fit)) "invalid_parent" else if (isTRUE(parent$fallback))
        "inherited_fallback" else NULL
    if (is.null(inactive)) {
        reference <- stage3_loglik(parent$fit, anchors, h)
        inactive <- if (is.na(reference)) "unresolved_reference" else if (!is.finite(reference))
            "zero_reference_mass" else NULL
    }
    if (!is.null(inactive)) {
        for (j in positive) {
            output[[j]]$stage3 <- stage3_details(weights[j], inactive)
            if (inactive %in% c("zero_reference_mass", "unresolved_reference")) {
                output[[j]]$fallback <- TRUE
                output[[j]]$reason <- inactive
            }
        }
        return(output)
    }

    native_hist <- stage3_parent_histogram(x, anchors, seed, parent)
    stage2_job(seed, function() {
        first <- stage3_first_pass(x, parent)
        if (!identical(first$hist, native_hist))
            stop("Frozen parent and weighted first-pass histogram edges or counts differ")
        hist <- stage3_rebin_hist(first$hist, hist_factor)
        store <- stage3_new_trial_store(hist, anchors, h, reference)
        hash <- digest::digest(hist, algo = "sha256")
        original <- parent$fit
        profile <- stage3_profile(hist, original$Lambda, original$Mu, original$Sigma)[1L, ]
        parent_tuple <- NULL
        if (is.finite(profile[["C_H"]])) {
            parent_tuple <- c(lambda = original$Lambda, mu = original$Mu, sigma = original$Sigma,
                              profile, A = 0, J = unname(profile["C_H"]) / sqrt(store$B))
        }
        if (identical(hist, native_hist)) {
            # The reference is the exact saved native tuple. A cross-language
            # summation difference alone must never become a scientific update.
            if (is.null(parent_tuple) ||
                abs(profile[["C_H"]] - original$Cost) > 1e-10 * max(1, abs(original$Cost)))
                stop("Native histogram profile does not reproduce the frozen parent cost")
            parent_tuple[c("C_H", "P", "rf", "J")] <-
                c(original$Cost, original$P, original$rf, original$Cost / sqrt(store$B))
        }

        second_state <- stage2_rng()
        refined <- new.env(parent = emptyenv())
        lambda <- stage3_initial_lambda()
        for (j in positive) {
            w <- weights[j]
            branch <- "weighted"
            reason <- "weighted"
            trace <- first$trace
            best <- tryCatch({
                first_best <- stage3_search_pass(lambda, first$regions, store, w)
                if (is.null(first_best)) stop("pass1_grid: no admissible model")
                index <- min(length(lambda) - 2L, max(3L, which.min(abs(lambda - first_best["lambda"]))))
                key <- as.character(index)
                second <- refined[[key]]
                if (is.null(second)) {
                    stage2_restore_rng(second_state)
                    ctx <- stage3_context(parent$election, 2L, first$trace)
                    next_lambda <- stage3_refined_lambda(lambda, index)
                    regions <- stage2_regions(first$data, next_lambda, first$rounding,
                                              first$regions$abEst, ctx)
                    second <- list(regions = regions, lambda = next_lambda, trace = ctx$trace)
                    refined[[key]] <- second
                }
                trace <- second$trace
                stage3_search_pass(second$lambda, second$regions, store, w, first_best)
            }, error = function(e) {
                # Numerical/search failure is distinct from an ordinary tie.
                reason <<- paste("weighted search:", conditionMessage(e))
                NULL
            })
            if (is.null(best)) {
                branch <- "search_fallback"
                output[[j]]$fallback <- TRUE
            } else {
                same_shape <- !is.null(parent_tuple) &&
                    all(best[c("lambda", "mu", "sigma")] == parent_tuple[c("lambda", "mu", "sigma")])
                if (!is.null(parent_tuple) && (same_shape || best[["J"]] >= parent_tuple[["J"]])) {
                    best <- parent_tuple
                    branch <- "retained_parent"
                    reason <- branch
                }
                fit <- original
                if (branch != "retained_parent" || !identical(hist, native_hist)) {
                    fit[c("Lambda", "Mu", "Sigma", "P", "Cost", "rf")] <-
                        as.list(unname(best[c("lambda", "mu", "sigma", "P", "C_H", "rf")]))
                }
                stopifnot(stage2_valid_fit(fit))
                output[[j]]$fit <- fit
                output[[j]]$peak_trace <- trace
            }
            tuple <- if (is.null(best)) parent_tuple else best
            output[[j]]$reason <- reason
            output[[j]]$stage3 <- stage3_details(w, branch, store$B, hist$overlapFactor,
                                                  hash, tuple, parent_tuple)
        }
        output
    })
}

stage3_primary <- function(x, anchors, h, seed, parent = NULL, w, prepared = NULL,
                           baseline = NULL, hist_factor = 1) {
    if (w == 0) return(stage2_selected_fit(x, anchors, h, seed, prepared, baseline))
    if (is.null(parent)) parent <- stage2_selected_fit(x, anchors, h, seed, prepared, baseline)
    stage3_primary_many(x, anchors, h, seed, parent, w, hist_factor)[[1L]]
}
