# Experimental Stage 2 single-fit entry point. K is explicit during development.
fit_guided <- function(x, anchors, increment, seed, K, arm = "full") {
    stage2_fit(x = x, anchors = anchors, h = increment, seed = seed, K = K, arm = arm)
}
