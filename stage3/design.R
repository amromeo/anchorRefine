# Stage 3 development and influence fixtures, protocol 4b82c69. Drawing a
# sample requires an explicit call to stage3_generate with an authorized row.
stage3_design <- function(phase) {
    stopifnot(phase %in% c("influence", "development"), length(phase) == 1L)
    old <- read.csv("stage2/development-design.csv", stringsAsFactors = FALSE)
    families <- unique(old[c("family", "lambda", "mu", "sigma", "healthy_sd",
                              "truth_lower", "truth_upper")])
    stopifnot(nrow(families) == 3L)
    patterns <- c("left_separated", "right_separated", "left_shoulder",
                  "right_shoulder", "bilateral_separated", "overlapping")
    sizes <- c(1000L, 1500L, 5000L, 50000L)
    fractions <- c(0.10, 0.20, 0.25, 0.45, 0.60)
    if (phase == "influence") {
        cells <- data.frame(disease = c("left_shoulder", "right_shoulder", "overlapping",
                                          "right_shoulder"), fraction = c(.45, .45, .60, .10))
    } else {
        cells <- expand.grid(disease = patterns, fraction = fractions, KEEP.OUT.ATTRS = FALSE,
                             stringsAsFactors = FALSE)
    }
    frame <- expand.grid(rounding_fraction = c(0.05, 0.25), scenario = seq_len(nrow(cells)),
                         N = sizes, family_id = seq_len(nrow(families)),
                         stringsAsFactors = FALSE, KEEP.OUT.ATTRS = FALSE)
    frame$cell_id <- seq_len(nrow(frame))
    frame$disease <- cells$disease[frame$scenario]
    frame$fraction <- cells$fraction[frame$scenario]
    reps <- if (phase == "influence") rep(1L, nrow(frame)) else
        ifelse(frame$fraction > 0.20 & frame$disease %in% c("left_shoulder", "right_shoulder",
                                                            "overlapping"), 8L, 4L)
    rep_id <- sequence(reps)
    frame <- frame[rep(seq_len(nrow(frame)), reps), ]
    j <- seq_len(nrow(frame))
    seed <- if (phase == "influence") 81000000L else 82000000L
    seeds <- seed + 10L * j
    f <- families[frame$family_id, , drop = FALSE]
    h <- f$healthy_sd * frame$rounding_fraction
    ans <- data.frame(phase, j, cell_id = frame$cell_id, f[c("family", "lambda", "mu", "sigma")],
        N = frame$N, fraction = frame$fraction, disease = frame$disease,
        rounding_fraction = frame$rounding_fraction, h, precision = h, replicate = rep_id,
        f[c("healthy_sd", "truth_lower", "truth_upper")], routine_seed = seeds,
        anchor_seed = seeds + 1L, diagnostic_seed = seeds + 2L, fitter_seed = seeds + 3L,
        pit_primary_seed = seeds + 4L, pit_alternate_seed = seeds + 5L,
        diagnostic_primary_seed = seeds + 6L, diagnostic_alternate_seed = seeds + 7L,
        stringsAsFactors = FALSE, row.names = NULL)
    stopifnot(nrow(ans) == if (phase == "development") 3744L else 96L,
              !anyDuplicated(ans[c("cell_id", "replicate")]))
    ans
}

# Reuse the frozen Stage 2 generator's entire draw and rounding sequence.
# Replace only its phase-specific guard, as for the Stage 2 holdout.
stage3_generate <- local({
    generate <- stage2_generate
    steps <- as.list(body(generate))
    original_guard <- quote(stopifnot(is.data.frame(row), nrow(row) == 1L,
        row$j %in% seq_len(1440L), row$routine_seed == 62000000L + 10L * row$j,
        row$anchor_seed == row$routine_seed + 1L, row$diagnostic_seed == row$routine_seed + 2L))
    stopifnot(identical(steps[[2L]], original_guard))
    steps[[2L]] <- quote(stopifnot(is.data.frame(row), nrow(row) == 1L,
        (row$phase == "influence" && row$j %in% seq_len(96L) &&
         row$routine_seed == 81000000L + 10L * row$j) ||
        (row$phase == "development" && row$j %in% seq_len(3744L) &&
         row$routine_seed == 82000000L + 10L * row$j),
        row$anchor_seed == row$routine_seed + 1L, row$diagnostic_seed == row$routine_seed + 2L,
        row$fitter_seed == row$routine_seed + 3L, row$pit_primary_seed == row$routine_seed + 4L,
        row$pit_alternate_seed == row$routine_seed + 5L,
        row$diagnostic_primary_seed == row$routine_seed + 6L,
        row$diagnostic_alternate_seed == row$routine_seed + 7L))
    body(generate) <- as.call(steps)
    generate
})

stage3_manifest <- function(phase) {
    expected <- stage3_design(phase)
    actual <- read.csv(file.path("stage3", paste0("design-", phase, ".csv")),
                       colClasses = vapply(expected, typeof, character(1)),
                       stringsAsFactors = FALSE)
    stopifnot(identical(names(actual), names(expected)), nrow(actual) == nrow(expected))
    for (field in names(expected)) {
        if (is.double(expected[[field]])) {
            stopifnot(isTRUE(all.equal(actual[[field]], expected[[field]], tolerance = 5e-15)))
        } else {
            stopifnot(identical(actual[[field]], expected[[field]]))
        }
    }
    actual
}
