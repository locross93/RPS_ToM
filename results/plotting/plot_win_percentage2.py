# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 13:58:26 2024

@author: locro
"""

import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import sem

# Define the directory containing the CSV files
directory = '/Users/locro/Documents/Stanford/RPS_ToM/results/all_models'

# Initialize an empty list to store the DataFrames
dataframes = []

# Iterate over each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # Load the CSV file into a DataFrame
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        
        # Extract llm_type, bot_type, and seed from the filename
        parts = filename.split('_')
        llm_type = parts[0] + '_' + parts[1]  # e.g., 'gpt_4o'
        bot_type = '_'.join(parts[2:-3])  # e.g., 'self_transition_up'
        seed = int(parts[-1].split('.')[0])  # Last part before the file extension
        datetime = parts[-3]  # Second to last part
        breakpoint()
        
        # Add columns for llm_type, bot_type, and seed
        df['llm_type'] = llm_type
        df['bot_type'] = bot_type
        df['seed'] = seed
        
        # Append the DataFrame to the list
        dataframes.append(df)

# Combine all the DataFrames into one
combined_df = pd.concat(dataframes, ignore_index=True)

# Filter for only 'gpt_4o' models
gpt_4o_df = combined_df[combined_df['llm_type'] == 'gpt_4o']

# Calculate the win percentage for each entry
gpt_4o_df['win'] = gpt_4o_df['tom_agent_reward'] == 3
gpt_4o_df['loss'] = gpt_4o_df['tom_agent_reward'] == -1

# Group by bot_type and seed to calculate win percentages
grouped_df = gpt_4o_df.groupby(['bot_type', 'seed']).agg(
    total_wins=('win', 'sum'),
    total_losses=('loss', 'sum')
).reset_index()

grouped_df['win_percentage'] = grouped_df['total_wins'] / (grouped_df['total_wins'] + grouped_df['total_losses']) * 100

# Calculate the average win percentage and SEM across seeds for each bot_type
avg_win_percentage = grouped_df.groupby('bot_type').agg(
    mean_win_percentage=('win_percentage', 'mean'),
    sem_win_percentage=('win_percentage', sem)
).reset_index()

# Create the bar graph using Seaborn
plt.figure(figsize=(12, 6))
sns.barplot(x='bot_type', y='mean_win_percentage', data=avg_win_percentage, ci=None)
sns.despine(top=True, right=True)
plt.errorbar(x=range(len(avg_win_percentage)), y=avg_win_percentage['mean_win_percentage'], 
             yerr=avg_win_percentage['sem_win_percentage'], fmt='none', c='black', capsize=5)
plt.title('Average Win Percentage by Bot Type for GPT-4O in Rock Paper Scissors', fontsize=16)
plt.xlabel('Bot Type', fontsize=14)
plt.ylabel('Average Win Percentage (%)', fontsize=14)
plt.ylim(0, 100)  # Set the y-axis limit from 0 to 100 for percentage scale
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Print the results
print(avg_win_percentage)