# RIbench's published hashes describe numeric values, but fread can leave an
# internal growable-vector flag that R serializes. Copying through +0L removes
# that flag without changing values or integer/double type. The original
# RIbench hash validation still runs and must pass before any fit.
fread <- function(...) {
 out<-data.table::fread(...)
 for(n in names(out))if(is.numeric(out[[n]])){
  old<-out[[n]];new<-old+0L
  stopifnot(identical(typeof(old),typeof(new)),identical(as.vector(old),as.vector(new)))
  data.table::set(out,j=n,value=new)
 }
 out
}
