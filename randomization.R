#install.packages('blockrand')
library(blockrand)

randomization <- function(){
  bfla <- blockrand(n = 60,
                      num.levels = 3, # three treatments
                      levels = c("CS", "CS/Tofa", "CS/Upa"), # arm names
                      stratum = "Bfail.LowAlb", # stratum name
                      id.prefix = "BfLA", # stratum abbrev
                      block.sizes = c(1,2,3), # times arms = 3,6,9
                      block.prefix = "BfLA" # stratum abbrev
  )

  return(bfla)
}