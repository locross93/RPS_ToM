# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 08:24:45 2024

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
        
        # Extract llm_type and seed from the filename
        llm_type_parts = filename.split('_')
        llm_type = '_'.join(llm_type_parts[:-3])  # Everything before 'rps_scores'
        seed = int(llm_type_parts[-1].split('.')[0])  # Last part before the file extension
        
        # Add columns for llm_type and seed
        df['llm_type'] = llm_type
        df['seed'] = seed
        
        # Append the DataFrame to the list
        dataframes.append(df)

# Combine all the DataFrames into one
combined_df = pd.concat(dataframes, ignore_index=True)

# Calculate the win percentage for each entry
combined_df['win'] = combined_df['tom_agent_reward'] == 3
combined_df['loss'] = combined_df['tom_agent_reward'] == -1

# Group by llm_type and seed to calculate win percentages
grouped_df = combined_df.groupby(['llm_type', 'seed']).agg(
    total_wins=('win', 'sum'),
    total_losses=('loss', 'sum')
).reset_index()

grouped_df['win_percentage'] = grouped_df['total_wins'] / (grouped_df['total_wins'] + grouped_df['total_losses']) * 100

# Calculate the average win percentage and SEM across seeds for each llm_type
avg_win_percentage = grouped_df.groupby('llm_type').agg(
    mean_win_percentage=('win_percentage', 'mean'),
    sem_win_percentage=('win_percentage', sem)
).reset_index()

# Create the bar graph using Seaborn
plt.figure(figsize=(10, 6))
sns.barplot(x='llm_type', y='mean_win_percentage', data=avg_win_percentage, ci=None)
sns.despine(top=True, right=True)
plt.errorbar(x=avg_win_percentage['llm_type'], y=avg_win_percentage['mean_win_percentage'], 
             yerr=avg_win_percentage['sem_win_percentage'], fmt='none', c='black', capsize=5)
plt.title('Average Win Percentage by LLM Type in Rock Paper Scissors', fontsize=18)
plt.xlabel('LLM Type', fontsize=20)
plt.ylabel('Average Win Percentage (%)', fontsize=20)
plt.ylim(0, 100)  # Set the y-axis limit from 0 to 100 for percentage scale
plt.show()

# Define a function to calculate win percentage in 30-round increments
def calculate_win_percentage_by_round(df, increment=30):
    # Initialize a list to hold the results
    results = []
    
    # Loop through the DataFrame in 30-round increments
    for start in range(0, df['round_index'].max(), increment):
        end = start + increment
        # Filter the DataFrame for the current round range
        round_df = df[(df['round_index'] >= start) & (df['round_index'] < end)]
        
        # Calculate the win percentage for each llm_type
        win_percentage = round_df.groupby('llm_type')['tom_agent_reward'].apply(
            lambda x: (x == 3).sum() / ((x == 3).sum() + (x == -1).sum()) * 100).reset_index()
        
        # Calculate the SEM
        win_percentage['SEM'] = round_df.groupby('llm_type')['tom_agent_reward'].apply(
            lambda x: sem((x == 3).sum() / ((x == 3).sum() + (x == -1).sum()) * 100))
        
        # Add the round range to the DataFrame
        win_percentage['Round'] = f'{start + 1}-{end}'
        
        # Append the results to the list
        results.append(win_percentage)
    
    return pd.concat(results, ignore_index=True)

# Apply the function to calculate the average win percentages, SEMs, and round labels
plot_df = calculate_win_percentage_by_round(combined_df)

# Create the scatter plot using Seaborn with hue for llm_type
plt.figure(figsize=(10, 6))
sns.scatterplot(data=plot_df, x='Round', y='tom_agent_reward', hue='llm_type', s=100)
plt.errorbar(x=plot_df['Round'], y=plot_df['tom_agent_reward'], yerr=plot_df['SEM'], fmt='none', capsize=5, color='black')
plt.title('Average Win Percentage by Round (30-round increments) with LLM Type')
plt.xlabel('Round Range')
plt.ylabel('Average Win Percentage (%)')
plt.xticks(rotation=45)
plt.ylim(0, 100)
plt.tight_layout()
plt.legend(title='LLM Type')
plt.show()