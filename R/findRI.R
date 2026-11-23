# Pass all arguments, including missing arguments, to the original implementation.
findRI <- function(..., mode = "passthrough") {
    if (!identical(mode, "passthrough")) {
        stop('The supported mode is "passthrough".', call. = FALSE)
    }
    refineR::findRI(...)
}
