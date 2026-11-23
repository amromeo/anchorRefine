# Recreate routine input identities for archived N = 50,000 fits.
# Run on Actions after the small cohort, from the repository root:
# Rscript --vanilla stage1/large/verify-routines.R BUNDLE OUTCSV
args <- commandArgs(TRUE)
stopifnot(length(args) == 2L)
source("stage0/common.R")
use_libraries(args[1], "cran")
stopifnot(packageVersion("RIbench") == "1.0.2",
          packageVersion("data.table") == "1.16.4",
          packageVersion("digest") == "0.6.39")
source("stage1/large/source/reader-compat.R")

verify_routines <- function(output) {
    sets <- RIbench::loadTestsetDefinition()
    sets <- sets[sets$N == 50000, ]
    manifest <- read.csv("stage1/large/testsets.csv", stringsAsFactors = FALSE)
    inventory <- read.csv("stage1/large/members.csv", stringsAsFactors = FALSE)
    stopifnot(nrow(sets) == 1440L, !anyDuplicated(sets$Index),
              identical(sets$Index, manifest$Index), identical(sets$Index, inventory$Index),
              identical(sets$HashCode, manifest$HashCode),
              identical(sets$HashCode, inventory$routine_HashCode))
    original_shards <- (seq_len(nrow(sets)) - 1L) %% 60L + 1L
    first <- match(seq_len(60L), original_shards)
    # RIbench 1.0.2 draws every test set in definition order for each subset.
    # The subset supplies the initial analyte/seed and selects files at fwrite().
    # These checks allow the 60 original subsets to share one traversal.
    stopifnot(all(sets$Analyte[first] == "Hb"), all(sets$startSeed[first] == 123L),
              all(tabulate(original_shards, nbins = 60L) == 24L))

    directory <- tempfile("stage1-routine-data-")
    dir.create(directory)
    on.exit(unlink(directory, recursive = TRUE), add = TRUE)
    RIbench::generateBiomarkerTestSets(workingDir = directory, subset = sets,
                                       rounding = TRUE, verbose = FALSE)
    rows <- vector("list", nrow(sets))
    for (i in seq_len(nrow(sets))) {
        s <- sets[i, ]
        name <- sprintf("%d_%s_seed_%d.csv", s$Index, s$Analyte, s$startSeed)
        x <- fread(file.path(directory, "Data", s$Analyte, name))$V1
        md5 <- digest::digest(x, algo = "md5", serializeVersion = 2, ascii = TRUE)
        if (!identical(md5, s$HashCode)) {
            stop(sprintf("Routine identity mismatch at Index %d: expected %s, found %s",
                         s$Index, s$HashCode, md5))
        }
        rows[[i]] <- data.frame(Index = s$Index, routine_md5 = md5,
                                routine_sha256 = digest::digest(x, algo = "sha256"),
                                origin_shard = original_shards[i], n_routine = length(x))
    }
    result <- do.call(rbind, rows)
    stopifnot(identical(result$Index, manifest$Index), !anyDuplicated(result$routine_sha256))
    dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
    staged <- tempfile("routine-hashes-", tmpdir = dirname(output))
    on.exit(unlink(staged), add = TRUE)
    write.csv(result, staged, row.names = FALSE)
    stopifnot(file.rename(staged, output))
    message(sprintf("Verified all %d archived routine vector identities.", nrow(result)))
}
verify_routines(args[2])
