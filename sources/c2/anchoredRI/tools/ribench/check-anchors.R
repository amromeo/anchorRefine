verify_anchors<-function(testsets,workingDir){
 hashes<-vapply(seq_len(nrow(testsets)),function(i){s<-testsets[i,];set.seed(17000000L+s$Index);a<-RIbench:::invBoxCox(rnorm(40,s$nonp_mu,s$nonp_sigma),s$nonp_lambda)+s$nonp_shift;a<-round(a[is.finite(a)&a>=0],s$decimals);digest::digest(a,algo='sha256')},character(1))
 stopifnot(length(hashes)==2880L,!anyDuplicated(hashes))
 write.csv(data.frame(Index=testsets$Index,seed=17000000L+testsets$Index,sha256=hashes),file.path(workingDir,'anchor-sample-hashes.csv'),row.names=FALSE)
 cat('Verified 2880 distinct rounded anchor samples before fitting\n')
}
