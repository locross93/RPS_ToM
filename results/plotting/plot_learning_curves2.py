# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 18:11:17 2025

@author: locro
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import numpy as np

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_all_rounds.csv')

# Load the data
df = pd.read_csv(file_path, low_memory=False)
print("Initial data shape:", df.shape)

# Convert relevant columns to numeric where necessary
numeric_columns = ['tom_agent_num_hypotheses', 'round_index', 
                   'sequential_agent_reward', 'tom_agent_reward']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with missing values in essential columns
df = df.dropna(subset=['tom_agent_class', 'tom_agent_num_hypotheses', 'round_index'])

# Create a 'model_name' column based on agent class and number of hypotheses
def label_model(row):
    if row['tom_agent_class'] == 'gpt4o':
        if row['tom_agent_num_hypotheses'] == 5:
            return 'Hypothetical Minds'
        elif row['tom_agent_num_hypotheses'] == 0:
            return 'No Hypothesis Evaluation'
        elif 'react' in row['tom_agent_class'].lower():
            return 'ReAct'
    elif row['tom_agent_class'] == 'base_llm_gpt4o':
        return 'Base LLM'
    return None

df['model_name'] = df.apply(label_model, axis=1)

# Drop rows where model_name is None (unwanted models)
df = df.dropna(subset=['model_name'])

# Define opponent categories based on sequential agent class
opponent_types = [
    'self_transition_up',
    'self_transition_down',
    'opponent_transition_up',
    'opponent_transition_stay',
    'W_stay_L_up_T_down',
    'W_up_L_down_T_stay',
    'prev_outcome_prev_transition'
]

# Filter only rounds from these known opponent types
df = df[df['sequential_agent_class'].isin(opponent_types)]

# Bin the rounds into 30-round intervals
df['round_bin'] = (df['round_index'] // 30) * 30

# Compute win rate per model, opponent, and round bin
win_rate_summary = df.groupby(['model_name', 'sequential_agent_class', 'round_bin']).agg(
    win_rate=('tom_agent_reward', lambda x: (x > 0).mean())
).reset_index()

# Plotting
import matplotlib.pyplot as plt

plt.figure(figsize=(16, 10))

# Colors for consistency
colors = plt.cm.get_cmap('tab10', len(opponent_types))

for model in win_rate_summary['model_name'].unique():
    print(model)
    plt.figure(figsize=(10, 6))
    for i, opponent in enumerate(opponent_types):
        subset = win_rate_summary[(win_rate_summary['model_name'] == model) & 
                                  (win_rate_summary['sequential_agent_class'] == opponent)]
        plt.plot(subset['round_bin'], subset['win_rate'], label=opponent, color=colors(i))
    
    # Add horizontal line for random performance
    plt.axhline(y=0.33, color='gray', linestyle='--', label='Random (33%)')
    
    plt.title(f'Learning Curve for {model}')
    plt.xlabel('Round (30-round bins)')
    plt.ylabel('Win Rate')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()
