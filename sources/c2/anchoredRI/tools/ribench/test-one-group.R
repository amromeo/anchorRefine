old<-new.env();new<-new.env()
for(f in c('fit_anchored_ri.R','fit_anchored_shifted.R')){
 eval(parse(text=system(paste0('git show 55eee86b3f4111197b0043cc062ef0b781dc2057:anchoredRI/R/',f),intern=TRUE)),old)
 sys.source(file.path('R',f),new)
}
set.seed(472);x<-round(c(rnorm(300,30,3),rnorm(200,40,5)),2);a<-rnorm(40,30,3);g<-rep(c('a','b'),250)
for(t in c('identity','log','shifted_log')){
 p<-old$fit_anchored_ri(x,g,a,transform=t);q<-new$fit_anchored_ri(x,g,a,transform=t)
 stopifnot(isTRUE(all.equal(p,q,tolerance=1e-10)))
 one<-new$fit_anchored_ri(x,rep('pooled',length(x)),a,transform=t)
 stopifnot(ncol(one$weights)==1,all(is.finite(one$limits)),one$limits[1]<one$limits[2],abs(sum(one$weights)-1)<1e-10)
}
# One-group shifted objective gradient, including shift and mixture weight.
x<-sort(unique(x));counts<-matrix(rep(1,length(x)),ncol=1);calc<-new$.anchored_shift_objective(x,a,counts,2)
p<-c(log(30),log(40),log(.1),log(.15),0,0);eps<-1e-5
num<-sapply(seq_along(p),function(j){lo<-hi<-p;lo[j]<-lo[j]-eps;hi[j]<-hi[j]+eps;(calc(hi)-calc(lo))/(2*eps)})
stopifnot(max(abs(num-calc(p,TRUE)))<1e-5)
cat('Two-group regression, one-group fits, and analytic-gradient checks passed\n')
