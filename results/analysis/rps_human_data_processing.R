
#'
#' This script converts raw human performance data in csv format to .RData
#' NB: THIS ONLY NEEDS TO BE RUN ONCE
#'


# SETUP ----
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))
library(tidyverse)

# Globals
DATA_PATH = "../../.." # NB: this is just *outside* the root RPS_ToM directory
DATA_FILE = "rps_human_data.csv" # name of file containing full trial dataset for all rounds
FREE_RESP_FILE = "rps_human_free_resp.csv" # name of file containing free response strategy data for all participants
SLIDER_FILE = "rps_human_slider.csv" # name of file containing slider questionnaire data for all participants
GAME_ROUNDS = 300
STRATEGY_LEVELS = c("prev_move_positive", "prev_move_negative",
                    "opponent_prev_move_positive", "opponent_prev_move_nil",
                    "win_nil_lose_positive", "win_positive_lose_negative",
                    "outcome_transition_dual_dependency")


# READ DATA ----
# Note: the raw data csv has more unique participant data than we keep in this function.
# Some participants did not complete the full set of rounds.
# Several managed to complete 300 rounds twice with the same survey code.
# In this instance, we keep the earlier of the two to ensure parity with other participants.
# One participant emailed saying she had completed the full set of rounds, but we don't have complete data.
# All told, 218 students were given credit; the below produces 217 complete participant data sets.
read_bot_data = function(filename, strategy_levels, game_rounds) {
  # Read csv
  data = read_csv(filename)
  data$bot_strategy = factor(data$bot_strategy, levels = strategy_levels)
  # Remove all incomplete games
  incomplete_games = data %>%
    group_by(game_id, player_id) %>%
    summarize(rounds = max(round_index)) %>%
    filter(rounds < game_rounds) %>%
    select(game_id) %>%
    unique()
  data = data %>%
    filter(!(game_id %in% incomplete_games$game_id))
  # Remove any duplicate complete games that have the same completion code
  # NB: this can happen if somebody played all the way through but exited before receiving credit
  # First, fetch survey codes with multiple complete games
  repeat_codes = data %>%
    group_by(sona_survey_code) %>%
    filter(is_bot == 0) %>%
    summarize(trials = n()) %>%
    filter(trials > game_rounds) %>%
    select(sona_survey_code)
  # Next, get game id for the later complete game and remove it (below)
  duplicate_games = data %>%
    filter(sona_survey_code %in% repeat_codes$sona_survey_code &
             is_bot == 0  &
             round_index == game_rounds) %>%
    select(sona_survey_code, game_id, player_id, round_begin_ts) %>%
    group_by(sona_survey_code) %>%
    filter(round_begin_ts == max(round_begin_ts)) %>%
    distinct(game_id)
  data = data %>%
    filter(!game_id %in% duplicate_games$game_id)

  return(data)
}


# Read data
# NB: there are 3 participants who we have free resp (and slider) data but no trial data for,
# and 4 participants who we have trial data but no free resp data for.
# Below is not doing any filtering to remove people who aren't in intersection.
human_trial_data = read_bot_data(paste(DATA_PATH, DATA_FILE, sep = "/"),
                           STRATEGY_LEVELS,
                           GAME_ROUNDS)
human_free_resp_data = read_csv(paste(DATA_PATH, FREE_RESP_FILE, sep = "/"))
human_slider_data = read_csv(paste(DATA_PATH, SLIDER_FILE, sep = "/"))

# Save as RData
save(human_trial_data, file = "rps_human_trial_data.RData")
save(human_free_resp_data, file = "rps_human_free_resp_data.RData")
save(human_slider_data, file = "rps_human_slider_data.RData")





