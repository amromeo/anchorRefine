# Read the primary session's saved bytes before the shard is archived.
# Rscript --vanilla stage3/ribench/verify-taskg.R BUNDLE PRIMARY_DIRECTORY
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
source("stage0/common.R")
use_libraries(args[[1]], "vendored")
path <- args[[2]]
saved <- readRDS(file.path(path, "results.rds"))
sha <- function(x) digest::digest(x, algo = "sha256", serializeVersion = 2L)
arms <- c("baseline", "stage2", "w0", "w1", "t0", "t0.25", "anchorsOnly")
fits <- saved$fits
checks <- saved$checks
case_ids <- vapply(saved$cases, function(case) as.integer(case$j), integer(1))
stopifnot(identical(fits$j, fits$Index), identical(checks$j, checks$Index), !anyDuplicated(case_ids),
          setequal(case_ids, fits$j), setequal(case_ids, checks$j))
index <- lapply(seq_along(case_ids), function(slot) {
    case <- saved$cases[[slot]]
    rows <- fits[fits$j == case$j, , drop = FALSE]
    decisions <- checks[checks$j == case$j, , drop = FALSE]
    keep <- c("arm", "panel", "seed_kind")
    stopifnot(case$j == case$Index, nrow(rows) == length(arms), setequal(rows$arm, arms),
              all(rows$case_hash == sha(case)),
              setequal(names(case$arms), arms), identical(case$routine_hash, sha(case$routine)),
              all(rows$routine_hash == case$routine_hash), all(rows$routine_n == length(case$routine)), all(rows$N == rows$N[1L]),
              identical(names(case$panels), "guidance"),
              all(lengths(case$panels) == 40L),
              all(rows$anchor_hash == sha(case$panels$guidance)),
              nrow(decisions) == 2L * length(arms), !anyDuplicated(decisions[keep]),
              setequal(decisions$arm, arms), setequal(decisions$panel, "guidance"),
              setequal(decisions$seed_kind, c("primary","alternate")))
    for (arm in arms) {
        model <- case$arms[[arm]]
        fit <- model$search$fit
        row <- rows[rows$arm == arm, , drop = FALSE]
        stopifnot(identical(row$fit_status, model$search$status),
                  identical(row$fit_hash, model$full_fit_hash),
                  is.logical(model$uses_routine), length(model$uses_routine) == 1L)
        if (model$uses_routine) {
            stopifnot("Data" %in% names(fit), is.null(fit$Data))
            fit$Data <- case$routine
        }
        if (is.null(fit)) {
            stopifnot(is.na(model$full_fit_hash), row$fit_status == "fit_failed")
        } else {
            stopifnot(identical(sha(fit), model$full_fit_hash))
        }
        if (row$fit_status == "ResultFound") {
            if (arm == "anchorsOnly") {
                stopifnot(!model$uses_routine, fit$transform == row$ao_transform,
                          fit$mu == row$ao_location, fit$sd == row$ao_spread,
                          fit$shift == row$ao_shift)
            } else {
                stopifnot(model$uses_routine, identical(fit$Data, case$routine))
            }
        }
    }
    data.frame(Index = case$Index, j = case$j, rds_position = slot, N = rows$N[1L],
               routine_n = length(case$routine),
               routine_hash = case$routine_hash, anchor_hash = rows$anchor_hash[1],
               stringsAsFactors = FALSE)
})
write_table(do.call(rbind, index), file.path(path, "object-index.csv"))
