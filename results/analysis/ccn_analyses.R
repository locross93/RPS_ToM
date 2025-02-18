
#
# Figure generation for CCN 2025
#


# INIT ----
rm(list=ls())
setwd(dirname(rstudioapi::getSourceEditorContext()$path))

library(patchwork)
library(tidyverse)
library(viridis)


load("data_processed/rps_human_trial_data.RData")
glimpse(human_trial_data_clean)


# GLOBALS ----

FIGURE_PATH = 'figures'

STRATEGY_LABELS = c(
  'Self-transition (+)',
  'Self-transition (−)',
  'Opponent-transition (+)',
  'Opponent-transition (0)',
  'Previous outcome \n(W0L+T−)',
  'Previous outcome \n(W+L−T0)',
  'Previous outcome, \nprevious transition'
)

HUMAN_TRIAL_STRATEGY_LOOKUP = list('prev_move_positive' = 'Self-transition (+)',
                                   'prev_move_negative' = 'Self-transition (−)',
                                   'opponent_prev_move_positive' = 'Opponent-transition (+)',
                                   'opponent_prev_move_nil' = 'Opponent-transition (0)',
                                   'win_nil_lose_positive' = 'Previous outcome \n(W0L+T−)',
                                   'win_positive_lose_negative' = 'Previous outcome \n(W+L−T0)',
                                   'outcome_transition_dual_dependency' = 'Previous outcome, \nprevious transition'
)
TOM_AGENT_STRATEGY_LOOKUP = list('self_transition_up' = 'Self-transition (+)',
                                 'self_transition_down' = 'Self-transition (−)',
                                 'opponent_transition_up' = 'Opponent-transition (+)',
                                 'opponent_transition_stay' = 'Opponent-transition (0)',
                                 'W_stay_L_up_T_down' = 'Previous outcome \n(W0L+T−)',
                                 'W_up_L_down_T_stay' = 'Previous outcome \n(W+L−T0)',
                                 'prev_outcome_prev_transition' = 'Previous outcome, \nprevious transition'
)

COLORS = scales::viridis_pal()(length(STRATEGY_LABELS)) # "#440154FF" "#443A83FF" "#31688EFF" "#21908CFF" "#35B779FF" "#8FD744FF" "#FDE725FF"
HUMAN_TRIAL_COLOR_LOOKUP = list('prev_move_positive' = COLORS[1],
                                'prev_move_negative' = COLORS[2],
                                'opponent_prev_move_positive' = COLORS[3],
                                'opponent_prev_move_nil' = COLORS[4],
                                'win_nil_lose_positive' = COLORS[5],
                                'win_positive_lose_negative' = COLORS[6],
                                'outcome_transition_dual_dependency' = COLORS[7]
)



DEFAULT_PLOT_THEME = theme(
  # text
  plot.title = element_text(size = 24, family = 'Avenir', color = 'black', margin = margin(b = 0.5, unit = 'line')),
  axis.title.y = element_text(size = 24, family = 'Avenir', color = 'black', margin = margin(r = 0.5, unit = 'line')),
  axis.title.x = element_text(size = 24, family = 'Avenir', color = 'black', margin = margin(t = 0.5, unit = 'line')),
  axis.text.y = element_text(size = 18, family = 'Avenir', color = 'black'),
  axis.text.x = element_text(size = 18, family = 'Avenir', color = 'black'),
  legend.title = element_text(size = 20, family = 'Avenir', color = 'black'),
  legend.text = element_text(size = 14, family = 'Avenir', color = 'black'),
  # backgrounds, lines
  panel.background = element_blank(),
  strip.background = element_blank(),
  panel.grid.major.x = element_blank(),
  panel.grid.minor.x = element_blank(),
  panel.grid.major.y = element_blank(),
  panel.grid.minor.y = element_blank(),
  axis.line = element_line(color = 'black'),
  axis.ticks = element_line(color = 'black')
)


# FUNCTIONS ----
get_subject_block_win_pct = function(data, blocksize) {
  data |>
    filter(is_bot == 0) |>
    group_by(bot_strategy, round_index) |>
    # NB: round_block is 0-indexed
    mutate(round_block = ceiling(round_index / blocksize) - 1) |>
    select(bot_strategy, round_index, game_id, player_id, player_outcome, round_block) |>
    group_by(bot_strategy, game_id, player_id, round_block) |>
    count(win = player_outcome == "win") |>
    mutate(total = sum(n),
           win_pct = n / total) |>
    filter(win == TRUE) |>
    ungroup()
}



# FIGURE: Human summary ----

# Get overall win rate
human_win_pct = get_subject_block_win_pct(human_trial_data_clean, blocksize = 300)
# Add strategy string factors
human_win_pct = human_win_pct |> rowwise() |>
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )

# Plot: 95% CI
human_win_pct_fig = human_win_pct |>
  ggplot(
    aes(
      x = bot_strategy_str,
      y = win_pct,
      color = bot_strategy_str
    )
  ) +
  stat_summary(
    fun.data = 'mean_cl_boot',
    size = 1.1,
    linewidth = 1,
  ) +
  # chance line
  geom_hline(
    yintercept = 1/3,
    linewidth = 0.75,
    linetype = 'dashed',
    color = 'black'
  ) +
  # noise ceiling
  geom_hline(
    yintercept = 0.9,
    linewidth = 0.75,
    linetype = 'dashed',
    color = 'black'
  ) +
  ggtitle('Human win rate (overall)') +
  scale_y_continuous(
    name = 'win rate',
    breaks = seq(0.25, 1.0, by = 0.25),
    labels = seq(0.25, 1.0, by = 0.25),
    limits = c(0.2, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank(),
    labels = element_blank()
  ) +
  scale_color_viridis(
    discrete = TRUE,
    name = element_blank()
  ) +
  DEFAULT_PLOT_THEME +
  theme(
    # remove X axis text and ticks
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    legend.position = "none",
  )
human_win_pct_fig

# Save figure
ggsave(
  human_win_pct_fig,
  filename = 'human_win_rate.pdf',
  path = FIGURE_PATH,
  device = cairo_pdf,
  width = 8,
  height = 7,
)


# FIGURE: Human learning curves ----

# Get block win rates
human_block_win_pct = get_subject_block_win_pct(human_trial_data_clean, blocksize = 30)

# Add strategy string factors
human_block_win_pct = human_block_win_pct |>
  rowwise() |>
  mutate(
    bot_strategy_str = factor(HUMAN_TRIAL_STRATEGY_LOOKUP[[bot_strategy]],
                              levels = STRATEGY_LABELS)
  )
# Add labels for round indices
block_labels = c('0' = '30', '1' = '60', '2' = '90', '3' = '120', '4' = '150',
                 '5' = '180', '6' = '210', '7' = '240', '8' = '270', '9' = '300')

human_learning_curve_fig = human_block_win_pct |>
  ggplot(
    aes(
      x = round_block,
      y = win_pct,
      color = bot_strategy_str
    )
  ) +
  stat_summary(
    fun.data = 'mean_cl_boot',
    size = 1.1,
    linewidth = 1,
  ) +
  # chance line
  geom_hline(
    yintercept = 1/3,
    linewidth = 0.75,
    linetype = 'dashed',
    color = 'black'
  ) +
  # noise ceiling
  geom_hline(
    yintercept = 0.9,
    linewidth = 0.75,
    linetype = 'dashed',
    color = 'black'
  ) +
  ggtitle('Human learning curves') +
  scale_color_viridis(discrete = T,
                      name = 'Sequential pattern',
                      labels = function(x) str_wrap(x, width = 24)
  ) +
  scale_x_continuous(
    name = element_blank(),
    labels = block_labels,
    breaks = seq(0, 9)) +
  scale_y_continuous(
    # name = 'win rate',
    name = element_blank(),
    breaks = seq(0.25, 1.0, by = 0.25),
    labels = seq(0.25, 1.0, by = 0.25),
    limits = c(0.2, 1.0)
  ) +
  DEFAULT_PLOT_THEME +
  theme(
    # Make X axis text sideways
    axis.text.x = element_text(size = 14, angle = 45, vjust = 0.5, family = 'Avenir', color = 'black'),
    legend.position = 'right'
  )

human_learning_curve_fig
# Save figure
ggsave(
  human_learning_curve_fig,
  filename = 'human_learning_curves.pdf',
  path = FIGURE_PATH,
  device = cairo_pdf,
  width = 8,
  height = 7,
)

# Combine figures
win_rate_combined = human_win_pct_fig + human_learning_curve_fig
win_rate_combined
# Save figure
ggsave(
  win_rate_combined,
  filename = 'human_results_combined.pdf',
  path = FIGURE_PATH,
  device = cairo_pdf,
  width = 14,
  height = 7,
)



# FIGURE: GPT baseline comparisons ----

# Load GPT data
gpt_data = read_csv('../all_models/rps_scores_per_episode.csv')
glimpse(gpt_data)

# Make 'HM ablation' class
# TODO: only 2 seeds of `opponent_transition_stay` here
gpt_data$tom_agent_class[gpt_data$tom_agent_class == 'hm_gpt4o' & gpt_data$tom_agent_num_hypotheses == 0] = 'hm_ablation_gpt4o'

# Sanity check: seeds per agent class / opponent
gpt_data |>
  group_by(tom_agent_class, sequential_agent_class, tom_agent_softmax_temp, tom_agent_num_hypotheses) |>
  summarize(seeds = n()) |>
  print(n = 100)


bot_levels = c(
  'self_transition_up',
  'self_transition_down',
  'opponent_transition_up',
  'opponent_transition_stay',
  'W_stay_L_up_T_down',
  'W_up_L_down_T_stay',
  'prev_outcome_prev_transition'
)

opponent_lookup = c(
  'human' = 'Humans',
  'hm_gpt4o' = 'Hypothetical Minds',
  'hm_ablation_gpt4o' = 'HM Ablation',
  'react_gpt4o' = 'ReAct',
  'base_llm_gpt4o' = 'Base LLM'
)
opponent_levels = c(
  'Humans',
  'Hypothetical Minds',
  'HM Ablation',
  'ReAct',
  'Base LLM'
)

# Keep human colors
color_lookup = c(
  'Self-transition (+)-Humans' = COLORS[1], #'#440154'
  'Self-transition (+)-Hypothetical Minds' = 'black',
  'Self-transition (+)-HM Ablation' = 'darkgray',
  'Self-transition (+)-ReAct' = 'lightgray',
  'Self-transition (+)-Base LLM' = 'white',

  'Self-transition (−)-Humans' = COLORS[2], # '#443a83'
  'Self-transition (−)-Hypothetical Minds' = 'black',
  'Self-transition (−)-HM Ablation' = 'darkgray',
  'Self-transition (−)-ReAct' = 'lightgray',
  'Self-transition (−)-Base LLM' = 'white',

  'Opponent-transition (+)-Humans' = COLORS[3], # '#31688e'
  'Opponent-transition (+)-Hypothetical Minds' = 'black',
  'Opponent-transition (+)-HM Ablation' = 'darkgray',
  'Opponent-transition (+)-ReAct' = 'lightgray',
  'Opponent-transition (+)-Base LLM' = 'white',

  'Opponent-transition (0)-Humans' = COLORS[4], # '#21908c'
  'Opponent-transition (0)-Hypothetical Minds' = 'black',
  'Opponent-transition (0)-HM Ablation' = 'darkgray',
  'Opponent-transition (0)-ReAct' = 'lightgray',
  'Opponent-transition (0)-Base LLM' = 'white',

  'Previous outcome \n(W0L+T−)-Humans' = COLORS[5], # '#35b779'
  'Previous outcome \n(W0L+T−)-Hypothetical Minds' = 'black',
  'Previous outcome \n(W0L+T−)-HM Ablation' = 'darkgray',
  'Previous outcome \n(W0L+T−)-ReAct' = 'lightgray',
  'Previous outcome \n(W0L+T−)-Base LLM' = 'white',

  'Previous outcome \n(W+L−T0)-Humans' = COLORS[6], # '#8fd744'
  'Previous outcome \n(W+L−T0)-Hypothetical Minds' = 'black',
  'Previous outcome \n(W+L−T0)-HM Ablation' = 'darkgray',
  'Previous outcome \n(W+L−T0)-ReAct' = 'lightgray',
  'Previous outcome \n(W+L−T0)-Base LLM' = 'white',

  'Previous outcome, \nprevious transition-Humans' = COLORS[7], # '#fde725'
  'Previous outcome, \nprevious transition-Hypothetical Minds' = 'black',
  'Previous outcome, \nprevious transition-HM Ablation' = 'darkgray',
  'Previous outcome, \nprevious transition-ReAct' = 'lightgray',
  'Previous outcome, \nprevious transition-Base LLM' = 'white'
)

# Merge human and GPT baseline comparisons
human_summary = human_win_pct |>
  group_by(
    bot_strategy_str
  ) |>
  summarize(
    mean_win_rate = mean(win_pct),
    seeds = n(),
    se_win_rate = sd(win_pct) / sqrt(n())
  ) |>
  ungroup() |>
  mutate(
    opponent = 'human'
  )
# Add relevant GPT rows
model_subset = gpt_data |>
  filter(
    # Base LLM and ReAct
    # TODO we end up with 5 seeds of `opponent_transition_stay` here on base LLM
    # TODO we end up with 2 seeds of `opponent_transition_stay` here on HM ablation
    (tom_agent_class %in% c('base_llm_gpt4o', 'react_gpt4o', 'hm_ablation_gpt4o')) |
    # TODO we end up with > 3 seeds on most of the agents here -- use timestamps to restrict?
    (tom_agent_class == 'hm_gpt4o' & tom_agent_num_hypotheses == 5 & sequential_agent_class %in% bot_levels)
  ) |>
  group_by(tom_agent_class, sequential_agent_class) |>
  summarize(
    mean_win_rate = mean(win_percentage),
    seeds = n(),
    se_win_rate = sd(win_percentage) / sqrt(n())
  ) |>
  ungroup() |>
  rename(
    bot_strategy_str = sequential_agent_class,
    opponent = tom_agent_class
  ) |>
  rowwise() |>
  mutate(
    bot_strategy_str = factor(TOM_AGENT_STRATEGY_LOOKUP[[bot_strategy_str]],
                              levels = STRATEGY_LABELS)
  )
# Combine human and model subset data
summary_data = human_summary |>
  bind_rows(
    model_subset
  ) |>
  rowwise() |>
  mutate(
    opponent = factor(opponent_lookup[[opponent]],
                      levels = opponent_levels)
  )


# Figure
baseline_comparison = summary_data |>
  ggplot(
    aes(
      x = bot_strategy_str,
      y = mean_win_rate,
      color = opponent,
      fill = paste(bot_strategy_str, opponent, sep = '-')
    )
  ) +
  geom_bar(
    stat = 'identity',
    position = position_dodge(0.9),
    width = 0.7,
    # alpha = 0.5
  ) +
  geom_errorbar(
    aes(
      ymin = mean_win_rate - se_win_rate,
      ymax = mean_win_rate + se_win_rate,
      color = opponent
      # color = paste(opponent, bot_strategy_str, sep = '-')
    ),
    position = position_dodge(width = 0.9), # NB: needs to match position above
    linewidth = 0.5,
    width = 0,
    # color = 'black'
  ) +
  # chance line
  geom_hline(
    yintercept = 1/3,
    linewidth = 0.5,
    linetype = 'dashed',
    color = 'black'
  ) +
  # noise ceiling
  geom_hline(
    yintercept = 0.9,
    linewidth = 0.5,
    linetype = 'dashed',
    color = 'black'
  ) +
  scale_y_continuous(
    name = 'win rate',
    breaks = seq(0, 1.0, by = 0.25),
    labels = seq(0, 1.0, by = 0.25),
    limits = c(0, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank()
  ) +
  scale_fill_manual(
    values = color_lookup
  ) +
  scale_color_manual(
    values = c('black', 'black', 'black', 'black', 'black')
  ) +
  DEFAULT_PLOT_THEME +
  theme(
    legend.position = 'none',
    axis.text.x = element_text(size = 14),
  )

baseline_comparison
# Save figure
ggsave(
  baseline_comparison,
  filename = 'baseline_comparison_v2.pdf',
  path = FIGURE_PATH,
  device = cairo_pdf,
  width = 20,
  height = 7,
)



# FIGURE: GPT LLM comparisons ----

color_lookup = c(
  'Self-transition (+)-Humans' = COLORS[1], #'#440154'
  'Self-transition (+)-Hypothetical Minds' = 'black',
  'Self-transition (+)-GPT 3.5' = 'gray',
  'Self-transition (+)-Llama 3' = 'white',

  'Self-transition (−)-Humans' = COLORS[2], # '#443a83'
  'Self-transition (−)-Hypothetical Minds' = 'black',
  'Self-transition (−)-GPT 3.5' = 'gray',
  'Self-transition (−)-Llama 3' = 'white',

  'Opponent-transition (+)-Humans' = COLORS[3], # '#31688e'
  'Opponent-transition (+)-Hypothetical Minds' = 'black',
  'Opponent-transition (+)-GPT 3.5' = 'gray',
  'Opponent-transition (+)-Llama 3' = 'white',

  'Opponent-transition (0)-Humans' = COLORS[4], # '#21908c'
  'Opponent-transition (0)-Hypothetical Minds' = 'black',
  'Opponent-transition (0)-GPT 3.5' = 'gray',
  'Opponent-transition (0)-Llama 3' = 'white',

  'Previous outcome \n(W0L+T−)-Humans' = COLORS[5], # '#35b779'
  'Previous outcome \n(W0L+T−)-Hypothetical Minds' = 'black',
  'Previous outcome \n(W0L+T−)-GPT 3.5' = 'gray',
  'Previous outcome \n(W0L+T−)-Llama 3' = 'white',

  'Previous outcome \n(W+L−T0)-Humans' = COLORS[6], # '#8fd744'
  'Previous outcome \n(W+L−T0)-Hypothetical Minds' = 'black',
  'Previous outcome \n(W+L−T0)-GPT 3.5' = 'gray',
  'Previous outcome \n(W+L−T0)-Llama 3' = 'white',

  'Previous outcome, \nprevious transition-Humans' = COLORS[7], # '#fde725'
  'Previous outcome, \nprevious transition-Hypothetical Minds' = 'black',
  'Previous outcome, \nprevious transition-GPT 3.5' = 'gray',
  'Previous outcome, \nprevious transition-Llama 3' = 'white'
)

opponent_lookup = c(
  'human' = 'Humans',
  'hm_gpt4o' = 'Hypothetical Minds',
  'hm_gpt35' = 'GPT 3.5',
  'hm_llama3' = 'Llama 3'
)
opponent_levels = c(
  'Humans',
  'Hypothetical Minds',
  'GPT 3.5',
  'Llama 3'
)

# Add relevant GPT rows
model_subset = gpt_data |>
  filter(
    # GPT3.5
    # TODO we seem to be missing several agent class opponents here
    (tom_agent_class %in% c('hm_gpt35')) |
      # Llama3
      # TODO several of these have > 3 seeds, a couple have only 2
      (tom_agent_class %in% c('hm_llama3') & tom_agent_num_hypotheses == 5) |
      # TODO we end up with > 3 seeds on most of the agents here -- use timestamps to restrict?
      (tom_agent_class == 'hm_gpt4o' & tom_agent_num_hypotheses == 5 & sequential_agent_class %in% bot_levels)
  ) |>
  group_by(tom_agent_class, sequential_agent_class) |>
  summarize(
    mean_win_rate = mean(win_percentage),
    seeds = n(),
    se_win_rate = sd(win_percentage) / sqrt(n())
  ) |>
  ungroup() |>
  rename(
    bot_strategy_str = sequential_agent_class,
    opponent = tom_agent_class
  ) |>
  rowwise() |>
  mutate(
    bot_strategy_str = factor(TOM_AGENT_STRATEGY_LOOKUP[[bot_strategy_str]],
                              levels = STRATEGY_LABELS)
  )
# Combine human and model subset data
summary_data = human_summary |>
  bind_rows(
    model_subset
  ) |>
  rowwise() |>
  mutate(
    opponent = factor(opponent_lookup[[opponent]],
                      levels = opponent_levels)
  )


# Figure
llm_comparison = summary_data |>
  ggplot(
    aes(
      x = bot_strategy_str,
      y = mean_win_rate,
      color = opponent,
      fill = paste(bot_strategy_str, opponent, sep = '-')
    )
  ) +
  geom_bar(
    stat = 'identity',
    position = position_dodge(0.9),
    width = 0.7,
    # alpha = 0.5
  ) +
  geom_errorbar(
    aes(
      ymin = mean_win_rate - se_win_rate,
      ymax = mean_win_rate + se_win_rate,
      color = opponent
      # color = paste(opponent, bot_strategy_str, sep = '-')
    ),
    position = position_dodge(width = 0.9), # NB: needs to match position above
    linewidth = 0.5,
    width = 0,
    # color = 'black'
  ) +
  # chance line
  geom_hline(
    yintercept = 1/3,
    linewidth = 0.5,
    linetype = 'dashed',
    color = 'black'
  ) +
  # noise ceiling
  geom_hline(
    yintercept = 0.9,
    linewidth = 0.5,
    linetype = 'dashed',
    color = 'black'
  ) +
  scale_y_continuous(
    name = 'win rate',
    breaks = seq(0, 1.0, by = 0.25),
    labels = seq(0, 1.0, by = 0.25),
    limits = c(0, 1.0)
  ) +
  scale_x_discrete(
    name = element_blank()
  ) +
  scale_fill_manual(
    values = color_lookup
  ) +
  scale_color_manual(
    values = c('black', 'black', 'black', 'black')
  ) +
  DEFAULT_PLOT_THEME +
  theme(
    legend.position = 'none',
    axis.text.x = element_text(size = 14),
  )

llm_comparison
# Save figure
ggsave(
  llm_comparison,
  filename = 'llm_comparison.pdf',
  path = FIGURE_PATH,
  device = cairo_pdf,
  width = 20,
  height = 7,
)






