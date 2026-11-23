# Independent readback using base R object equality and the full precision C2 RDS.
directory <- commandArgs(TRUE)[1]
cases <- read.csv("archive/c2/testsets.csv")
c2file <- "refineR-native-performance.rds"
unzip("archive/c2/ribench-scored-independent.zip", files=c2file, exdir=tempdir())
c2 <- do.call(rbind,readRDS(file.path(tempdir(),c2file))$resRIs)
same_table <- read.csv(gzfile(file.path(directory,"same-machine.csv.gz")))
cross_table <- read.csv(gzfile(file.path(directory,"historical-audit.csv.gz")))
total <- comparisons <- endpoints <- 0L
for (file in list.files(file.path(directory,"shards"), full.names=TRUE, pattern="[.]zip$")) {
    out <- tempfile(); dir.create(out)
    names <- c("cran-1", "vendored-1","cran-2","vendored-2")
    unzip(file, files=paste0(names,".rds"), exdir=out)
    saved <- lapply(file.path(out,paste0(names,".rds")),readRDS)
    for (j in seq_along(saved[[1]]$records)) {
        rec <- lapply(saved,function(s)s$records[[j]])
        index <- rec[[1]]$Index
        ref <- c2[match(index,c2$Index),]
        stopifnot(all(vapply(rec,function(x)x$Index==index,logical(1))))
        small <- same_table[same_table$Index==index,]
        pairs <- list(engines_first=c(1,2),engines_repeat=c(3,4),cran_repeat=c(1,3),vendored_repeat=c(2,4))
        for (pair in names(pairs)) {
            a<-rec[[pairs[[pair]][1]]]; b<-rec[[pairs[[pair]][2]]]
            ok <- all(vapply(c("fit","native","historical"), function(k)
                identical(a[[k]], b[[k]], num.eq=FALSE,single.NA=FALSE), logical(1)))
            stopifnot(nrow(small)==4L, identical(ok, small$exact[small$pair==pair]))
            comparisons <- comparisons+1L
        }
        crp <- ref$Analyte == "CRP"
        archived <- if(crp) ref$URL else c(ref$LRL,ref$URL)
        width <- if (crp) ref$URL else ref$URL-ref$LRL
        dst <- rec[[2]]$historical$value$PointEst
        hist <- cross_table[cross_table$Index==index,]
        hist <- hist[order(hist$probability),]
        stopifnot(length(dst)==nrow(hist), length(archived)==nrow(hist))
        inside <- is.finite(width) & width>0 & is.finite(dst) & is.finite(archived) &
                  abs(dst-archived)<=width/1000
        reconstructed <- !is.na(hist$reconstruction_error) & hist$reconstruction_error <= width/1000
        stopifnot(identical(as.logical(inside & reconstructed & hist$fit_status==hist$archived_status),
                            hist$historical_pass))
        endpoints <- endpoints+length(dst)
        total <- total+1L
    }
    unlink(out,recursive=TRUE)
}
stopifnot(total==nrow(cases), comparisons==11520L, endpoints==5472L)
cat("Independent native R readback verified", comparisons,"exact comparison flags and",endpoints,
    "C2 tolerance decisions over",total,"datasets.\n")
