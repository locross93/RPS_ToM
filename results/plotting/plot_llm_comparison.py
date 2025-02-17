import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

# Load the data
df_results = pd.read_csv(file_path)

# Only plot these models
models = ['hm_gpt4o', 'hm_llama3', 'hm_gpt35']
model_labels = ['GPT-4', 'Llama 3', 'GPT-3.5']
model_order = models
x_order = ['self_transition_up', 'self_transition_down', 'opponent_transition_up', 'opponent_transition_stay', 'W_stay_L_up_T_down', 'W_up_L_down_T_stay', 'prev_outcome_prev_transition']

# Filter for our models of interest
df_results = df_results[df_results['tom_agent_class'].isin(models)]

# do not plot the deterministic opponents
df_results = df_results[~df_results['sequential_agent_class'].str.contains('deterministic')]

# filter only runs with default hyperparameters
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

# also filter out only the runs before 2025 only for hm_gpt4o   
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
plt.title('Win Percentage by Sequential Agent and LLM Model')
plt.xlabel('Sequential Agent Class')
plt.ylabel('Win Percentage')
plt.legend(title='LLM Model', labels=model_labels)
plt.xticks(rotation=45)
# add a dashed line at y=0.33 for random performance
plt.axhline(y=0.33, color='black', linestyle='--')
plt.tight_layout()
plt.ylim([0, 1])
plt.show() 