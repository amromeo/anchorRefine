# Read-only post-run comparison. Only base R is required.
# Rscript --vanilla verify-archived-z.R small|large c2.zip primary/estimates.csv output-dir
args <- commandArgs(TRUE)
stopifnot(length(args) == 4L)
cohort <- match.arg(args[1], c("small", "large"))
archive <- args[2]
est_csv <- args[3]
out <- args[4]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
csv <- read.csv(est_csv, colClasses = "character", na.strings = "", stringsAsFactors = FALSE)
r <- readRDS(file.path(dirname(est_csv), "results.rds"))$estimates
key <- c("Index", "Analyte", "extraction", "method", "endpoint")
stopifnot(nrow(csv) == nrow(r), !anyDuplicated(csv[key]), !anyDuplicated(r[key]))
for (field in key) stopifnot(identical(as.character(r[[field]]), csv[[field]]))
fmt <- function(x) ifelse(is.na(x), NA_character_, sprintf("%.17g", x))
for (field in c("z", "estimate")) stopifnot(identical(fmt(r[[field]]), csv[[field]]))
r <- r[r$extraction == "historical", ]
methods <- c(refineR = "refineR", anchorsOnly = "anchorsOnly", anchoredRI_old = "anchoredRI")
members <- paste0(methods, "-native-performance.rds")
tmp <- tempfile("archive-scores-")
dir.create(tmp)
utils::unzip(archive, files = members, exdir = tmp)
expected_n <- if (cohort == "small") 2880L else 1440L
score_kind <- function(x) ifelse(is.nan(x), "NaN", ifelse(is.na(x), "NA", ifelse(is.infinite(x),
    ifelse(x > 0, "+Inf", "-Inf"), "finite")))
summaries <- list()
differences <- list()
for (method in names(methods)) {
    original <- readRDS(file.path(tmp, paste0(methods[[method]], "-native-performance.rds")))
    wide <- do.call(rbind, original$resRIs)
    stopifnot(!anyDuplicated(wide$Index), nrow(wide) == expected_n)
    for (endpoint in c("lower", "upper")) {
        cols <- if (endpoint == "lower") c("zzDev_LRL", "LRL") else c("zzDev_URL", "URL")
        ref <- if (endpoint == "lower") wide[wide$Analyte != "CRP", ] else wide
        actual <- r[r$method == method & r$endpoint == endpoint, ]
        stopifnot(setequal(actual$Index, ref$Index), !anyDuplicated(actual$Index))
        ref <- ref[match(actual$Index, ref$Index), ]
        stopifnot(identical(as.character(ref$Analyte), actual$Analyte))
        sel <- c(z = cols[1L], estimate = cols[2L])
        for (field in names(sel)) {
            x <- actual[[field]]
            y <- ref[[sel[[field]]]]
            same_kind <- score_kind(x) == score_kind(y)
            both_finite <- is.finite(x) & is.finite(y)
            same <- same_kind & (!both_finite | (x == y))
            err <- abs(x[both_finite] - y[both_finite])
            cut_diff <- function(cut, op) sum(op(abs(x[both_finite]), cut) != op(abs(y[both_finite]), cut))
            threshold <- field == "z"
            summaries[[length(summaries) + 1L]] <- data.frame(cohort, method, endpoint, field,
                matched_rows = length(x), exactly_equal = sum(same), both_finite = sum(both_finite),
                archived_nonfinite = sum(!is.finite(y)), results_nonfinite = sum(!is.finite(x)),
                nonfinite_kind_diff = sum(!same_kind), max_finite_abs_diff = fmt(max(c(0, err))),
                differs_abs_lt_0.25 = if (threshold) cut_diff(0.25, `<`) else NA,
                differs_abs_gt_1 = if (threshold) cut_diff(1, `>`) else NA,
                differs_abs_gt_5 = if (threshold) cut_diff(5, `>`) else NA)
            if (any(!same)) {
                d <- data.frame(actual[!same, c("Index", "Analyte", "N")], method, endpoint, field,
                                archived = fmt(y[!same]), stage1 = fmt(x[!same]))
                differences[[length(differences) + 1L]] <- d
            }
        }
    }
}
write.csv(do.call(rbind, summaries), file.path(out, paste0(cohort, "-archive-readback.csv")), row.names = FALSE, na = "")
if (length(differences)) {
    write.csv(do.call(rbind, differences), file.path(out, paste0(cohort, "-archive-differences.csv")), row.names = FALSE)
}
