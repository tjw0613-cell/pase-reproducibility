args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
cohort <- read.delim(args[1], check.names=FALSE)
reported <- read.delim(args[2], check.names=FALSE)
for (method in c("equal_t","reml_hksj")) {
    d <- cohort[cohort$analysis=="primary" & cohort$method==method,]
    result <- reported[reported$method==method,]
    fisher <- method=="reml_hksj"
    y <- if (fisher) d$estimate_z else d$estimate
    v <- d$se^2
    contrast <- rbind(c(1,0,-1),c(0,1,-1))
    diff <- as.vector(contrast %*% y)
    objective <- function(tau2){
        covariance <- contrast %*% diag(v+tau2) %*% t(contrast)
        as.numeric(determinant(covariance,logarithm=TRUE)$modulus) + sum(diff * solve(covariance,diff))
    }
    opt <- optimize(objective,c(0,1),tol=1e-14)
    tau2 <- if(objective(0)<opt$objective) 0 else opt$minimum
    w <- 1/(v+tau2)
    mean <- weighted.mean(y,w)
    s <- sqrt(max(1,sum(w*(y-mean)^2)/2)/sum(w))
    fc <- weighted.mean(y,1/v); Q <- sum((y-fc)^2/v)
    widths <- c(s*qt(.975,2),sqrt(tau2+s^2)*qt(.975,1))
    target <- c(mean,mean-widths[1],mean+widths[1],mean-widths[2],mean+widths[2])
    if(fisher) target <- tanh(target)
    actual <- unlist(result[c("estimate","low","high","pi_low","pi_high")],use.names=FALSE)
    stopifnot(length(y)==3, max(abs(target-actual))<3e-7,
              abs(result$tau2-tau2)<1e-8, abs(result$I2_percent-100*max(0,(Q-2)/Q))<1e-7)
    cat(method, "max abs difference:", max(abs(target-actual)),"\n")
}
