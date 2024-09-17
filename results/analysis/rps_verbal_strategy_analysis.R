
#'
#' Examine human free response descriptions of sequential opponent strategies
#'


# SETUP ----
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))

library(tidyverse)

load("data_processed/rps_human_free_resp_data.RData")
# load("data_processed/rps_human_trial_data.RData")


# GLOBALS ----

STRATEGY_LABELS = c(
  "Self-transition (+)",
  "Self-transition (−)",
  "Opponent-transition (+)",
  "Opponent-transition (0)",
  "Previous outcome (W0L+T−)",
  "Previous outcome (W+L−T0)",
  "Previous outcome, \nprevious transition"
)

HUMAN_TRIAL_STRATEGY_LOOKUP = list("prev_move_positive" = "Self-transition (+)",
                                   "prev_move_negative" = "Self-transition (−)",
                                   "opponent_prev_move_positive" = "Opponent-transition (+)",
                                   "opponent_prev_move_nil" = "Opponent-transition (0)",
                                   "win_nil_lose_positive" = "Previous outcome (W0L+T−)",
                                   "win_positive_lose_negative" = "Previous outcome (W+L−T0)",
                                   "outcome_transition_dual_dependency" = "Previous outcome, \nprevious transition"
)


# Get condition and win percentage for each participant's free response
# NB: this excludes 3 participants for whom we don't have trial data
human_free_resp_data = human_free_resp_data %>%
  filter(
    player_id %in% unique(human_trial_data$player_id)
  ) %>%
  inner_join(
    # calculate win percentage here as a potential covariate
    # (was saying the right opponent strategy contingent on winning?)
    human_trial_data %>%
      group_by(game_id, player_id, bot_strategy) %>%
      count(win = player_outcome == "win") %>%
      mutate(total = sum(n),
             win_pct = n / total) %>%
      filter(win == TRUE) %>%
      select(game_id, player_id, bot_strategy, win_pct),
    by = c("game_id", "player_id")
  ) %>%
  rowwise() %>%
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )


# Print responses in each condition, ordered by win rate (desc)
human_free_resp_data %>%
  arrange(bot_strategy_str, desc(win_pct)) %>%
  select(bot_strategy_str, player_id, win_pct, free_resp_answer)



