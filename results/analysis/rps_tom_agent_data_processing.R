

#'
#' This script converts raw TOM Agent data in csv format to .RData
#' NB: this only needs to be run once
#'


# Setup
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))
library(tidyverse)

# Globals
DATA_PATH = "../all_models" # NB: adjust as needed
DATA_FILE = "rps_scores_all_rounds.csv" # name of file containing full dataset for all rounds
DATA_OUTPUT_PATH = "data_processed" # name of directory for output RData file
DATA_OUTPUT_FILE = "rps_tom_agent_data.RData" # name of output RData file

# Read data
tom_agent_data = read_csv(paste(DATA_PATH, DATA_FILE, sep = "/"))
glimpse(tom_agent_data)

# Filter
tom_agent_data_clean = tom_agent_data %>% select(sequential_agent_class:timestamp)


# Examine
tom_agent_data_clean %>%
  group_by(tom_agent_class, sequential_agent_class) %>%
  summarize(rounds = n_distinct(timestamp))




# Save as RData
save(tom_agent_data_clean,
     file = paste(DATA_OUTPUT_PATH, DATA_OUTPUT_FILE, sep = "/"))



