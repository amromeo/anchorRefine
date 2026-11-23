library(RIbench)
w<-commandArgs(TRUE)[1];t<-loadTestsetDefinition();t<-t[t$N==as.integer(Sys.getenv("RIBENCH_N")),]
d<-do.call(rbind,lapply(list.files(w,pattern='^custom-[0-9]+[.]csv$',full.names=TRUE),read.csv))
a<-read.csv(file.path(w,'anchoredRI-all-performance.csv'));b<-read.csv(file.path(w,'anchorsOnly-all-performance.csv'));r<-read.csv(file.path(w,'refineR-all-performance.csv'))
rows<-list()
for(other in c('anchorsOnly','refineR')){
 q<-if(other=='anchorsOnly')b else r
 z<-merge(a[,c('Index','zzDevAbs_Ov')],q[,c('Index','zzDevAbs_Ov')],by='Index',suffixes=c('_anchored','_other'));z<-merge(z,t,by='Index');z$pathology<-ifelse(z$fractionPathol<=.2,'low (<=20%)','high (>20%)')
 for(dist in unique(z$Distribution))for(p in unique(z$pathology)){
  x<-z[z$Distribution==dist&z$pathology==p,];dif<-x$zzDevAbs_Ov_anchored-x$zzDevAbs_Ov_other
  rows[[length(rows)+1]]<-data.frame(distribution=dist,pathology=p,comparator=other,n=nrow(x),complete=sum(is.finite(dif)),mean_difference=mean(dif,na.rm=TRUE),anchored_wins=sum(dif<0,na.rm=TRUE),ties=sum(dif==0,na.rm=TRUE),comparator_wins=sum(dif>0,na.rm=TRUE))
 }
}
write.csv(do.call(rbind,rows),file.path(w,'paired-strata.csv'),row.names=FALSE)
extreme<-list()
for(algo in c('anchoredRI','anchorsOnly','refineR')){
 q<-switch(algo,anchoredRI=a,anchorsOnly=b,refineR=r)
 bad<-abs(q$zzDev_LRL)>5|abs(q$zzDev_URL)>5
 bad[q$Analyte=='CRP']<-abs(q$zzDev_URL[q$Analyte=='CRP'])>5
 q<-q[which(bad),];q<-merge(q,t[,c('Index','fractionPathol','Distribution')],by='Index')
 if(algo!='refineR')q<-merge(q,d[d$algo==algo,c('Index','model','components','at_bound')],by='Index',all.x=TRUE) else {
  q$model<-paste0('BoxCox lambda=',q$Est_Lambda,'; shift=',q$Est_Shift);q$components<-1L;q$at_bound<-NA
 }
 extreme[[algo]]<-q[,c('Index','Analyte','Algorithm','fractionPathol','Distribution','model','components','at_bound','zzDev_LRL','zzDev_URL')]
}
write.csv(do.call(rbind,extreme),file.path(w,'extreme-errors.csv'),row.names=FALSE)
