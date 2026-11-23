\name{findRI}
\alias{findRI}
\alias{getRI}
\title{Fit a reference interval using refineR 2.0.0}
\usage{
findRI(..., mode = "passthrough")
}
\arguments{
  \item{...}{Arguments to \code{\link[refineR]{findRI}}, including the routine measurement vector \code{Data}.}
  \item{mode}{Use \code{"passthrough"} to run the vendored version of refineR.}
}
\description{
  Runs the upstream algorithm. Use the re-exported \code{\link[refineR]{getRI}}
  to calculate limits from the fitted model. See the upstream manual for the
  model choices, bootstrap options, percentile conventions and returned fields.
}
\value{\code{findRI} returns the upstream \code{RWDRI} fit. \code{getRI}
returns the upstream data frame of limits.}
\details{
  anchorRefine is derived from refineR 2.0.0 by Matthias Beck, Tatjana Ammer,
  Christopher M Rank and Andre Schuetzenmeister. It is an independent project
  and is not endorsed by the refineR authors.
}
