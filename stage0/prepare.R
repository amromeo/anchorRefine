# Verify the archived identities and compile inputs without fitting any model.
source("stage0/common.R")
args <- commandArgs(TRUE)
bundle <- args[[1]]
n_shards <- as.integer(args[[2]])
use_libraries(bundle, "cran")
source("sources/c2/anchoredRI/tools/ribench/reader-compat.R")
lock <- read.delim("stage0/dependencies.tsv")
for (i in seq_len(nrow(lock))) {
    installed <- packageDescription(lock$package[i], fields = "Version")
    if (!identical(installed, lock$version[i])) {
        stop(sprintf("Expected %s %s, found %s", lock$package[i], lock$version[i], installed))
    }
}
stopifnot(packageVersion("RIbench") == "1.0.2")
unpacked <- tempfile("c2")
dir.create(unpacked)
unzip("archive/c2/ribench-data-small.zip", exdir = unpacked)
scored <- "archive/c2/ribench-scored-independent.zip"
members <- unzip(scored, list = TRUE)$Name
fit_paths <- grep("^Results/refineR/.+[.]Rdata$", members, value = TRUE)
unzip(scored, files = c(fit_paths, "refineR-native-performance.rds"), exdir = unpacked)

sets <- RIbench::loadTestsetDefinition()
sets <- sets[sets$N <= 5000, ]
defs <- read.csv("archive/c2/testsets.csv")
stopifnot(nrow(sets) == 2880, !anyDuplicated(sets$Index), nrow(defs) == nrow(sets))
for (key in c("Index", "Analyte", "N", "startSeed", "HashCode")) {
    stopifnot(identical(as.character(sets[[key]]), as.character(defs[[key]])))
}
sets <- sets[order(sets$Index), ]
anchors <- read.csv("archive/c2/anchor-sample-hashes.csv")
models <- read.csv("archive/c2/model-inventory.csv")
perf <- readRDS(file.path(unpacked, "refineR-native-performance.rds"))
historical <- do.call(rbind, perf$resRIs)
for (table in list(anchors, models, historical)) {
    stopifnot(!anyDuplicated(table$Index), setequal(table$Index, sets$Index))
}
stopifnot(length(fit_paths) == 2880, setequal(fit_paths, models$file))
inputs <- vector("list", nrow(sets))
identities <- vector("list", nrow(sets))
for (i in seq_len(nrow(sets))) {
    s <- sets[i, ]
    stem <- sprintf("%d_%s_seed_%d", s$Index, s$Analyte, s$startSeed)
    csv <- file.path(unpacked, "Data", s$Analyte, paste0(stem, ".csv"))
    x <- fread(file = csv)$V1
    routine_md5 <- digest::digest(x, algo = "md5", serializeVersion = 2, ascii = TRUE)
    stopifnot(routine_md5 == s$HashCode)
    set.seed(17000000L + s$Index)
    a <- RIbench:::invBoxCox(rnorm(40, s$nonp_mu, s$nonp_sigma), s$nonp_lambda) + s$nonp_shift
    a <- round(a[is.finite(a) & a >= 0], s$decimals)
    h <- anchors[match(s$Index, anchors$Index), ]
    a_sha <- digest::digest(a, algo = "sha256")
    stopifnot(length(a) == 40, h$seed == 17000000L + s$Index, h$sha256 == a_sha)

    m <- models[match(s$Index, models$Index), ]
    expected_file <- file.path("Results", "refineR", s$Analyte, paste0(stem, "_refineR.Rdata"))
    stopifnot(m$file == expected_file)
    fit_path <- file.path(unpacked, m$file)
    stopifnot(digest::digest(file = fit_path, algo = "sha256") == m$sha256)
    env <- new.env(parent = emptyenv())
    stopifnot(identical(load(fit_path, envir = env), "fit"))
    f <- env$fit
    archived <- historical[match(s$Index, historical$Index), ]
    params <- c("Mu", "Sigma", "Lambda", "Shift")
    for (name in params) {
        stopifnot(is.finite(f[[name]]), identical(f[[name]], archived[[paste0("Est_", name)]]))
    }
    stopifnot(inherits(f, "RWDRI"), f$Model == "BoxCox", f$NBootstrap == 0,
              as.character(f$PkgVersion) == "2.0.0", f$Status == archived$Status,
              f$Analyte == s$Analyte, archived$Analyte == s$Analyte,
              f$N == length(x), f$Sigma > 0)
    archived_limits <- if (s$Analyte == "CRP") archived$URL else c(archived$LRL, archived$URL)
    # Anchors and benchmark truth are intentionally absent from both fitting calls.
    inputs[[i]] <- list(Index = s$Index, Analyte = s$Analyte, N = s$N, x = x,
                        archived = f, archived_limits = archived_limits)
    identities[[i]] <- data.frame(Index = s$Index, routine_md5, archive_sha256 = m$sha256,
                                  routine_sha256 = digest::digest(x, algo = "sha256"),
                                  anchor_sha256 = a_sha, n_anchor = length(a))
}
dir.create(file.path(bundle, "inputs"), showWarnings = FALSE)
# Round-robin by sorted Index distributes all analytes across runners.
group <- (seq_along(inputs) - 1L) %% n_shards + 1L
for (shard in seq_len(n_shards)) saveRDS(inputs[group == shard], shard_path(bundle, shard))
identity_table <- do.call(rbind, identities)
stopifnot(!anyDuplicated(identity_table$anchor_sha256))
write_table(identity_table, file.path(bundle, "inputs", "verified-inputs.csv"))
writeLines(c(capture.output(sessionInfo()), capture.output(extSoftVersion()),
             paste("RNG", paste(RNGkind(), collapse = ", "))), file.path(bundle, "inputs", "build-session.txt"))
cat("Verified", nrow(sets), "archived routine vectors, anchor panels and models.\n")
