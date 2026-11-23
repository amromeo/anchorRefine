library(RIbench)
a<-commandArgs(TRUE);workingDir<-normalizePath(a[1]);testsets<-loadTestsetDefinition();testsets<-testsets[testsets$N==as.integer(Sys.getenv("RIBENCH_N")),]
algos<-c('anchoredRI','anchorsOnly','refineR')
for(algo in algos)stopifnot(length(list.files(file.path(workingDir,'Results',algo),pattern='Rdata$',recursive=TRUE))==1440)
score<-tryCatch(evaluateAlgorithmResults(workingDir,algoNames=algos,subset=testsets),error=function(e){
 if(!grepl('length(errorList) == length(nameList)',conditionMessage(e),fixed=TRUE))stop(e)
 writeLines(conditionMessage(e),file.path(workingDir,'RIbench-subset-plot-error.txt'))
 message('RIbench subset plot failed; exporting unchanged native metrics and stage category scores.')
 NULL
})
saveRDS(score,file.path(workingDir,'stage-benchmark-score.rds'));capture.output(str(score),file=file.path(workingDir,'stage-benchmark-score.txt'))
# Preserve the native per-dataset performance tables, including FT4 alone.
all<-list()
for(algo in algos){
 markers<-unique(testsets$Analyte)
 res<-RIbench:::readResultFilesAll(analytes=markers,algo=algo,baseDir=workingDir,tableTCs=testsets)
 ri<-if(inherits(res[[1]][[1]],'RWDRI'))RIbench:::computeRIsAll(analytes=markers,algo=algo,resIn=res,tableTCs=testsets,truncNormal=FALSE) else RIbench:::getRIsAllwithoutModel(analytes=markers,algo=algo,resIn=res,tableTCs=testsets)
 perf<-RIbench:::computePerfMeasAll(analytes=markers,algo=algo,risIn=ri,tableTCs=testsets,cutoffZ=5)
 all[[algo]]<-perf
 saveRDS(perf,file.path(workingDir,paste0(algo,'-native-performance.rds')))
 write.csv(perf$summaryError,file.path(workingDir,paste0(algo,'-native-summary.csv')),row.names=FALSE)
 for(marker in names(perf$resRIs))write.csv(perf$resRIs[[marker]],file.path(workingDir,paste0(algo,'-',marker,'-performance.csv')),row.names=FALSE)
 write.csv(ri[['FT4']],file.path(workingDir,paste0(algo,'-lambda-0.432.csv')),row.names=FALSE)
 saveRDS(ri[['FT4']],file.path(workingDir,paste0(algo,'-lambda-0.432.rds')))
}
saveRDS(all,file.path(workingDir,'all-performance.rds'))
# Keep RIbench's fixed 27-row layout; absent high-N categories remain NA.
# The overall row summarizes only this observed stage subset.
small_score<-RIbench:::getBenchmarkResults(errorList=all,nameVec=algos,tableTCs=testsets,cutoffZ=5,
 perfCombination='mean')
saveRDS(small_score,file.path(workingDir,'stage-category-score.rds'))
capture.output(print(small_score),file=file.path(workingDir,'stage-category-score.txt'))
cat('Completed stage scoring; lambda=0.432 results retained separately\n')
rows<-list()
for(algo in algos){
 p<-do.call(rbind,all[[algo]]$resRIs)
 write.csv(p,file.path(workingDir,paste0(algo,'-all-performance.csv')),row.names=FALSE)
 for(group in c('all','lambda=0.432',unique(p$Analyte))){
  q<-if(group=='all')p else if(group=='lambda=0.432')p[abs(p$GT_Lambda-.432)<1e-12,] else p[p$Analyte==group,]
  valid<-is.finite(q$LRL)&is.finite(q$URL)
  rows[[length(rows)+1]]<-data.frame(group=group,algorithm=algo,n=nrow(q),failed=sum(!valid),mean_abs_z=mean(q$zzDevAbs_Ov,na.rm=TRUE),mean_capped_abs_z=mean(q$zzDevAbsCutoff_Ov,na.rm=TRUE),mean_abs_percent_error=mean(q$AbsPercError_Ov,na.rm=TRUE),runtime_total_seconds=sum(q$Runtime,na.rm=TRUE),runtime_median_seconds=median(q$Runtime,na.rm=TRUE),runtime_p90_seconds=unname(quantile(q$Runtime,.9,na.rm=TRUE)))
 }
}
summary<-do.call(rbind,rows);write.csv(summary,file.path(workingDir,'summary.csv'),row.names=FALSE)
text<-c(paste('# RIbench N =',Sys.getenv('RIBENCH_N')),'', 'RIbench evaluateAlgorithmResults stopped at a sample-size subset plot. Native per-dataset metrics and category scores were recovered using its unchanged computePerfMeasAll and getBenchmarkResults functions. No fits were rerun.', '', 'All 1,440 datasets were evaluated with each of three methods. This is a subset evaluation, not the published full RIbench benchmark score. AnchoredRI and anchorsOnly receive simulated screened anchors; refineR receives only routine data.','', 'Runtime below is the sum of per-fit elapsed seconds, excluding generation, installation and workflow queueing. Parallel execution wall time should be reported separately.','', '| Subset | Method | N | Failed | Mean absolute Z deviation | Capped mean | Fit runtime (minutes) |','|---|---|---:|---:|---:|---:|---:|')
for(i in which(summary$group %in% c('all','lambda=0.432'))){r<-summary[i,];text<-c(text,sprintf('| %s | %s | %d | %d | %.4f | %.4f | %.2f |',r$group,r$algorithm,r$n,r$failed,r$mean_abs_z,r$mean_capped_abs_z,r$runtime_total_seconds/60))}
text<-c(text,'','The uncapped metric summarizes available results; inspect failure counts with it. Capped deviations and RIbench subset scores retain RIbench conventions. FT4 is the lambda=0.432 subset. CRP uses its one-sided 95th percentile.','', 'Stage sample size is specified above. Runtime is the sum of fit times. Source versions and native outputs are retained.')
writeLines(text,file.path(workingDir,'REPORT.md'))
