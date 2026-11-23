# Evaluate one shard of the frozen development design.
# Rscript --vanilla stage2/run.R BUNDLE SHARD N_SHARDS OUT
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 4L)
source("stage0/common.R")
use_libraries(args[1L], "vendored")
stopifnot(packageVersion("RIbench") == "1.0.2")
future::plan(future::sequential)
source("R/anchor-check.R")
source("R/stage2-peaks.R")
source("R/stage2-grid.R")
source("R/stage2-search.R")
source("stage2/generator.R")

out <- args[4L]
shard <- as.integer(args[2L])
n_shards <- as.integer(args[3L])
stopifnot(!is.na(shard), !is.na(n_shards), n_shards <= 1440L, 1L <= shard, shard <= n_shards)
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))

# Read H, h, truth, seed and factorial assignments from the signed-off design.
# The constructor is deterministic and draws no samples.
planned <- stage2_design()
design <- read.csv("stage2/development-design.csv", stringsAsFactors = FALSE,
                   colClasses = vapply(planned, typeof, character(1)))
stopifnot(identical(names(design), names(planned)), identical(design$j, seq_len(1440L)))
for (field in names(planned)) {
    if (is.double(planned[[field]])) {
        stopifnot(isTRUE(all.equal(design[[field]], planned[[field]], tolerance = 5e-15)))
    } else {
        stopifnot(identical(design[[field]], planned[[field]]))
    }
}
design <- design[(design$j - 1L) %% n_shards == shard - 1L, , drop = FALSE]

sha <- function(x) digest::digest(x, algo = "sha256", serializeVersion = 2)
arms <- c("baseline", "K24", "K28")
thresholds <- c(baseline = NA_integer_, K24 = 24L, K28 = 28L)
probs <- c(0.025, 0.975)
extractors <- c("native", "historical")
panel_names <- c("guidance", "diagnostic")

capture_conditions <- function(expr) {
    warnings <- messages <- character()
    error <- NA_character_
    value <- tryCatch(withCallingHandlers(expr,
        warning = function(w) {
            warnings <<- c(warnings, conditionMessage(w))
            invokeRestart("muffleWarning")
        },
        message = function(m) {
            messages <<- c(messages, conditionMessage(m))
            invokeRestart("muffleMessage")
        }), error = function(e) {
            error <<- conditionMessage(e)
            NULL
        })
    list(value = value, error = error, warnings = warnings, messages = messages)
}

raw_limits <- function(fit, extraction) {
    table <- if (extraction == "native") refineR::getRI(fit, RIperc = probs) else
        RIbench::getRI(fit, RIperc = probs, truncNormal = FALSE)
    stopifnot(is.data.frame(table), identical(as.numeric(table$Percentile), probs),
              is.numeric(table$PointEst), length(table$PointEst) == length(probs))
    as.numeric(table$PointEst)
}

evaluate_model <- function(fit, valid, panels, row) {
    summary <- list()
    conditions <- list()
    truth_scores <- stage2_healthy_z(c(row$truth_lower, row$truth_upper),
                                     row$lambda, row$mu, row$sigma)
    stopifnot(all(is.finite(truth_scores)), max(abs(truth_scores - qnorm(probs))) < 1e-12)
    for (extraction in extractors) {
        limits <- rep(NA_real_, 2L)
        if (valid) {
            result <- capture_conditions(raw_limits(fit, extraction))
            if (!is.null(result$value)) limits <- result$value
            conditions[[extraction]] <- result[c("error", "warnings", "messages")]
        }
        z <- truth_scores - stage2_healthy_z(limits, row$lambda, row$mu, row$sigma)
        finite <- is.finite(limits)
        data <- list(lower = limits[1L], upper = limits[2L], z_lower = z[1L], z_upper = z[2L],
            out_lower = if (finite[1L]) limits[1L] <= 0 else NA,
            out_upper = if (finite[2L]) limits[2L] <= 0 else NA,
            ordered = if (all(finite)) limits[1L] < limits[2L] else NA, nonfinite = !all(finite))
        names(data) <- paste(extraction, names(data), sep = "_")
        summary <- c(summary, data)
    }

    decisions <- list()
    for (panel in panel_names) for (kind in c("primary", "alternate")) {
        stem <- if (panel == "guidance") "pit" else "diagnostic"
        seed <- row[[paste(stem, kind, "seed", sep = "_")]]
        if (valid) {
            record <- capture_conditions(stage2_check(fit, panels[[panel]], row$h, seed))
            check <- record$value
            conditions[[paste(panel, kind, sep = "_")]] <- record[c("error", "warnings", "messages")]
            if (is.null(check)) check <- list(status = "check_failed", reason = "anchor_test_error",
                                               p = NA_real_, statistic = NA_real_)
            stopifnot(check$status %in% c("keep", "decline", "check_failed"))
        } else {
            check <- list(status = "fit_failed", reason = "fit_failed", p = NA_real_, statistic = NA_real_)
        }
        test <- data.frame(panel, seed_kind = kind, seed, status = check$status, reason = check$reason,
                           statistic = check$statistic, p = check$p, stringsAsFactors = FALSE)
        for (extraction in extractors) {
            finite <- !summary[[paste0(extraction, "_nonfinite")]]
            for (side in c("lower", "upper")) {
                endpoint <- paste(extraction, side, sep = "_")
                test[[paste0("released_", endpoint)]] <-
                    if (finite && check$status == "keep") summary[[endpoint]] else NA_real_
            }
        }
        decisions[[length(decisions) + 1L]] <- test
    }
    list(summary = as.data.frame(summary), checks = do.call(rbind, decisions), conditions = conditions)
}

collapse_int <- function(x) paste(x, collapse = ",")
one <- function(x, default = NA_real_) if (length(x) == 1L) unname(x) else default
election_fields <- function(result) {
    election <- result$election
    trace <- result$peak_trace
    coarse <- fine <- phase <- pass <- ""
    if (!is.null(trace) && nrow(trace) > 0L) {
        coarse <- collapse_int(trace$coarse)
        fine <- collapse_int(trace$fine)
        pass <- collapse_int(trace$pass)
        phase <- paste(trace$phase, collapse = ",")
    }
    votes <- one(election$votes, NA_integer_)
    runner <- one(election$runner_up, NA_integer_)
    data.frame(clarity = one(election$ok, NA), election_reason = one(election$reason, NA_character_),
        peak_index = one(election$index, NA_integer_), winner_basin = one(election$winner, NA_integer_),
        peak_location = one(election$peak_x), peak_left = one(election$bounds[1L]),
        peak_right = one(election$bounds[2L]), peak_target = one(election$target),
        winner_votes = votes, runner_up = runner, vote_lead = votes - runner,
        basin_counts = collapse_int(election$counts), assignments = collapse_int(election$assignments),
        peak_phases = phase, peak_passes = pass, peak_coarse_indices = coarse, peak_fine_indices = fine,
        stringsAsFactors = FALSE)
}

evaluate_case <- function(row) {
    sample <- stage2_generate(row)
    panels <- list(guidance = sample$anchors, diagnostic = sample$diagnostic)
    stopifnot(is.numeric(sample$x), length(sample$x) == row$N, all(is.finite(sample$x)),
              all(sample$x >= 0), identical(sample$h, row$h), all(lengths(panels) == 40L),
              identical(unname(sample$truth), c(row$truth_lower, row$truth_upper)))
    routine_hash <- sha(sample$x)
    anchor_hash <- sha(panels$guidance)
    diagnostic_hash <- sha(panels$diagnostic)
    inputs <- data.frame(cell_id = (row$j - 1L) %/% 4L + 1L, routine_hash, anchor_hash, diagnostic_hash)

    # Only routine data, the guidance panel, precision and seed enter the search.
    # Unexpected program errors stop the shard. The search represents ordinary
    # fit failures and fallbacks separately for each planned arm.
    search <- capture_conditions(stage2_fit_pair(sample$x, panels$guidance, sample$h, row$fitter_seed))
    pair <- search$value
    if (!is.na(search$error)) stop("Search infrastructure error for j=", row$j, ": ", search$error)
    stopifnot(identical(sort(names(pair)), sort(arms)))
    scores <- new.env(parent = emptyenv())
    fits <- checks <- detail <- setNames(vector("list", length(arms)), arms)
    for (arm in arms) {
        result <- pair[[arm]]
        fit <- result$fit
        valid <- identical(result$status, "ResultFound")
        stopifnot(result$status %in% c("ResultFound", "fit_failed"), is.logical(result$fallback),
                  length(result$fallback) == 1L, !is.na(result$fallback))
        if (result$fallback) {
            stopifnot(identical(fit, pair$baseline$fit), identical(result$status, pair$baseline$status))
        }
        if (valid) {
            stopifnot(inherits(fit, "RWDRI"), identical(fit$Data, sample$x),
                all(is.finite(c(fit$Mu, fit$Sigma, fit$Lambda, fit$Shift))), fit$Sigma > 0)
        }
        hash <- if (is.null(fit)) NA_character_ else sha(fit)
        key <- if (valid) hash else "fit_failed"
        if (!exists(key, scores, inherits = FALSE))
            assign(key, evaluate_model(fit, valid, panels, row), scores)
        evaluated <- get(key, scores, inherits = FALSE)
        meta <- data.frame(arm, K = unname(thresholds[arm]), fit_hash = hash, fit_status = result$status,
            fallback = result$fallback, reason = one(result$reason, NA_character_),
            guidance_used = arm != "baseline" && !result$fallback && valid,
            fit_upstream_status = one(fit$Status, NA_character_),
            Mu = one(fit$Mu), Sigma = one(fit$Sigma), Lambda = one(fit$Lambda), Shift = one(fit$Shift),
            P = one(fit$P), Cost = one(fit$Cost), rf = one(fit$rf), stringsAsFactors = FALSE)
        fits[[arm]] <- cbind(row, inputs, meta, election_fields(result), evaluated$summary)
        checks[[arm]] <- data.frame(j = row$j, arm, evaluated$checks, row.names = NULL)

        # Upstream embeds its full ordered routine vector in every fit. Retain
        # the remaining fit fields and its full hash. The frozen generator and
        # routine seed recover Data; the two short panels are preserved below.
        if (!is.null(result$fit) && !is.null(result$fit$Data)) {
            stopifnot(identical(result$fit$Data, sample$x))
            result$fit$Data <- NULL
        }
        detail[[arm]] <- list(search = result, full_fit_hash = hash, scoring = evaluated$conditions)
    }
    fit_table <- do.call(rbind, unname(fits))
    check_table <- do.call(rbind, unname(checks))
    row.names(fit_table) <- row.names(check_table) <- NULL
    record <- list(j = row$j, routine_hash = routine_hash, panels = panels, arms = detail,
                   search_conditions = search[c("error", "warnings", "messages")])
    result_hash <- sha(list(record = record, fits = fit_table, checks = check_table))
    fit_table$result_hash <- result_hash
    list(record = record, fits = fit_table, checks = check_table)
}

cases <- vector("list", nrow(design))
for (i in seq_len(nrow(design))) {
    cases[[i]] <- evaluate_case(design[i, , drop = FALSE])
    cat("Completed development j =", design$j[i], "(", i, "of", nrow(design), ")\n")
    flush.console()
}
fits <- do.call(rbind, lapply(cases, "[[", "fits"))
checks <- do.call(rbind, lapply(cases, "[[", "checks"))
row.names(fits) <- row.names(checks) <- NULL
stopifnot(nrow(fits) == 3L * nrow(design), nrow(checks) == 12L * nrow(design),
          !anyDuplicated(fits[c("j", "arm")]), !anyDuplicated(checks[c("j", "arm", "panel", "seed_kind")]))
write_table(fits, file.path(out, "fits.csv"))
write_table(checks, file.path(out, "checks.csv"))
saveRDS(list(fits = fits, checks = checks, cases = lapply(cases, "[[", "record")),
        file.path(out, "results.rds"), version = 2, compress = FALSE)
