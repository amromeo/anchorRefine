# Recover the original ordered routine vector and independently screened anchors.
stage2_ribench_inputs <- function(bundle, cohort, shard, n_shards, cache = NULL) {
    planned <- stage2_ribench_design(cohort)
    manifest <- read.csv(stage2_ribench_manifest_path(cohort), stringsAsFactors = FALSE,
                         colClasses = vapply(planned, typeof, character(1)))
    stopifnot(identical(names(planned), names(manifest)))
    for (field in names(planned)) {
        if (is.double(planned[[field]])) {
            stopifnot(isTRUE(all.equal(planned[[field]], manifest[[field]], tolerance = 5e-15)))
        } else stopifnot(identical(planned[[field]], manifest[[field]]))
    }
    definitions <- stage2_ribench_definition(cohort)
    ordinals <- seq.int(shard, nrow(manifest), by = n_shards)
    ids <- manifest$Index[ordinals]
    if (cohort == "small") {
        original_shards <- unique((ordinals - 1L) %% 20L + 1L)
        samples <- list()
        for (s in original_shards) {
            part <- readRDS(shard_path(bundle, s))
            for (one in part) {
                if (one$Index %in% ids) {
                    id <- as.character(one$Index)
                    stopifnot(is.null(samples[[id]]))
                    samples[[id]] <- one$x
                }
            }
        }
    } else {
        stopifnot(is.character(cache), length(cache) == 1L)
        samples <- readRDS(file.path(cache, sprintf("shard-%03d.rds", shard)))
    }
    stopifnot(!anyDuplicated(names(samples)), setequal(names(samples), as.character(ids)))
    lapply(ordinals, function(i) {
        def <- definitions[i, , drop = FALSE]
        m <- manifest[i, , drop = FALSE]
        x <- samples[[as.character(m$Index)]]
        stopifnot(is.numeric(x), length(x) == m$routine_n, identical(m$Index, def$Index),
                  identical(digest::digest(x, algo = "md5", ascii = TRUE, serializeVersion = 2), m$ribench_hashcode),
                  identical(digest::digest(x, algo = "sha256"), m$routine_hash))
        set.seed(m$anchor_seed)
        a <- RIbench:::invBoxCox(stats::rnorm(40L, def$nonp_mu, def$nonp_sigma), def$nonp_lambda) + def$nonp_shift
        a <- round(a[is.finite(a) & a >= 0], def$decimals)
        stopifnot(length(a) == m$anchor_n, identical(digest::digest(a, algo = "sha256"), m$anchor_hash))
        row.names(m) <- row.names(def) <- NULL
        list(x = x, a = a, definition = def, meta = m)
    })
}
