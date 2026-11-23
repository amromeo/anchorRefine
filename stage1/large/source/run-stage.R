library(RIbench)
data.table::setDTthreads(1)
source('tools/ribench/reader-compat.R')
source('R/fit_anchored_ri.R');source('R/fit_anchored_shifted.R');source('tools/anchors-only/estimators.R')
args<-commandArgs(TRUE);workingDir<-normalizePath(args[1]);shard<-as.integer(args[2]);shards<-as.integer(args[3])
stage_n<-as.integer(Sys.getenv('RIBENCH_N'));stopifnot(stage_n %in% c(50000L,500000L))
testsets<-loadTestsetDefinition();testsets<-testsets[testsets$N==stage_n,];stopifnot(nrow(testsets)==1440)
source('tools/ribench/check-stage-anchors.R')
verify_anchors(testsets,workingDir)
testsets<-testsets[(seq_len(nrow(testsets))-1)%%shards==shard-1,]
generation<-system.time(generateBiomarkerTestSets(workingDir,subset=testsets,verbose=FALSE))
write.csv(data.frame(shard=shard,N=stage_n,seconds=generation[['elapsed']]),file.path(workingDir,paste0('generation-',shard,'.csv')),row.names=FALSE)
# Drop invalid/negative draws without replacement, as requested. Only the
# sample-size guard differs from Task A if fewer than 40 draws survive.
auto_anchors<-ao_auto
body(auto_anchors)<-parse(text=sub('length(a) == 40L','length(a) >= 2L',paste(deparse(body(ao_auto)),collapse='\n'),fixed=TRUE))[[1]]
percentiles_from_fit<-function(f,probs){
 z<-switch(f$transform,identity=f$limits,log=log(f$limits),shifted_log=log(f$limits-f$shift))
 mu<-mean(z);sigma<-diff(z)/(2*qnorm(.975));y<-mu+qnorm(probs)*sigma
 if(f$transform=='identity')y else f$shift+exp(y)
}
rows<-list();start<-proc.time()[['elapsed']]
for(i in seq_len(nrow(testsets))){
 s<-testsets[i,];stem<-paste0(s$Index,'_',s$Analyte,'_seed_',s$startSeed)
 x<-fread(file.path(workingDir,'Data',s$Analyte,paste0(stem,'.csv')))$V1
 stopifnot(digest::digest(x,algo='md5',serializeVersion=2,ascii=TRUE)==s$HashCode)
 set.seed(s$Index+17000000L)
 a<-RIbench:::invBoxCox(rnorm(40,s$nonp_mu,s$nonp_sigma),s$nonp_lambda)+s$nonp_shift
 a<-round(a[is.finite(a)&a>=0],s$decimals)
 probs<-if(s$Analyte=='CRP').95 else c(.025,.975)
 for(algo in c('anchoredRI','anchorsOnly')){
  error<-'';model<-'';shift<-NA_real_;components<-NA_integer_;bound<-NA;lrt_stat<-lrt_p<-NA_real_
  runtime<-system.time({estimate<-tryCatch({
   if(algo=='anchoredRI'){
    f<-fit_anchored_ri(x,rep('pooled',length(x)),a,transform='auto');components<-f$components
    result<-percentiles_from_fit(f,probs)
    tr<-function(v)switch(f$transform,identity=v,log=log(v),shifted_log=log(v-f$shift))
    tryCatch({y<-tr(a);z<-tr(f$limits);mu<-mean(z);sigma<-diff(z)/(2*qnorm(.975))
    own<-ao_normal(y);lrt_stat<-max(0,2*(own$loglik-sum(dnorm(y,mu,sigma,log=TRUE))));lrt_p<-pchisq(lrt_stat,2,lower.tail=FALSE)},error=function(e)NULL)
   }else{
    f<-auto_anchors(a);z<-f$mu+qnorm(probs)*f$sd
    result<-if(f$transform=='identity')z else f$shift+exp(z)
    # Retain Task A's exact 1.96 endpoints for the two-sided interval.
    if(length(probs)==2)result<-f$limits
   }
   model<-f$transform;shift<-f$shift;bound<-f$at_bound
   if(algo=="anchorsOnly")components<-1L
   if(any(!is.finite(result)))stop('Nonfinite estimate')
   as.numeric(result)
  },error=function(e){error<<-conditionMessage(e);rep(NA_real_,length(probs))})})
  # Exact structure observed from RIbench's percentile wrapper: object fit,
  # data.frame columns Percentile, PointEst, Runtime; only first row timed.
  fit<-data.frame(Percentile=probs,PointEst=estimate,Runtime=c(unname(runtime[3]),rep(NA_real_,length(probs)-1)))
  dest<-file.path(workingDir,'Results',algo,s$Analyte);dir.create(dest,recursive=TRUE,showWarnings=FALSE)
  save(fit,file=file.path(dest,paste0(stem,'_',algo,'.Rdata')))
  rows[[length(rows)+1]]<-data.frame(Index=s$Index,Analyte=s$Analyte,N=s$N,lambda=s$nonp_lambda,algo=algo,anchor_seed=s$Index+17000000L,anchors=length(a),model=model,shift=shift,components=components,runtime=unname(runtime[3]),error=error,at_bound=bound,lrt_statistic=lrt_stat,lrt_p=lrt_p)
 }
 cat('shard',shard,'completed',i,'of',nrow(testsets),'\n');flush.console()
}
write.csv(do.call(rbind,rows),file.path(workingDir,paste0('custom-',shard,'.csv')),row.names=FALSE)
# RIbench invokes refineR::findRI in its own Rscript process and saves its own format.
evaluateBiomarkerTestSets(workingDir,algoName='refineR',algoFunction='findRI',libs='refineR',sourceFiles=normalizePath('tools/ribench/reader-compat.R'),subset=testsets,verbose=FALSE)
write.csv(data.frame(shard=shard,n=nrow(testsets),wall_seconds=proc.time()[['elapsed']]-start),file.path(workingDir,paste0('runtime-',shard,'.csv')),row.names=FALSE)
writeLines(c(capture.output(sessionInfo()),paste('RIbench',packageVersion('RIbench'))),file.path(workingDir,paste0('versions-',shard,'.txt')))

paths<-c(list.files('R',full.names=TRUE),list.files('tools/ribench',pattern='[.]R$|[.]md$',full.names=TRUE),'tools/anchors-only/estimators.R')
write.csv(data.frame(path=paths,md5=unname(tools::md5sum(paths))),file.path(workingDir,paste0('sources-',shard,'.csv')),row.names=FALSE)
