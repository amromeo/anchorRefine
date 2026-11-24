# Use the signed development generator's exact sample-drawing body. Its guard
# explicitly accepts development IDs only; replace that one statement in the
# private confirmation copy. The design manifest validates all row fields.
stage2_confirmation_generate <- local({
    generate <- stage2_generate
    steps <- as.list(body(generate))
    original_guard <- quote(stopifnot(is.data.frame(row), nrow(row) == 1L,
        row$j %in% seq_len(1440L), row$routine_seed == 62000000L + 10L * row$j,
        row$anchor_seed == row$routine_seed + 1L, row$diagnostic_seed == row$routine_seed + 2L))
    stopifnot(identical(steps[[2L]], original_guard))
    steps[[2L]] <- quote(stopifnot(is.data.frame(row), nrow(row) == 1L,
        row$j %in% seq_len(2880L), row$routine_seed == 72000000L + 10L * row$j,
        row$anchor_seed == row$routine_seed + 1L, row$diagnostic_seed == row$routine_seed + 2L,
        row$fitter_seed == row$routine_seed + 3L,
        row$pit_primary_seed == row$routine_seed + 4L, row$pit_alternate_seed == row$routine_seed + 5L,
        row$diagnostic_primary_seed == row$routine_seed + 6L,
        row$diagnostic_alternate_seed == row$routine_seed + 7L))
    body(generate) <- as.call(steps)
    generate
})
