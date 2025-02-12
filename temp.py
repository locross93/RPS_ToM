import pandas as pd

# Process rps_scores_all_rounds.csv
df_rounds = pd.read_csv('results/all_models/rps_scores_all_rounds.csv', low_memory=False)

# Insert new empty columns after tom_agent_class
#df_rounds.insert(df_rounds.columns.get_loc('tom_agent_class') + 1, 'tom_agent_softmax_temp', '')
#df_rounds.insert(df_rounds.columns.get_loc('tom_agent_softmax_temp') + 1, 'tom_agent_num_hypotheses', '')

# Explicitly set the column order using the actual column names from your file
desired_order = [
    'sequential_agent_class', 
    'tom_agent_class',
    'tom_agent_softmax_temp',
    'tom_agent_num_hypotheses',
    'round_index',
    'sequential_agent_move',  # instead of opponent_action
    'tom_agent_move',        # instead of agent_action
    'sequential_agent_reward',
    'tom_agent_reward',
    'timestamp',
    'Unnamed: 0',
    'win',
    'loss',
    'win_percentage',
    'tie',
    'loss_percentage',
    'tie_percentage'
]

# Reorder columns
df_rounds = df_rounds[desired_order]

# Save with the correct order
df_rounds.to_csv('results/all_models/rps_scores_all_rounds.csv', index=False)

print("Added new columns to rps_scores_all_rounds.csv in the correct position!")
