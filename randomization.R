#install.packages('blockrand')
library(blockrand)

randomization <- function(number_of_participants, number_of_interventions, interventions)
{
  bfla <- blockrand(number_of_participants,
                    num.levels = number_of_interventions, # number of treatments
                    levels = c(interventions, recursive=TRUE), # arm names
                    # #stratum = "Bfail.LowAlb", # stratum name
                    id.prefix = "BfLA", # stratum abbrev
                    block.sizes = c(1,2,3), # times arms = 3,6,9
                    block.prefix = "BfLA" # stratum abbrev
  )
  return(bfla)
}