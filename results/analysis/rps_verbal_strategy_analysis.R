
#'
#' Examine human free response descriptions of sequential opponent strategies
#'


# SETUP ----
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))

library(tidyverse)

load("data_processed/rps_human_free_resp_data.RData") # human free response answers
load("data_processed/rps_tom_agent_free_resp_data.RData") # hypothetical minds descriptions of opponent strategy


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

HYP_MINDS_STRATEGY_LOOKUP = list("self_transition_up" = "Self-transition (+)",
                                 "self_transition_down" = "Self-transition (−)",
                                 "opponent_transition_up" = "Opponent-transition (+)",
                                 "opponent_transition_stay" = "Opponent-transition (0)",
                                 "W_stay_L_up_T_down" = "Previous outcome (W0L+T−)",
                                 "W_up_L_down_T_stay" = "Previous outcome (W+L−T0)",
                                 "prev_outcome_prev_transition" = "Previous outcome, \nprevious transition"
)



# ANALYSIS: Human responses ----
human_free_resp_data_clean = human_free_resp_data_clean %>%
  rowwise() %>%
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )


# Print responses in each condition, ordered by win rate (desc)
human_free_resp_data_clean %>%
  arrange(bot_strategy_str, desc(win_pct)) %>%
  select(bot_strategy_str, player_id, win_pct, free_resp_answer) %>%
  print(n = nrow(.))


# Good exemplars:
# Self-transiiton (+)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "f3540a99-31be-4868-aa91-39801ac216ba"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "f3540a99-31be-4868-aa91-39801ac216ba"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "6c6c787a-5e80-4818-98f0-c0d1c0cb33c5"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "6c6c787a-5e80-4818-98f0-c0d1c0cb33c5"]

# Self-transition (-)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "c44472de-22f9-4cbf-89a4-8d330fd6f35a"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "c44472de-22f9-4cbf-89a4-8d330fd6f35a"]

# Opponent-transition (+)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "d75c7e2e-b1ba-4877-a14d-628d817fa2af"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "d75c7e2e-b1ba-4877-a14d-628d817fa2af"]

# Opponent-transition (0)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "352fa34b-d5b4-4a35-832e-e9365fd3dd76"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "352fa34b-d5b4-4a35-832e-e9365fd3dd76"]

# Previous outcome (W0L+T−)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "962a402b-2bef-478e-a21b-22cb97548ebb"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "962a402b-2bef-478e-a21b-22cb97548ebb"]

# Previous outcome (W+L−T0)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "7b94c71f-98ec-4000-a5d3-15423810e156"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "7b94c71f-98ec-4000-a5d3-15423810e156"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "22bf7dfd-ed4f-4c31-9afc-1d74b2be2cde"]
human_free_resp_data_clean$win_pct[human_free_resp_data_clean$player_id == "22bf7dfd-ed4f-4c31-9afc-1d74b2be2cde"]

# Unsuccessful responses
# "Theory of mind"
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "316a464e-fe5a-461c-aa9a-55eebd75c4d9"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "f6737a3d-489b-40b7-a169-ae6fc00cb7d5"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "a10fe586-6c42-4ed4-84dd-ac277d502d12"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "ec0c5956-7f17-4849-98fd-0f8102d6d09c"]

# "No strategy"
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "69310af3-7899-4218-a29f-c142b951a2f6"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "9292407d-9be8-430d-aade-cda0c1226a63"]

# "Bottom up" (e.g. trying different patterns and seeing what works)
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "06f2b367-47a8-4d55-912c-974cee03256e"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "48ddce11-71ba-4338-a7f5-7cba53baa4d5"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "0e9118bd-02a1-49bd-b09d-cdfeab15f9c2"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "902f6e89-e2bb-47fc-b236-b1504f7fd2ce"]

human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "fa5449d2-5c2e-4a6e-b029-8f87d636672f"]
human_free_resp_data_clean$free_resp_answer[human_free_resp_data_clean$player_id == "c9506a67-9a35-4b1c-b246-a953274f7fe7"]



# ANALYSIS: Hypothetical Minds responses ----

glimpse(tom_agent_hypotheses)

tom_agent_hypotheses = tom_agent_hypotheses %>%
  rowwise() %>%
  mutate(
    bot_strategy_str = factor(HYP_MINDS_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )

# Print responses in each condition, ordered by win rate
tom_agent_hypotheses %>%
  filter(llm == "gpt4o") %>%
  arrange(bot_strategy_str, desc(win_pct)) %>%
  select(bot_strategy_str, timestamp, win_pct, hypothesis) %>%
  print(n = nrow(.))



# Self-transition (+)
tom_agent_hypotheses$hypothesis[tom_agent_hypotheses$timestamp == "2024-08-12_20-35-40"]
tom_agent_hypotheses$win_pct[tom_agent_hypotheses$timestamp == "2024-08-12_20-35-40"]

tom_agent_hypotheses$hypothesis[tom_agent_hypotheses$timestamp == "2024-08-22_14-07-00"]
tom_agent_hypotheses$win_pct[tom_agent_hypotheses$timestamp == "2024-08-22_14-07-00"]

tom_agent_hypotheses$hypothesis[tom_agent_hypotheses$timestamp == "2024-08-21_15-13-00"]
tom_agent_hypotheses$win_pct[tom_agent_hypotheses$timestamp == "2024-08-21_15-13-00"]


