# Evaluate archived full-data fits for the approved Stage 1 cohort.
# Rscript --vanilla stage1/cohort.R BUNDLE small|large OUTDIR
source("stage0/common.R")
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3L)
bundle <- args[1L]
cohort <- match.arg(args[2L], c("small", "large"))
out <- args[3L]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
writeLines(as.character(Sys.getpid()), file.path(out, "r-pid.txt"))
use_libraries(bundle, "vendored")
stopifnot(packageVersion("RIbench") == "1.0.2")
current_lib <- normalizePath(Sys.getenv("STAGE1_LIB"), mustWork = TRUE)
.libPaths(c(current_lib, .libPaths()), include.site = FALSE)
stopifnot(packageVersion("anchorRefine") == "0.1.0",
          normalizePath(find.package("anchorRefine")) == file.path(current_lib, "anchorRefine"))

small <- cohort == "small"
input_dir <- if (small) "archive/c2" else "stage1/large"
archive <- file.path(input_dir, if (small) "ribench-scored-independent.zip" else
                                            "ribench-scored-independent-50000.zip")
unpacked <- tempfile("c2-input-")
dir.create(unpacked)
unzip(archive, exdir = unpacked)
read_input <- function(name) read.csv(file.path(input_dir, name), stringsAsFactors = FALSE)

# Every archived table must cover exactly the same prespecified Index values.
sets <- RIbench::loadTestsetDefinition()
sets <- sets[if (small) sets$N <= 5000L else sets$N == 50000L, ]
sets <- sets[order(sets$Index), , drop = FALSE]
row.names(sets) <- NULL
count <- nrow(sets)
stopifnot(!anyDuplicated(sets$Index), count == if (small) 2880L else 1440L)
by_index <- function(table) {
    stopifnot(!anyDuplicated(table$Index), setequal(table$Index, sets$Index))
    table <- table[match(sets$Index, table$Index), , drop = FALSE]
    row.names(table) <- NULL
    table
}
defs <- by_index(read_input("testsets.csv"))
for (field in c("Index", "Analyte", "N", "startSeed", "HashCode")) {
    stopifnot(identical(as.character(sets[[field]]), as.character(defs[[field]])))
}
models <- by_index(read_input("model-inventory.csv"))
hashes <- by_index(read.csv(file.path(unpacked, "anchor-sample-hashes.csv")))
stopifnot(!anyDuplicated(hashes$sha256), all(hashes$seed == 17000000L + sets$Index))

if (small) {
    routines <- by_index(read.csv(file.path(bundle, "inputs", "verified-inputs.csv")))
    # Re-read the frozen vectors. No routine data enter the anchor test.
    for (shard in seq_len(20)) {
        for (case in readRDS(shard_path(bundle, shard))) {
            i <- match(case$Index, sets$Index)
            stopifnot(digest::digest(case$x, algo = "sha256") == routines$routine_sha256[i],
                      digest::digest(case$x, algo = "md5", serializeVersion = 2, ascii = TRUE) ==
                          sets$HashCode[i])
        }
    }
    stopifnot(identical(hashes$sha256, routines$anchor_sha256))
} else {
    # The large preflight reproduces the routine vectors and verifies their C2 hashes.
    routines <- by_index(read.csv("stage1-inputs/large-routines.csv"))
}
stopifnot(identical(routines$routine_md5, sets$HashCode),
          all(grepl("^[[:xdigit:]]{64}$", routines$routine_sha256)))

primary_methods <- c(refineR = "refineR", anchorsOnly = "anchorsOnly", anchoredRI_old = "anchoredRI")
read_performance <- function(algo) {
    rds <- file.path(unpacked, paste0(algo, "-native-performance.rds"))
    p <- by_index(do.call(rbind, readRDS(rds)$resRIs))
    stopifnot(all(p$Algorithm == algo), identical(as.character(p$Analyte), sets$Analyte))
    for (field in c("GT_LRL", "GT_URL")) {
        stopifnot(identical(p[[field]], sets[[field]]))
    }
    p
}
perf <- lapply(primary_methods, read_performance)
custom <- do.call(rbind, lapply(list.files(unpacked, "^custom-[0-9]+[.]csv$", full.names = TRUE), read.csv))
for (algo in c("anchoredRI", "anchorsOnly")) {
    run <- by_index(custom[custom$algo == algo, ])
    stopifnot(all(run$N == sets$N), all(run$Analyte == sets$Analyte),
              all(run$anchor_seed == hashes$seed), all(run$anchors == 40L))
}

load_fit <- function(file) {
    env <- new.env(parent = emptyenv())
    stopifnot(identical(load(file, envir = env), "fit"))
    env$fit
}
limits <- function(x, n) {
    x <- as.numeric(x)
    stopifnot(length(x) == n)
    # RIbench uses two columns internally even for CRP. Only its upper result is exported.
    c(lower = x[1L], upper = x[n])
}
check_records <- vector("list", count)
native <- historical <- matrix(NA_real_, nrow = count, ncol = 2L)
reconstruction <- numeric(count)
definition <- sets[c("Index", "Analyte", "N", "Scenario", "fractionPathol")]
for (i in seq_len(count)) {
    s <- sets[i, ]
    stem <- sprintf("%d_%s_seed_%d", s$Index, s$Analyte, s$startSeed)
    path <- file.path("Results", "refineR", s$Analyte, paste0(stem, "_refineR.Rdata"))
    stopifnot(models$file[i] == path)
    dst <- file.path(unpacked, path)
    stopifnot(digest::digest(file = dst, algo = "sha256") == models$sha256[i])
    fit <- load_fit(dst)
    stopifnot(inherits(fit, "RWDRI"), fit$Model == "BoxCox", fit$NBootstrap == 0,
              as.character(fit$PkgVersion) == "2.0.0", fit$Analyte == s$Analyte,
              fit$Status == perf$refineR$Status[i])
    if (!small) stopifnot(fit$N == routines$n_routine[i])
    pars <- c("Mu", "Sigma", "Lambda", "Shift")
    for (field in pars) {
        stopifnot(identical(fit[[field]], perf$refineR[[paste0("Est_", field)]][i]))
    }
    probs <- percentiles(s$Analyte)
    n <- length(probs)
    conditions <- character()
    capture_conditions <- function(label, expr) {
        tryCatch(withCallingHandlers(expr,
            warning = function(w) {
                conditions <<- c(conditions, paste(label, conditionMessage(w)))
                invokeRestart("muffleWarning")
            }), error = function(e) {
                conditions <<- c(conditions, paste(label, conditionMessage(e)))
                NULL
            })
    }

    native_ri <- capture_conditions("native", anchorRefine::getRI(fit, RIperc = probs))
    hist_ri <- capture_conditions("historical", RIbench::getRI(fit, RIperc = probs, truncNormal = FALSE))
    if (!is.null(native_ri)) native[i, ] <- limits(native_ri$PointEst, n)
    if (!is.null(hist_ri)) historical[i, ] <- limits(hist_ri$PointEst, n)
    archived <- if (n == 1L) perf$refineR$URL[i] else c(perf$refineR$LRL[i], perf$refineR$URL[i])
    width <- if (n == 1L) archived else diff(archived)
    reconstructed <- if (n == 1L) historical[i, 2L] else historical[i, ]
    # Failure here means the supplied archive is unsuitable for fit reuse.
    stopifnot(length(width) == 1L, is.finite(width), width > 0, all(is.finite(reconstructed)))
    reconstruction[i] <- max(abs(archived - reconstructed)) / width
    stopifnot(reconstruction[i] <= 0.001)
    for (method in c("anchorsOnly", "anchoredRI_old")) {
        algo <- primary_methods[[method]]
        raw <- load_fit(file.path(unpacked, "Results", algo, s$Analyte, paste0(stem, "_", algo, ".Rdata")))
        scored <- if (n == 1L) perf[[method]]$URL[i] else c(perf[[method]]$LRL[i], perf[[method]]$URL[i])
        stopifnot(identical(as.numeric(raw$Percentile), probs),
                  identical(as.numeric(raw$PointEst), scored))
    }

    set.seed(hashes$seed[i])
    a <- RIbench:::invBoxCox(rnorm(40, s$nonp_mu, s$nonp_sigma), s$nonp_lambda) + s$nonp_shift
    a <- round(a[is.finite(a) & a >= 0], s$decimals)
    stopifnot(length(a) == 40L, digest::digest(a, algo = "sha256") == hashes$sha256[i])
    call_check <- function(seed) {
        test <- capture_conditions("anchor test", anchorRefine::check_anchors(
            fit = fit, anchors = a, decimals = s$decimals, seed = seed))
        if (is.null(test)) {
            test <- list(status = "check_failed", reason = "anchor_test_error",
                         statistic = NA_real_, p = NA_real_)
        }
        stopifnot(test$status %in% c("keep", "decline", "check_failed"))
        test
    }
    main_seed <- 38000000L + s$Index
    alt_seed <- 39000000L + s$Index
    main <- call_check(main_seed)
    alt <- call_check(alt_seed)
    check_records[[i]] <- data.frame(definition[i, ], routine_hash = routines$routine_sha256[i],
        ribench_hashcode = sets$HashCode[i], routine_n = fit$N,
        anchor_hash = hashes$sha256[i], anchor_seed = hashes$seed[i], anchor_n = length(a),
        decimals = s$decimals, model_sha256 = models$sha256[i], fit_source = "archived",
        fit_valid = fit$Status == "ResultFound" && all(is.finite(unlist(fit[pars]))) && fit$Sigma > 0,
        Mu = fit$Mu, Sigma = fit$Sigma, Lambda = fit$Lambda, Shift = fit$Shift,
        primary_seed = main_seed, primary_statistic = main$statistic, primary_p = main$p,
        primary_status = main$status, primary_reason = main$reason,
        secondary_seed = alt_seed, secondary_statistic = alt$statistic, secondary_p = alt$p,
        secondary_status = alt$status, secondary_reason = alt$reason,
        reconstruction_fraction = reconstruction[i], diagnostics = paste(conditions, collapse = " | "))
}
checks <- do.call(rbind, check_records)
row.names(checks) <- NULL

# Compute signed endpoint z exactly as RIbench does for each analyte. Running its
# original scoring function on an entire group preserves group-level support handling.
score <- function(method, extraction, lower, upper, statuses = NULL, task_status = NA_character_) {
    crp <- sets$Analyte == "CRP"
    lower[crp] <- upper[crp]
    finite <- (crp | is.finite(lower)) & is.finite(upper)
    ordered <- ifelse(crp, NA, lower < upper)
    if (is.null(statuses)) statuses <- ifelse(finite, "returned", "unavailable")
    zlo <- zhi <- rep(NA_real_, count)
    for (marker in unique(sets$Analyte)) {
        idx <- which(sets$Analyte == marker)
        s <- sets[idx, , drop = FALSE]
        wide <- data.frame(GT_LRL = s$GT_LRL, GT_URL = s$GT_URL, LRL = lower[idx], URL = upper[idx])
        scored <- RIbench:::computePerfMeas(marker, method, wide, s, RIperc = percentiles(marker),
                                            cutoffZ = 5)$resRIs
        zlo[idx] <- scored$zzDev_LRL
        zhi[idx] <- scored$zzDev_URL
    }
    id <- data.frame(definition, extraction, method, paired = TRUE, status = statuses,
                     ordered_interval = ordered, original_taskE_status = task_status)
    lo <- data.frame(id, endpoint = "lower", probability = 0.025,
                     truth = sets$GT_LRL, estimate = lower, z = zlo)
    hi <- data.frame(id, endpoint = "upper", probability = ifelse(crp, 0.95, 0.975),
                     truth = sets$GT_URL, estimate = upper, z = zhi)
    release <- function(data) {
        data$released_primary <- data$released_secondary <- rep(NA_real_, nrow(data))
        if (method == "refineR") {
            keep <- checks$primary_status == "keep"
            data$released_primary[keep] <- data$estimate[keep]
            keep <- checks$secondary_status == "keep"
            data$released_secondary[keep] <- data$estimate[keep]
        }
        data
    }
    rbind(release(lo)[!crp, ], release(hi))
}
comparison <- list()
for (ext in c("historical", "native")) {
    rr <- if (ext == "historical") historical else native
    comparison[[length(comparison) + 1L]] <- score("refineR", ext, rr[, 1L], rr[, 2L])
}
# The comparators supply their own limits, which are the same in both panels.
add_comparator <- function(method, lower, upper, statuses = NULL, task_status = NA_character_) {
    a <- score(method, "historical", lower, upper, statuses, task_status)
    b <- a
    b$extraction <- "native"
    rbind(a, b)
}
for (m in c("anchorsOnly", "anchoredRI_old")) {
    comparison[[length(comparison) + 1L]] <- add_comparator(m, perf[[m]]$LRL, perf[[m]]$URL)
}
if (small) {
    te <- read.csv("stage1/task-e/anchoredRI-comparator.csv", na.strings = c("", "NA"),
                   stringsAsFactors = FALSE)
    te <- by_index(te[te$benchmark == "RIbench" & te$N <= 5000 & !is.na(te$Index), ])
    stopifnot(all(te$dataset_id == paste0("r-", sets$Index)), all(te$routine_hash == checks$routine_hash),
              all(te$anchor_hash == checks$anchor_hash), all(te$ribench_hashcode == sets$HashCode),
              all(te$N == sets$N), all(te$Analyte == sets$Analyte), all(te$n_anchor == 40),
              all(te$n_routine == checks$routine_n), all(te$anchor_seed == hashes$seed))
    comparison[[length(comparison) + 1L]] <- add_comparator("anchoredRI_taskE_raw",
        te$lower, te$upper, task_status = te$report_status)
    available <- is.finite(te$reported_upper) & (sets$Analyte == "CRP" | is.finite(te$reported_lower))
    statuses <- ifelse(available, "returned",
                       ifelse(te$declined %in% TRUE & !te$technical %in% TRUE, "declined", "unavailable"))
    comparison[[length(comparison) + 1L]] <- add_comparator("anchoredRI_taskE_reported",
        te$reported_lower, te$reported_upper, statuses, te$report_status)
}
estimates <- do.call(rbind, comparison)
estimates <- estimates[order(estimates$Index, estimates$extraction, estimates$method, estimates$probability), ]
row.names(estimates) <- NULL
groups <- split(seq_len(nrow(estimates)), estimates$Index)
checks$result_hash <- vapply(seq_len(nrow(checks)), function(i) {
    fit_rows <- estimates[groups[[as.character(checks$Index[i])]], , drop = FALSE]
    # Reset row numbers so the digest identifies content independently of file position.
    row <- checks[i, , drop = FALSE]
    row.names(fit_rows) <- NULL
    row.names(row) <- NULL
    digest::digest(list(check = row, estimates = fit_rows), algo = "sha256", serializeVersion = 2)
}, character(1))
write_table(checks, file.path(out, "checks.csv"))
write_table(estimates, file.path(out, "estimates.csv"))
saveRDS(list(checks = checks, estimates = estimates), file.path(out, "results.rds"),
        version = 2, compress = FALSE)
cat("Completed", nrow(checks), "paired tests with", nrow(estimates), "method/endpoint rows.\n")
