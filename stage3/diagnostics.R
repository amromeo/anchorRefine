# Diagnostics run after the assigned fits. Their scores never select study weights.
stage3_identity <- function(j, metric, variant, observed, reference, required = TRUE) {
    ok <- is.finite(observed) && is.finite(reference) &&
        abs(observed - reference) <= 1e-10 * max(1, abs(reference))
    data.frame(j = as.integer(j), metric, variant, observed, reference, passed = ok,
               required, stringsAsFactors = FALSE)
}

stage3_algebra_checks <- function(j) {
    rows <- list()
    compare <- function(name, variant, value, reference) {
        rows[[length(rows) + 1L]] <<- stage3_identity(j, name, variant, value, reference)
    }
    # Check the normal-count algebra using two different selections, a zero
    # residual, a nonzero residual, and nonunit peak and tail penalties.
    means <- c(22, 35, 28, 42, 50)
    data <- c(22, 34, 27, 45, 48)
    for (selected in list(1:3, c(1L, 3L, 4L, 5L))) {
        k <- length(selected)
        m <- means[selected]
        d <- data[selected]
        ratio <- .78 * .91 * .84
        residual <- (d - m)^2 / (2 * m)
        summands <- log(m / (2*pi)) / 2 - residual + log(ratio)
        native <- -sum(summands) / sqrt(k)
        direct <- -sum(dnorm(d, mean = m, sd = sqrt(m), log = TRUE) +
                       log(m) + log(ratio)) / sqrt(k)
        id <- paste0("k", k)
        compare("normal_count_score", id, native, direct)
        copies <- 3L
        copied <- -sum(rep(summands, copies)) /
            (sqrt(k * copies) * sqrt(length(means) * copies))
        compare("overlap_replication", id, copied, native / sqrt(length(means)))
        doubled <- .5 * log(2 * m / (2*pi)) - (2*d - 2*m)^2 / (4*m) + log(ratio)
        compare("fixed_mask_doubled_N", id, sum(doubled - summands),
                k * .5 * log(2) - sum(residual))
    }
    # Integrate the density in original units, independently of the anchor
    # CDF calculation, including a rounded bin crossing zero.
    for (lambda in c(0, .5, 1)) {
        fit <- list(Mu = if (lambda == 0) log(2) else .3, Sigma = .8,
                    Lambda = lambda, Shift = 0)
        label <- paste0("lambda", lambda)
        lower <- if (lambda == 0) -Inf else -1/lambda
        survival <- pnorm(lower, fit$Mu, fit$Sigma, lower.tail = FALSE)
        density <- function(x) {
            result <- numeric(length(x))
            use <- is.finite(x) & x > 0
            v <- x[use]
            y <- if (lambda == 0) log(v) else expm1(lambda * log(v)) / lambda
            result[use] <- exp(dnorm(y, fit$Mu, fit$Sigma, log = TRUE) +
                (lambda-1) * log(v) - log(survival))
            result
        }
        quad <- function(lo, hi) integrate(density, lo, hi, rel.tol = 5e-13,
            abs.tol = 1e-14, subdivisions = 1000L)$value
        compare("normalized_original_density", label, quad(0, Inf), 1)
        for (x in c(0, 1, 2.5)) {
            h <- .5
            q <- quad(max(0, x - h/2), x + h/2)
            est <- stage3_loglik(fit, rep(x, 40L), h)
            compare("rounded_bin_quadrature", paste(label, x, sep = "/"), est, log(q))
        }
        for (c_units in c(.1, 10)) {
            map <- function(fit) {
                b <- c_units^lambda
                d <- if (lambda == 0) log(c_units) else expm1(lambda*log(c_units))/lambda
                fit$Mu <- b*fit$Mu + d
                fit$Sigma <- b*fit$Sigma
                fit$Shift <- c_units*fit$Shift
                fit
            }
            reference <- fit
            reference$Mu <- reference$Mu + .3
            reference$Sigma <- reference$Sigma * 1.2
            for (h in c(0, .5)) {
                x <- rep(c(.5, 1, 1.5, 2, 2.5), 8L)
                old <- stage3_loglik(reference,x,h) - stage3_loglik(fit,x,h)
                new <- stage3_loglik(map(reference),x*c_units,h*c_units) -
                    stage3_loglik(map(fit),x*c_units,h*c_units)
                compare("mapped_relative_anchor_score", paste(label,c_units,h,sep="/"),new,old)
            }
            counts <- function(edges, model) {
                y <- refineR::BoxCox(edges - model$Shift, model$Lambda)
                norm <- diff(pnorm(range(y), model$Mu, model$Sigma))
                lookup <- stage3_lookup
                lookup_cdf <- refineR:::pnormApprox(y, pNormVal = lookup$val,
                    mean = model$Mu, oneOverSd = 1/model$Sigma, oneOverH = 1/lookup$h)
                1000 * diff(lookup_cdf) / norm
            }
            edges <- c(.25, .5, .75, 1.25, 2, 3, 4)
            expected <- counts(edges, fit)
            converted <- counts(c_units * edges, map(fit))
            for (i in seq_along(expected)) compare("mapped_trial_count",
                paste(label,c_units,i,sep="/"),converted[i],expected[i])
            exact <- stage3_loglik(fit, rep(1.5,40L), 0)
            compare("exact_original_density", paste(label,c_units,sep="/"), exact, log(density(1.5)))
            for (t in c(0, .25, .5, .75, 1)) {
                blend <- function(f, anchor) {
                    f$Mu <- (1-t)*f$Mu + t*anchor$Mu
                    f$Sigma <- f$Sigma * exp(t*log(anchor$Sigma/f$Sigma))
                    f
                }
                original <- map(blend(fit, reference))
                converted <- blend(map(fit), map(reference))
                for (field in c("Mu","Sigma")) {
                    compare("mapped_postfit_blend",paste(label,c_units,t,field,sep="/"),
                        converted[[field]], original[[field]])
                }
            }
        }
        impossible <- stage3_loglik(fit, rep(-1,40L), .5)
        compare("structural_zero_support", label, as.numeric(identical(impossible,-Inf)),1)
    }
    do.call(rbind, rows)
}

stage3_original_profile <- function(j, x, seed, parent) {
    valid <- stage2_valid_fit(parent$fit)
    path <- if (isTRUE(parent$fallback)) "unguided" else "guided"
    coverage <- stage3_identity(j, "profile_available", path, as.integer(valid),
                                as.integer(valid))
    if (!valid) return(coverage)
    hist <- stage3_histogram(x, seed, parent)
    fit <- parent$fit
    step <- .002
    lookup <- list(h = step, val = pnorm(seq(-5.2, 5.2 + step, by = step)))
    native <- refineR:::calculateCostHist(fit$Lambda, fit$Mu, fit$Sigma, hist,
                                         .01, .1, lookup)
    profile <- stage3_profile(hist, fit$Lambda, fit$Mu, fit$Sigma)
    scores <- c(native[5], native[4], native[6])
    derived <- as.numeric(profile[1L, c("C_H", "P", "rf")])
    identities <- lapply(seq_along(scores), function(i)
        stage3_identity(j, "native_profile", c("C_H","P","rf")[i], derived[i], scores[i]))
    # Check mapped histogram edges with transformed parent parameters. Use the
    # same observed counts and same tail borders on both sides of the comparison.
    for (factor in c(.1, 10)) {
        mapped <- hist
        mapped$breakL <- factor * hist$breakL
        mapped$breakR <- factor * hist$breakR
        mapped$mids <- factor * hist$mids
        mapped$abOr <- factor * hist$abOr
        mapped$fullHist$breaks <- factor * hist$fullHist$breaks
        mapped$fullHist$mids <- factor * hist$fullHist$mids
        lambda <- fit$Lambda
        b <- factor^lambda
        shift <- if (abs(lambda) < 1e-20) log(factor) else expm1(lambda*log(factor))/lambda
        # Peak masks at exact cutoffs and the source's absolute floors can
        # change the P search on real cases. Record these sensitivity results.
        test <- stage3_profile(mapped, lambda, b*fit$Mu+shift,b*fit$Sigma)
        for (field in c("C_H","P","rf","k")) {
            identities[[length(identities)+1L]] <- stage3_identity(j,
                "mapped_native_profile", paste(factor,field,sep="/"),
                test[1L,field], profile[1L,field], required = FALSE)
        }
    }
    do.call(rbind, c(list(coverage), identities))
}

stage3_sensitivity_template <- function() {
    data.frame(j = integer(), N = integer(), arm = character(), w = numeric(),
        variant = character(), status = character(), branch = character(),
        B = numeric(), overlap = numeric(), k = numeric(), C_H = numeric(),
        A = numeric(), J = numeric(), lower = numeric(), upper = numeric(),
        base_lower = numeric(), base_upper = numeric(), endpoint_delta_lower = numeric(),
        endpoint_delta_upper = numeric(), stringsAsFactors = FALSE)
}

stage3_sensitivity_limits <- function(obj) {
    if (is.null(obj) || !stage2_valid_fit(obj$fit)) return(c(NA_real_,NA_real_))
    ans <- tryCatch(refineR::getRI(obj$fit, RIperc = c(.025,.975))$PointEst,
                    error = function(e) c(NA_real_,NA_real_))
    if (length(ans) == 2L) as.numeric(ans) else c(NA_real_,NA_real_)
}

stage3_sensitivity <- function(row, x, anchors, h, seed, parent, primary, post) {
    weights <- c(0,1,10,100,1000,10000)
    blends <- c(0,.25,.5,.75,1)
    keys <- function(v) format(v, scientific = FALSE, trim = TRUE, digits = 15)
    pkey <- function(v) as.character(v)
    if (is.null(post)) {
        est <- if (stage2_valid_fit(parent$fit)) stage3_post_estimate(parent, anchors, h)
        post <- setNames(lapply(blends, function(t) stage3_post(parent,anchors,h,t,est)),
                         pkey(blends))
    }
    results <- list()
    for (variant in c("units_0.1","units_10","width_0.5","width_2","duplicate_2")) {
        factor <- switch(variant, units_0.1 = .1, units_10 = 10, 1)
        xvar <- if (variant == "duplicate_2") rep(x,2L) else x*factor
        avar <- anchors*factor
        hvar <- h*factor
        g <- switch(variant, width_0.5 = .5, width_2 = 2, 1)
        parent_var <- if (startsWith(variant, "width")) parent else
            stage2_selected_fit(xvar,avar,hvar,seed)
        fits <- stage3_primary_many(xvar,avar,hvar,seed,parent_var,weights,hist_factor = g)
        add <- function(arm, weight, obj, base) {
            lim <- stage3_sensitivity_limits(obj)/factor
            base_lim <- stage3_sensitivity_limits(base)
            details <- obj$stage3
            num <- function(name) {
                v <- details[[name]]
                if (length(v) == 1L && is.numeric(v)) as.numeric(v) else NA_real_
            }
            branch <- if (length(details$branch) == 1L) details$branch else obj$reason
            if (length(branch) != 1L) branch <- "unavailable"
            if (startsWith(variant,"width") && weight == 0) branch <- "frozen_weight_zero"
            results[[length(results) + 1L]] <<- data.frame(j = row$j, N = row$N,
                arm, w = weight, variant, status = obj$status, branch = as.character(branch),
                B = num("B"), overlap = num("overlap"), k = num("k"), C_H = num("C_H"),
                A = num("A"), J = num("J"), lower = lim[1L], upper = lim[2L],
                base_lower = base_lim[1L], base_upper = base_lim[2L],
                endpoint_delta_lower = lim[1L]-base_lim[1L], endpoint_delta_upper = lim[2L]-base_lim[2L],
                stringsAsFactors = FALSE)
        }
        for (w in weights) add("primary",w,fits[[paste0("w",keys(w))]],primary[[keys(w)]])
        if (startsWith(variant,"units")) {
            est <- if (stage2_valid_fit(parent_var$fit)) stage3_post_estimate(parent_var,avar,hvar)
            for (t in blends) {
                updated <- stage3_post(parent_var,avar,hvar,t,est)
                add("postfit",t,updated,post[[pkey(t)]])
            }
        }
    }
    do.call(rbind, results)
}

stage3_diagnostics <- function(phase, row, x, anchors, h, seed, parent, primary, post = NULL) {
    rng <- stage2_rng()
    on.exit(stage2_restore_rng(rng))
    ids <- stage3_identity(0L,"","",0,0)[FALSE,]
    extra <- stage3_sensitivity_template()
    if (phase == "influence") {
        ids <- stage3_original_profile(row$j, x, seed, parent)
        if (row$j == 1L) ids <- rbind(ids, stage3_algebra_checks(row$j))
    } else if (row$replicate == 1L) {
        extra <- stage3_sensitivity(row, x, anchors, h, seed, parent, primary, post)
    }
    list(identities = ids, sensitivity = extra)
}
