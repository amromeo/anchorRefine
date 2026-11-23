library(RIbench)
workingDir<-normalizePath('tools/ribench',mustWork=TRUE);workingDir<-file.path(workingDir,'probe')
testsets<-loadTestsetDefinition();print(table(testsets$N));print(unique(testsets[,c('Analyte','nonp_lambda','nonp_shift')]))
s<-testsets[1,,drop=FALSE]
if(!file.exists(file.path(workingDir,'Data','Hb','1_Hb_seed_123.csv')))generateBiomarkerTestSets(workingDir,subset=s,verbose=FALSE)
evaluateBiomarkerTestSets(workingDir,algoName='probe',algoFunction='probe_percentiles',libs='stats',sourceFiles=normalizePath('tools/ribench/probe-wrapper.R'),requirePercentiles=TRUE,subset=s,verbose=FALSE)
p<-list.files(file.path(workingDir,'Results'),recursive=TRUE,full.names=TRUE,pattern='Rdata$');stopifnot(length(p)==1)
e<-new.env();objnames<-load(p,e);stopifnot(identical(objnames,'fit'),is.data.frame(e$fit),identical(names(e$fit),c('Percentile','PointEst','Runtime')),all(is.finite(e$fit$PointEst)));print(objnames);str(e$fit);dput(e$fit,file='tools/ribench/saved-format.R')
