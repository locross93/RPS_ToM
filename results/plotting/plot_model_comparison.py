# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 15:31:08 2025

@author: locro
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

current_dir = os.path.dirname(__file__)  # Directory of the current script
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

# Load the data
df_results = pd.read_csv(file_path)

# Only plot these models
models = ['hm_gpt4o', 'hm_gpt4o_no_hyp', 'react_gpt4o', 'base_llm_gpt4o']
model_labels = ['Hypothetical Minds', 'No Hypothesis Evaluation', 'ReAct', 'Base LLM']
model_order = models
x_order = ['self_transition_up', 'self_transition_down', 'opponent_transition_up', 'opponent_transition_stay', 'W_stay_L_up_T_down', 'W_up_L_down_T_stay', 'prev_outcome_prev_transition']

# First, create a new column for the no hypothesis variant
df_results.loc[
    (df_results['tom_agent_class'] == 'hm_gpt4o') & 
    (df_results['tom_agent_num_hypotheses'] == 0), 
    'tom_agent_class'
] = 'hm_gpt4o_no_hyp'

# Filter for our models of interest
df_results = df_results[df_results['tom_agent_class'].isin(models)]

# do not plot the deterministic opponents
df_results = df_results[~df_results['sequential_agent_class'].str.contains('deterministic')]

# filter only hm_gpt4o runs with default hyperparameters, keep other models as is
softmax_threshold = 0.2
num_hypotheses = 5
df_results = df_results[
    (~df_results['tom_agent_class'].eq('hm_gpt4o')) | 
    (
        (df_results['tom_agent_class'].eq('hm_gpt4o')) & 
        (df_results['tom_agent_softmax_temp'] == softmax_threshold) & 
        (df_results['tom_agent_num_hypotheses'] == num_hypotheses)
    )
]

# Convert timestamp to datetime with custom format
df_results['timestamp'] = pd.to_datetime(df_results['timestamp'], format='%Y-%m-%d_%H-%M-%S')

# also filter out only the hm_gpt4o runs before 2025
df_results = df_results[
    (~df_results['tom_agent_class'].eq('hm_gpt4o')) | 
    (
        (df_results['tom_agent_class'].eq('hm_gpt4o')) & 
        (df_results['timestamp'] < '2024-10-01')
    )
]

combination_counts = df_results.groupby(['tom_agent_class', 'sequential_agent_class']).size()

# Print the counts and keep only the latest 3 seeds for each combination
for (tom_agent, sequential_agent), count in combination_counts.items():
    print(f"tom_agent_class: {tom_agent}, sequential_agent_class: {sequential_agent}, count: {count}")
    if count > 3:
        # Get the indices of the latest 3 runs for this combination
        mask = (df_results['tom_agent_class'] == tom_agent) & (df_results['sequential_agent_class'] == sequential_agent)
        indices_to_keep = df_results[mask].sort_values('timestamp', ascending=False).head(3).index
        
        # Update df_results to keep only the latest 3 runs for this combination
        df_results = df_results[
            ~mask | df_results.index.isin(indices_to_keep)
        ]

plt.figure(figsize=(12, 6))
sns.barplot(x='sequential_agent_class', y='win_percentage', hue='tom_agent_class', 
           data=df_results, hue_order=model_order, order=x_order)
plt.title('Win Percentage by Sequential Agent and TOM Agent Classes')
plt.xlabel('Sequential Agent Class')
plt.ylabel('Win Percentage')
plt.legend(title='TOM Agent Class', labels=model_labels)
plt.xticks(rotation=45)
# add a dashed line at y=0.33 for random performance
plt.axhline(y=0.33, color='black', linestyle='--')
plt.tight_layout()
plt.ylim([0, 1])
plt.show()