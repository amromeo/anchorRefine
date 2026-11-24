# After the small technical audit, regenerate the exact large routine vectors once.
# Rscript --vanilla stage2/ribench/prepare-large.R BUNDLE OUT
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
source("stage0/common.R")
use_libraries(args[1L], "cran")
stopifnot(packageVersion("RIbench") == "1.0.2", packageVersion("data.table") == "1.16.4",
          packageVersion("digest") == "0.6.39")
source("stage1/large/source/reader-compat.R")

prepare_large <- function(out) {
    work <- tempfile("ribench-large-")
    dir.create(work)
    on.exit(unlink(work, recursive = TRUE), add = TRUE)
    archive <- "results/stage1-45276858699/artifacts/large-inputs.zip"
    utils::unzip(archive, files = "large-routines.csv", exdir = work)
    old <- read.csv(file.path(work, "large-routines.csv"), stringsAsFactors = FALSE)
    frozen <- read.csv("stage1/large/testsets.csv", stringsAsFactors = FALSE)
    sets <- RIbench::loadTestsetDefinition()
    sets <- sets[sets$N == 50000, ]
    stopifnot(nrow(sets) == 1440L, !anyDuplicated(sets$Index),
              identical(sets$Index, frozen$Index), identical(sets$Index, old$Index),
              identical(sets$HashCode, frozen$HashCode), identical(sets$HashCode, old$routine_md5),
              all(old$n_routine > 0L & old$n_routine <= sets$N), !anyDuplicated(old$routine_sha256))

    # Every original C2 shard began with Hb and seed 123, then traversed
    # the full generator in definition order. Delay sorting until after generation.
    origin <- (seq_len(nrow(sets)) - 1L) %% 60L + 1L
    first <- match(seq_len(60L), origin)
    stopifnot(identical(origin, old$origin_shard), all(sets$Analyte[first] == "Hb"),
              all(sets$startSeed[first] == 123L))
    RIbench::generateBiomarkerTestSets(workingDir = work, subset = sets,
                                       rounding = TRUE, verbose = FALSE)
    ix <- order(sets$Index)
    sets <- sets[ix, ]
    old <- old[ix, ]
    shard_numbers <- (seq_len(nrow(sets)) - 1L) %% 48L + 1L
    for (group in seq_len(6L)) {
        directory <- file.path(out, paste0("group-", group))
        dir.create(directory, recursive = TRUE, showWarnings = FALSE)
        files <- character()
        for (shard in seq.int(8L * (group - 1L) + 1L, 8L * group)) {
            pos <- which(shard_numbers == shard)
            vectors <- vector("list", length(pos))
            names(vectors) <- as.character(sets$Index[pos])
            for (k in seq_along(pos)) {
                i <- pos[k]
                file <- sprintf("%d_%s_seed_%d.csv", sets$Index[i], sets$Analyte[i], sets$startSeed[i])
                x <- fread(file.path(work, "Data", sets$Analyte[i], file))$V1
                md5 <- digest::digest(x, algo = "md5", serializeVersion = 2, ascii = TRUE)
                sha256 <- digest::digest(x, algo = "sha256")
                stopifnot(length(x) == old$n_routine[i], identical(md5, old$routine_md5[i]),
                          identical(sha256, old$routine_sha256[i]))
                vectors[[k]] <- x
            }
            path <- file.path(directory, sprintf("shard-%03d.rds", shard))
            saveRDS(vectors, path, version = 2, compress = "gzip")
            files <- c(files, path)
        }
        lines <- vapply(files, function(f) paste0(digest::digest(file = f, algo = "sha256"),
                                                  "  ", basename(f)), character(1))
        writeLines(unname(lines), file.path(directory, sprintf("group-%d.sha256", group)))
        message("Verified and saved eight routine shards in group ", group)
    }
}
prepare_large(args[2L])
