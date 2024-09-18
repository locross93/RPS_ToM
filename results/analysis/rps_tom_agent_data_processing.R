

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
FREE_RESP_FILE = "rps_scores_and_hyps.csv" # name of file containing model hypotheses about opponent strategy
OUTPUT_PATH = "data_processed" # name of directory for output RData file
# DATA_OUTPUT_FILE = "rps_tom_agent_data.RData" # name of output RData file
# FREE_RESP_OUTPUT_FILE = "rps_tom_agent_free_resp_data.RData" # name of output RData file for hypotheses about opponent strategy

# Read data
tom_agent_data = read_csv(paste(DATA_PATH, DATA_FILE, sep = "/"))
glimpse(tom_agent_data)


tom_agent_hypotheses = read_csv(paste(DATA_PATH, FREE_RESP_FILE, sep = "/"))
glimpse(tom_agent_hypotheses)


# Filter
tom_agent_data_clean = tom_agent_data %>% select(sequential_agent_class:timestamp)


# Examine
tom_agent_data_clean %>%
  group_by(tom_agent_class, sequential_agent_class) %>%
  summarize(rounds = n_distinct(timestamp))




# Save as RData
save(tom_agent_data_clean,
     file = paste(OUTPUT_PATH, "rps_tom_agent_data.RData", sep = "/"))
save(tom_agent_hypotheses,
     file = paste(OUTPUT_PATH, "rps_tom_agent_free_resp_data.RData", sep = "/"))


