import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import euclidean_distances
import os

current_dir = os.path.dirname(__file__)
model_file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')
human_file_path = os.path.join(current_dir, '..', 'analysis', 'data_processed', 'rps_human_trial_data_summary.csv')

# Strategy mapping
strategy_mapping = {
    'opponent_prev_move_positive': 'opponent_transition_up',
    'opponent_prev_move_nil': 'opponent_transition_stay',
    'prev_move_positive': 'self_transition_up',
    'prev_move_negative': 'self_transition_down',
    'win_positive_lose_negative': 'W_up_L_down_T_stay',
    'win_nil_lose_positive': 'W_stay_L_up_T_down',
    'outcome_transition_dual_dependency': 'prev_outcome_prev_transition'
}

# Load both datasets
df_models = pd.read_csv(model_file_path)
df_humans = pd.read_csv(human_file_path)

# Map human bot strategies to our current labels
df_humans['sequential_agent_class'] = df_humans['bot_strategy'].map(strategy_mapping)
df_humans['tom_agent_class'] = 'human'  # Add a column to identify human data
df_humans['win_percentage'] = df_humans['win_pct']  # Align column names

# Models configuration
models = ['hm_gpt4o', 'hm_gpt4o_no_hyp', 'react_gpt4o', 'base_llm_gpt4o', 'human']
model_labels = ['Hypothetical Minds', 'No Hypothesis\n Evaluation', 'ReAct', 'Base LLM', 'Human']
x_order = ['self_transition_up', 'self_transition_down', 'opponent_transition_up', 
           'opponent_transition_stay', 'W_stay_L_up_T_down', 'W_up_L_down_T_stay', 
           'prev_outcome_prev_transition']

# Process model data as before
df_models.loc[
    (df_models['tom_agent_class'] == 'hm_gpt4o') & 
    (df_models['tom_agent_num_hypotheses'] == 0), 
    'tom_agent_class'
] = 'hm_gpt4o_no_hyp'

# Filter and combine datasets
df_models = df_models[df_models['tom_agent_class'].isin(models[:-1])]  # Exclude 'human' from models filter
df_models = df_models[~df_models['sequential_agent_class'].str.contains('deterministic')]

# Filter hm_gpt4o hyperparameters
df_models = df_models[
    (~df_models['tom_agent_class'].eq('hm_gpt4o')) | 
    (
        (df_models['tom_agent_class'].eq('hm_gpt4o')) & 
        (df_models['tom_agent_softmax_temp'] == 0.2) & 
        (df_models['tom_agent_num_hypotheses'] == 5)
    )
]

# Convert timestamp to datetime with custom format
df_models['timestamp'] = pd.to_datetime(df_models['timestamp'], format='%Y-%m-%d_%H-%M-%S')

# also filter out only the hm_gpt4o runs before 2025
df_models = df_models[
    (~df_models['tom_agent_class'].eq('hm_gpt4o')) | 
    (
        (df_models['tom_agent_class'].eq('hm_gpt4o')) & 
        (df_models['timestamp'] < '2024-10-01')
    )
]

combination_counts = df_models.groupby(['tom_agent_class', 'sequential_agent_class']).size()

# Print the counts and keep only the latest 3 seeds for each combination
for (tom_agent, sequential_agent), count in combination_counts.items():
    print(f"tom_agent_class: {tom_agent}, sequential_agent_class: {sequential_agent}, count: {count}")
    if count > 3:
        # Get the indices of the latest 3 runs for this combination
        mask = (df_models['tom_agent_class'] == tom_agent) & (df_models['sequential_agent_class'] == sequential_agent)
        indices_to_keep = df_models[mask].sort_values('timestamp', ascending=False).head(3).index

        # Update df_results to keep only the latest 3 runs for this combination
        df_models = df_models[
            ~mask | df_models.index.isin(indices_to_keep)
        ]

# Combine model and human data
df_combined = pd.concat([
    df_models[['tom_agent_class', 'sequential_agent_class', 'win_percentage']],
    df_humans[['tom_agent_class', 'sequential_agent_class', 'win_percentage']]
])

model_order = ['human', 'hm_gpt4o', 'hm_gpt4o_no_hyp', 'react_gpt4o', 'base_llm_gpt4o']

plt.figure(figsize=(12, 6))
sns.barplot(x='sequential_agent_class', y='win_percentage', hue='tom_agent_class', 
           data=df_combined, hue_order=model_order, order=x_order)
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

# Create win rate matrix (models x opponents)
win_rates = []
for model in models:
    model_rates = []
    for opponent in x_order:
        rate = df_combined[
            (df_combined['tom_agent_class'] == model) & 
            (df_combined['sequential_agent_class'] == opponent)
        ]['win_percentage'].mean()
        model_rates.append(rate)
    win_rates.append(model_rates)

win_rates = np.array(win_rates)

# Calculate pairwise L2 distances
distances = euclidean_distances(win_rates)

# Create heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(distances, 
            annot=True, 
            fmt='.3f',
            xticklabels=model_labels,
            yticklabels=model_labels,
            cmap='YlOrRd')

plt.title('L2 Distance Between Model/Human Win Rate Patterns')
plt.tight_layout()
plt.show()

# Create heatmap comparing human win rates to model win rates
plt.figure(figsize=(12, 3))

# Get the human row (last row) compared to all model rows (excluding human)
human_model_distances = distances[-1, :-1]  # Get distances between human and all models
human_model_distances = human_model_distances.reshape(1, -1)  # Reshape to 1 x 4 matrix

# Create heatmap with just the human-to-model comparisons
ax = sns.heatmap(human_model_distances,
                 annot=False,
                 fmt='.3f', 
                 xticklabels=model_labels[:-1],  # Exclude 'Human' from x-axis
                 yticklabels=['Human'],
                 cmap='YlOrRd')
                 #annot_kws={'size': 18, 'color': 'black'})  # Make annotations larger
ax.set_xticklabels(ax.get_xticklabels(), fontsize=14)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=14)
for col_i, val in enumerate(human_model_distances[0]):
    # Coordinates (col_i + 0.5, row_i + 0.5) will center the text in the cell
    # Here row_i=0 because there's only one row
    ax.text(col_i + 0.5, 0.5, f"{val:.3f}",
            ha='center', va='center',
            color='black', fontsize=24)

plt.title(r'$L^2$ Distance Between Human and Model Win Rate Patterns', fontsize=20)
plt.tight_layout()

# After creating your heatmap and storing the Axes in 'ax':
cbar = ax.collections[0].colorbar
# Increase tick label fontsize
cbar.ax.tick_params(labelsize=12)

# Save the plot
plt.savefig(os.path.join(current_dir, 'human_model_correlations_heatmap.png'), 
            bbox_inches='tight', dpi=300)
plt.show()

# Print the actual distances for verification
print("\nL2 distances between human and model performance:")
for model, distance in zip(model_labels[:-1], human_model_distances[0]):
    print(f"{model}: {distance:.3f}")