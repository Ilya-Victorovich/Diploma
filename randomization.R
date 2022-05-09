#install.packages('blockrand')
library(blockrand)

randomization <- function(number_of_participants, number_of_interventions, interventions, max_group_size)
{
  sizes <- c()
  i <- 0
  while(TRUE)
  {
    i <- i+1
    if(i * number_of_interventions > max_group_size)
      break
    else
      sizes <- c(sizes, i)
  }
  print(sizes)
  bfla <- blockrand(number_of_participants,
                    num.levels = number_of_interventions, # number of treatments
                    levels = c(interventions, recursive=TRUE), # arm names
                    # #stratum = "Bfail.LowAlb", # stratum name
                    id.prefix = "BfLA", # stratum abbrev
                    #block.sizes = c(1,2,3), # times arms = 3,6,9
                    block.sizes = sizes,
                    block.prefix = "BfLA" # stratum abbrev
  )
  return(bfla)
}