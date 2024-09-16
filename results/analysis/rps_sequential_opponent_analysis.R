
#'
#' Plot human and ToM Agent RPS data
#'


# SETUP ----
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))

library(patchwork)
library(tidyverse)
library(viridis)


load("data_processed/rps_human_trial_data.RData")
load("data_processed/rps_tom_agent_data.RData")


# GLOBALS ----

PLOT_THEME_DEFAULT = theme(
  # text
  plot.title = element_text(size = 24, family = "Avenir", color = "black", margin = margin(b = 0.5, unit = "line")),
  axis.title.y = element_text(size = 24, family = "Avenir", color = "black", margin = margin(r = 0.5, unit = "line")),
  axis.title.x = element_text(size = 24, family = "Avenir", color = "black", margin = margin(t = 0.5, unit = "line")),
  axis.text.y = element_text(size = 18, family = "Avenir", color = "black"),
  axis.text.x = element_text(size = 18, family = "Avenir", color = "black"),
  legend.title = element_text(size = 20, family = "Avenir", color = "black"),
  legend.text = element_text(size = 14, family = "Avenir", color = "black"),
  # backgrounds, lines
  panel.background = element_blank(),
  strip.background = element_blank(),
  panel.grid.major.x = element_blank(),
  panel.grid.minor.x = element_blank(),
  panel.grid.major.y = element_blank(),
  panel.grid.minor.y = element_blank(),
  axis.line = element_line(color = "black"),
  axis.ticks = element_line(color = "black")
)

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

TOM_AGENT_STRATEGY_LOOKUP = list("self_transition_up" = "Self-transition (+)",
                                 "self_transition_down" = "Self-transition (−)",
                                 "opponent_transition_up" = "Opponent-transition (+)",
                                 "opponent_transition_stay" = "Opponent-transition (0)",
                                 "W_stay_L_up_T_down" = "Previous outcome (W0L+T−)",
                                 "W_up_L_down_T_stay" = "Previous outcome (W+L−T0)",
                                 "prev_outcome_prev_transition" = "Previous outcome, \nprevious transition"
                                 )


# ANALYSIS FUNCTIONS ----

# Divide each human subject's trials into blocks of size blocksize (e.g. 10 trials) and calculate win percent in each block
get_subject_block_win_pct = function(data, blocksize) {
  data %>%
    filter(is_bot == 0) %>%
    group_by(bot_strategy, round_index) %>%
    # NB: round_block is 0-indexed
    mutate(round_block = ceiling(round_index / blocksize) - 1) %>%
    select(bot_strategy, round_index, game_id, player_id, player_outcome, round_block) %>%
    group_by(bot_strategy, game_id, player_id, round_block) %>%
    count(win = player_outcome == "win") %>%
    mutate(total = sum(n),
           win_pct = n / total) %>%
    filter(win == TRUE)
}

# Take in subject block win percent (calculated above) and summarize by bot strategy across subjects
get_subject_win_pct_summary = function(subject_block_data) {
  subject_block_data %>%
    group_by(bot_strategy, round_block) %>%
    summarize(subjects = n(),
              mean_win_pct = mean(win_pct),
              se_win_pct = sd(win_pct) / sqrt(subjects))
}

# Divide each ToM Agent's trials into blocks of size blocksize (e.g. 10 trials) and calculate win percent in each block
get_tom_agent_block_win_pct = function(data, blocksize) {
  data %>%
    mutate(round_index = round_index + 1) %>%
    group_by(sequential_agent_class, round_index) %>%
    # NB: round_block is 0-indexed
    mutate(round_block = ceiling(round_index / blocksize) - 1) %>%
    group_by(sequential_agent_class, tom_agent_class, timestamp, round_block) %>%
    count(win = tom_agent_reward == 3) %>%
    mutate(total = sum(n),
           win_pct = n / total) %>%
    filter(win == TRUE)
}

# Take in subject block win percent (calculated above) and summarize by bot strategy across subjects
get_tom_agent_win_pct_summary = function(subject_block_data) {
  subject_block_data %>%
    group_by(sequential_agent_class, round_block) %>%
    summarize(subjects = n(),
              mean_win_pct = mean(win_pct),
              se_win_pct = sd(win_pct) / sqrt(subjects))
}





# FIGURE: Human win percentages overall ----

# Sanity checks
glimpse(human_trial_data_clean)
sum(is.na(human_trial_data_clean$player_outcome))
length(unique(human_trial_data_clean$player_id))
human_trial_data_clean %>%
  group_by(bot_strategy) %>%
  summarize(
    participants = n_distinct(player_id)
  )


human_win_pct = get_subject_block_win_pct(human_trial_data_clean, blocksize = 300)
human_win_pct_summary = get_subject_win_pct_summary(human_win_pct)
human_win_pct_summary = human_win_pct_summary %>%
  rowwise() %>%
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )
# Fig
human_win_pct_fig = human_win_pct_summary %>%
  ggplot(aes(x = bot_strategy_str, y = mean_win_pct, color = bot_strategy_str)) +
  geom_point(size = 6) +
  geom_errorbar(aes(ymin = mean_win_pct - se_win_pct, ymax = mean_win_pct + se_win_pct),
                width = 0, linewidth = 1) +
  geom_hline(yintercept = 1/3, linewidth = 0.75, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 0.9, linewidth = 0.75, linetype = "solid", color = "black") +
  ggtitle("Humans") +
  scale_color_viridis(discrete = TRUE,
                      name = element_blank()) +
  scale_y_continuous(
    name = "win rate",
    breaks = seq(0.0, 1.0, by = 0.25),
    labels = seq(0.0, 1.0, by = 0.25),
    limits = c(0.0, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank(),
    labels = element_blank()
  ) +
  PLOT_THEME_DEFAULT +
  theme(
    # remove X axis text and ticks
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    legend.position = "none",
  )
human_win_pct_fig



# FIGURE: ToM Agent win percentages overall (gpt3.5) ----

# Sanity checks
glimpse(tom_agent_data_clean)
tom_agent_data_clean %>%
  group_by(tom_agent_class, sequential_agent_class) %>%
  summarize(games = n_distinct(timestamp))


tom_agent_data_gpt35 = tom_agent_data_clean %>% filter(tom_agent_class == "gpt35")
tom_agent_win_pct_gpt35 = get_tom_agent_block_win_pct(tom_agent_data_gpt35, blocksize = 300)
tom_agent_win_pct_summary_gpt35 = get_tom_agent_win_pct_summary(tom_agent_win_pct_gpt35)
tom_agent_win_pct_summary_gpt35 = tom_agent_win_pct_summary_gpt35 %>%
  rowwise() %>%
  mutate(
    sequential_agent_str = factor(TOM_AGENT_STRATEGY_LOOKUP[[sequential_agent_class]],
                                  levels = STRATEGY_LABELS)
  )
tom_agent_win_pct_fig_gpt35 = tom_agent_win_pct_summary_gpt35 %>%
  ggplot(aes(x = sequential_agent_str, y = mean_win_pct, color = sequential_agent_str)) +
  geom_point(size = 6) +
  geom_errorbar(aes(ymin = mean_win_pct - se_win_pct, ymax = mean_win_pct + se_win_pct),
                width = 0, linewidth = 1) +
  geom_hline(yintercept = 1/3, linewidth = 0.75, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 0.9, linewidth = 0.75, linetype = "solid", color = "black") +
  ggtitle("ToM agent: GPT3.5") +
  scale_color_viridis(discrete = TRUE,
                      name = element_blank()) +
  scale_y_continuous(
    # name = "win percentage",
    name = element_blank(),
    breaks = seq(0.0, 1.0, by = 0.25),
    labels = c("", "", "", "", ""),
    limits = c(0.0, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank(),
    labels = element_blank()
  ) +
  PLOT_THEME_DEFAULT +
  theme(
    # remove X axis text and ticks
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    legend.position = "none"
  )
tom_agent_win_pct_fig_gpt35


# FIGURE: ToM Agent win percentages overall (gpt4o) ----

tom_agent_data_gpt4 = tom_agent_data_clean %>% filter(tom_agent_class == "gpt4o")
tom_agent_win_pct_gpt4 = get_tom_agent_block_win_pct(tom_agent_data_gpt4, blocksize = 300)
tom_agent_win_pct_summary_gpt4 = get_tom_agent_win_pct_summary(tom_agent_win_pct_gpt4)
tom_agent_win_pct_summary_gpt4 = tom_agent_win_pct_summary_gpt4 %>%
  rowwise() %>%
  mutate(
    sequential_agent_str = factor(TOM_AGENT_STRATEGY_LOOKUP[[sequential_agent_class]],
                                  levels = STRATEGY_LABELS)
  )
tom_agent_win_pct_fig_gpt4 = tom_agent_win_pct_summary_gpt4 %>%
  ggplot(aes(x = sequential_agent_str, y = mean_win_pct, color = sequential_agent_str)) +
  geom_point(size = 6) +
  geom_errorbar(aes(ymin = mean_win_pct - se_win_pct, ymax = mean_win_pct + se_win_pct),
                width = 0, linewidth = 1) +
  geom_hline(yintercept = 1/3, linewidth = 0.75, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 0.9, linewidth = 0.75, linetype = "solid", color = "black") +
  ggtitle("ToM agent: GPT4O") +
  scale_color_viridis(discrete = TRUE,
                      name = element_blank()) +
  scale_y_continuous(
    # name = "win percentage",
    name = element_blank(),
    breaks = seq(0.0, 1.0, by = 0.25),
    labels = c("", "", "", "", ""),
    limits = c(0.0, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank(),
    labels = element_blank()
  ) +
  PLOT_THEME_DEFAULT +
  theme(
    # remove X axis text and ticks
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    # legend.position = "none",
    # Add legend formatting
    legend.position = "right",
    legend.key = element_rect(colour = "transparent", fill = "transparent"),
    legend.spacing.y = unit(0, "lines"),
    legend.key.size = unit(3, "lines")
  )
tom_agent_win_pct_fig_gpt4


# Combine figures
win_pct_combined = human_win_pct_fig + tom_agent_win_pct_fig_gpt35 + tom_agent_win_pct_fig_gpt4
win_pct_combined
ggsave(
  win_pct_combined,
  filename = "win_pct.pdf",
  device = cairo_pdf,
  path = "figures",
  width = 18,
  height = 6,
  dpi = 300
)


# FIGURE: human learning curves ----
human_block_win_pct = get_subject_block_win_pct(human_trial_data_clean, blocksize = 30)
human_block_win_pct_summary = get_subject_win_pct_summary(human_block_win_pct)
human_block_win_pct_summary = human_block_win_pct_summary %>%
  rowwise() %>%
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )
# Fig
block_labels = c("0" = "30", "1" = "60", "2" = "90", "3" = "120", "4" = "150",
                 "5" = "180", "6" = "210", "7" = "240", "8" = "270", "9" = "300")
human_learning_curve_fig = human_block_win_pct_summary %>%
  ggplot(aes(x = round_block, y = mean_win_pct, color = bot_strategy_str)) +
  geom_point(size = 6) +
  geom_errorbar(aes(ymin = mean_win_pct - se_win_pct, ymax = mean_win_pct + se_win_pct), linewidth = 1, width = 0) +
  geom_hline(yintercept = 1/3, linewidth = 0.75, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 0.9, linewidth = 0.75, linetype = "solid", color = "black") +
  ggtitle("Humans") +
  scale_color_viridis(discrete = T,
                      name = "Sequential pattern",
                      labels = function(x) str_wrap(x, width = 24)
  ) +
  scale_x_continuous(
    name = element_blank(),
    labels = block_labels,
    breaks = seq(0, 9)) +
  scale_y_continuous(
    name = "win rate",
    breaks = seq(0.0, 1.0, by = 0.25),
    labels = seq(0.0, 1.0, by = 0.25),
    limits = c(0.0, 1.0)
  ) +
  PLOT_THEME_DEFAULT +
  theme(
    # Make X axis text sideways
    axis.text.x = element_text(size = 14, angle = 45, vjust = 0.5, family = "Avenir", color = "black"),
    legend.position = "none"
    )
human_learning_curve_fig


# FIGURE: ToM Agent learning curves (gpt4o) ----
tom_agent_block_win_pct = get_tom_agent_block_win_pct(tom_agent_data_gpt4, blocksize = 30)
tom_agent_block_win_pct_summary = get_tom_agent_win_pct_summary(tom_agent_block_win_pct)
tom_agent_block_win_pct_summary = tom_agent_block_win_pct_summary %>%
  rowwise() %>%
  mutate(
    sequential_agent_str = factor(TOM_AGENT_STRATEGY_LOOKUP[[sequential_agent_class]],
                                  levels = STRATEGY_LABELS)
  )
# NB: same as identically named variable above
block_labels = c("0" = "30", "1" = "60", "2" = "90", "3" = "120", "4" = "150",
                 "5" = "180", "6" = "210", "7" = "240", "8" = "270", "9" = "300")
tom_agent_learning_curve_fig = tom_agent_block_win_pct_summary %>%
  ggplot(aes(x = round_block, y = mean_win_pct, color = sequential_agent_str)) +
  geom_point(size = 6) +
  geom_errorbar(aes(ymin = mean_win_pct - se_win_pct, ymax = mean_win_pct + se_win_pct), linewidth = 1, width = 0) +
  geom_hline(yintercept = 1/3, linewidth = 0.75, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 0.9, linewidth = 0.75, linetype = "solid", color = "black") +
  ggtitle("ToM Agent (GPT4O)") +
  scale_color_viridis(discrete = T,
                      name = "Sequential pattern",
                      labels = function(x) str_wrap(x, width = 24)
  ) +
  scale_x_continuous(
    name = element_blank(),
    labels = block_labels,
    breaks = seq(0, 9)) +
  scale_y_continuous(
    name = element_blank(),
    breaks = seq(0.0, 1.0, by = 0.25),
    labels = c("", "", "", "", ""),
    limits = c(0.0, 1.0)
  ) +
  PLOT_THEME_DEFAULT +
  theme(
    # Make X axis text sideways
    axis.text.x = element_text(size = 14, angle = 45, vjust = 0.5, family = "Avenir", color = "black"),
    # Add legend formatting
    legend.position = "right",
    legend.key = element_rect(colour = "transparent", fill = "transparent"),
    legend.spacing.y = unit(0, "lines"),
    legend.key.size = unit(3, "lines"))
tom_agent_learning_curve_fig


# Combine figures
learning_curve_combined = human_learning_curve_fig + tom_agent_learning_curve_fig
learning_curve_combined
ggsave(
  learning_curve_combined,
  filename = "learning_curve.pdf",
  device = cairo_pdf,
  path = "figures",
  width = 12,
  height = 6,
  dpi = 300
)




