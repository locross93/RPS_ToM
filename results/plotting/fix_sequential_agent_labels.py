import pandas as pd
import os

# Load both dataframes
current_dir = os.path.dirname(__file__)
rounds_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_all_rounds.csv')
episodes_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

df_rounds = pd.read_csv(rounds_path, low_memory=False)
df_episodes = pd.read_csv(episodes_path, low_memory=False)

print("Initial shapes:")
print("Rounds data:", df_rounds.shape)
print("Episodes data:", df_episodes.shape)

# Check how many NaN values we have in sequential_agent_class
print("\nNaN values in sequential_agent_class:", df_rounds['sequential_agent_class'].isna().sum())

# Create a mapping from timestamp to sequential_agent_class from episodes data
timestamp_to_agent = dict(zip(df_episodes['timestamp'], df_episodes['sequential_agent_class']))

# Fill NaN values in rounds data using the mapping
df_rounds.loc[df_rounds['sequential_agent_class'].isna(), 'sequential_agent_class'] = \
    df_rounds.loc[df_rounds['sequential_agent_class'].isna(), 'timestamp'].map(timestamp_to_agent)

# Check if we fixed the NaNs
print("\nAfter fixing:")
print("NaN values remaining:", df_rounds['sequential_agent_class'].isna().sum())
print("\nUnique sequential_agent_class values:", df_rounds['sequential_agent_class'].unique())

# Save the fixed dataframe
output_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_all_rounds_fixed.csv')
df_rounds.to_csv(output_path, index=False)
print(f"\nSaved fixed data to: {output_path}")

# Print some verification stats
print("\nVerification:")
print("Number of unique timestamps:", len(df_rounds['timestamp'].unique()))
print("Number of unique timestamps in episodes:", len(df_episodes['timestamp'].unique()))
print("\nSample of fixed rows:")
sample_fixed = df_rounds[df_rounds['sequential_agent_class'].notna()].sample(5)
print(sample_fixed[['timestamp', 'sequential_agent_class', 'tom_agent_class']]) 