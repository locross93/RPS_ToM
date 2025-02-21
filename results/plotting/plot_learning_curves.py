import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Load the data
current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_all_rounds_fixed.csv')
df_results = pd.read_csv(file_path, low_memory=False)

print("Initial data shape:", df_results.shape)

# Let's inspect the hm_gpt4o data
hm_data = df_results[df_results['tom_agent_class'] == 'gpt4o']
print("\nHM_GPT4O data:")
print("Total rows:", len(hm_data))
print("\nUnique num_hypotheses values:", hm_data['tom_agent_num_hypotheses'].unique())
print("Unique softmax_temp values:", hm_data['tom_agent_softmax_temp'].unique())
print("\nValue counts for sequential_agent_class:")
print(hm_data['sequential_agent_class'].value_counts())

# Now filter with the correct values we found
df_filtered = df_results[
    (df_results['tom_agent_class'] == 'gpt4o') &
    (df_results['tom_agent_num_hypotheses'] == 5) &
    (df_results['tom_agent_softmax_temp'] == 0.2) &
    df_results['sequential_agent_class'].notna() &
    ~df_results['sequential_agent_class'].str.contains('deterministic', na=False)
]

print("\nAfter filtering:")
print("Total rows:", len(df_filtered))
print("Unique opponents:", df_filtered['sequential_agent_class'].unique())
print("Number of rounds:", df_filtered['round_index'].max() if len(df_filtered) > 0 else 'No data')

# If we have data, continue with plotting
if len(df_filtered) > 0:
    # Create round bins (0-9, 10-19, etc.)
    df_filtered = df_filtered.copy()  # Create a copy to avoid SettingWithCopyWarning
    df_filtered['round_bin'] = pd.cut(df_filtered['round_index'], 
                                     bins=range(0, 301, 10),
                                     labels=[f'{i}-{i+9}' for i in range(0, 291, 10)])

    # Calculate win rates for each opponent and round bin
    win_rates = []
    for opponent in df_filtered['sequential_agent_class'].unique():
        opponent_data = df_filtered[df_filtered['sequential_agent_class'] == opponent]
        if not opponent_data.empty:
            print(f"\nProcessing opponent: {opponent}")
            print(f"Number of rounds: {len(opponent_data)}")
            
            win_rate_by_bin = opponent_data.groupby('round_bin').apply(
                lambda x: (x['tom_agent_reward'] > 0).mean()
            ).reset_index()
            win_rate_by_bin.columns = ['round_bin', 'win_rate']  # Name the columns
            win_rate_by_bin['opponent'] = opponent
            win_rates.append(win_rate_by_bin)

    if win_rates:
        win_rates_df = pd.concat(win_rates, ignore_index=True)
        print("\nWin rates dataframe:")
        print(win_rates_df.head())

        # Create the plot
        plt.figure(figsize=(15, 6))  # Made figure wider to accommodate more x-ticks
        sns.lineplot(data=win_rates_df, 
                    x='round_bin', 
                    y='win_rate',
                    hue='opponent', 
                    marker='o')

        plt.title('Hypothetical Minds (5 hypotheses) Learning Curves')
        plt.xlabel('Rounds')
        plt.ylabel('Win Rate')
        plt.axhline(y=0.33, color='black', linestyle='--', alpha=0.5, label='Random Performance')
        plt.xticks(rotation=45)
        plt.ylim(0, 1)
        plt.legend(title='Opponent', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        # Save the plot
        plt.savefig(os.path.join(current_dir, 'hm_gpt4o_learning_curves.png'), 
                    bbox_inches='tight', dpi=300)
        plt.show()

        print("\nPlot has been saved as 'hm_gpt4o_learning_curves.png'")
    else:
        print("\nNo data to plot after filtering!")
else:
    print("\nNo data after filtering. Please check the filter criteria.") 