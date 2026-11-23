source("stage0/common.R")
args <- commandArgs(TRUE)
bundle <- args[[1]]
engine <- match.arg(args[[2]], c("cran", "vendored"))
repetition <- as.integer(args[[3]])
shard <- as.integer(args[[4]])
out <- args[[5]]
use_libraries(bundle, engine)
suppressPackageStartupMessages(loadNamespace("RIbench"))
future::plan(future::sequential)
fit_fn <- if (engine == "cran") refineR::findRI else anchorRefine::findRI
native_fn <- if (engine == "cran") refineR::getRI else anchorRefine::getRI
cases <- readRDS(shard_path(bundle, shard))

capture_call <- function(expr) {
    warnings <- messages <- character()
    error <- NULL
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

records <- vector("list", length(cases))
for (i in seq_along(cases)) {
    case <- cases[[i]]
    probs <- percentiles(case$Analyte)
    set.seed(123)
    start <- proc.time()[["elapsed"]]
    fit <- capture_call(fit_fn(case$x))
    native <- historical <- NULL
    if (!is.null(fit$value)) {
        native <- capture_call(native_fn(fit$value, RIperc = probs))
        historical <- capture_call(RIbench::getRI(fit$value, RIperc = probs, truncNormal = FALSE))
    }
    records[[i]] <- list(Index = case$Index, fit = fit, native = native, historical = historical,
                         elapsed = proc.time()[["elapsed"]] - start)
    if (i %% 12 == 0 || i == length(cases)) {
        cat(engine, "repeat", repetition, "finished", i, "of", length(cases), "\n")
        flush.console()
    }
}
sample <- list(records = records, engine = engine, repetition = repetition, shard = shard,
               pid = Sys.getpid(), host = unname(Sys.info()["nodename"]),
               lib = getNamespaceInfo(asNamespace("refineR"), "path"),
               session = capture.output(sessionInfo()))
saveRDS(sample, file.path(out, sprintf("%s-%d.rds", engine, repetition)), version = 2)
