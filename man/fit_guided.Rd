\name{fit_guided}
\alias{fit_guided}
\title{Fit an anchor-guided refineR Box-Cox model}
\usage{
fit_guided(x, anchors, increment, seed, K, arm = "full")
}
\arguments{
  \item{x}{Routine numeric measurements.}
  \item{anchors}{Forty independent screened healthy measurements in original draw order.}
  \item{increment}{Positive rounding increment of the anchor measurements.}
  \item{seed}{Integer seed for the routine fitter.}
  \item{K}{Minimum number of anchor votes, 24 or 28.}
  \item{arm}{One of "full", "peak", "start", "region", or "baseline".}
}
\description{Uses screened healthy observations to guide refineR's peak and parameter search. A failed or ambiguous search falls back to the original routine-data fit.}
\value{A list with the fitted RWDRI object (or NULL on failure), fit status, fallback flag, reason and peak diagnostics. This function returns the fit before applying the anchor compatibility check.}
