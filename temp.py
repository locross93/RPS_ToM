import pandas as pd

# Process rps_scores_all_rounds.csv
df_rounds = pd.read_csv('results/all_models/rps_scores_all_rounds.csv', low_memory=False)
# Backfill empty values with defaults
df_rounds['tom_agent_softmax_temp'] = df_rounds['tom_agent_softmax_temp'].fillna(0.2)
df_rounds['tom_agent_num_hypotheses'] = df_rounds['tom_agent_num_hypotheses'].fillna(5)
# Save with the correct order
df_rounds.to_csv('results/all_models/rps_scores_all_rounds.csv', index=False)

# Process rps_scores_per_episode.csv
df_episode = pd.read_csv('results/all_models/rps_scores_per_episode.csv', low_memory=False)
# Backfill empty values with defaults
df_episode['tom_agent_softmax_temp'] = df_episode['tom_agent_softmax_temp'].fillna(0.2)
df_episode['tom_agent_num_hypotheses'] = df_episode['tom_agent_num_hypotheses'].fillna(5)
# Save with the correct order
df_episode.to_csv('results/all_models/rps_scores_per_episode.csv', index=False)

print("Backfilled default values for tom_agent_softmax_temp and tom_agent_num_hypotheses in both CSV files!")
