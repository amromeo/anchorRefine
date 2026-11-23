# Study-only estimators. See PROTOCOL.md for the approved specification.
ao_normal <- function(y, jacobian=0, k=2L) {
 n<-length(y);mu<-mean(y);sigma<-sqrt(mean((y-mu)^2));s<-sd(y)
 if(any(!is.finite(y))||!is.finite(sigma)||sigma<=0)stop('Invalid transformed sample')
 ll<-sum(dnorm(y,mu,sigma,log=TRUE))+jacobian
 list(mu=mu,sd=s,mle_sd=sigma,loglik=ll,bic=-2*ll+k*log(n))
}
ao_oracle <- function(a,family) {
 y<-switch(family,normal=a,lognormal=log(a),shifted=log(a-10),stop('Unknown family'))
 f<-ao_normal(y);f$transform<-switch(family,normal='identity',lognormal='log',shifted='shifted_log')
 f$shift<-if(family=='shifted')10 else 0
 z<-f$mu+c(-1,1)*1.96*f$sd
 f$limits<-if(family=='normal')z else f$shift+exp(z)
 f$at_bound<-FALSE;f
}
ao_auto <- function(a) {
 stopifnot(is.numeric(a),length(a)==40L,all(is.finite(a)))
 fits<-list();diag<-list()
 add<-function(name,fun) {
  f<-tryCatch(fun(),error=identity)
  if(inherits(f,'error')) {diag[[name]]<<-data.frame(transform=name,bic=NA_real_,loglik=NA_real_,shift=NA_real_,at_bound=NA,status='failed',error=conditionMessage(f));return()}
  diag[[name]]<<-data.frame(transform=name,bic=f$bic,loglik=f$loglik,shift=f$shift,at_bound=f$at_bound,status='ok',error='')
  fits[[name]]<<-f
 }
 fixed<-function(name) {
  if(name=='log'&&any(a<=0))stop('Log domain invalid')
  y<-if(name=='identity')a else log(a)
  f<-ao_normal(y,if(name=='log')-sum(y)else 0)
  f$shift<-0;f$transform<-name;f$at_bound<-FALSE
  z<-f$mu+c(-1,1)*1.96*f$sd;f$limits<-if(name=='log')exp(z)else z;f
 }
 add('identity',function()fixed('identity'));add('log',function()fixed('log'))
 add('shifted_log',function(){
  spread<-mad(a);if(!is.finite(spread)||spread<=0)stop('Invalid anchor MAD')
  bounds<-min(a)+spread*c(-5,-.001);tol<-1e-8*max(1,diff(bounds))
  profile<-function(c){y<-log(a-c);ao_normal(y,-sum(y),3L)}
  objective<-function(c)profile(c)$loglik
  grid<-seq(bounds[1],bounds[2],length.out=1001L)
  vals<-vapply(grid,objective,numeric(1))
  loc<-which(vals[2:1000]>=vals[1:999]&vals[2:1000]>=vals[3:1001])+1L
  refined<-vapply(loc,function(i)optimize(objective,c(grid[i-1L],grid[i+1L]),maximum=TRUE,tol=tol)$maximum,numeric(1))
  candidates<-c(grid,refined);ll<-c(vals,vapply(refined,objective,numeric(1)))
  c<-candidates[which.max(ll)];f<-profile(c)
  f$shift<-c;f$transform<-'shifted_log';f$at_bound<-any(abs(c-bounds)<=tol)
  f$limits<-c+exp(f$mu+c(-1,1)*1.96*f$sd);f$bounds<-bounds;f
 })
 diagnostics<-do.call(rbind,diag)
 if(!length(fits))return(list(limits=c(NA_real_,NA_real_),diagnostics=diagnostics,error='No valid candidate'))
 scores<-vapply(fits,function(f)f$bic,numeric(1));i<-which(scores<=min(scores)+1e-8)[1]
 f<-fits[[i]];f$diagnostics<-diagnostics;f$error<-'';f
}
