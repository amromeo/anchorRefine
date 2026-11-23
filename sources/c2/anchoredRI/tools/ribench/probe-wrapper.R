source('tools/ribench/reader-compat.R')
probe_percentiles <- function(data,percentiles) data.frame(Percentile=percentiles,PointEst=as.numeric(quantile(data,percentiles)))
