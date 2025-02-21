import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

current_dir = os.path.dirname(__file__)  # Directory of the current script
file_path = os.path.join(current_dir, '..', 'all_models', 'rps_scores_per_episode.csv')

# Load the data
df_results = pd.read_csv(file_path)

# Filter for gpt4o ToM agents only
df_results = df_results[df_results['tom_agent_class'] == 'hm_gpt4o']
df_results = df_results[~df_results['sequential_agent_class'].str.contains('deterministic')]

# Create the bar plot
plt.figure(figsize=(12, 6))
sns.barplot(x='sequential_agent_class', y='win_percentage', hue='tom_agent_num_hypotheses', data=df_results)
plt.title('Win Percentage by Sequential Agent and Number of Hypotheses (GPT-4)')
plt.xlabel('Sequential Agent Class')
plt.ylabel('Win Percentage')
plt.legend(title='Number of Hypotheses')
plt.xticks(rotation=90)
plt.tight_layout()
plt.ylim([0, 1])
plt.show()

# Print the counts for verification
combination_counts = df_results.groupby(['tom_agent_num_hypotheses', 'sequential_agent_class']).size()

# Print the counts
for (num_hypotheses, sequential_agent), count in combination_counts.items():
    print(f"Number of hypotheses: {num_hypotheses}, sequential_agent_class: {sequential_agent}, count: {count}")