# Freeze the planned Index, input digests, healthy truth and random seeds.
# This constructor reads prior-stage evidence and definitions only.
stage2_ribench_definition <- function(cohort) {
    stopifnot(cohort %in% c("small", "large"), packageVersion("RIbench") == "1.0.2")
    sets <- RIbench::loadTestsetDefinition()
    sets <- sets[if (cohort == "small") sets$N <= 5000 else sets$N == 50000, ]
    sets <- sets[order(sets$Index), , drop = FALSE]
    row.names(sets) <- NULL
    stopifnot(nrow(sets) == if (cohort == "small") 2880L else 1440L, !anyDuplicated(sets$Index))
    sets
}

stage2_ribench_design <- function(cohort) {
    sets <- stage2_ribench_definition(cohort)
    source <- if (cohort == "small") "archive/c2" else "stage1/large"
    original <- read.csv(file.path(source, "testsets.csv"), stringsAsFactors = FALSE)
    hashes <- read.csv(file.path(source, "anchor-sample-hashes.csv"), stringsAsFactors = FALSE)
    path <- file.path("results/stage1-45276858699", cohort, "checks.csv.gz")
    stage1 <- read.csv(path, stringsAsFactors = FALSE)
    align <- function(table) {
        stopifnot(!anyDuplicated(table$Index), setequal(sets$Index, table$Index))
        table[match(sets$Index, table$Index), , drop = FALSE]
    }
    original <- align(original)
    stage1 <- align(stage1)
    hashes <- align(hashes)
    for (field in c("Index", "Analyte", "N", "startSeed", "Scenario", "decimals", "HashCode",
                    "fractionPathol", "GT_LRL", "GT_URL", "nonp_lambda", "nonp_mu", "nonp_sigma", "nonp_shift"))
        stopifnot(identical(as.character(sets[[field]]), as.character(original[[field]])))
    stopifnot(all(stage1$N == sets$N), all(stage1$Analyte == sets$Analyte),
              all(stage1$Scenario == sets$Scenario), all(stage1$fractionPathol == sets$fractionPathol),
              all(stage1$decimals == sets$decimals), all(stage1$ribench_hashcode == sets$HashCode),
              all(stage1$anchor_n == 40), all(stage1$anchor_hash == hashes$sha256),
              all(stage1$anchor_seed == 17000000L + sets$Index), all(hashes$seed == stage1$anchor_seed),
              all(stage1$primary_seed == 38000000L + sets$Index),
              all(stage1$secondary_seed == 39000000L + sets$Index))
    lower <- sets$Analyte != "CRP"
    data.frame(sets[c("Index", "Analyte", "N", "Scenario", "fractionPathol", "startSeed", "decimals")],
        h = 10^(-sets$decimals), truth_lower = ifelse(lower, sets$GT_LRL, NA_real_),
        truth_upper = sets$GT_URL, requested_lower = lower, upper_probability = ifelse(lower, 0.975, 0.95),
        nonp_lambda = sets$nonp_lambda, nonp_mu = sets$nonp_mu, nonp_sigma = sets$nonp_sigma,
        nonp_shift = sets$nonp_shift, routine_n = stage1$routine_n, anchor_n = stage1$anchor_n,
        routine_hash = stage1$routine_hash, anchor_hash = stage1$anchor_hash,
        ribench_hashcode = sets$HashCode, anchor_seed = stage1$anchor_seed, fitter_seed = 123L,
        pit_primary_seed = stage1$primary_seed, pit_alternate_seed = stage1$secondary_seed,
        stage1_model_sha256 = stage1$model_sha256, stage1_result_hash = stage1$result_hash,
        stringsAsFactors = FALSE)
}

stage2_ribench_manifest_path <- function(cohort) file.path("stage2/ribench", paste0("design-", cohort, ".csv"))

stage2_ribench_write_manifests <- function() {
    for (cohort in c("small", "large")) {
        rows <- stage2_ribench_design(cohort)
        for (field in names(rows)) {
            if (is.double(rows[[field]])) {
                x <- rows[[field]]
                rows[[field]] <- ifelse(is.na(x), NA_character_, sprintf("%.17g", x))
            }
        }
        utils::write.table(rows, stage2_ribench_manifest_path(cohort), sep = ",", quote = FALSE,
                           row.names = FALSE, na = "")
    }
}
