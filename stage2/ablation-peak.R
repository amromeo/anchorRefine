# Development diagnostic using Tatjana Ammer's refineR 2.0.0 findMainPeak
# (GPL >= 3). Execute the pristine function's coarse scoring code. Capture
# its exact winning detected index before the clamp for 3-bin interpolation.
stage2_original_first_coarse <- local({
    upstream <- refineR:::findMainPeak
    steps <- as.list(body(upstream))
    assigns_peak <- function(e) {
        is.call(e) && identical(e[[1L]], quote(`<-`)) && identical(e[[2L]], quote(peakInd))
    }
    assignments <- which(vapply(steps, assigns_peak, logical(1)))
    stopifnot(length(assignments) == 2L)
    first <- assignments[1L]
    choice <- steps[[first]][[3L]]
    stopifnot(identical(choice, quote(min(length(qDensFullTr$x) - 1,
                                          max(2, peaks[which.max(area + height95 - locPrevP)])))))
    pre_clamp <- choice[[3L]][[3L]]
    capture <- substitute(list(index = INDEX, density = qDensFullTr, peaks = peaks, valleys = valleys),
                          list(INDEX = pre_clamp))
    body(upstream) <- as.call(c(steps[seq_len(first - 1L)], list(capture)))
    upstream
})

stage2_development_peak <- function(x, anchors, h, seed, election) {
    result <- data.frame(upstream_peak_index = NA_integer_, anchor_initial_index = NA_integer_,
                         same_peak = NA, initial_peak_count = length(election$peak_indices))
    if (!isTRUE(election$ok)) return(result)
    state <- stage2_rng()
    on.exit(stage2_restore_rng(state))
    stage2_job(seed, function() {
        raw <- stage2_routine(x)
        data <- rep(raw, times = ceiling(250 / length(raw))) - 0
        work <- stage2_working_data(data, refineR:::findRoundingBase(data))
        ab <- stage2_first_window(work$qData)
        original <- stage2_original_first_coarse(work$qData, ab, mStart = 24,
                                                 withHeight = TRUE, prevPeak = NULL)
        replay <- stage2_elect_peak(original$density, original$peaks, original$valleys,
                                    anchors, h, election$K)
        # Includes every raw detected coordinate, basin edge, vote and assignment.
        stopifnot(identical(replay, election), length(original$index) == 1L,
                  original$index %in% original$peaks)
        result$upstream_peak_index <- as.integer(original$index)
        result$anchor_initial_index <- as.integer(replay$index)
        result$same_peak <- result$upstream_peak_index == result$anchor_initial_index
        result
    })
}
