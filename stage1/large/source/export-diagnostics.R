library(RIbench)
w<-commandArgs(TRUE)[1];t<-loadTestsetDefinition();t<-t[t$N==as.integer(Sys.getenv('RIBENCH_N')),]
d<-do.call(rbind,lapply(list.files(w,pattern='^custom-[0-9]+[.]csv$',full.names=TRUE),read.csv))
rows<-list()
for(algo in c('anchoredRI','anchorsOnly','refineR')){
 p<-read.csv(file.path(w,paste0(algo,'-all-performance.csv')))
 p<-merge(p,t[,c('Index','N','Distribution','fractionPathol')],by='Index')
 if(algo=='refineR'){
  p$model<-'BoxCox';p$shift<-p$Est_Shift;p$components<-1L;p$lrt_p<-NA_real_;p$lrt_statistic<-NA_real_;p$at_bound<-NA;p$anchor_seed<-NA_integer_
 }else p<-merge(p,d[d$algo==algo,c('Index','model','shift','components','lrt_p','lrt_statistic','at_bound','anchor_seed')],by='Index')
 rows[[algo]]<-p[,c('Analyte','Index','N','Distribution','fractionPathol','Algorithm','model','Est_Lambda','shift','components','at_bound','anchor_seed','lrt_statistic','lrt_p','zzDev_LRL','zzDev_URL','zzDevAbs_Ov')]
}
x<-do.call(rbind,rows);stopifnot(nrow(x)==4320,!anyDuplicated(x[,c('Index','Algorithm')]))
write.csv(x,file.path(w,'per-dataset-diagnostics.csv'),row.names=FALSE)
