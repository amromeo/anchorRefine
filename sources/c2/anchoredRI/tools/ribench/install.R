install.packages('https://cran.r-project.org/src/contrib/Archive/data.table/data.table_1.16.4.tar.gz',repos=NULL,type='source')
install.packages(c('RIbench','refineR','digest'),repos='https://cloud.r-project.org')
stopifnot(as.character(packageVersion('RIbench'))=='1.0.2',as.character(packageVersion('data.table'))=='1.16.4',as.character(packageVersion('refineR'))=='2.0.0')
