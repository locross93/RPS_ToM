# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 10:37:00 2024

@author: locro
"""

import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import sem

# Define the directory containing the CSV files
directory = '/Users/locro/Documents/Stanford/RPS_ToM/results/all_models'

# load rps_scores_all_rounds.csv
df = pd.read_csv(f'{directory}/rps_scores_all_rounds.csv')

# Filter for only 'gpt_4o' models
gpt_4o_df = df[df['tom_agent_class'] == 'gpt4o']

# Calculate the win percentage for each entry
gpt_4o_df['win'] = gpt_4o_df['tom_agent_reward'] == 3
gpt_4o_df['loss'] = gpt_4o_df['tom_agent_reward'] == -1
gpt_4o_df['tie'] = gpt_4o_df['tom_agent_reward'] == 0

# Group by bot_type and seed to calculate win percentages
grouped_df = gpt_4o_df.groupby(['sequential_agent_class', 'timestamp']).agg(
    total_wins=('win', 'sum'),
    total_losses=('loss', 'sum'),
    total_ties=('tie', 'sum')
).reset_index()

grouped_df['win_percentage'] = grouped_df['total_wins'] / (grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties']) * 100
grouped_df['num_rounds'] = grouped_df['total_wins'] + grouped_df['total_losses'] + grouped_df['total_ties']
# exclude rows that do not have 300 rounds
grouped_df = grouped_df[grouped_df['num_rounds'] == 300]

# Calculate the average win percentage and SEM across seeds for each bot_type
avg_win_percentage = grouped_df.groupby('sequential_agent_class').agg(
    mean_win_percentage=('win_percentage', 'mean'),
    sem_win_percentage=('win_percentage', sem)
).reset_index()

# Create the bar graph using Seaborn
plt.figure(figsize=(12, 6))
sns.barplot(x='sequential_agent_class', y='mean_win_percentage', data=avg_win_percentage, errorbar=None)
sns.despine(top=True, right=True)
plt.errorbar(x=range(len(avg_win_percentage)), y=avg_win_percentage['mean_win_percentage'], 
             yerr=avg_win_percentage['sem_win_percentage'], fmt='none', c='black', capsize=5)
plt.title('Average Win Percentage by Bot Type for GPT-4o in Rock Paper Scissors', fontsize=16)
plt.xlabel('Bot Type', fontsize=14)
plt.ylabel('Average Win Percentage (%)', fontsize=14)
plt.ylim(0, 100)  # Set the y-axis limit from 0 to 100 for percentage scale
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()