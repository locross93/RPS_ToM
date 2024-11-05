# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 15:55:11 2024

@author: locro
"""

import pandas as pd
import os
import numpy as np

# Define file paths
current_dir = os.path.dirname(__file__)  # Directory of the current script
all_rounds_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_all_rounds.csv')
per_episode_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

# Load the 300-round results and per-episode data
gpt_4o_df = pd.read_csv(all_rounds_path)
df_per_episode = pd.read_csv(per_episode_path)

# Calculate win, loss, and tie for each round
gpt_4o_df['win'] = gpt_4o_df['tom_agent_reward'] == 3
gpt_4o_df['loss'] = gpt_4o_df['tom_agent_reward'] == -1
gpt_4o_df['tie'] = gpt_4o_df['tom_agent_reward'] == 0

# Group by agent class, tom_agent_class, and timestamp to get per-episode stats
grouped_df = gpt_4o_df.groupby(['sequential_agent_class', 'tom_agent_class', 'timestamp']).agg(
    total_wins=('win', 'sum'),
    total_losses=('loss', 'sum'),
    total_ties=('tie', 'sum')
).reset_index()

# Calculate win, loss, and tie percentages
grouped_df['win_percentage'] = grouped_df['total_wins'] / (grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties'])
grouped_df['loss_percentage'] = grouped_df['total_losses'] / (grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties'])
grouped_df['tie_percentage'] = grouped_df['total_ties'] / (grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties'])

# Filter for sessions with exactly 300 rounds
grouped_df['num_rounds'] = grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties']
grouped_df = grouped_df[grouped_df['num_rounds'] == 300].drop(columns='num_rounds')

# Add remaining columns to match df_per_episode structure
grouped_df['seed'] = np.nan  # Placeholder for missing seed data
grouped_df['total_cost'] = np.nan  # Placeholder for missing total cost data

# Ensure columns are in the correct order to match df_per_episode
grouped_df = grouped_df[['sequential_agent_class', 'tom_agent_class', 'timestamp', 'total_wins', 'total_losses', 
                         'win_percentage', 'total_ties', 'loss_percentage', 'tie_percentage', 'seed', 'total_cost']]

# Remove any existing entries in df_per_episode with the same timestamp and tom_agent_class
df_per_episode = df_per_episode[~df_per_episode.set_index(['timestamp', 'tom_agent_class']).index.isin(
    grouped_df.set_index(['timestamp', 'tom_agent_class']).index
)]

# Append to the per-episode DataFrame
df_per_episode = pd.concat([df_per_episode, grouped_df], ignore_index=True)

# Save the updated per-episode results back to the CSV
df_per_episode.to_csv(per_episode_path, index=False)

print("Updated per-episode results saved to:", per_episode_path)

