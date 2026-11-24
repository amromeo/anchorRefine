# Reconstruct the read-only comparator table. Run at the repository root
# with the original RIbench 1.0.2 and digest libraries; see README.md.
args <- commandArgs(TRUE)
stopifnot(length(args) == 2L, packageVersion("RIbench") == "1.0.2")
src <- args[1L]
read <- function(path) read.csv(path, na.strings = c("", "NA"), stringsAsFactors = FALSE)
ref <- file.path("results", "stage1-45276858699")
input <- do.call(rbind, lapply(c("small", "large"), function(cohort)
    read(file.path(ref, cohort, "checks.csv.gz"))))
sets <- rbind(read("archive/c2/testsets.csv"), read("stage1/large/testsets.csv"))
sets <- sets[match(input$Index, sets$Index), ]
stopifnot(nrow(input) == 4320L, !anyDuplicated(input$Index), identical(input$Index, sets$Index),
          identical(input$ribench_hashcode, sets$HashCode))
meta <- input[, c("Index", "N", "Analyte", "Scenario", "fractionPathol", "routine_hash",
                  "anchor_hash", "ribench_hashcode", "anchor_seed")]
source_rows <- function(path, method, name) {
    df <- read(file.path(src, path))
    df <- df[df$benchmark == "RIbench" & df$method == method, ]
    ix <- match(df$Index, meta$Index)
    stopifnot(!anyNA(ix), !anyDuplicated(ix), all(df$dataset_id == paste0("r-", df$Index)),
              all(df$routine_hash == meta$routine_hash[ix]), all(df$anchor_hash == meta$anchor_hash[ix]),
              all(df$ribench_hashcode == meta$ribench_hashcode[ix]), all(df$n_anchor == 40L),
              all(df$anchor_seed == meta$anchor_seed[ix]), all(df$N == meta$N[ix]),
              all(df$Analyte == meta$Analyte[ix]), all(df$scenario == meta$Scenario[ix]),
              all(as.numeric(df$pathological_fraction) == meta$fractionPathol[ix]),
              all(df$technical == FALSE), all(df$report_status %in% c("reported", "declined")),
              all(df$report_status == ifelse(df$declined, "declined", "reported")),
              all(df$upper_probability == ifelse(df$Analyte == "CRP", .95, .975)),
              all(ifelse(df$Analyte == "CRP", is.na(df$lower_probability), df$lower_probability == .025)),
              all(df$max_components == if (method == "armB") 5 else 3),
              all(df$fitter_source_commit == "ec3dd35197759424d32a6a341320173e5db08c89"))
    data.frame(meta[ix, ], method = name, status = "returned", lower = df$lower, upper = df$upper,
               reported_status = ifelse(df$declined, "declined", "returned"),
               reported_lower = df$reported_lower, reported_upper = df$reported_upper)
}
baseline <- source_rows("anchoredRI-comparator.csv", "anchoredRI", "anchoredRI_improved")
large <- source_rows("armB-fits.csv", "armB", "taskE_armB")
stopifnot(nrow(baseline) == 4320L, nrow(large) == 1440L, all(large$N == 50000L))
diag <- do.call(rbind, lapply(list.files(file.path(src, "accuracy", "results", "diagnostics"),
    pattern = "^part-[0-9]+[.]csv$", full.names = TRUE), read))
diag <- diag[diag$stage == "small" & diag$method == "armB", ]
provenance <- read(file.path(src, "runtime-provenance.csv"))
provenance <- provenance[match(diag$dataset_id, provenance$key), ]
stopifnot(nrow(diag) == 2880L, !anyDuplicated(diag$Index), all(diag$dataset_id == provenance$key),
          all(!diag$technical), all(diag$reported == !diag$declined),
          all(provenance$run == 45257620744), all(provenance$runtime == "Actions"))
component_path <- "stage2/ribench/comparators/small-armB-selected.csv.gz"
if (dir.exists(file.path(src, "fits"))) {
    # Re-extract from the accepted per-Index RDS for a full source audit.
    component <- do.call(rbind, lapply(seq_len(nrow(diag)), function(i) {
        d <- diag[i, ]
        path <- file.path(src, "fits", paste0(d$dataset_id, ".rds"))
        stopifnot(digest::digest(file = path, algo = "sha256") == provenance$sha256[i])
        fit <- readRDS(path)
        model <- fit$models[[paste(d$transform, d$components)]]
        stopifnot(identical(fit$key, d$dataset_id), model$k == d$components, model$k <= 5L,
                  model$bic == min(vapply(fit$models, function(x) x$bic, numeric(1))))
        data.frame(Index = d$Index, routine_hash = fit$routine, anchor_hash = fit$anchor,
                   transform = model$transform, components = model$k, mu = model$p$mu[1L],
                   sigma = model$p$sigma[1L], shift = model$p$shift, lambda = model$p$lambda,
                   fit_sha256 = provenance$sha256[i])
    }))
    source("stage0/common.R")
    write_table(component, file.path(src, "small-armB-selected.csv"))
    if (file.exists(component_path))
        stopifnot(identical(read(component_path), read(file.path(src, "small-armB-selected.csv"))))
} else {
    component <- read(component_path)
}
small <- do.call(rbind, lapply(seq_len(nrow(diag)), function(i) {
    d <- diag[i, ]
    m <- meta[match(d$Index, meta$Index), ]
    p <- component[match(d$Index, component$Index), ]
    stopifnot(identical(p$fit_sha256, provenance$sha256[i]), identical(p$routine_hash, m$routine_hash),
              identical(p$anchor_hash, m$anchor_hash), d$Analyte == m$Analyte,
              d$scenario == m$Scenario, d$fraction == m$fractionPathol, d$transform == p$transform,
              d$components == p$components, d$transform %in% c("identity", "log", "shifted_log"))
    probs <- if (m$Analyte == "CRP") .95 else c(.025, .975)
    y <- p$mu + qnorm(probs) * p$sigma
    # Same measured-scale quantiles as the Task E v2_table export.
    limits <- if (p$transform == "identity") y + 1 else {
        stopifnot(p$lambda == 0)
        p$shift + exp(y)
    }
    limits <- if (length(limits) == 1L) c(NA_real_, limits) else limits
    stopifnot(isTRUE(all.equal(limits, c(d$lower, d$upper), tolerance = 2e-13)))
    data.frame(m, method = "taskE_armB", status = "returned", lower = limits[1L], upper = limits[2L],
               reported_status = if (d$declined) "declined" else "returned",
               reported_lower = if (d$reported) limits[1L] else NA_real_,
               reported_upper = if (d$reported) limits[2L] else NA_real_)
}))
anchor <- do.call(rbind, lapply(c("small", "large"), function(cohort) {
    e <- read(file.path(ref, cohort, "estimates.csv.gz"))
    e <- e[e$method == "anchorsOnly" & e$extraction == "native", ]
    hi <- e[e$endpoint == "upper", ]
    lo <- e[e$endpoint == "lower", ]
    idx <- match(hi$Index, meta$Index)
    lower <- lo$estimate[match(hi$Index, lo$Index)]
    stopifnot(nrow(hi) > 0L, !anyNA(idx), all(e$paired), all(e$status == "returned"),
              all(hi$truth == sets$GT_URL[idx]),
              all(lo$truth == sets$GT_LRL[match(lo$Index, sets$Index)]))
    data.frame(meta[idx, ], method = "anchorsOnly", status = "returned", lower, upper = hi$estimate,
               reported_status = "returned", reported_lower = lower, reported_upper = hi$estimate)
}))
out <- rbind(baseline, large, small, anchor)
stopifnot(nrow(out) == 4320L * 3L, !anyDuplicated(out[c("Index", "method")]),
          all(is.na(out$lower) == (out$Analyte == "CRP")), all(is.finite(out$upper)))
score <- function(rows, prefix) {
    st <- sets[match(rows$Index, sets$Index), ]
    lower <- rows[[paste0(prefix, "lower")]]
    upper <- rows[[paste0(prefix, "upper")]]
    crp <- rows$Analyte[1L] == "CRP"
    if (crp) lower <- upper
    frame <- data.frame(GT_LRL = st$GT_LRL, GT_URL = st$GT_URL, LRL = lower, URL = upper)
    z <- RIbench:::computePerfMeas(st$Analyte[1], rows$method[1], frame, st,
        RIperc = if (crp) .95 else c(.025, .975), cutoffZ = 5)$resRIs
    list(lower = if (crp) rep(NA_real_, nrow(rows)) else z$zzDev_LRL, upper = z$zzDev_URL)
}
# The benchmark scorer's support path can depend on the full analyte group.
for (prefix in c("", "reported_")) {
    out[[paste0(prefix, "z_lower")]] <- out[[paste0(prefix, "z_upper")]] <- NA_real_
    for (idx in split(seq_len(nrow(out)), list(out$method, out$N == 50000, out$Analyte))) {
        z <- score(out[idx, ], prefix)
        out[[paste0(prefix, "z_lower")]][idx] <- z$lower
        out[[paste0(prefix, "z_upper")]][idx] <- z$upper
    }
}
out <- out[order(out$Index, out$method), ]
source("stage0/common.R")
write_table(out, args[2L])
