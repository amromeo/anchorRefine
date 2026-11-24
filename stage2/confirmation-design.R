# Metadata only. Sourcing this file or writing its manifest draws no observations.
# Load stage2/generator.R first for the frozen factorial design and healthy truth.
stage2_confirmation_design <- function() {
    cells <- stage2_design()
    cells <- cells[cells$replicate == 1L, , drop = FALSE]
    stopifnot(nrow(cells) == 360L)
    design <- cells[rep(seq_len(nrow(cells)), each = 8L), , drop = FALSE]
    row.names(design) <- NULL
    design$j <- seq_len(nrow(design))
    design$replicate <- rep(seq_len(8L), times = nrow(cells))
    base <- 72000000L + 10L * design$j
    seed_fields <- c("routine_seed", "anchor_seed", "diagnostic_seed", "fitter_seed",
                     "pit_primary_seed", "pit_alternate_seed",
                     "diagnostic_primary_seed", "diagnostic_alternate_seed")
    for (i in seq_along(seed_fields)) design[[seed_fields[i]]] <- base + (i - 1L)
    stopifnot(nrow(design) == 2880L, sum(design$fraction > 0.20) == 1728L,
              sum(design$fraction <= 0.20) == 1152L,
              !anyDuplicated(unlist(design[seed_fields], use.names = FALSE)))
    design
}

stage2_write_confirmation_design <- function(path) {
    design <- stage2_confirmation_design()
    for (field in names(design)) {
        if (is.double(design[[field]])) design[[field]] <- sprintf("%.17g", design[[field]])
    }
    utils::write.table(design, path, sep = ",", row.names = FALSE, quote = FALSE)
}
