

#'
#' This script converts raw TOM Agent data in csv format to .RData
#' NB: THIS ONLY NEEDS TO BE RUN ONCE
#'


# Setup
setwd(dirname(rstudioapi::getSourceEditorContext()$path))
library(tidyverse)

# Globals
DATA_PATH = "../results/all_results" # NB: adjust as needed
DATA_FILE = "all_results.csv" # name of file containing full dataset for all rounds


# Read data
tom_agent_data = read_csv(paste(DATA_PATH, DATA_FILE, sep = "/"))
# Save as RData
save(tom_agent_data, file = "rps_tom_agent_data.RData")
