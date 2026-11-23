source("stage0/common.R")
args <- commandArgs(TRUE)
bundle <- args[[1]]
shard <- as.integer(args[[2]])
out <- args[[3]]
use_libraries(bundle, "vendored")
samples <- lapply(c("cran-1", "vendored-1", "cran-2", "vendored-2"), function(name) {
    readRDS(file.path(out, paste0(name, ".rds")))
})
cases <- readRDS(shard_path(bundle, shard))
keys <- function(rows) vapply(rows, function(x) as.integer(x$Index), integer(1))
engine <- c("cran", "vendored", "cran", "vendored")
repetition <- c(1L, 1L, 2L, 2L)
for (j in seq_along(samples)) {
    run <- samples[[j]]
    stopifnot(identical(keys(cases), keys(run$records)), run$shard == shard,
              run$host == samples[[1]]$host, run$engine == engine[j],
              run$repetition == repetition[j],
              run$lib == normalizePath(file.path(bundle, engine[j], "refineR")))
}
stopifnot(length(unique(vapply(samples, function(x) x$pid, integer(1)))) == 4)
byte_equal <- function(x, y) {
    identical(serialize(x, NULL, version = 2, xdr = TRUE), serialize(y, NULL, version = 2, xdr = TRUE))
}
points <- function(call, n) {
    x <- call$value$PointEst
    if (length(x) == n) as.numeric(x) else rep(NA_real_, n)
}
fit_status <- function(f) {
    if (is.null(f$value) || !is.null(f$error)) return("fit_error")
    pars <- unlist(f$value[c("Mu", "Sigma", "Lambda", "Shift")], use.names = FALSE)
    if (length(pars) != 4 || any(!is.finite(pars)) || f$value$Sigma <= 0) return("invalid_model")
    if (is.null(f$value$Status)) return("ResultFound")
    as.character(f$value$Status)
}

numbers <- function(x) {
    fields <- c("Mu", "Sigma", "Lambda", "Shift", "P", "Cost", "rf", "roundingBase")
    values <- vapply(fields, function(field) {
        if (length(x[[field]]) == 1L) as.numeric(x[[field]]) else NA_real_
    }, numeric(1))
    ab <- if (length(x$abOr) == 2L) x$abOr else rep(NA_real_, 2L)
    c(values, ab_left = ab[1], ab_right = ab[2])
}

same <- cross <- parameters <- conditions <- list()
pair_indices <- list(c(1, 2), c(3, 4), c(1, 3), c(2, 4))
names(pair_indices) <- c("engines_first", "engines_repeat", "cran_repeat", "vendored_repeat")
for (i in seq_along(cases)) {
    case <- cases[[i]]
    id <- data.frame(Index = case$Index, Analyte = case$Analyte, N = case$N, shard = shard)
    rec <- lapply(samples, function(run) run$records[[i]])
    for (pair in names(pair_indices)) {
        ids <- pair_indices[[pair]]
        fields <- vapply(c("fit", "native", "historical"), function(field) {
            byte_equal(rec[[ids[1]]][[field]], rec[[ids[2]]][[field]])
        }, logical(1))
        same[[length(same) + 1L]] <- cbind(id, pair, fit_equal = fields[[1]],
             native_equal = fields[[2]], historical_equal = fields[[3]], exact = all(fields))
    }
    for (j in seq_along(rec)) {
        for (field in c("fit", "native", "historical")) {
            call <- rec[[j]][[field]]
            for (kind in c("error", "warnings", "messages")) {
                for (message in call[[kind]]) {
                    conditions[[length(conditions) + 1L]] <- cbind(id, engine = engine[j],
                        repetition = repetition[j], operation = field, kind = kind, message = message)
                }
            }
        }
    }
    fit <- rec[[2]]$fit$value
    probs <- percentiles(case$Analyte)
    n <- length(probs)
    baseline <- case$archived_limits
    width <- if (n == 1L) baseline else diff(baseline)
    checked_width <- length(width) == 1L && is.finite(width) && width > 0
    state <- fit_status(rec[[2]]$fit)
    archived_state <- as.character(case$archived$Status)
    value <- points(rec[[2]]$historical, n)
    native <- points(rec[[2]]$native, n)
    recovered <- RIbench::getRI(case$archived, RIperc = probs, truncNormal = FALSE)$PointEst
    stopifnot(length(recovered) == n, length(baseline) == n)
    diff_c2 <- abs(value - baseline)
    diff_recovered <- abs(recovered - baseline)
    tolerance <- 0.001 * width
    finite <- is.finite(value) & is.finite(baseline) & is.finite(recovered)
    ok <- checked_width & finite & state == archived_state &
          diff_c2 <= tolerance & diff_recovered <= tolerance
    ratio <- if (checked_width) diff_c2 / width else rep(NA_real_, n)
    cross[[i]] <- cbind(id[rep(1L, n), , drop = FALSE], probability = probs,
        endpoint = if (n == 1L) "upper" else c("lower", "upper"),
        archived = baseline, reconstructed = recovered, candidate_historical = value,
        candidate_native = native, native_minus_historical = native - value,
        width = rep(width, n), tolerance = rep(tolerance, n), absolute_difference = diff_c2,
        fraction_of_width = ratio, reconstruction_error = diff_recovered,
        fit_status = state, archived_status = archived_state,
        native_valid = is.finite(native), historical_pass = ok)
    new <- numbers(fit)
    old <- numbers(case$archived)
    parameters[[i]] <- cbind(id, as.data.frame(as.list(new - old)),
        elapsed_cran_1 = rec[[1]]$elapsed, elapsed_vendored_1 = rec[[2]]$elapsed,
        elapsed_cran_2 = rec[[3]]$elapsed, elapsed_vendored_2 = rec[[4]]$elapsed)
}
write_table(do.call(rbind, same), file.path(out, "same-machine.csv"))
write_table(do.call(rbind, cross), file.path(out, "historical-audit.csv"))
write_table(do.call(rbind, parameters), file.path(out, "parameter-differences.csv"))
empty <- data.frame(Index = integer(), Analyte = character(), N = integer(), shard = integer(),
    engine = character(), repetition = integer(), operation = character(), kind = character(),
    message = character())
write_table(if (length(conditions)) do.call(rbind, conditions) else empty, file.path(out, "conditions.csv"))
writeLines(c("Observed sessions, archived in full in each RDS", unlist(lapply(samples, function(s) {
    c(paste(s$engine, "repetition", s$repetition, "pid", s$pid, "host", s$host, "library", s$lib), s$session)
}))), file.path(out, "sessions.txt"))
