# The frozen Stage 2 candidate uses the previously evaluated peak-only arm.
stage2_selected_rule <- "peak"

stage2_selected_fit <- function(x, anchors, h, seed, prepared = NULL, baseline = NULL) {
    stage2_fit(x = x, anchors = anchors, h = h, seed = seed, K = 24L,
               arm = stage2_selected_rule, prepared = prepared, baseline = baseline)
}
