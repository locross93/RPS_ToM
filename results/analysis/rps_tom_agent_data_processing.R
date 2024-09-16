

#'
#' This script converts raw TOM Agent data in csv format to .RData
#' NB: this only needs to be run once
#'

# TODO if we don't add complexity to this script, consider consolidating with `rps_human_data_processing.R`

# Setup
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))
library(tidyverse)

# Globals
DATA_PATH = "../all_models" # NB: adjust as needed
DATA_FILE = "rps_scores_all_rounds.csv" # name of file containing full dataset for all rounds


# Read data
tom_agent_data = read_csv(paste(DATA_PATH, DATA_FILE, sep = "/"))
# Save as RData
save(tom_agent_data, file = "rps_tom_agent_data.RData")



