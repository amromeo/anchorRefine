\name{check_anchors}
\alias{check_anchors}
\title{Check a refineR fit against 40 independently screened healthy anchors}
\usage{
check_anchors(fit, anchors, decimals, seed)
}
\arguments{
  \item{fit}{A refineR fit with finite Mu, Sigma, Lambda and Shift. The supported healthy model has positive Sigma and nonnegative Lambda and Shift.}
  \item{anchors}{Numeric vector of 40 independent screened healthy observations, in their original draw order.}
  \item{decimals}{Number of decimal places used to round the anchor measurements. A negative value denotes rounding to a power of ten above one.}
  \item{seed}{Integer seed for randomization within the observed rounding intervals. In RIbench the primary seed is 38000000 + Index, with 39000000 + Index for sensitivity analysis.}
}
\description{Evaluates compatibility with the fitted healthy model by a randomized probability integral transform that accounts for the measurement precision. The likelihood-ratio test compares location and spread of the transformed observations to a standard normal distribution. It uses the finite-sample null distribution with the routine-data model held fixed.}
\value{A list containing status (keep, decline or check_failed), reason, statistic and p. At p below 0.01 the proposed interval is declined. Use the original fitted limits for a kept result.}
