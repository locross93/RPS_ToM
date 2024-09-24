import pandas as pd
import os
import re
import ast
from datetime import datetime

def extract_last_round_hypothesis(log_text):
    # Find the last round (299) interaction
    last_round_match = re.search(r"An interaction with the other player has occurred at round 299,.*?You previously guessed that their policy or strategy is: (\{.*?\}).", log_text, re.DOTALL)
    
    if not last_round_match:
        return None, None, False

    hypothesis_str = last_round_match.group(1)
    
    # Check if it's a good hypothesis
    is_good_hypothesis = "Good hypothesis found:" in log_text.split("round 299,")[-1]
    
    if is_good_hypothesis:
        good_hypothesis_match = re.search(r"Good hypothesis found: (\{.*?\})", log_text.split("round 299,")[-1], re.DOTALL)
        if good_hypothesis_match:
            hypothesis_str = good_hypothesis_match.group(1)

    # Use regex to extract strategy and value
    strategy_match = re.search(r"'Opponent_strategy': '(.*?)'", hypothesis_str)
    value_match = re.search(r"'value': ([\d.]+)", hypothesis_str)

    if strategy_match:
        strategy = strategy_match.group(1)
    else:
        return None, None, False

    if value_match:
        try:
            value = round(float(value_match.group(1)), 3)
        except ValueError:
            value = 0.0
    else:
        value = 0.0

    return strategy, value, is_good_hypothesis

# Load the CSV file
df = pd.read_csv('/Users/locro/Documents/Stanford/RPS_ToM/results/all_models/rps_scores_all_rounds.csv')

# Calculate wins, losses, and ties
df['win'] = df['tom_agent_reward'] == 3
df['loss'] = df['tom_agent_reward'] == -1
df['tie'] = df['tom_agent_reward'] == 0

# Group by bot_strategy (sequential_agent_class), llm (tom_agent_class), and timestamp
grouped_df = df.groupby(['sequential_agent_class', 'tom_agent_class', 'timestamp']).agg(
    total_points=('tom_agent_reward', 'sum'),
    total_win=('win', 'sum'),
    total_loss=('loss', 'sum'),
    total_tie=('tie', 'sum')
).reset_index()

grouped_df['win_pct'] = grouped_df['total_win'] / (grouped_df['total_win'] + grouped_df['total_loss'] + grouped_df['total_tie']) * 100

def process_log_file(timestamp, llm_type):
    base_path = '/Users/locro/Documents/Stanford/RPS_ToM/results/'
    
    if llm_type == 'gpt35':
        log_file_path = f'{base_path}agent_hm_gpt35_{timestamp}/all_output_data.txt'
    else:  # default to gpt4o
        log_file_path = f'{base_path}agent_hm_gpt4o_{timestamp}/all_output_data.txt'
    
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as file:
            log_text = file.read()
        return extract_last_round_hypothesis(log_text)
    return None, None, False

# In the main loop, modify the function call:
for index, row in grouped_df.iterrows():
    timestamp = row['timestamp']
    llm_type = row['tom_agent_class']
    hypothesis, value, is_good_hypothesis = process_log_file(timestamp, llm_type)
    grouped_df.loc[index, 'hypothesis'] = hypothesis
    grouped_df.loc[index, 'hypothesis_value'] = value
    grouped_df.loc[index, 'is_good_hypothesis'] = is_good_hypothesis

# Rename columns for consistency with your desired output
grouped_df = grouped_df.rename(columns={
    'sequential_agent_class': 'bot_strategy',
    'tom_agent_class': 'llm'
})

# Reorder columns to match the desired output
column_order = ['bot_strategy', 'llm', 'total_points', 'total_win', 'total_loss', 'total_tie', 'win_pct', 'hypothesis', 'hypothesis_value', 'is_good_hypothesis', 'timestamp']
grouped_df = grouped_df[column_order]

# Print the resulting DataFrame
print(grouped_df)

# Optionally, save the updated DataFrame to a new CSV file
grouped_df.to_csv('/Users/locro/Documents/Stanford/RPS_ToM/results/all_models/rps_scores_and_hyps.csv', index=False)